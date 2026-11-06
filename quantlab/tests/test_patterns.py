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


H4 = pd.Timedelta(hours=4)


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
        ok = eligible(df, h, t.iloc[0], ee, H4)
        last_ok = np.where(ok)[0].max()
        assert last_ok == len(df) - 1 - h                # bar i needs bar i+h to exist
        assert not ok[len(df) - h:].any()                # the last h bars can never be events
        assert ok[len(df) - 1 - h]                       # ...and the last bar WITH a full horizon is still eligible
    # an evaluation window that ends BEFORE the data does: horizon bar must open before eval_end
    ee2 = t.iloc[300]
    ok5 = eligible(df, 5, t.iloc[0], ee2, H4)
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
        exp_window = np.where(eligible(df, h, es, ee, H4))[0]
        assert np.array_equal(seen[k], exp_window)                    # control candidates == eligible bars for THIS horizon
        row = tab[tab["horizon"] == h].iloc[0]
        assert row["n_control_candidates"] == len(exp_window)
        assert row["n"] == int(eligible(df, h, es, ee, H4)[idx].sum())    # events filtered by the same mask
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
    ab = t[t["kind"] == "aborted"].iloc[0]
    assert np.isnan(ab["p_raw"]) and ab["p_holm"] == 1.0 and ab["p_bonferroni"] == 1.0        # missing p: raw empty, adjusted = 1
    assert t["p_holm"].notna().all() and t["p_bonferroni"].notna().all()
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


# ---------------------------------------------------------------- bar CLOSE time at the DEV / VALID boundary (review round 2)
def _bars(tf_hours, start, n, seed=5):
    rng = np.random.default_rng(seed)
    t = pd.date_range(start, periods=n, freq=f"{tf_hours}h")
    c = 1000 + np.cumsum(rng.normal(0, 3, n))
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"time": t, "open": o, "high": np.maximum(o, c) + 1, "low": np.minimum(o, c) - 1, "close": c,
                         "tick_volume": 1, "spread": 0, "real_volume": 0})


@pytest.mark.parametrize("tf_hours,td", [(4, pd.Timedelta(hours=4)), (24, pd.Timedelta(days=1))])
@pytest.mark.parametrize("h", [1, 3, 5])
def test_horizon_bar_must_CLOSE_inside_dev_aligned_boundary(tf_hours, td, h):
    """DEV ends at 2019-01-01 00:00. The df also holds VALID bars. A horizon bar that closes exactly AT the boundary is allowed;
    the first VALID bar (opens at the boundary) never is - so no VALID movement is ever used by a DEV event."""
    from quantlab.events import eligible
    ee = pd.Timestamp("2019-01-01")
    n_before = 300
    df = _bars(tf_hours, ee - n_before * td, n_before + 80)
    t = pd.to_datetime(df["time"])
    first_valid = int(np.where(t >= ee)[0][0])                  # index of the first bar that opens at/after the boundary
    assert first_valid == n_before and t.iloc[first_valid - 1] + td == ee      # last DEV bar closes exactly at the boundary
    ok = eligible(df, h, t.iloc[0], ee, td)
    last_i = np.where(ok)[0].max()
    assert last_i + h == first_valid - 1                        # horizon bar = last DEV bar (closes AT ee): allowed
    assert not ok[last_i + 1:].any()                            # nothing later, in particular no horizon bar from VALID
    for i in np.where(ok)[0]:
        assert t.iloc[i + h] + td <= ee and t.iloc[i + 1] < ee


@pytest.mark.parametrize("tf_hours,td,ee", [(4, pd.Timedelta(hours=4), pd.Timestamp("2019-01-01 02:00")),
                                             (24, pd.Timedelta(days=1), pd.Timestamp("2019-01-01 12:00"))])
