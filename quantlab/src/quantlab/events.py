"""Event study: does a condition change forward price movement BEFORE any strategy rules / costs are added?

Forward move is measured from the next open, in ATR units (comparable across years and symbols), and compared
with random bars drawn from the same window with the same long/short mix. This is a gross, cost-free screen:
an event with no gross edge cannot become a strategy; an event with a gross edge still has to survive costs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .engine import atr


def dedupe_events(idx: np.ndarray, min_gap: int) -> np.ndarray:
    out, last = [], -10**9
    for i in sorted(idx):
        if i - last >= min_gap:
            out.append(i)
            last = i
    return np.array(out, dtype=int)


def event_study(df: pd.DataFrame, idx, side, horizons=(1, 3, 5, 10, 20), eval_start=None, eval_end=None,
                n_ctrl: int = 2000, seed: int = 1) -> pd.DataFrame:
    """idx: signal-bar indices (condition known at close). side: +1/-1 (scalar or array aligned with idx)."""
    df = df.reset_index(drop=True)
    a = atr(df, 14)
    o, c, t = df["open"].to_numpy(float), df["close"].to_numpy(float), df["time"]
    idx = np.asarray(idx, int)
    side = np.broadcast_to(np.asarray(side), idx.shape).astype(int)
    es = pd.Timestamp(eval_start) if eval_start is not None else t.min()
    ee = pd.Timestamp(eval_end) if eval_end is not None else t.max() + pd.Timedelta(days=1)
    in_win = ((t >= es) & (t < ee)).to_numpy()
    rng = np.random.default_rng(seed)
    rows = []
    for h in horizons:
        valid = lambda i: (i + h < len(df)) and in_win[i + 1 if i + 1 < len(df) else i] and np.isfinite(a[i]) and a[i] > 0
        keep = np.array([valid(i) for i in idx]) if len(idx) else np.array([], bool)
        ii, ss = idx[keep], side[keep]
        if len(ii) == 0:
            rows.append({"horizon": h, "n": 0})
            continue
        fwd = ss * (c[ii + h] - o[ii + 1]) / a[ii]
        pool = np.array([i for i in range(len(df) - h - 1) if in_win[i + 1] and np.isfinite(a[i]) and a[i] > 0])
        raw = (c[pool + h] - o[pool + 1]) / a[pool]
        frac_long = float((ss == 1).mean())
        base_mean = frac_long * raw.mean() - (1 - frac_long) * raw.mean()
        ctrl = np.empty(n_ctrl)
        for k in range(n_ctrl):
            pick = rng.integers(0, len(pool), size=len(ii))
            ctrl[k] = (ss * raw[pick]).mean()
        obs = float(fwd.mean())
        rows.append({"horizon": h, "n": int(len(ii)), "mean_ATR": obs, "median_ATR": float(np.median(fwd)),
                     "hit_rate": float((fwd > 0).mean()), "baseline_mean_ATR": float(ctrl.mean()),
                     "edge_ATR": obs - float(ctrl.mean()),
                     "p_vs_random": (1 + int((ctrl >= obs).sum())) / (1 + n_ctrl)})
    return pd.DataFrame(rows)
