"""SYNTHETIC data generator - for testing the CODE only. Never research evidence.

Files are written in the same format as the MT5 export, and ingest() is told synthetic=True so the registry
refuses to log them as research (unless QUANTLAB_ALLOW_SYNTH=1 is set, which only the test-suite does).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROFILES = {
    "XAUUSD": dict(p0=1300.0, sigma=0.0009, point=0.01, spread=(18, 35)),
    "EURUSD": dict(p0=1.20, sigma=0.00035, point=0.00001, spread=(6, 14)),
}


def make_m15(symbol: str, start: str, end: str, seed: int = 0, drift: float = 0.0) -> pd.DataFrame:
    prof = PROFILES[symbol]
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, end)
    slots = pd.timedelta_range("0h", "22h45min", freq="15min")          # daily break 23:00-24:00 server time
    idx = (days.values[:, None] + slots.values[None, :]).ravel()
    idx = pd.DatetimeIndex(idx)
    n = len(idx)
    hour = idx.hour.values
    vol = prof["sigma"] * (0.6 + 0.8 * np.exp(-((hour - 14) ** 2) / 30.0))
    ret = rng.standard_normal(n) * vol + drift
    close = prof["p0"] * np.exp(np.cumsum(ret))
    openp = np.r_[prof["p0"], close[:-1]]
    wick = np.abs(rng.standard_normal((n, 2))) * vol[:, None] * 0.5
    high = np.maximum(openp, close) * np.exp(wick[:, 0])
    low = np.minimum(openp, close) * np.exp(-wick[:, 1])
    dg = 2 if symbol == "XAUUSD" else 5
    lo, hi = prof["spread"]
    spread = rng.integers(lo, hi, n)
    tv = rng.poisson(300, n) + 1
    df = pd.DataFrame({"time": idx, "open": openp.round(dg), "high": high.round(dg), "low": low.round(dg), "close": close.round(dg),
                       "tick_volume": tv, "spread": spread, "real_volume": 0})
    df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
    df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
    return df


def aggregate(m15: pd.DataFrame, tf: str) -> pd.DataFrame:
    if tf == "M15":
        return m15.copy()
    rule = {"H1": "1h", "H4": "4h", "D1": "1D"}[tf]
    g = m15.set_index("time").resample(rule, label="left", closed="left")
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                        "tick_volume": g["tick_volume"].sum(), "spread": g["spread"].first(), "real_volume": 0}).dropna(subset=["open"])
    return out.reset_index()


def write_mt5_csv(df: pd.DataFrame, path) -> None:
    d = df.copy()
    d["time"] = pd.to_datetime(d["time"]).dt.strftime("%Y.%m.%d %H:%M")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(path, index=False)


def make_all(outdir, symbols=("XAUUSD", "EURUSD"), start="2018-01-01", end="2025-06-30", tfs=("D1", "H4", "H1", "M15"), seed: int = 0) -> list[Path]:
    paths = []
    for k, s in enumerate(symbols):
        m15 = make_m15(s, start, end, seed + k)
        for tf in tfs:
            p = Path(outdir) / f"SYNTH_{s}_{tf}.csv"
            write_mt5_csv(aggregate(m15, tf), p)
            paths.append(p)
    return paths