@pytest.mark.parametrize("h", [1, 5])
def test_bar_that_opens_before_but_closes_after_the_boundary_is_not_eligible(tf_hours, td, ee, h):
    """Boundary in the MIDDLE of a bar: that bar opens before ee but closes after it. The old open-time rule accepted it as a
    horizon bar; the close-time rule must not (part of its movement belongs to the next period)."""
    from quantlab.events import eligible
    df = _bars(tf_hours, pd.Timestamp("2019-01-01") - 300 * td, 380)
    t = pd.to_datetime(df["time"])
    straddle = int(np.where((t < ee) & (t + td > ee))[0][0])
    ok = eligible(df, h, t.iloc[0], ee, td)
    open_rule = np.zeros(len(df), bool)
    for i in range(len(df) - h):
        open_rule[i] = (t.iloc[i + 1] < ee) and (t.iloc[i + h] < ee)
    assert open_rule[straddle - h]                               # the OLD rule would have allowed using the straddling bar...
    assert not ok[straddle - h]                                  # ...the new rule does not
    assert np.where(ok)[0].max() + h == straddle - 1             # last allowed horizon bar closes at/before the boundary


@pytest.mark.parametrize("tf_hours,td", [(4, pd.Timedelta(hours=4)), (24, pd.Timedelta(days=1))])
def test_dev_event_study_is_blind_to_everything_after_the_boundary(tf_hours, td):
    """Replace every bar from VALID by absurd prices: the DEV event study (events AND control) must not change at all."""
    ee = pd.Timestamp("2019-01-01")
    df = _bars(tf_hours, ee - 600 * td, 700, seed=9)
    t = pd.to_datetime(df["time"])
    idx = np.arange(40, 590, 7)
    a = event_study(df, idx, 1, horizons=(1, 5), eval_start=t.iloc[0], eval_end=ee, n_ctrl=300, primary_h=5, n_ctrl_primary=300,
                    bar_td=td)
    df2 = df.copy()
    post = t >= ee
    for col in ("open", "high", "low", "close"):
        df2.loc[post, col] = df2.loc[post, col] * 50 + 10_000
    b = event_study(df2, idx, 1, horizons=(1, 5), eval_start=t.iloc[0], eval_end=ee, n_ctrl=300, primary_h=5, n_ctrl_primary=300,
                    bar_td=td)
    pd.testing.assert_frame_equal(a.drop(columns="control_warning"), b.drop(columns="control_warning"))
    c = event_study(df[~post], idx, 1, horizons=(1, 5), eval_start=t.iloc[0], eval_end=ee, n_ctrl=300, primary_h=5, n_ctrl_primary=300,
                    bar_td=td)                                                       # df physically truncated at the boundary
    pd.testing.assert_frame_equal(a.drop(columns="control_warning"), c.drop(columns="control_warning"))


# ---------------------------------------------------------------- control sets obey the real events' non-overlap rule (review round 2)
def test_control_sets_never_repeat_a_bar_and_keep_the_minimum_gap():
    from quantlab.events import _place_chunk
    rng = np.random.default_rng(3)
    n_bars, k, gap = 600, 40, 5
    shared = np.arange(30, 570)
    own = [np.arange(30, 570) if j % 3 else np.arange(100 + j, 400 + j) for j in range(k)]     # mixture of stratum pools
    picks, ok = _place_chunk(own, 500, n_bars, gap, rng)
    assert ok.mean() > 0.9
    for d in np.where(ok)[0]:
        row = picks[d]
        assert len(set(row)) == k                                     # no bar used twice
        assert all(row[j] in set(own[j]) for j in range(k))           # each control bar comes from its event's own pool
        s = np.sort(row)
        assert (np.diff(s) >= gap).all()                              # same non-overlap rule as event_arrays (gap >= 5)


def test_control_gap_rule_is_the_same_constant_as_the_real_event_dedup():
    from quantlab.patterns import EVENT_MIN_GAP, PRIMARY_HORIZON
    import inspect
    from quantlab import experiment
    assert EVENT_MIN_GAP == PRIMARY_HORIZON == 5
    assert "min_gap=EVENT_MIN_GAP" in inspect.getsource(experiment.run_event_study)


