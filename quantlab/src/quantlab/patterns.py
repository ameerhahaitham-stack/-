"""Numeric definitions of the DEV hypotheses (one function per hypothesis).

Every function sees only bars <= i when it emits an event at bar i (signal at the CLOSE of bar i; the engine enters at the next
open). Each returns a list of Ev(i, side, stop) with a structural / ATR stop. Common, pre-declared filter for ALL hypotheses
(`_finalize`): the stop must be between 0.5 and 4.0 ATR(14) from the signal-bar close, so costs are not dominated by microscopic
stops and no stop is absurdly wide. Look-ahead freedom is verified for every function by truncation tests.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .engine import Signal, atr

MIN_STOP_ATR, MAX_STOP_ATR = 0.5, 4.0
PRIMARY_HORIZON = 5          # bars; the ONE horizon on which an event study is tested (other horizons are descriptive)
EVENT_MIN_GAP = PRIMARY_HORIZON


@dataclass
class Ev:
    i: int
    side: int
    stop: float


def _arr(df):
    return (df["open"].to_numpy(float), df["high"].to_numpy(float), df["low"].to_numpy(float), df["close"].to_numpy(float))


def _roll_max_prev(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).max().shift(1).to_numpy()


def _roll_min_prev(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).min().shift(1).to_numpy()


def _finalize(df, evs: list[Ev]) -> list[Ev]:
    a = atr(df, 14)
    c = df["close"].to_numpy(float)
    out = []
    for e in evs:
        d = (c[e.i] - e.stop) * e.side
        if np.isfinite(a[e.i]) and a[e.i] > 0 and np.isfinite(e.stop) and MIN_STOP_ATR * a[e.i] <= d <= MAX_STOP_ATR * a[e.i]:
            out.append(e)
    return out


# ----------------------------------------------------------------------------------------------------- H01..H07
def h01_false_breakout(df, N=20):
    o, h, l, c = _arr(df)
    hi, lo = _roll_max_prev(h, N), _roll_min_prev(l, N)
    evs = []
    for i in range(N + 1, len(df)):
        up_fail = h[i] > hi[i] and c[i] < hi[i]
        dn_fail = l[i] < lo[i] and c[i] > lo[i]
        if up_fail and not dn_fail:
            evs.append(Ev(i, -1, h[i]))
        elif dn_fail and not up_fail:
            evs.append(Ev(i, 1, l[i]))
    return _finalize(df, evs)


def h02_trend_pullback(df, fast=20, slow=50, slope_lag=10):
    o, h, l, c = _arr(df)
    s = pd.Series(c)
    ef = s.ewm(span=fast, adjust=False).mean().to_numpy()
    sm = s.rolling(slow).mean().to_numpy()
    evs = []
    for i in range(slow + slope_lag, len(df)):
        up = c[i] > sm[i] and sm[i] > sm[i - slope_lag]
        dn = c[i] < sm[i] and sm[i] < sm[i - slope_lag]
        if up and l[i] <= ef[i] < c[i] and c[i] > o[i]:
            evs.append(Ev(i, 1, float(l[i - 2:i + 1].min())))
        elif dn and h[i] >= ef[i] > c[i] and c[i] < o[i]:
            evs.append(Ev(i, -1, float(h[i - 2:i + 1].max())))
    return _finalize(df, evs)


def h03_consolidation_breakout(df, N=10, box_atr=2.5):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    bh, bl = _roll_max_prev(h, N), _roll_min_prev(l, N)
    evs = []
    for i in range(N + 15, len(df)):
        if not np.isfinite(a[i - 1]) or (bh[i] - bl[i]) > box_atr * a[i - 1]:
            continue
        if c[i] > bh[i]:
            evs.append(Ev(i, 1, bl[i]))
        elif c[i] < bl[i]:
            evs.append(Ev(i, -1, bh[i]))
    return _finalize(df, evs)


def _prev_day_levels(df):
    day = pd.to_datetime(df["time"]).dt.normalize()
    g = df.assign(_d=day).groupby("_d")
    dh, dl = g["high"].max(), g["low"].min()
    prev_h = dh.shift(1).reindex(day).to_numpy()
    prev_l = dl.shift(1).reindex(day).to_numpy()
    return prev_h, prev_l


def h04_prev_day_range(df, k_stop=1.5):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    pdh, pdl = _prev_day_levels(df)
    evs = []
    for i in range(15, len(df)):
        if not (np.isfinite(pdh[i]) and np.isfinite(a[i])):
            continue
        if c[i] > pdh[i] and c[i - 1] <= pdh[i]:
            evs.append(Ev(i, 1, c[i] - k_stop * a[i]))
        elif c[i] < pdl[i] and c[i - 1] >= pdl[i]:
            evs.append(Ev(i, -1, c[i] + k_stop * a[i]))
    return _finalize(df, evs)


def h05_extended_reversal(df, K=10, ext_atr=3.0):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    evs = []
    for i in range(K + 15, len(df)):
        move = c[i - 1] - c[i - 1 - K]
        if not np.isfinite(a[i - 1]):
            continue
        if move >= ext_atr * a[i - 1] and c[i] < o[i] and c[i] < l[i - 1]:
            evs.append(Ev(i, -1, float(h[i - 2:i + 1].max())))
        elif move <= -ext_atr * a[i - 1] and c[i] > o[i] and c[i] > h[i - 1]:
            evs.append(Ev(i, 1, float(l[i - 2:i + 1].min())))
    return _finalize(df, evs)


def _pivots(h, l, p):
    """Confirmed fractal pivots: pivot at j is known at bar j+p. Returns boolean arrays indexed by j."""
    n = len(h)
    ph, pl = np.zeros(n, bool), np.zeros(n, bool)
    for j in range(p, n - p):
        ph[j] = h[j] > h[j - p:j].max() and h[j] > h[j + 1:j + 1 + p].max()
        pl[j] = l[j] < l[j - p:j].min() and l[j] < l[j + 1:j + 1 + p].min()
    return ph, pl


def h06_liquidity_sweep(df, wick=0.5, sweep_atr=0.1, p=3, look=50):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    n = len(df)
    evs = []
    last_pl = last_ph = None        # (index, level) of the most recent pivot CONFIRMED at or before the current bar
    for i in range(20, n):
        j = i - p                    # pivot at j becomes known at bar i (needs j+1..j+p, i.e. bars up to i)
        if j >= p:
            if l[j] < l[j - p:j].min() and l[j] < l[j + 1:j + 1 + p].min():
                last_pl = (j, l[j])
            if h[j] > h[j - p:j].max() and h[j] > h[j + 1:j + 1 + p].max():
                last_ph = (j, h[j])
        rng = h[i] - l[i]
        if rng <= 0 or not np.isfinite(a[i]):
            continue
        if last_pl and i - last_pl[0] <= look and l[i] < last_pl[1] - sweep_atr * a[i] and c[i] > last_pl[1] \
                and (min(o[i], c[i]) - l[i]) >= wick * rng:
            evs.append(Ev(i, 1, l[i]))
        elif last_ph and i - last_ph[0] <= look and h[i] > last_ph[1] + sweep_atr * a[i] and c[i] < last_ph[1] \
                and (h[i] - max(o[i], c[i])) >= wick * rng:
            evs.append(Ev(i, -1, h[i]))
    return _finalize(df, evs)


def h07_double_top_bottom(df, p=3, tol_atr=0.3, min_sep=5, max_sep=40, depth_atr=1.0, max_after=20):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    n = len(df)
    tops, bots, evs = [], [], []
    for i in range(20, n):
        j = i - p
        if j >= p:
            if h[j] > h[j - p:j].max() and h[j] > h[j + 1:j + 1 + p].max():
                tops.append(j)
            if l[j] < l[j - p:j].min() and l[j] < l[j + 1:j + 1 + p].min():
                bots.append(j)
        if not np.isfinite(a[i]) or a[i] <= 0:
            continue
        if len(tops) >= 2:
            j1, j2 = tops[-2], tops[-1]
            if min_sep <= j2 - j1 <= max_sep and abs(h[j1] - h[j2]) <= tol_atr * a[i] and 0 < i - j2 <= max_after:
                neck = l[j1:j2 + 1].min()
                if min(h[j1], h[j2]) - neck >= depth_atr * a[i] and c[i] < neck and c[j2 + 1:i].min(initial=np.inf) >= neck:
                    evs.append(Ev(i, -1, max(h[j1], h[j2])))
        if len(bots) >= 2:
            j1, j2 = bots[-2], bots[-1]
            if min_sep <= j2 - j1 <= max_sep and abs(l[j1] - l[j2]) <= tol_atr * a[i] and 0 < i - j2 <= max_after:
                neck = h[j1:j2 + 1].max()
                if neck - max(l[j1], l[j2]) >= depth_atr * a[i] and c[i] > neck and c[j2 + 1:i].max(initial=-np.inf) <= neck:
                    evs.append(Ev(i, 1, min(l[j1], l[j2])))
    return _finalize(df, evs)


# ----------------------------------------------------------------------------------------------------- H08 closed discovery set
def h08a_inside_bar_break(df):
    o, h, l, c = _arr(df)
    evs = []
    for i in range(16, len(df)):
        if h[i - 1] <= h[i - 2] and l[i - 1] >= l[i - 2]:
            if c[i] > h[i - 1]:
                evs.append(Ev(i, 1, l[i - 1]))
            elif c[i] < l[i - 1]:
                evs.append(Ev(i, -1, h[i - 1]))
    return _finalize(df, evs)


def h08b_outside_bar_reversal(df):
    o, h, l, c = _arr(df)
    evs = []
    for i in range(16, len(df)):
        rng = h[i] - l[i]
        if rng > 0 and h[i] > h[i - 1] and l[i] < l[i - 1]:
            clv = (c[i] - l[i]) / rng
            if clv >= 0.75:
                evs.append(Ev(i, 1, l[i]))
            elif clv <= 0.25:
                evs.append(Ev(i, -1, h[i]))
    return _finalize(df, evs)


def h08c_three_bar_exhaustion(df, drop_atr=2.0):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    evs = []
    for i in range(16, len(df)):
        if not np.isfinite(a[i]):
            continue
        if c[i] < c[i - 1] < c[i - 2] < c[i - 3] and (c[i - 3] - c[i]) >= drop_atr * a[i]:
            evs.append(Ev(i, 1, float(l[i - 2:i + 1].min())))
        elif c[i] > c[i - 1] > c[i - 2] > c[i - 3] and (c[i] - c[i - 3]) >= drop_atr * a[i]:
            evs.append(Ev(i, -1, float(h[i - 2:i + 1].max())))
    return _finalize(df, evs)


def h08d_close_extreme_continuation(df, range_atr=1.2):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    evs = []
    for i in range(16, len(df)):
        rng = h[i] - l[i]
        if rng <= 0 or not np.isfinite(a[i]) or rng < range_atr * a[i]:
            continue
        clv = (c[i] - l[i]) / rng
        if clv >= 0.9:
            evs.append(Ev(i, 1, l[i]))
        elif clv <= 0.1:
            evs.append(Ev(i, -1, h[i]))
    return _finalize(df, evs)


def h08e_gap_and_go(df, gap_atr=0.5):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    evs = []
    for i in range(16, len(df)):
        if not np.isfinite(a[i - 1]):
            continue
        gap = o[i] - c[i - 1]
        if gap >= gap_atr * a[i - 1] and c[i] > o[i]:
            evs.append(Ev(i, 1, l[i]))
        elif gap <= -gap_atr * a[i - 1] and c[i] < o[i]:
            evs.append(Ev(i, -1, h[i]))
    return _finalize(df, evs)


def h08f_nr7_breakout(df):
    o, h, l, c = _arr(df)
    rng = h - l
    evs = []
    for i in range(16, len(df)):
        if rng[i - 1] <= rng[i - 7:i].min():
            if c[i] > h[i - 1]:
                evs.append(Ev(i, 1, l[i - 1]))
            elif c[i] < l[i - 1]:
                evs.append(Ev(i, -1, h[i - 1]))
    return _finalize(df, evs)


# ----------------------------------------------------------------------------------------------------- extras
def x01_donchian_trend(df, N=55, k_stop=3.0):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    hi, lo = _roll_max_prev(h, N), _roll_min_prev(l, N)
    evs = []
    for i in range(N + 1, len(df)):
        if not np.isfinite(a[i]):
            continue
        if c[i] > hi[i]:
            evs.append(Ev(i, 1, c[i] - k_stop * a[i]))
        elif c[i] < lo[i]:
            evs.append(Ev(i, -1, c[i] + k_stop * a[i]))
    return _finalize(df, evs)


def x02_bollinger_reversion_in_trend(df, n=20, k=2.0, trend=200, k_stop=2.0):
    o, h, l, c = _arr(df)
    a = atr(df, 14)
    s = pd.Series(c)
    m, sd = s.rolling(n).mean().to_numpy(), s.rolling(n).std(ddof=0).to_numpy()
    tr = s.rolling(trend).mean().to_numpy()
    evs = []
    for i in range(trend, len(df)):
        if not np.isfinite(a[i]):
            continue
        if c[i] > tr[i] and c[i] < m[i] - k * sd[i]:
            evs.append(Ev(i, 1, c[i] - k_stop * a[i]))
        elif c[i] < tr[i] and c[i] > m[i] + k * sd[i]:
            evs.append(Ev(i, -1, c[i] + k_stop * a[i]))
    return _finalize(df, evs)


PATTERNS = {
    "H01_FALSE_BREAKOUT": h01_false_breakout, "H02_TREND_PULLBACK": h02_trend_pullback,
    "H03_CONSOLIDATION_BREAKOUT": h03_consolidation_breakout, "H04_PREV_DAY_RANGE": h04_prev_day_range,
    "H05_EXTENDED_REVERSAL": h05_extended_reversal, "H06_LIQUIDITY_SWEEP": h06_liquidity_sweep,
    "H07_DOUBLE_TOP_BOTTOM": h07_double_top_bottom,
    "H08A_INSIDE_BAR_BREAK": h08a_inside_bar_break, "H08B_OUTSIDE_BAR_REVERSAL": h08b_outside_bar_reversal,
    "H08C_THREE_BAR_EXHAUSTION": h08c_three_bar_exhaustion, "H08D_CLOSE_EXTREME_CONTINUATION": h08d_close_extreme_continuation,
    "H08E_GAP_AND_GO": h08e_gap_and_go, "H08F_NR7_BREAKOUT": h08f_nr7_breakout,
    "X01_DONCHIAN_TREND": x01_donchian_trend, "X02_BOLLINGER_REVERSION_IN_TREND": x02_bollinger_reversion_in_trend,
}


def event_arrays(evs: list[Ev], min_gap: int = EVENT_MIN_GAP):
    """Event-study input: de-duplicated so forward windows do not overlap more than the primary horizon."""
    last, idx, side = -10**9, [], []
    for e in sorted(evs, key=lambda e: e.i):
        if e.i - last >= min_gap:
            idx.append(e.i)
            side.append(e.side)
            last = e.i
    return np.array(idx, int), np.array(side, int)


def strategy_signals(df, hid: str, pattern_params: dict | None = None, rr: float = 2.0, max_hold: int = 20) -> list[Signal]:
    """Stage-2 signal function: the pattern's events with their stops, a take-profit at rr x risk and a time stop."""
    evs = PATTERNS[hid](df, **(pattern_params or {}))
    return [Signal(e.i, e.side, e.stop, rr, max_hold, tag=hid) for e in evs]
