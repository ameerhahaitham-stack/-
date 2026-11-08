"""Synthetic OHLC series for the audit: AR(1) returns (phi) with optional stochastic volatility (log-vol AR(1))."""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_series(n: int = 1600, phi: float = 0.8, seed: int = 0, sigma: float = 3.0, sv: tuple[float, float] | None = None,
                start: str = "2018-01-01", freq: str = "4h", hl: str = "scaled") -> pd.DataFrame:
    """r_k = phi*r_{k-1} + sigma_k*e_k, close = 1000 + cumsum(r). sv=(rho, nu): log sigma_k follows an AR(1) with persistence rho and
    innovation sd nu (volatility clustering); sv=None gives constant sigma. High/low ranges scale with sigma_k so ATR tracks volatility."""
    rng = np.random.default_rng(seed)
    e = rng.normal(0, 1, n)
    if sv is None:
        sig = np.full(n, sigma)
    else:
        rho, nu = sv
        h = np.zeros(n)
        eta = rng.normal(0, nu, n)
        for k in range(1, n):
            h[k] = rho * h[k - 1] + eta[k]
        sig = sigma * np.exp(h - 0.5 * nu * nu / (1 - rho * rho))
    r = np.zeros(n)
    for k in range(1, n):
        r[k] = phi * r[k - 1] + sig[k] * e[k]
    c = 1000.0 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]]
    if hl == "unit":                                  # identical to calibration.ar_series (+-1 wicks) when sv is None
        u1 = u2 = np.ones(n)
    else:
        u1, u2 = np.abs(rng.normal(0, 0.5, n)) * sig, np.abs(rng.normal(0, 0.5, n)) * sig
    t = pd.date_range(start, periods=n, freq=freq)
    return pd.DataFrame({"time": t, "open": o, "high": np.maximum(o, c) + u1, "low": np.minimum(o, c) - u2, "close": c,
                         "tick_volume": 1, "spread": 0, "real_volume": 0})
