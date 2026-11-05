"""Pattern library: no look-ahead, correct stop sides, hand-built examples, logged event studies, stage-2 plumbing."""
import numpy as np
import pandas as pd
import pytest

from conftest import mk
from quantlab import data, registry, synth
from quantlab.config import root
from quantlab.engine import Signal, check_no_lookahead
from quantlab.events import event_study
from quantlab.experiment import LookaheadError, run_event_study, run_trial
from quantlab.hypotheses import SPEC, make_event_fn, make_signal_fn, planned_family, register_all
from quantlab.patterns import PATTERNS, event_arrays
from test_integrity import _frame
from test_stats_sizing_replay import _setup


def _trendy(n=2500, seed=21):
    rng = np.random.default_rng(seed)
    t = pd.date_range("2018-01-01", periods=n, freq="4h")
    drift = np.sign(np.sin(np.arange(n) / 150.0)) * 0.6
    c = 1000 + np.cumsum(rng.normal(drift, 3, n))
    o = np.r_[c[0], c[:-1]] + rng.normal(0, 0.8, n)          # small gaps
    h = np.maximum(o, c) + rng.uniform(0, 3, n)
    l = np.minimum(o, c) - rng.uniform(0, 3, n)
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c, "tick_volume": 1, "spread": 0, "real_volume": 0})


@pytest.mark.parametrize("hid", list(PATTERNS))
def test_no_lookahead_and_stop_sides(hid):
    df = _trendy()
    fn = lambda d: [Signal(e.i, e.side, e.stop) for e in PATTERNS[hid](d)]
    assert check_no_lookahead(fn, df, n_checks=6, seed=3) == []
    for e in PATTERNS[hid](df):
        assert (df["close"].iloc[e.i] - e.stop) * e.side > 0                 # stop is on the loss side of the signal close
        assert e.side in (1, -1)


def test_every_pattern_produces_events_on_trendy_data_except_rare_ones():
    df = _trendy()
    counts = {h: len(f(df)) for h, f in PATTERNS.items()}
    assert sum(1 for v in counts.values() if v > 0) >= 12, counts


def test_false_breakout_hand_example():
    # 20 flat bars (high 101), then a bar that pokes to 102 and closes at 100.5 -> short with stop at 102
    bars = [(100, 101, 99, 100)] * 25 + [(100, 102, 99.5, 100.5)] + [(100.5, 101, 99, 100)] * 3
    df = mk(bars)
    evs = PATTERNS["H01_FALSE_BREAKOUT"](df, N=20)
    assert [(e.i, e.side, float(e.stop)) for e in evs] == [(25, -1, 102.0)]          # exactly one short, stop at the poke high


def test_double_top_hand_example():
    base = [(100, 101, 99, 100)] * 25
    up1 = [(100, 105, 99.5, 104)] + [(104, 110, 103, 109)] + [(109, 120, 108, 119)] + [(119, 119.5, 112, 113)] + [(113, 114, 105, 106)] * 3
    mid = [(106, 108, 100, 101)] * 4 + [(101, 104, 100, 103)] * 2
    up2 = [(103, 110, 102, 109)] + [(109, 120, 108, 119.5)] + [(119.5, 119.6, 112, 113)] + [(113, 114, 105, 106)] * 3
    brk = [(106, 106, 95, 96)]
    df = mk(base + up1 + mid + up2 + brk)
    evs = PATTERNS["H07_DOUBLE_TOP_BOTTOM"](df, p=3, tol_atr=1.0, min_sep=5, max_sep=40, depth_atr=0.5, max_after=20)
    assert [(e.i, e.side, float(e.stop)) for e in evs] == [(44, -1, 120.0)]          # neckline break on the last bar, stop at the tops


def test_event_arrays_dedup_and_primary_horizon_const():
    idx, side = event_arrays([type("E", (), {"i": i, "side": 1, "stop": 0})() for i in [10, 11, 12, 20, 21, 30]], min_gap=5)
    assert idx.tolist() == [10, 20, 30]


def test_stratified_event_study_no_false_edge_on_pure_drift_and_detects_planted_edge():
    df = _trendy(3000, seed=5)
    a_idx = np.arange(40, len(df) - 30, 11)                              # arbitrary events, direction long: exposure-matched control
    r = event_study(df, a_idx, 1, horizons=(5,), n_ctrl=800, seed=2)
    assert r.loc[0, "p_vs_random"] > 0.02                                # arbitrary events show no edge vs. matched control
    from quantlab.engine import atr
    d2 = df.copy()
    a = atr(d2, 14)
    for i in a_idx[:150]:
        if i + 6 < len(d2):
            d2.loc[i + 5, "close"] = d2.loc[i + 1, "open"] + 1.0 * a[i]
            d2.loc[i + 5, "high"] = max(d2.loc[i + 5, "high"], d2.loc[i + 5, "close"])
    r2 = event_study(d2, a_idx, 1, horizons=(5,), n_ctrl=800, seed=2)
    assert r2.loc[0, "p_vs_random"] < 0.01 and r2.loc[0, "edge_ATR"] > 0.3


def test_event_study_is_logged_counted_and_dev_only(lab):
    _setup(lab, tfs=("H4",))
    registry.register_hypothesis("H01_FALSE_BREAKOUT", "false_breakout", "test")
    before = registry.trial_count(("dev", "valid"))
    r = run_event_study("H01_FALSE_BREAKOUT", "XAUUSD", "H4", make_event_fn("H01_FALSE_BREAKOUT"), {"N": 20}, n_ctrl=300)
    assert r["summary"]["kind"] == "event_study" and registry.trial_count(("dev", "valid")) == before + 1
    t = registry.trials_df().iloc[-1]
    assert t["split"] == "dev" and "event_study" in t["note"]
    assert list((root() / "results" / "H01_FALSE_BREAKOUT").glob("event_dev_*.json"))


def test_register_all_and_stage2_plumbing(lab):
    _setup(lab, tfs=("H4",))
    out = register_all("testcommit")
    assert len(out) == len(SPEC) == 15 and registry.verify_chain()[0]
    assert registry.hypotheses_df()["status"].eq("registered").all()
    run = run_trial("H03_CONSOLIDATION_BREAKOUT", "XAUUSD", "H4", "dev", {"rr": 2.0, "max_hold": 30},
                    make_signal_fn("H03_CONSOLIDATION_BREAKOUT"), control=False)
    assert run["summary"]["n_trades"] >= 0
    pf = planned_family()
    assert pf["stage1_event_studies"] == 46 and pf["dev_trials_max"] == 82


def test_pair_with_too_few_events_is_recorded_not_tested_and_not_counted(lab):
    _setup(lab, tfs=("H4",))
    registry.register_hypothesis("H08E_GAP_AND_GO", "discovery_closed_set", "rare")
    before = registry.trial_count(("dev", "valid"))
    r = run_event_study("H08E_GAP_AND_GO", "XAUUSD", "H4", make_event_fn("H08E_GAP_AND_GO"), {"gap_atr": 0.5}, n_ctrl=100)
    assert r["summary"]["kind"] == "not_testable" and registry.trial_count(("dev", "valid")) == before
    assert any(e["type"] == "pair_not_testable" for e in registry.read_events()) and registry.verify_chain()[0]
