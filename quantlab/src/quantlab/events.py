"""Event study: does a condition change forward price movement BEFORE any strategy rules / costs are added?

Forward move is measured from the next open, in ATR units (comparable across years and symbols), and compared
with random bars drawn from the same window with the same long/short mix. This is a gross, cost-free screen:
an event with no gross edge cannot become a strategy; an event with a gross edge still has to survive costs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .engine import _control_pools, atr, strata_labels


def dedupe_events(idx: np.ndarray, min_gap: int) -> np.ndarray:
    out, last = [], -10**9
    for i in sorted(idx):
        if i - last >= min_gap:
            out.append(i)
            last = i
    return np.array(out, dtype=int)


def eligible(df: pd.DataFrame, h: int, eval_start, eval_end, a: np.ndarray | None = None) -> np.ndarray:
    """THE eligibility rule, used for the real events AND for the random-control candidates, for every horizon h.

    Bar i can be a signal/control bar at horizon h iff: the entry bar i+1 exists and opens inside [eval_start, eval_end),
    the horizon bar i+h exists and closes inside the evaluation window (its open time is < eval_end), and ATR(i) is finite and > 0.
    So no event or control ever needs a bar beyond the window, and both samples are filtered identically."""
    n = len(df)
    a = atr(df, 14) if a is None else a
    t = pd.to_datetime(df["time"]).to_numpy()
    es, ee = np.datetime64(pd.Timestamp(eval_start)), np.datetime64(pd.Timestamp(eval_end))
    ok = np.zeros(n, bool)
    last = n - 1 - h                                   # i + h <= n - 1
    if last < 0:
        return ok
    i = np.arange(0, last + 1)
    ok[i] = (t[i + 1] >= es) & (t[i + 1] < ee) & (t[i + h] < ee) & np.isfinite(a[i]) & (a[i] > 0)
    return ok


def event_study(df: pd.DataFrame, idx, side, horizons=(1, 3, 5, 10, 20), eval_start=None, eval_end=None,
                n_ctrl: int = 2000, seed: int = 1, min_stratum: int = 5, primary_h: int | None = None,
                n_ctrl_primary: int = 20000, refine_below: float = 0.005, n_ctrl_refine: int = 200000) -> pd.DataFrame:
    """idx: signal-bar indices (condition known at close). side: +1/-1 (scalar or array aligned with idx).

    The control for every event is a random bar from the SAME exposure stratum (year x time-of-day slot x past-only volatility
    regime, falling back to year x slot, then slot, then all eligible bars) taken with the same side. Events and control candidates
    are filtered by the SAME per-horizon eligibility rule (`eligible`).

    Precision of the p-value (the control distribution has n_ctrl draws; the smallest possible p is 1/(n_ctrl+1)):
      * descriptive horizons: n_ctrl draws (default 2000, resolution 1/2001) - never used for a decision;
      * the primary horizon: n_ctrl_primary = 20000 (resolution 1/20001 = 0.00005); ADAPTIVE refinement: if that p < refine_below
        (0.005) the primary horizon is re-estimated with n_ctrl_refine = 200000 draws (resolution 0.000005), so the small
        p-values that matter under multiple-testing correction are resolved to well below the required ~0.001.
      * The bootstrap p of strategy trials has a different resolution: 1/5001 (5000 resamples, locked in the protocol).
    """
    df = df.reset_index(drop=True)
    a = atr(df, 14)
    o, c, t = df["open"].to_numpy(float), df["close"].to_numpy(float), df["time"]
    idx = np.asarray(idx, int)
    side = np.broadcast_to(np.asarray(side), idx.shape).astype(int)
    es = pd.Timestamp(eval_start) if eval_start is not None else t.min()
    ee = pd.Timestamp(eval_end) if eval_end is not None else t.max() + pd.Timedelta(days=1)
    strata = strata_labels(df)
    year, slot, vol = strata
    rng = np.random.default_rng(seed)

    def draw_mean(ii, ss, raw_all, pools, window, n):
        def pool_for(i):
            for key in ((int(year[i]), int(slot[i]), vol[i]), (int(year[i]), int(slot[i])), (int(slot[i]),)):
                cand = pools.get(key)
                if cand is not None and len(cand) >= min_stratum:
                    return cand
            return window
        ctrl = np.zeros(n)
        for i, sd in zip(ii, ss):
            pool = pool_for(i)
            ctrl += sd * raw_all[pool[rng.integers(0, len(pool), size=n)]]
        return ctrl / len(ii)

    rows = []
    for h in horizons:
        elig = eligible(df, h, es, ee, a)
        window = np.where(elig)[0]
        keep = elig[idx] if len(idx) else np.array([], bool)
        ii, ss = idx[keep], side[keep]
        if len(ii) == 0 or len(window) == 0:
            rows.append({"horizon": h, "n": 0, "n_control_candidates": int(len(window))})
            continue
        pools, _, _, _ = _control_pools(df, window, strata)
        raw_all = np.full(len(df), np.nan)
        raw_all[window] = (c[window + h] - o[window + 1]) / a[window]
        fwd = ss * (c[ii + h] - o[ii + 1]) / a[ii]
        obs = float(fwd.mean())
        n_used = n_ctrl_primary if (primary_h is not None and h == primary_h) else n_ctrl
        ctrl = draw_mean(ii, ss, raw_all, pools, window, n_used)
        p = (1 + int((ctrl >= obs).sum())) / (1 + n_used)
        if primary_h is not None and h == primary_h and p < refine_below:
            n_used = n_ctrl_refine
            ctrl = draw_mean(ii, ss, raw_all, pools, window, n_used)
            p = (1 + int((ctrl >= obs).sum())) / (1 + n_used)
        rows.append({"horizon": h, "n": int(len(ii)), "n_control_candidates": int(len(window)), "mean_ATR": obs,
                     "median_ATR": float(np.median(fwd)), "hit_rate": float((fwd > 0).mean()),
                     "baseline_mean_ATR": float(ctrl.mean()), "edge_ATR": obs - float(ctrl.mean()),
                     "p_vs_random": p, "n_ctrl": int(n_used), "p_resolution": 1.0 / (1 + n_used)})
    return pd.DataFrame(rows)
