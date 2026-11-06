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


def infer_bar_td(df: pd.DataFrame) -> pd.Timedelta:
    """Nominal bar length = the most common spacing between consecutive bar-open times (D1 -> 1 day, H4 -> 4 hours)."""
    d = pd.to_datetime(df["time"]).diff().dropna()
    return pd.Timedelta(d.mode().iloc[0])


def eligible(df: pd.DataFrame, h: int, eval_start, eval_end, bar_td, a: np.ndarray | None = None) -> np.ndarray:
    """THE eligibility rule, used for the real events AND for the random-control candidates, for every horizon h.

    TIME CONVENTION: MT5 stamps a bar with its OPEN time. The outcome at horizon h is measured at the CLOSE of bar i+h, which
    happens at open(i+h) + bar_td (bar_td = nominal bar length: 1 day for D1, 4 hours for H4). Evaluation windows are half-open
    [eval_start, eval_end).

    Bar i can be a signal/control bar at horizon h iff:
      * the entry bar i+1 exists and OPENS inside [eval_start, eval_end);
      * the horizon bar i+h exists and CLOSES no later than eval_end:  open(i+h) + bar_td <= eval_end.
        (A bar that closes exactly AT eval_end lies entirely inside the window and is allowed; a bar that opens before eval_end but
        closes after it straddles the boundary - part of its movement belongs to the next period - and is NOT allowed.)
      * ATR(i) is finite and > 0.
    So neither an event nor a control candidate ever uses any price movement from after the window, and both samples are
    filtered by exactly this one rule."""
    n = len(df)
    a = atr(df, 14) if a is None else a
    t = pd.to_datetime(df["time"]).to_numpy()
    es, ee = np.datetime64(pd.Timestamp(eval_start)), np.datetime64(pd.Timestamp(eval_end))
    td = np.timedelta64(int(pd.Timedelta(bar_td).value), "ns")
    ok = np.zeros(n, bool)
    last = n - 1 - h                                   # i + h <= n - 1
    if last < 0:
        return ok
    i = np.arange(0, last + 1)
    ok[i] = (t[i + 1] >= es) & (t[i + 1] < ee) & (t[i + h] + td <= ee) & np.isfinite(a[i]) & (a[i] > 0)
    return ok


CONTROL_MIN_COVERAGE = 0.90      # engine diagnostic (NOT a protocol threshold): below this share of fully placed draws the comparison is flagged incomplete


def _place_chunk(pools, n_draws: int, n_bars: int, min_gap: int, rng, max_tries: int = 40):
    """Place ONE control event per real event, for `n_draws` independent control sets at once, such that inside every set
    (a) no bar is used twice and (b) any two chosen bars are >= min_gap bars apart - the same non-overlap rule `event_arrays`
    applies to the real events. Each event draws uniformly from its own stratum pool among the bars still allowed.

    Events are placed in a random order (fixed within the chunk, different between chunks) so that no event is systematically
    favoured. Returns (picks[n_draws, k], ok[n_draws]); a draw is not ok if some event found no allowed bar (greedy dead end)."""
    k = len(pools)
    picks = np.full((n_draws, k), -1, dtype=np.int64)
    blocked = np.zeros((n_draws, n_bars), dtype=bool)
    ok = np.ones(n_draws, dtype=bool)
    rows_all = np.arange(n_draws)
    offs = np.arange(-(min_gap - 1), min_gap)
    for j in rng.permutation(k):
        pool = pools[j]
        todo = rows_all[ok]
        cand = np.full(n_draws, -1, dtype=np.int64)
        for _ in range(max_tries):
            if len(todo) == 0:
                break
            c = pool[rng.integers(0, len(pool), size=len(todo))]
            good = ~blocked[todo, c]
            cand[todo[good]] = c[good]
            todo = todo[~good]
        for d in todo:                                    # exact fallback (uniform over the remaining allowed bars)
            allowed = pool[~blocked[d, pool]]
            if len(allowed) == 0:
                ok[d] = False
            else:
                cand[d] = allowed[rng.integers(0, len(allowed))]
        placed = rows_all[ok & (cand >= 0)]
        picks[placed, j] = cand[placed]
        for off in offs:
            blocked[placed, np.clip(cand[placed] + off, 0, n_bars - 1)] = True
    return picks, ok


ATTEMPT_BUDGET = 4        # at most 4 x n_draws placement attempts to obtain n_draws FULLY placed control sets


def control_means(pools, raw_all, sides, n_draws: int, n_bars: int, min_gap: int, rng, chunk: int = 2000, budget: int = ATTEMPT_BUDGET):
    """Mean signed forward move (side x raw_all[bar]) of up to `n_draws` FULLY placed gap-constrained control sets.

    A set whose greedy placement dead-ends is discarded and replaced by a fresh attempt (each kept set is a valid constraint-
    satisfying draw), up to budget x n_draws attempts. Returns (means, n_attempts, n_placed_total): fewer than n_draws means
    means the real events are packed so tightly that a random control cannot be built - the caller must report that."""
    out, got, attempts, placed_total = [], 0, 0, 0
    while got < n_draws and attempts < budget * n_draws:
        picks, ok = _place_chunk(pools, chunk, n_bars, min_gap, rng)
        attempts += chunk
        if ok.any():
            m = (raw_all[picks[ok]] * sides[None, :]).mean(axis=1)
            out.append(m)
            got += len(m)
            placed_total += len(m)
        elif attempts >= 5 * chunk and placed_total == 0:       # hopeless: stop early, coverage 0
            break
    means = np.concatenate(out)[:n_draws] if out else np.array([])
    return means, attempts, placed_total


