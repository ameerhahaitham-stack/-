"""Calibration of the event-study random control on SYNTHETIC null series (no market data, no registry, no HOLD access).

Question answered: when the 'events' are random bars (no edge by construction) on autocorrelated prices, are the event-vs-control
p-values uniform? i.e. P(p <= alpha) ~ alpha. Used by tests/test_patterns.py and scripts/control_calibration.py."""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from .events import event_study
from .patterns import Ev, event_arrays

H4 = pd.Timedelta(hours=4)


@dataclass(frozen=True)
class CalibConfig:
    n_series: int = 1000
    n_bars: int = 1600            # H4 bars per synthetic series
    phi: float = 0.8              # AR(1) coefficient of the bar returns
    sigma: float = 3.0            # innovation sd (price units)
    n_raw_events: int = 140       # random bars drawn before de-duplication (min gap 5 -> ~99 events)
    n_ctrl: int = 400             # control sets per study (resolution 1/401)
    horizon: int = 5
    series_seed0: int = 0         # series k uses seed series_seed0 + k
    event_seed0: int = 1000       # event placement of series k uses seed event_seed0 + k
    # event_study(seed=...) of series k is series_seed0 + k


def ar_series(n: int, phi: float, seed: int, sigma: float = 3.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = np.zeros(n)
    e = rng.normal(0, sigma, n)
    for k in range(1, n):
        r[k] = phi * r[k - 1] + e[k]
    c = 1000 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]]
    t = pd.date_range("2018-01-01", periods=n, freq="4h")
    return pd.DataFrame({"time": t, "open": o, "high": np.maximum(o, c) + 1, "low": np.minimum(o, c) - 1, "close": c,
                         "tick_volume": 1, "spread": 0, "real_volume": 0})


def one_study(cfg: CalibConfig, k: int) -> dict:
    df = ar_series(cfg.n_bars, cfg.phi, cfg.series_seed0 + k, cfg.sigma)
    rng = np.random.default_rng(cfg.event_seed0 + k)
    raw = np.sort(rng.choice(np.arange(60, cfg.n_bars - 50), size=cfg.n_raw_events, replace=False))
    idx, _ = event_arrays([Ev(int(i), 1, 0.0) for i in raw])
    t = pd.to_datetime(df["time"])
    r = event_study(df, idx, 1, horizons=(cfg.horizon,), eval_start=t.iloc[0], eval_end=t.iloc[-1] + H4, n_ctrl=cfg.n_ctrl,
                    primary_h=cfg.horizon, n_ctrl_primary=cfg.n_ctrl, bar_td=H4, seed=cfg.series_seed0 + k).iloc[0]
    return {"p": float(r["p_vs_random"]), "coverage": float(r["control_coverage"]), "n_events": int(r["n"])}


def _worker(args):
    cfg, ks = args
    return [one_study(cfg, k) for k in ks]


def run_calibration(cfg: CalibConfig, procs: int = 1) -> pd.DataFrame:
    ks = list(range(cfg.n_series))
    if procs > 1:
        from multiprocessing import Pool
        chunks = [ks[i::procs] for i in range(procs)]
        with Pool(procs) as pool:
            parts = pool.map(_worker, [(cfg, c) for c in chunks])
        rows = [None] * len(ks)
        for c, part in zip(chunks, parts):
            for k, r in zip(c, part):
                rows[k] = r
    else:
        rows = [one_study(cfg, k) for k in ks]
    return pd.DataFrame(rows)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def summarize(df: pd.DataFrame, alphas=(0.10, 0.05)) -> dict:
    n = len(df)
    out = {"n_series": n, "mean_p": float(df["p"].mean()), "min_coverage": float(df["coverage"].min()),
           "mean_events": float(df["n_events"].mean())}
    for a in alphas:
        k = int((df["p"] <= a).sum())
        lo, hi = wilson(k, n)
        lo99, hi99 = wilson(k, n, 2.576)
        out[f"alpha_{a}"] = {"rate": k / n, "k": k, "ci95": [lo, hi], "ci99": [lo99, hi99], "nominal": a}
    return out


def config_dict(cfg: CalibConfig) -> dict:
    return asdict(cfg)


