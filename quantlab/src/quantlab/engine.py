"""Independent bar-by-bar backtest engine.

Conventions (all declared, none optimistic)
- Signals are formed at the CLOSE of bar i using data up to bar i. Entry is at the OPEN of bar i+1.
- MT5 history bars are BID prices. Long entry pays ask = bid + spread; long exits at bid.
  Short entry sells at bid; short stops/exits trigger and fill on the ask = bid + spread.
- If stop and take-profit are both touched inside one bar, the STOP is assumed first.
- Stop gaps fill at the (worse) open. A take-profit that is gapped through still fills at the TP level (no price improvement).
- Slippage is adverse on market entries and on stop/time exits; take-profit limits get none.
- R is the actual risk: |fill - stop| at the real (cost-inclusive) entry. gross_R is the same signal simulated with zero costs;
  cost_R = gross_R - net_R measures what costs really took, relative to this trade's stop distance.
- One open position per run (per symbol/timeframe). Signals arriving while a position is open are skipped and counted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .costs import ZERO, CostModel, swap_nights


@dataclass
class Signal:
    i: int                      # index of the bar whose close generated the signal
    side: int                   # +1 long / -1 short
    stop: float                 # absolute stop price
    rr: float | None = None     # take-profit as multiple of risk (None = no TP)
    max_hold: int | None = None # exit at close after this many bars
    tag: str = ""


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    rejects: dict
    warnings: list = field(default_factory=list)


def atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    """Wilder ATR on closed bars. atr[i] uses bars <= i only."""
    h, l, c = df["high"].to_numpy(float), df["low"].to_numpy(float), df["close"].to_numpy(float)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.maximum.reduce([h - l, np.abs(h - pc), np.abs(l - pc)])
    tr[0] = h[0] - l[0]
    out = np.full(len(df), np.nan)
    if len(df) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for i in range(n, len(df)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def _arrays(df: pd.DataFrame, cm: CostModel, fallback_px: float):
    return dict(t=df["time"].to_numpy(), o=df["open"].to_numpy(float), h=df["high"].to_numpy(float),
                l=df["low"].to_numpy(float), c=df["close"].to_numpy(float), sp=cm.spread_array(df, fallback_px))


def _sim(A: dict, sg: Signal, cm: CostModel, n: int):
    """Simulate one trade. Returns (record | None, reject_reason | None)."""
    e = sg.i + 1
    if e >= n:
        return None, "no_next_bar"
    o, h, l, c, sp = A["o"], A["h"], A["l"], A["c"], A["sp"]
    side = sg.side
    fill = o[e] + sp[e] + cm.slippage_in_px if side == 1 else o[e] - cm.slippage_in_px
    risk = fill - sg.stop if side == 1 else sg.stop - fill
    if not np.isfinite(risk) or risk <= 0:
        return None, "stop_wrong_side"
    tp = fill + side * sg.rr * risk if sg.rr else None
    exit_fill = exit_raw = None
    reason = None
    j_exit = n - 1
    mfe_px = 0.0
    mae_px = 0.0
    for j in range(e, n):
        s = sp[j]
        if side == 1:
            stop_hit = l[j] <= sg.stop
            gap = j > e and o[j] <= sg.stop
            tp_hit = tp is not None and h[j] >= tp
            adverse_px, fav_px = fill - l[j], h[j] - fill
        else:
            stop_hit = h[j] + s >= sg.stop
            gap = j > e and o[j] + s >= sg.stop
            tp_hit = tp is not None and l[j] + s <= tp
            adverse_px, fav_px = h[j] + s - fill, fill - l[j]
        mae_px, mfe_px = max(mae_px, adverse_px), max(mfe_px, fav_px)
        if stop_hit:
            exit_raw = (o[j] if side == 1 else o[j] + s) if gap else sg.stop
            exit_fill = exit_raw - side * cm.slippage_out_px
            reason, j_exit = "stop", j
            break
        if tp_hit:
            exit_raw = exit_fill = tp
            reason, j_exit = "tp", j
            break
        if sg.max_hold and (j - e + 1) >= sg.max_hold:
            exit_raw = c[j] if side == 1 else c[j] + s
            exit_fill = exit_raw - side * cm.slippage_out_px
            reason, j_exit = "time", j
            break
    if reason is None:
        j = n - 1
        exit_raw = c[j] if side == 1 else c[j] + sp[j]
        exit_fill = exit_raw - side * cm.slippage_out_px
        reason, j_exit = "data_end", j
    pnl_px = (exit_fill - fill) * side
    t_in, t_out = pd.Timestamp(A["t"][e]), pd.Timestamp(A["t"][j_exit])
    swap_pts = cm.swap_long_pts if side == 1 else cm.swap_short_pts
    swap_cost_px = -swap_pts * cm.point * swap_nights(t_in, t_out) if swap_pts else 0.0
    comm_px = cm.commission_px
    net_px = pnl_px - comm_px - swap_cost_px
    return {"signal_bar": sg.i, "entry_bar": e, "exit_bar": j_exit, "entry_time": t_in, "exit_time": t_out, "side": side,
            "entry_fill": fill, "stop": sg.stop, "tp": tp, "exit_fill": exit_fill, "exit_reason": reason,
            "bars_held": j_exit - e + 1, "risk_px": risk, "spread_px": sp[e], "commission_px": comm_px,
            "slippage_px": cm.slippage_in_px + (cm.slippage_out_px if reason != "tp" else 0.0), "swap_px": swap_cost_px,
            "pnl_px_net": net_px, "net_R": net_px / risk, "mae_R": mae_px / risk, "mfe_R": mfe_px / risk,
            "forced_close": reason == "data_end", "tag": sg.tag}, None


def run_backtest(df: pd.DataFrame, signals: list[Signal], cm: CostModel, eval_start=None, eval_end=None,
                 fallback_spread_px: float = 0.0) -> BacktestResult:
    """Run signals through the engine. Trades are kept only if ENTERED inside [eval_start, eval_end)."""
    df = df.reset_index(drop=True)
    n = len(df)
    A = _arrays(df, cm, fallback_spread_px)
    G = _arrays(df, ZERO, 0.0)
    rejects = {"outside_window": 0, "skipped_concurrent": 0, "stop_wrong_side": 0, "no_next_bar": 0}
    warns = []
    if cm.spread_mode == "measured" and ("spread" not in df or df["spread"].isna().all()):
        warns.append("no spread data: fallback spread used for every bar")
    rows = []
    last_exit = -1
    es = pd.Timestamp(eval_start) if eval_start is not None else None
    ee = pd.Timestamp(eval_end) if eval_end is not None else None
    for sg in sorted(signals, key=lambda s: s.i):
        e = sg.i + 1
        if e >= n:
            rejects["no_next_bar"] += 1
            continue
        te = pd.Timestamp(A["t"][e])
        if (es is not None and te < es) or (ee is not None and te >= ee):
            rejects["outside_window"] += 1
            continue
        if e <= last_exit:
            rejects["skipped_concurrent"] += 1
            continue
        rec, why = _sim(A, sg, cm, n)
        if rec is None:
            rejects[why] += 1
            continue
        g, _ = _sim(G, sg, ZERO, n)
        rec["gross_R"] = g["net_R"] if g is not None else np.nan
        rec["cost_R"] = rec["gross_R"] - rec["net_R"] if g is not None else np.nan
        rec["cost_pct_of_stop"] = (rec["spread_px"] + rec["commission_px"] + rec["slippage_px"]) / rec["risk_px"]
        rows.append(rec)
        last_exit = rec["exit_bar"]
    trades = pd.DataFrame(rows)
    if len(trades):
        trades["forced_close"] = trades["forced_close"].astype(bool)
    return BacktestResult(trades=trades, rejects=rejects, warnings=warns)


# --------------------------------------------------------------------------- controls & look-ahead
def matched_control(df: pd.DataFrame, signals: list[Signal], cm: CostModel, eval_start, eval_end,
                    n_reps: int = 500, seed: int = 777, fallback_spread_px: float = 0.0) -> dict:
    """Random-entry control: same side, same stop distance in ATR units, same rr/max_hold, random bars in the window.

    Returns the signal mean net R, the distribution of control means and a one-sided p-value
    P(control_mean >= signal_mean). A real edge must beat entries placed at random with the same exits and costs.
    """
    df = df.reset_index(drop=True)
    a = atr(df, 14)
    t = df["time"]
    es, ee = pd.Timestamp(eval_start), pd.Timestamp(eval_end)
    window = np.where((t >= es).to_numpy() & (t < ee).to_numpy() & ~np.isnan(a))[0]
    window = window[window < len(df) - 2]
    real = run_backtest(df, signals, cm, eval_start, eval_end, fallback_spread_px).trades
    if len(real) == 0 or len(window) == 0:
        return {"signal_mean": float("nan"), "control_mean": float("nan"), "diff": float("nan"), "p_vs_control": float("nan"), "n_reps": 0}
    rng = np.random.default_rng(seed)
    o = df["open"].to_numpy(float)
    spec = []
    for r in real.itertuples():
        i0, e0 = r.signal_bar, r.entry_bar
        if np.isnan(a[i0]) or a[i0] <= 0:
            continue
        sg0 = next((s for s in signals if s.i == i0), None)
        spec.append((r.side, abs(o[e0] - sg0.stop) / a[i0], sg0.rr, sg0.max_hold))
    means = []
    for _ in range(n_reps):
        idx = rng.choice(window, size=len(spec), replace=True)
        sigs = []
        for (side, k, rr, mh), i in zip(spec, idx):
            sigs.append(Signal(int(i), side, o[i + 1] - side * k * a[i], rr, mh))
        res = run_backtest(df, sigs, cm, eval_start, eval_end, fallback_spread_px).trades
        if len(res):
            means.append(float(res["net_R"].mean()))
    means = np.array(means)
    sig_mean = float(real["net_R"].mean())
    p = (1 + int((means >= sig_mean).sum())) / (1 + len(means)) if len(means) else float("nan")
    return {"signal_mean": sig_mean, "control_mean": float(means.mean()) if len(means) else float("nan"),
            "diff": sig_mean - (float(means.mean()) if len(means) else float("nan")), "p_vs_control": p, "n_reps": int(len(means))}


def check_no_lookahead(signal_fn, df: pd.DataFrame, n_checks: int = 5, seed: int = 99) -> list[dict]:
    """Signals computed on a truncated series must equal those computed on the full series (up to the cut).

    Returns a list of mismatches (empty list = no look-ahead detected by this test).
    """
    df = df.reset_index(drop=True)
    full = {s.i: (s.side, round(s.stop, 8), s.rr, s.max_hold) for s in signal_fn(df)}
    rng = np.random.default_rng(seed)
    lo = max(int(len(df) * 0.3), 50)
    cuts = sorted(rng.integers(lo, len(df) - 2, size=n_checks).tolist())
    bad = []
    for k in cuts:
        part = {s.i: (s.side, round(s.stop, 8), s.rr, s.max_hold) for s in signal_fn(df.iloc[: k + 1].copy())}
        want = {i: v for i, v in full.items() if i <= k}
        if part != want:
            diff = sorted(set(part.items()) ^ set(want.items()), key=lambda x: x[0])[:3]
            bad.append({"cut": k, "n_cut": len(part), "n_full": len(want), "examples": [str(d) for d in diff]})
    return bad
