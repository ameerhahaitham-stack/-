"""The closed list of hypotheses for DEV (single source of truth) and the two-stage plan with its family-size budget.

Stage 1 - event study (gross, cost-free) for every hypothesis x dataset, ONE fixed definition each, primary horizon 5 bars.
          Each study is logged and counts as a trial in the multiple-testing family.
Stage 2 - strategy with costs ONLY for (hypothesis, dataset) pairs that passed the DEV screen in stage 1
          (n_events >= 30, positive gross edge, p_vs_random <= 0.10), best 12 pairs by p at most.
          Grid per pair: rr in {1.5, 2.0, 3.0}; max_hold = 20 bars (D1) / 30 bars (H4) - three trials per pair.
Nothing else may be tested on DEV; any new idea is a NEW hypothesis registered (with derived_from if it comes from one of these).
"""
from __future__ import annotations

from . import registry
from .patterns import PATTERNS

DATASETS = [("XAUUSD", "D1"), ("XAUUSD", "H4"), ("EURUSD", "D1"), ("EURUSD", "H4")]
PRIMARY_HORIZON = 5
STAGE2_RR = [1.5, 2.0, 3.0]
STAGE2_MAX_HOLD = {"D1": 20, "H4": 30}
STAGE2_MAX_PAIRS = 12
EVENT_SCREEN = {"min_events": 30, "min_edge_ATR": 0.0, "max_p": 0.10}

def event_screen_passed(summary: dict) -> bool:
    """Stage-1 screen (thresholds exactly as registered in EVENT_SCREEN) plus the validity precondition that the random comparison
    was actually built (control_complete). A pair whose control could not be built has p = None and can never pass."""
    s, e = EVENT_SCREEN, summary
    if e.get("kind") != "event_study" or not e.get("control_complete") or e.get("p_raw") is None or e.get("edge_ATR") is None:
        return False
    return e["n_events"] >= s["min_events"] and e["edge_ATR"] > s["min_edge_ATR"] and e["p_raw"] <= s["max_p"]


SPEC = {
    "H01_FALSE_BREAKOUT": ("false_breakout", "Fake breakout of the prior 20-bar high/low: the bar pokes beyond the level and closes back inside. Trade against the poke; stop at the bar extreme.", {"N": 20}),
    "H02_TREND_PULLBACK": ("pullback", "Trend (close > SMA50 and SMA50 rising vs 10 bars ago) with a bar that touches EMA20 and closes back above it as an up bar. Mirror for downtrends; stop at the 3-bar extreme.", {"fast": 20, "slow": 50, "slope_lag": 10}),
    "H03_CONSOLIDATION_BREAKOUT": ("consolidation", "10-bar box no wider than 2.5 ATR; close beyond the box high/low. Stop at the opposite side of the box.", {"N": 10, "box_atr": 2.5}),
    "H04_PREV_DAY_RANGE": ("prev_day_range", "First close beyond the previous day's high/low (completed server-days). Continuation; stop 1.5 ATR from the close.", {"k_stop": 1.5}),
    "H05_EXTENDED_REVERSAL": ("reversal", "Move over the last 10 bars >= 3 ATR followed by a reversal bar (closes against the move, beyond the prior bar's extreme). Counter-trend; stop at the 3-bar extreme.", {"K": 10, "ext_atr": 3.0}),
    "H06_LIQUIDITY_SWEEP": ("liquidity", "Sweep of a confirmed 3-bar fractal pivot (within 50 bars) by >= 0.1 ATR with a close back beyond the level and a wick >= 50% of the range. Trade the rejection; stop at the sweep extreme.", {"wick": 0.5, "sweep_atr": 0.1, "p": 3, "look": 50}),
    "H07_DOUBLE_TOP_BOTTOM": ("classic", "Double top/bottom: two confirmed pivots 5-40 bars apart within 0.3 ATR, depth >= 1 ATR, first close beyond the neckline within 20 bars of the second pivot. Stop beyond the pattern.", {"p": 3, "tol_atr": 0.3, "min_sep": 5, "max_sep": 40, "depth_atr": 1.0, "max_after": 20}),
    "H08A_INSIDE_BAR_BREAK": ("discovery_closed_set", "Inside bar followed by a close beyond its high/low. Stop at the inside bar's opposite extreme.", {}),
    "H08B_OUTSIDE_BAR_REVERSAL": ("discovery_closed_set", "Outside bar closing in its top/bottom quarter: trade in the direction of the close. Stop at the bar extreme.", {}),
    "H08C_THREE_BAR_EXHAUSTION": ("discovery_closed_set", "Three consecutive closes in one direction with total move >= 2 ATR: fade it. Stop at the 3-bar extreme.", {"drop_atr": 2.0}),
    "H08D_CLOSE_EXTREME_CONTINUATION": ("discovery_closed_set", "Bar range >= 1.2 ATR closing in its top/bottom 10%: continuation. Stop at the bar extreme.", {"range_atr": 1.2}),
    "H08E_GAP_AND_GO": ("discovery_closed_set", "Open gaps >= 0.5 ATR from the prior close and the bar closes in the gap direction: continuation. Stop at the bar extreme.", {"gap_atr": 0.5}),
    "H08F_NR7_BREAKOUT": ("discovery_closed_set", "Narrowest range of the last 7 bars followed by a close beyond its high/low. Stop at the NR7 bar's opposite extreme.", {}),
    "X01_DONCHIAN_TREND": ("extra_trend", "Close beyond the prior 55-bar high/low (Donchian trend entry); stop 3 ATR. NOTE: a related D1 Donchian test (100/50/3ATR) was run in an earlier, separate project in Oct 2026 and was inconclusive.", {"N": 55, "k_stop": 3.0}),
    "X02_BOLLINGER_REVERSION_IN_TREND": ("extra_reversion", "Mean reversion inside a trend: long when close > SMA200 and close is below the lower Bollinger(20, 2 sigma) band; short when close < SMA200 and close is above the upper band. Stop 2 ATR.", {"n": 20, "k": 2.0, "trend": 200, "k_stop": 2.0}),
}
assert set(SPEC) == set(PATTERNS)