# =====================================================================================================================
# TAIL calibration (review round 4): do small p-values (0.001 - 0.005) of the event-study control behave like null p-values?
# Synthetic data only. Two independent p-values per study on the SAME series and the SAME event set:
#   p_prod : the production path  events.event_study(...)  (gap-constrained, stratum-matched control, 20000 draws, adaptive 200000)
#   p_ref  : an EXACT randomization p-value from the null's own generator G (no strata, no control sampler): the observed event
#            set is one more draw from G, so it is exchangeable with R_ref reference draws and p_ref is (super-)uniform by construction.
# G = "draw n_raw bar positions iid uniform on [60, n_bars-50), sort, greedy de-duplicate with min gap 5" (same rule as event_arrays).
# =====================================================================================================================
@dataclass(frozen=True)
class TailConfig:
    phi: float = 0.8
    n_series: int = 20000
    n_bars: int = 1600
    sigma: float = 3.0
    n_raw_events: int = 140
    horizon: int = 5
    n_ctrl_primary: int = 20000        # production defaults of event_study
    refine_below: float = 0.005
    n_ctrl_refine: int = 200000
    r_ref: int = 20000                 # reference draws of G per study (exact p_ref, resolution 1/20001)
    series_seed0: int = 100_000        # series k: seed series_seed0 + k  (also the event_study control seed)
    event_seed0: int = 3_000_000       # observed event set of series k: seed event_seed0 + k
    ref_seed0: int = 5_000_000         # reference draws of series k: seed ref_seed0 + k
    min_gap: int = 5


def dedupe_mask(x: np.ndarray, gap: int = 5) -> np.ndarray:
    """Vectorised greedy de-duplication of SORTED position rows: identical to patterns.event_arrays applied to each row."""
    last = np.full(x.shape[0], -10**9, dtype=np.int64)
    mask = np.zeros(x.shape, dtype=bool)
    for j in range(x.shape[1]):
        keep = (x[:, j] - last) >= gap
        mask[:, j] = keep
        last = np.where(keep, x[:, j], last)
    return mask


def draw_sets(rng, n_sets: int, lo: int, hi: int, n_raw: int, gap: int):
    x = np.sort(rng.integers(lo, hi, size=(n_sets, n_raw)), axis=1)
    return x, dedupe_mask(x, gap)


def tail_study(cfg: TailConfig, k: int) -> dict:
    from .engine import atr
    df = ar_series(cfg.n_bars, cfg.phi, cfg.series_seed0 + k, cfg.sigma)
    t = pd.to_datetime(df["time"])
    o, c, a = df["open"].to_numpy(float), df["close"].to_numpy(float), atr(df, 14)
    h, lo, hi = cfg.horizon, 60, cfg.n_bars - 50
    raw_all = np.full(len(df), np.nan)
    ii = np.arange(lo, hi)
    raw_all[ii] = (c[ii + h] - o[ii + 1]) / a[ii]
    # observed (null) event set = one draw of G
    x0, m0 = draw_sets(np.random.default_rng(cfg.event_seed0 + k), 1, lo, hi, cfg.n_raw_events, cfg.min_gap)
    idx = x0[0][m0[0]]
    obs = float(raw_all[idx].mean())
    # exact reference p-value
    xr, mr = draw_sets(np.random.default_rng(cfg.ref_seed0 + k), cfg.r_ref, lo, hi, cfg.n_raw_events, cfg.min_gap)
    ref = (np.where(mr, raw_all[xr], 0.0).sum(axis=1)) / mr.sum(axis=1)
    p_ref = (1 + int((ref >= obs).sum())) / (1 + cfg.r_ref)
    # production p-value
    r = event_study(df, idx, 1, horizons=(h,), eval_start=t.iloc[0], eval_end=t.iloc[-1] + H4, n_ctrl=2000, primary_h=h,
                    n_ctrl_primary=cfg.n_ctrl_primary, refine_below=cfg.refine_below, n_ctrl_refine=cfg.n_ctrl_refine,
                    bar_td=H4, seed=cfg.series_seed0 + k, min_gap=cfg.min_gap).iloc[0]
    assert abs(r["mean_ATR"] - obs) < 1e-9, (r["mean_ATR"], obs)          # both paths measure the same statistic on the same events
    return {"k": k, "n_events": int(len(idx)), "obs": obs, "p_prod": float(r["p_vs_random"]), "p_ref": float(p_ref),
            "coverage": float(r["control_coverage"]), "n_ctrl_used": int(r["n_ctrl"]), "refined": bool(r["n_ctrl_requested"] > cfg.n_ctrl_primary)}


def _tail_worker(args):
    cfg, ks = args
    return [tail_study(cfg, k) for k in ks]


def run_tail_block(cfg: TailConfig, ks: list[int], procs: int = 2) -> list[dict]:
    if procs <= 1:
        return _tail_worker((cfg, ks))
    from multiprocessing import Pool
    chunks = [ks[i::procs] for i in range(procs)]
    with Pool(procs) as pool:
        parts = pool.map(_tail_worker, [(cfg, c) for c in chunks])
    return sorted([r for part in parts for r in part], key=lambda r: r["k"])
