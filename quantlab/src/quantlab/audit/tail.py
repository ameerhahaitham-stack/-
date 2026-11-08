"""Tasks 2-3: tail calibration of the production event-study p-value under several NULL event processes (synthetic only).

Modes (how the observed event set is generated; always independent of the returns => the null is TRUE):
  G : calibration's G (iid uniform bars, sorted, greedy de-dup)  -> comparable with docs/calibration_raw/tail_phi*.csv (same seeds)
  S : matched null: observed event set = ONE draw of the production control sampler for the template of a G draw
      (obs and controls are i.i.d. from the same conditional law given the template => exchangeable by construction)
  C : clustered events (Neyman-Scott bursts)       R : quasi-regular events (time-of-day-like rule)
Per study: p_prod (production event_study, production defaults), p_ref (exact G-reference, mode G only), p_shift (circular-shift
reference over the evaluation window; audit candidate, resolution 1/(L-1))."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..calibration import H4, ar_series, draw_sets
from ..engine import atr
from ..events import _place_chunk, eligible, event_study
from . import sampler as S
from .events_null import gen_G, gen_clustered, gen_regular

DEFAULT_SEEDS = {"G": 100_000, "S": 400_000, "C": 500_000, "R": 600_000, "W": 900_000}


@dataclass(frozen=True)
class TailAudit:
    phi: float = 0.8
    mode: str = "G"
    n_bars: int = 1600
    sigma: float = 3.0
    n_raw_events: int = 140
    horizon: int = 5
    n_ctrl_primary: int = 20000
    refine_below: float = 0.005
    n_ctrl_refine: int = 200000
    r_ref: int = 20000
    n_pre: int = 2000                 # tiered evaluation: cheap pre-screen draws (a study whose pre-screen p > pre_cut cannot reach p <= 0.01)
    pre_cut: float = 0.02
    n_full: int = 0                   # studies k < k0 + n_full always get the full production p (for the 0.10 / 0.05 levels)
    k_full0: int = 0
    min_gap: int = 5
    series_seed0: int = -1
    event_seed0: int = 3_000_000
    ref_seed0: int = 5_000_000
    obs_seed0: int = 6_000_000

    def sseed(self) -> int:
        if self.series_seed0 >= 0:
            return self.series_seed0
        if self.mode == "G" and abs(self.phi - 0.95) < 1e-9:
            return 200_000                    # the earlier phi=0.95 tail study (docs/calibration_raw/tail_phi0.95.csv) used series seed 200000+k
        return DEFAULT_SEEDS[self.mode]


def shift_p(raw, idx, w0, w1, obs, R, rng):
    L = w1 - w0 + 1
    s = rng.integers(1, L, size=R)
    pos = (idx[None, :] - w0 + s[:, None]) % L + w0
    m = raw[pos].mean(axis=1)
    return (1 + int((m >= obs).sum())) / (1 + R)


def shift_p_exact(raw, idx, w0, w1, obs):
    """Exact circular-shift permutation p: all L-1 non-trivial cyclic shifts of the event configuration over the eligible window."""
    L = w1 - w0 + 1
    s = np.arange(1, L)
    pos = (idx[None, :] - w0 + s[:, None]) % L + w0
    m = raw[pos].mean(axis=1)
    return (1 + int((m >= obs).sum())) / (1 + len(s))


def make_study(cfg: TailAudit, k: int):
    """Series, eligibility, forward-move field and the observed (null) event set of study k. Shared by the production-path and BC-reference runners."""
    s0 = cfg.sseed()
    df = ar_series(cfg.n_bars, cfg.phi, s0 + k, cfg.sigma)
    t = pd.to_datetime(df["time"])
    o, c, a = df["open"].to_numpy(float), df["close"].to_numpy(float), atr(df, 14)
    h, lo, hi = cfg.horizon, 60, cfg.n_bars - 50
    el = eligible(df, h, t.iloc[0], t.iloc[-1] + H4, H4, a)
    window = np.where(el)[0]
    raw = np.full(len(df), np.nan)
    raw[window] = (c[window + h] - o[window + 1]) / a[window]
    rg = np.random.default_rng(cfg.event_seed0 + k)
    fb, preserved = 0, True
    if cfg.mode == "G":
        x0, m0 = draw_sets(rg, 1, lo, hi, cfg.n_raw_events, cfg.min_gap)
        idx = x0[0][m0[0]]
    elif cfg.mode == "W":                          # G on the WHOLE eligible window: removes the synthetic support mismatch (events only in [60, n-50))
        lo, hi = int(window[0]), int(window[-1]) + 1
        x0, m0 = draw_sets(rg, 1, lo, hi, cfg.n_raw_events, cfg.min_gap)
        idx = x0[0][m0[0]]
    elif cfg.mode == "S":
        idxT = gen_G(rg, lo, hi, cfg.n_raw_events, cfg.min_gap)
        pf = S.pool_function(df, window, "full")
        pools = [pf(i) for i in idxT]
        fb = int(sum(len(p) == len(window) for p in pools))
        ro = np.random.default_rng(cfg.obs_seed0 + k)
        for _ in range(100):
            P, ok = _place_chunk(pools, 1, len(df), cfg.min_gap, ro)
            if ok[0]:
                break
        idx = np.sort(P[0])
        from ..engine import strata_labels
        y, sl, v = strata_labels(df)
        key = lambda ii: sorted((int(y[i]), int(sl[i]), v[i]) for i in ii)
        preserved = key(idx) == key(idxT)
    elif cfg.mode == "C":
        idx = gen_clustered(rg, lo, hi, 100, cfg.min_gap)
    elif cfg.mode == "R":
        idx = gen_regular(rg, lo, hi, 100, cfg.min_gap)
    else:
        raise ValueError(cfg.mode)
    idx = idx[el[idx]]
    return df, t, el, window, raw, idx, fb, preserved, s0


def tail_audit_study(cfg: TailAudit, k: int) -> list[dict]:
    df, t, el, window, raw, idx, fb, preserved, s0 = make_study(cfg, k)
    h, lo, hi = cfg.horizon, 60, cfg.n_bars - 50
    if cfg.mode == "W":
        lo, hi = int(window[0]), int(window[-1]) + 1
    obs = float(raw[idx].mean())
    kw = dict(horizons=(h,), eval_start=t.iloc[0], eval_end=t.iloc[-1] + H4, n_ctrl=2000, primary_h=h, bar_td=H4, seed=s0 + k, min_gap=cfg.min_gap)
    pre = event_study(df, idx, 1, n_ctrl_primary=cfg.n_pre, refine_below=0.0, **kw).iloc[0]
    p_pre = float(pre["p_vs_random"])
    full = (cfg.k_full0 <= k < cfg.k_full0 + cfg.n_full) or p_pre <= cfg.pre_cut
    p_prod, cov, n_used, refined = float("nan"), float(pre["control_coverage"]), int(pre["n_ctrl"]), 0
    if full:
        r = event_study(df, idx, 1, n_ctrl_primary=cfg.n_ctrl_primary, refine_below=cfg.refine_below, n_ctrl_refine=cfg.n_ctrl_refine, **kw).iloc[0]
        assert abs(r["mean_ATR"] - obs) < 1e-9
        p_prod, cov, n_used, refined = float(r["p_vs_random"]), float(r["control_coverage"]), int(r["n_ctrl"]), int(r["n_ctrl_requested"] > cfg.n_ctrl_primary)
    p_ref, p_ref_pre = float("nan"), float("nan")
    if cfg.mode in ("G", "W"):
        xr, mr = draw_sets(np.random.default_rng(cfg.ref_seed0 + 2_000_000 + k), cfg.n_pre, lo, hi, cfg.n_raw_events, cfg.min_gap)
        ref = (np.where(mr, raw[xr], 0.0).sum(axis=1)) / mr.sum(axis=1)
        p_ref_pre = (1 + int((ref >= obs).sum())) / (1 + cfg.n_pre)
        if (cfg.k_full0 <= k < cfg.k_full0 + cfg.n_full) or p_ref_pre <= cfg.pre_cut:
            xr, mr = draw_sets(np.random.default_rng(cfg.ref_seed0 + k), cfg.r_ref, lo, hi, cfg.n_raw_events, cfg.min_gap)
            ref = (np.where(mr, raw[xr], 0.0).sum(axis=1)) / mr.sum(axis=1)
            p_ref = (1 + int((ref >= obs).sum())) / (1 + cfg.r_ref)
    p_shift = shift_p_exact(raw, idx, int(window[0]), int(window[-1]), obs)
    return [{"k": k, "n_events": int(len(idx)), "obs": obs, "p_pre": p_pre, "p_prod": p_prod, "p_ref_pre": p_ref_pre, "p_ref": p_ref, "p_shift": p_shift,
             "coverage": cov, "n_ctrl_used": n_used, "refined": refined, "fallback_events": fb, "template_preserved": int(preserved), "tier": int(full)}]