NOT_TESTABLE_BY_COUNT = 14      # pairs with < 30 de-duplicated DEV events (counted before any outcome was looked at): not tested, not trials


def planned_family() -> dict:
    n_h = len(SPEC)
    stage1 = n_h * len(DATASETS) - NOT_TESTABLE_BY_COUNT
    stage2_max = STAGE2_MAX_PAIRS * len(STAGE2_RR)
    return {"hypotheses": n_h, "datasets": len(DATASETS), "stage1_event_studies": stage1, "stage2_max_pairs": STAGE2_MAX_PAIRS,
            "stage2_max_trials": stage2_max, "dev_trials_max": stage1 + stage2_max,
            "expected_dev_trials": stage1 + 3 * 6,      # ~6 pairs expected to pass the screen (about 5 by chance alone)
            "valid_trials_budget_per_candidate": 3,     # frozen config + up to 2 neighbours (rr +-1 step)
            "required_raw_p_for_adjusted_0.10": "p_raw <= 0.10 / m ; for m=80 (DEV ~64 + VALID ~15) -> 0.00125 ; bootstrap resolution 1/5001=0.0002"}


def register_all(code_commit: str) -> list[dict]:
    out = []
    for hid, (family, rule, params) in SPEC.items():
        out.append(registry.register_hypothesis(hid, family, rule, rules={
            "pattern_params": params, "datasets": [f"{s} {t}" for s, t in DATASETS], "primary_horizon": PRIMARY_HORIZON,
            "stage1": "event study, gross, DEV only, matched stratified control, p at primary horizon", "event_screen": EVENT_SCREEN,
            "stage2_grid": {"rr": STAGE2_RR, "max_hold": STAGE2_MAX_HOLD}, "common_stop_filter_ATR": [0.5, 4.0],
            "code_commit": code_commit, "protocol": "v1.2"}))
    return out


def make_signal_fn(hid: str):
    """Stage-2 signal function for run_trial: params = {"rr": .., "max_hold": ..} (pattern parameters stay at their registered values)."""
    from .patterns import strategy_signals
    base = SPEC[hid][2]
    return lambda df, rr=2.0, max_hold=20: strategy_signals(df, hid, base, rr, max_hold)


def make_event_fn(hid: str):
    return PATTERNS[hid]
