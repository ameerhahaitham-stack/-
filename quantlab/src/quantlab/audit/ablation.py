"""Task 1: ablation of the production control sampler (which component makes p_prod optimistic?). SYNTHETIC ONLY."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..calibration import H4, dedupe_mask
from ..engine import atr, strata_labels
from ..events import eligible
from . import sampler as S
from .events_null import gen_G
from .synth import make_series

# name: (strata mode, gap, order, retry)
CONFIGS = {
    "indep":            ("none", 0, "random", True),     # independent draws from the whole window (the pre-round-2 control)
    "norepeat":         ("none", 1, "random", True),
    "gap5_rand":        ("none", 5, "random", True),
    "gap5_time":        ("none", 5, "time", True),
    "gap5_perdraw":     ("none", 5, "perdraw", True),
    "strata_only":      ("full", 0, "random", True),     # strata matching without any non-overlap rule
    "strata_norepeat":  ("full", 1, "random", True),
    "hour_gap5":        ("hour", 5, "random", True),
    "vol_gap5":         ("vol", 5, "random", True),
    "year_gap5":        ("year", 5, "random", True),
    "PROD":             ("full", 5, "random", True),     # = production
    "prod_time":        ("full", 5, "time", True),
    "prod_reverse":     ("full", 5, "reverse", True),
    "prod_perdraw":     ("full", 5, "perdraw", True),
    "prod_noretry":     ("full", 5, "random", False),
}


# configs that replace the production sampler by an EXACT law (positive controls): UNIF = uniform over all gap-feasible k-subsets of the window
# (bijection y_i = x_i - (i-1)(gap-1) of the sorted positions onto an ordinary k-subset), Gk = the null event process G conditioned on k.
EXTRA = ("UNIF_window", "UNIF_domain", "PROD_domain", "Gk")


def uniform_feasible(rng, n, w0, w1, k, gap):
    """Exact uniform draw of n sorted k-subsets of [w0, w1] with all gaps >= gap."""
    M = (w1 - w0 + 1) - (k - 1) * (gap - 1)
    y = np.sort(np.argpartition(rng.random((n, M)), k - 1, axis=1)[:, :k], axis=1)
    return w0 + y + np.arange(k)[None, :] * (gap - 1)


def g_given_k(rng, n, lo, hi, n_raw, gap, k, batch=20000):
    out = []
    while sum(len(o) for o in out) < n:
        x = np.sort(rng.integers(lo, hi, size=(batch, n_raw)), axis=1)
        m = dedupe_mask(x, gap)
        good = m.sum(axis=1) == k
        if good.any():
            out.append(x[good][m[good]].reshape(-1, k))
    return np.vstack(out)[:n]


@dataclass(frozen=True)
class AblCfg:
    name: str = "phi0.8"
    phi: float = 0.8
    sv: tuple | None = None
    start: str = "2018-01-01"
    hl: str = "unit"
    n_bars: int = 1600
    sigma: float = 3.0
    n_raw: int = 140
    horizon: int = 5
    n_draws: int = 2000
    r_ref: int = 2000
    gap: int = 5
    series_seed0: int = 700_000
    event_seed0: int = 7_000_000
    ctrl_seed0: int = 9_000_000


def ablation_study(cfg: AblCfg, k: int, which: str = "main") -> list[dict]:
    df = make_series(cfg.n_bars, cfg.phi, cfg.series_seed0 + k, cfg.sigma, cfg.sv, cfg.start, hl=cfg.hl)
    t = pd.to_datetime(df["time"])
    o, c, a = df["open"].to_numpy(float), df["close"].to_numpy(float), atr(df, 14)
    h = cfg.horizon
    el = eligible(df, h, t.iloc[0], t.iloc[-1] + H4, H4, a)
    window = np.where(el)[0]
    raw = np.full(len(df), np.nan)
    raw[window] = (c[window + h] - o[window + 1]) / a[window]
    lo, hi = 60, cfg.n_bars - 50
    idx = gen_G(np.random.default_rng(cfg.event_seed0 + k), lo, hi, cfg.n_raw, cfg.gap)
    idx = idx[el[idx]]
    kk = len(idx)
    obs = float(raw[idx].mean())
    K_obs = float(S.cov_index(idx[None, :], cfg.phi)[0])
    cp_obs = int(S.close_pairs(idx[None, :], 7)[0])
    strata = strata_labels(df)
    rows = []
    # exact G reference (same unconditional law as the events)
    rr = np.random.default_rng(cfg.ctrl_seed0 + k)
    x = np.sort(rr.integers(lo, hi, size=(cfg.r_ref, cfg.n_raw)), axis=1)
    m = dedupe_mask(x, cfg.gap)
    xe = np.where(el[x], raw[x], 0.0)
    ok_e = m & el[x]
    Mg = (np.where(ok_e, xe, 0.0).sum(axis=1)) / ok_e.sum(axis=1)
    rows.append(_row(k, "G_exact", obs, Mg, K_obs, None, cp_obs, None, 1.0, kk))
    if which == "extra":
        rg = np.random.default_rng(cfg.ctrl_seed0 + 20_000_000 + k)
        dom = window[(window >= lo) & (window < hi)]                 # the support of G (events never occur in the first 60 / last 50 bars)
        for name in EXTRA:
            if name == "UNIF_window":
                Pk = uniform_feasible(rg, cfg.n_draws, int(window[0]), int(window[-1]), kk, cfg.gap)
            elif name == "UNIF_domain":
                Pk = uniform_feasible(rg, cfg.n_draws, int(dom[0]), int(dom[-1]), kk, cfg.gap)
            elif name == "PROD_domain":                                  # production sampler (full strata, RSA) restricted to G's support
                pf = S.pool_function(df, dom, "full", strata=strata)
                Pp, att, kept, _ = S.control_draws([pf(i) for i in idx], cfg.n_draws, len(df), cfg.gap, rg, "random", True)
                Pk = np.sort(Pp, axis=1)
            else:
                Pk = g_given_k(rg, cfg.n_draws, lo, hi, cfg.n_raw, cfg.gap, kk)
            Mc = raw[Pk].mean(axis=1)
            rows.append(_row(k, name, obs, Mc, K_obs, S.cov_index(Pk, cfg.phi), cp_obs, S.close_pairs(Pk, 7), 1.0, kk))
        return rows
    for name, (mode, gap, order, retry) in CONFIGS.items():
        pf = S.pool_function(df, window, mode, strata=strata)
        pools = [pf(i) for i in idx]
        rng = np.random.default_rng(cfg.ctrl_seed0 + 10_000_000 + k)
        P, att, kept, ok = S.control_draws(pools, cfg.n_draws, len(df), gap, rng, order, retry)
        if len(P) == 0:
            continue
        if not retry:                                 # keep dead-end draws: unplaced events (-1) are dropped from the mean
            val = np.where(P >= 0, raw[np.clip(P, 0, None)], np.nan)
            Mc = np.nanmean(val, axis=1)
            Ps = np.sort(np.where(P >= 0, P, 10**6), axis=1)
            Pk = Ps[:, :kk]
        else:
            Mc = raw[P].mean(axis=1)
            Pk = np.sort(P, axis=1)
        Kc = S.cov_index(Pk, cfg.phi)
        cpc = S.close_pairs(Pk, 7)
        rows.append(_row(k, name, obs, Mc, K_obs, Kc, cp_obs, cpc, kept / max(att, 1), kk))
    return rows


def _row(k, name, obs, M, K_obs, Kc, cp_obs, cpc, succ, kk):
    n = len(M)
    d = {"k": k, "config": name, "n_events": kk, "obs": obs, "mean_c": float(M.mean()), "sd_c": float(M.std(ddof=1)),
         "p": (1 + int((M >= obs).sum())) / (1 + n), "n_c": n, "success": succ, "K_obs": K_obs, "cp7_obs": cp_obs}
    d["K_mean"] = float(Kc.mean()) if Kc is not None else float("nan")
    d["K_sd"] = float(Kc.std(ddof=1)) if Kc is not None else float("nan")
    d["cp7_mean"] = float(cpc.mean()) if cpc is not None else float("nan")
    d["cp7_sd"] = float(cpc.std(ddof=1)) if cpc is not None else float("nan")
    return d