def test_tight_control_is_redrawn_until_complete_and_still_valid():
    """8 events packed exactly 5 bars apart in a short window: a single greedy placement fails ~40 % of the time, but fresh draws
    complete the requested number of sets, so coverage is 1 and the per-attempt success rate (< 1) is reported honestly."""
    df = _bars(4, "2018-01-01", 62, seed=4)
    t = pd.to_datetime(df["time"])
    tab = event_study(df, np.arange(12, 52, 5), 1, horizons=(1,), eval_start=t.iloc[0], eval_end=t.iloc[-1] + H4, n_ctrl=400, bar_td=H4)
    r = tab.iloc[0]
    assert r["control_coverage"] == 1.0 and r["control_complete"] and r["n_ctrl"] == 400
    assert 0.2 < r["control_placement_success"] < 0.95


def test_incomplete_control_is_reported_not_hidden():
    """20 events packed exactly 5 bars apart in a 130-bar window: a random control with the same non-overlap rule essentially cannot
    be built. The shortfall must show up as coverage << 1, an explicit warning with the numbers, complete=False; the table must not
    pretend the comparison is complete."""
    df = _bars(4, "2018-01-01", 130, seed=4)
    t = pd.to_datetime(df["time"])
    idx = np.arange(12, 112, 5)
    tab = event_study(df, idx, 1, horizons=(1,), eval_start=t.iloc[0], eval_end=t.iloc[-1] + H4, n_ctrl=400, bar_td=H4)
    r = tab.iloc[0]
    assert r["control_coverage"] < 0.90 and not r["control_complete"]
    assert "INCOMPLETE" in r["control_warning"] and "NOT a complete comparison" in r["control_warning"]
    assert f"all {r['n']} events" in r["control_warning"] and f"{r['n_control_candidates']} eligible bars" in r["control_warning"]
    assert r["n_ctrl"] == round(r["control_coverage"] * r["n_ctrl_requested"])          # p uses the built sets only
    assert r["control_placement_success"] < 0.05
    full = event_study(_bars(4, "2018-01-01", 1500, seed=4), np.arange(40, 1400, 25), 1, horizons=(1,), n_ctrl=300, bar_td=H4).iloc[0]
    assert full["control_coverage"] == 1.0 and full["control_warning"] == "" and full["control_complete"]


def _ar_series(n, phi, seed):
    rng = np.random.default_rng(seed)
    r = np.zeros(n)
    e = rng.normal(0, 3, n)
    for k in range(1, n):
        r[k] = phi * r[k - 1] + e[k]                                  # strongly autocorrelated returns = persistent trends
    c = 1000 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]]
    t = pd.date_range("2018-01-01", periods=n, freq="4h")
    return pd.DataFrame({"time": t, "open": o, "high": np.maximum(o, c) + 1, "low": np.minimum(o, c) - 1, "close": c,
                         "tick_volume": 1, "spread": 0, "real_volume": 0})


def test_autocorrelated_null_series_is_calibrated_1000_series():
    """1000 independent synthetic null series (AR(1) returns, phi = 0.8, H4, 1600 bars; 'events' = random bars de-duplicated to gap >= 5,
    no edge by construction; 400 control sets; series seed k, event seed 1000+k, k = 0..999; see quantlab.calibration.CalibConfig).
    Full results with confidence intervals for phi = 0.0 / 0.5 / 0.8 and for the OLD independent-draw control:
    docs/CONTROL_CALIBRATION.md (scripts/control_calibration.py).  Bounds below were fixed in advance as regression guards:
    no excess of small p-values (no false edge) and no deficit (old control gave 0.055 / 0.025)."""
    from quantlab.calibration import CalibConfig, run_calibration, summarize
    cfg = CalibConfig(n_series=1000, phi=0.8)
    res = summarize(run_calibration(cfg, procs=2))
    r10, r05 = res["alpha_0.1"], res["alpha_0.05"]
    assert res["min_coverage"] == 1.0                                   # every study built a complete control
    assert 0.08 <= r10["rate"] <= 0.14 and r10["ci99"][0] <= 0.10 <= r10["ci99"][1]
    assert 0.04 <= r05["rate"] <= 0.09
    assert 0.45 <= res["mean_p"] <= 0.56


