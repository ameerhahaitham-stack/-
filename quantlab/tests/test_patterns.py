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


# ---------------------------------------------------------------- boundary tests near the END of DEV (review of PR #5)
def _flat(n=400, seed=2):
    return _trendy(n=n, seed=seed)


def test_eligibility_excludes_events_without_a_full_horizon_at_the_window_end():
    from quantlab.events import eligible
    df = _flat(400)
    t = pd.to_datetime(df["time"])
    ee = t.iloc[-1] + pd.Timedelta(hours=4)             # window ends right after the last bar (like DEV end)
    for h in (1, 3, 5, 10, 20):
        ok = eligible(df, h, t.iloc[0], ee)
        last_ok = np.where(ok)[0].max()
        assert last_ok == len(df) - 1 - h                # bar i needs bar i+h to exist
        assert not ok[len(df) - h:].any()                # the last h bars can never be events
        assert ok[len(df) - 1 - h]                       # ...and the last bar WITH a full horizon is still eligible
    # an evaluation window that ends BEFORE the data does: horizon bar must open before eval_end
    ee2 = t.iloc[300]
    ok5 = eligible(df, 5, t.iloc[0], ee2)
    assert (t.iloc[np.where(ok5)[0] + 5] < ee2).all() and (t.iloc[np.where(ok5)[0] + 1] < ee2).all()
    assert not ok5[300 - 5:].any()


def test_events_without_full_horizon_never_enter_the_event_sample():
    df = _flat(400)
    t = pd.to_datetime(df["time"])
    ee = t.iloc[-1] + pd.Timedelta(hours=4)
    idx = np.array([100, 200, 394, 395, 396, 398, 399])          # 394 is the last with full h=5 horizon (399-5)
    tab = event_study(df, idx, 1, horizons=(1, 5), eval_start=t.iloc[0], eval_end=ee, n_ctrl=50, primary_h=5, n_ctrl_primary=50)
    n = dict(zip(tab["horizon"], tab["n"]))
    assert n[5] == 3 and n[1] == 6          # h=5: {100,200,394}; h=1: everything up to bar 398 (399+1 does not exist)


def test_events_and_control_use_the_same_eligibility_rule_per_horizon(monkeypatch):
    """Spy on the pools: for every horizon the control window must equal the set the real events are filtered by."""
    import quantlab.events as ev
    from quantlab.events import eligible
    df = _flat(500)
    t = pd.to_datetime(df["time"])
    es, ee = t.iloc[30], t.iloc[430]                                  # eval window strictly inside the data
    seen = {}
    orig = ev._control_pools

    def spy(d, window, strata=None):
        seen[len(seen)] = np.array(window)
        return orig(d, window, strata)

    monkeypatch.setattr(ev, "_control_pools", spy)
    idx = np.arange(40, 480, 9)
    horizons = (1, 5, 20)
    tab = event_study(df, idx, 1, horizons=horizons, eval_start=es, eval_end=ee, n_ctrl=40, primary_h=5, n_ctrl_primary=40)
    for k, h in enumerate(horizons):
        exp_window = np.where(eligible(df, h, es, ee))[0]
        assert np.array_equal(seen[k], exp_window)                    # control candidates == eligible bars for THIS horizon
        row = tab[tab["horizon"] == h].iloc[0]
        assert row["n_control_candidates"] == len(exp_window)
        assert row["n"] == int(eligible(df, h, es, ee)[idx].sum())    # events filtered by the same mask
    n_by_h = tab.set_index("horizon")["n"]
    assert n_by_h[1] >= n_by_h[5] >= n_by_h[20]                       # longer horizon -> never MORE eligible events


def _fake_events(df, ids):
    from quantlab.patterns import Ev
    return lambda d, **kw: [Ev(int(i), 1, float(d["close"].iloc[i]) - 5.0) for i in ids]


def _dev_tail_indices(lab):
    df, es, ee, _ = data.load_with_context("XAUUSD", "H4", "dev")
    return df, len(df)


def test_run_event_study_counts_only_eligible_events_for_the_30_event_minimum(lab):
    _setup(lab, tfs=("H4",))
    df, n = _dev_tail_indices(lab)
    h = 5
    body = list(range(60, 60 + 30 * 6, 6))                       # 30 well-spaced eligible events (gap 6 >= 5)
    assert len(body) == 30 and body[-1] < n - 1 - h
    last_ok, bad = n - 1 - h, n - 1                               # last bar with a full horizon; a bar with none
    # 29 eligible + 1 ineligible at the very end of DEV  -> only 29 eligible -> NOT testable
    registry.register_hypothesis("B29", "test", "29 eligible + 1 without horizon")
    r = run_event_study("B29", "XAUUSD", "H4", _fake_events(df, body[:29] + [bad]), {}, n_ctrl=50, n_ctrl_primary=50, lookahead_check=False)
    assert r["summary"]["kind"] == "not_testable" and r["summary"]["n_events"] == 29
    nt = [e for e in registry.read_events() if e["type"] == "pair_not_testable"][-1]
    assert nt["detail"]["n_events_raw"] == 30 and nt["detail"]["n_eligible_dedup"] == 29
    # 30 eligible + 1 ineligible -> exactly 30 eligible -> testable (boundary case)
    registry.register_hypothesis("B30", "test", "30 eligible + 1 without horizon")
    r = run_event_study("B30", "XAUUSD", "H4", _fake_events(df, body + [bad]), {}, n_ctrl=50, n_ctrl_primary=50, lookahead_check=False)
    assert r["summary"]["kind"] == "event_study" and r["summary"]["n_events"] == 30 and r["summary"]["n_events_raw"] == 31
    # the last bar WITH a full horizon is accepted as an event; the one just after it is not
    registry.register_hypothesis("B30E", "test", "30 events, last one exactly at n-1-h")
    r = run_event_study("B30E", "XAUUSD", "H4", _fake_events(df, body[:29] + [last_ok, last_ok + 1]), {}, n_ctrl=50, n_ctrl_primary=50,
                        lookahead_check=False)
    assert r["summary"]["kind"] == "event_study" and r["summary"]["n_events"] == 30


