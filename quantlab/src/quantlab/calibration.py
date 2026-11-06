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