def test_planted_edge_is_still_detected_with_the_gap_constrained_control():
    from quantlab.patterns import event_arrays, Ev
    df = _ar_series(2400, 0.3, 77)
    c = df["close"].to_numpy().copy()
    o = df["open"].to_numpy().copy()
    rng = np.random.default_rng(5)
    idx0 = np.sort(rng.choice(np.arange(60, 2300), size=160, replace=False))
    idx, _ = event_arrays([Ev(int(i), 1, 0.0) for i in idx0])
    bump = np.zeros(len(df))
    for i in idx:                                                       # +1 ATR-ish drift in the 5 bars after each event
        bump[i + 1:i + 6] += 4.0
    shift = np.cumsum(bump)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col] + shift
    t = pd.to_datetime(df["time"])
    tab = event_study(df, idx, 1, horizons=(5,), eval_start=t.iloc[0], eval_end=t.iloc[-1] + H4, n_ctrl=500, primary_h=5,
                      n_ctrl_primary=500, bar_td=H4)
    assert tab.iloc[0]["p_vs_random"] < 0.02 and tab.iloc[0]["edge_ATR"] > 0


def test_unbuildable_control_logs_a_trial_with_missing_p_and_can_never_pass_the_screen(lab):
    """Densely packed events (the control cannot be built): the pair stays in the family (planned size unchanged), p is None
    (treated as 1 by Holm), control_complete is False and the screen cannot pass - nothing is hidden or silently dropped."""
    from quantlab.hypotheses import event_screen_passed
    _setup(lab, tfs=("H4",))
    df, n = _dev_tail_indices(lab)
    dense = list(range(30, n - 12, 5))                                # events exactly 5 bars apart over the WHOLE window
    registry.register_hypothesis("DENSE", "test", "dense events")
    r = run_event_study("DENSE", "XAUUSD", "H4", _fake_events(df, dense), {}, n_ctrl=100, n_ctrl_primary=100, lookahead_check=False)
    s = r["summary"]
    assert r["trial_seq"] is not None and s["kind"] == "event_study" and s["n_events"] > 100
    assert s["control_complete"] is False and s["p_raw"] is None and "INCOMPLETE" in s["control_warning"]
    assert s["evaluation_status"] == "NOT_EVALUABLE_CONTROL_INFEASIBLE" and s["evaluation_status"] != "REJECTED"
    assert not event_screen_passed(s)
    t = registry.family_table()
    row = t[t["seq"] == r["trial_seq"]].iloc[0]
    assert np.isnan(row["p_raw"]) and len(t) == registry.trial_count(("dev", "valid"))            # counted in m, p_raw stays empty
    assert row["evaluation"] == "NOT_EVALUABLE_CONTROL_INFEASIBLE"
    assert row["p_holm"] == 1.0 and row["p_bonferroni"] == 1.0                                    # ...but its adjusted p is 1
    registry.close_family("t")
    assert registry.final_adjusted_p(r["trial_seq"]) == 1.0
    good = dict(s, evaluation_status="EVALUATED", control_complete=True, p_raw=0.04, edge_ATR=0.1)
    assert event_screen_passed(good) and not event_screen_passed(dict(good, p_raw=0.2)) and not event_screen_passed(dict(good, edge_ATR=-0.1))
    assert not event_screen_passed(dict(good, n_events=29)) and not event_screen_passed(dict(good, control_complete=False))
    assert not event_screen_passed(dict(good, evaluation_status="NOT_EVALUABLE_CONTROL_INFEASIBLE"))