def event_study(df: pd.DataFrame, idx, side, horizons=(1, 3, 5, 10, 20), eval_start=None, eval_end=None,
                n_ctrl: int = 2000, seed: int = 1, min_stratum: int = 5, primary_h: int | None = None,
                n_ctrl_primary: int = 20000, refine_below: float = 0.005, n_ctrl_refine: int = 200000,
                bar_td=None, min_gap: int = 5) -> pd.DataFrame:
    """idx: signal-bar indices (condition known at close), already de-duplicated with `min_gap`. side: +1/-1 (scalar or array).

    The control for every event is a random bar from the SAME exposure stratum (year x time-of-day slot x past-only volatility
    regime, falling back to year x slot, then slot, then all eligible bars) taken with the same side. Events and control candidates
    are filtered by the SAME per-horizon eligibility rule (`eligible`, which uses the bar CLOSE time via `bar_td`), and every
    control SET obeys the same non-overlap rule as the real events: no bar twice, any two bars >= min_gap bars apart.
    A feasible placement always exists (the real events themselves are one), but the random greedy placement can dead-end; the
    dead-ended sets are discarded and re-drawn (budget: ATTEMPT_BUDGET x n_draws attempts). control_coverage = built sets /
    requested sets; below 1 a warning is attached, below CONTROL_MIN_COVERAGE the comparison is flagged NOT complete.
    The p-value uses only fully built sets.

    Precision of the p-value (smallest possible p = 1/(n_ok+1)):
      * descriptive horizons: n_ctrl draws (default 2000, resolution 1/2001) - never used for a decision;
      * the primary horizon: n_ctrl_primary = 20000 (resolution 1/20001); ADAPTIVE refinement: if that p < refine_below (0.005)
        it is re-estimated with n_ctrl_refine = 200000 draws (resolution 0.000005).
      * The bootstrap p of strategy trials has a different resolution: 1/5001 (5000 resamples, locked in the protocol).
    """
    df = df.reset_index(drop=True)
    bar_td = infer_bar_td(df) if bar_td is None else pd.Timedelta(bar_td)
    a = atr(df, 14)
    o, c, t = df["open"].to_numpy(float), df["close"].to_numpy(float), df["time"]
    idx = np.asarray(idx, int)
    side = np.broadcast_to(np.asarray(side), idx.shape).astype(int)
    es = pd.Timestamp(eval_start) if eval_start is not None else t.min()
    ee = pd.Timestamp(eval_end) if eval_end is not None else t.max() + bar_td
    strata = strata_labels(df)
    year, slot, vol = strata
    rng = np.random.default_rng(seed)
    n_bars = len(df)

    def estimate(ii, ss, raw_all, pools, window, obs, n):
        def pool_for(i):
            for key in ((int(year[i]), int(slot[i]), vol[i]), (int(year[i]), int(slot[i])), (int(slot[i]),)):
                cand = pools.get(key)
                if cand is not None and len(cand) >= min_stratum:
                    return cand
            return window
        ctrl, n_att, n_placed = control_means([pool_for(i) for i in ii], raw_all, ss.astype(float), n, n_bars, min_gap, rng)
        p = (1 + int((ctrl >= obs).sum())) / (1 + len(ctrl)) if len(ctrl) else float("nan")
        return ctrl, p, len(ctrl) / n, (n_placed / n_att if n_att else 0.0)

    rows = []
    for h in horizons:
        elig = eligible(df, h, es, ee, bar_td, a)
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
        ctrl, p, cov, succ = estimate(ii, ss, raw_all, pools, window, obs, n_used)
        if primary_h is not None and h == primary_h and np.isfinite(p) and p < refine_below:
            n_used = n_ctrl_refine
            ctrl, p, cov, succ = estimate(ii, ss, raw_all, pools, window, obs, n_used)
        warn = ""
        if cov < 1.0:
            warn = (f"control INCOMPLETE: only {cov:.1%} of the {n_used} requested control sets could be built (all {len(ii)} events placed "
                    f"with gap >= {min_gap} among {len(window)} eligible bars; placement success {succ:.1%} per attempt, budget {ATTEMPT_BUDGET}x); "
                    f"p uses the built sets only" + ("" if cov >= CONTROL_MIN_COVERAGE else " - NOT a complete comparison"))
        rows.append({"horizon": h, "n": int(len(ii)), "n_control_candidates": int(len(window)), "mean_ATR": obs,
                     "median_ATR": float(np.median(fwd)), "hit_rate": float((fwd > 0).mean()),
                     "baseline_mean_ATR": float(ctrl.mean()) if len(ctrl) else float("nan"),
                     "edge_ATR": obs - float(ctrl.mean()) if len(ctrl) else float("nan"),
                     "p_vs_random": p, "n_ctrl": int(len(ctrl)), "n_ctrl_requested": int(n_used),
                     "p_resolution": 1.0 / (1 + len(ctrl)) if len(ctrl) else float("nan"),
                     "control_coverage": float(cov), "control_placement_success": float(succ), "control_complete": bool(cov >= CONTROL_MIN_COVERAGE), "control_warning": warn})
    return pd.DataFrame(rows)