def test_matched_control_may_use_the_last_possible_signal_bar():
    """Strategy controls: a control signal needs an entry bar i+1, so the last admissible signal bar is n-2 (inclusive)."""
    from quantlab.engine import _control_pools
    df = _flat(300)
    window = np.arange(100, len(df))
    pools, _, _, _ = _control_pools(df, window[window < len(df) - 1])
    allbars = np.concatenate(list(pools.values()))
    assert allbars.max() == len(df) - 2 and (allbars < len(df) - 1).all()


# ---------------------------------------------------------------- family-wide Holm on raw p-values
def _log_p(hid, p, kind="event_study", split="dev"):
    return registry.log_trial(hid, "XAUUSD", "H4", split, {"k": float(p)}, {"kind": kind, "p_raw": p, "p_adjusted_provisional": min(1.0, p * 2)},
                              "test", synthetic=True)


def test_family_table_keeps_raw_p_and_recomputes_holm_over_the_complete_family(lab, monkeypatch):
    monkeypatch.setenv("QUANTLAB_ALLOW_SYNTH", "1")
    registry.lock_protocol()
    registry.register_hypothesis("F1", "t", "d")
    ps = [0.001, 0.02, 0.04, 0.30]
    for p in ps:
        _log_p("F1", p)
    registry.log_trial("F1", "XAUUSD", "H4", "dev", {"k": 99.0}, {"aborted": True, "reason": "boom"}, "test", synthetic=True)  # aborted: p treated as 1
    t = registry.family_table()
    assert len(t) == 5 and (t["status"] == "PROVISIONAL").all()
    assert sorted(t["p_raw"].dropna()) == ps                                     # every raw p preserved
    # Holm with m = 5 (the aborted trial counts): sorted p -> 0.001*5, 0.02*4, 0.04*3, 0.30*2, with running max
    h = dict(zip(t["p_raw"].round(4), t["p_holm"]))
    assert h[0.001] == pytest.approx(0.005) and h[0.02] == pytest.approx(0.08) and h[0.04] == pytest.approx(0.12) and h[0.3] == pytest.approx(0.6)
    with pytest.raises(registry.RegistryError, match="PROVISIONAL|open"):
        registry.final_adjusted_p(int(t["seq"].iloc[0]))                          # no final value before the family is closed
    registry.close_family("complete")
    assert (registry.family_table()["status"] == "FINAL").all()
    assert registry.final_adjusted_p(int(t["seq"].iloc[0])) == pytest.approx(0.005)
    # the staged value written at run time is NOT what final_adjusted_p returns
    assert t["p_staged_at_run"].iloc[0] != registry.final_adjusted_p(int(t["seq"].iloc[0]))
    assert registry.verify_chain()[0]


def test_closed_family_refuses_new_dev_and_valid_trials_and_code_update_cannot_change_definitions(lab, monkeypatch):
    monkeypatch.setenv("QUANTLAB_ALLOW_SYNTH", "1")
    registry.lock_protocol()
    registry.register_hypothesis("F2", "t", "d")
    _log_p("F2", 0.5)
    registry.close_family("done")
    with pytest.raises(registry.RegistryError, match="CLOSED"):
        _log_p("F2", 0.01)
    with pytest.raises(registry.RegistryError, match="already closed"):
        registry.close_family()
    registry.log_code_update("abc1234", "eligibility fix", {"patterns.py": "x", "SPEC": "y"})
    with pytest.raises(registry.RegistryError, match="NEW hypothesis"):
        registry.log_code_update("abc1235", "changed a rule", {}, definitions_changed=True)
    assert registry.verify_chain()[0]


def test_valid_verdict_requires_closed_family(lab, monkeypatch):
    monkeypatch.setenv("QUANTLAB_ALLOW_SYNTH", "1")
    registry.lock_protocol()
    registry.register_hypothesis("F3", "t", "d")
    registry.freeze_hypothesis("F3", [{"symbol": "XAUUSD", "tf": "H4", "params": {}}])
    with pytest.raises(registry.RegistryError, match="family"):
        registry.record_verdict("F3", "valid", True)
    registry.close_family("x")
    registry.record_verdict("F3", "valid", False)
