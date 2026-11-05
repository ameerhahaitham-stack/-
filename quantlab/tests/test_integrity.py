"""Statistical-integrity mechanisms: fair matched control, aborted trials counted, VALID->HOLD contamination, classification."""
import numpy as np
import pandas as pd
import pytest

from quantlab import data, registry, synth
from quantlab.config import root
from quantlab.engine import Signal, atr, matched_control, run_backtest
from quantlab.costs import CostModel
from quantlab.experiment import LookaheadError, neighbor_configs, neighbor_positive_share, run_trial
from quantlab.report import evaluate_valid
from test_stats_sizing_replay import _setup, donchian, leaky


def _frame(n=1500, seed=3):
    rng = np.random.default_rng(seed)
    t = pd.date_range("2018-01-01", periods=n, freq="4h")
    c = 1000 + np.cumsum(rng.normal(0, 3, n))
    o = np.r_[c[0], c[:-1]]
    h, l = np.maximum(o, c) + rng.uniform(0, 2, n), np.minimum(o, c) - rng.uniform(0, 2, n)
    return pd.DataFrame({"time": t, "open": o, "high": h, "low": l, "close": c, "tick_volume": 1, "spread": 0, "real_volume": 0})


CM = CostModel(name="t", spread_mode="none", point=1.0, value_per_px_per_lot=100.0)


def _sigs_at_slot(df, hour, k=1.5):
    a = atr(df, 14)
    return [Signal(i, 1, df["close"].iloc[i] - k * a[i], 2.0, 12) for i in range(30, len(df) - 20, 7)
            if df["time"].iloc[i].hour == hour and np.isfinite(a[i])]


def test_control_matches_trade_count_direction_and_reports_strata():
    df = _frame()
    sigs = _sigs_at_slot(df, 8)
    r = matched_control(df, sigs, CM, df["time"].iloc[0], df["time"].iloc[-1] + pd.Timedelta(hours=4), n_reps=30, seed=1)
    assert r["n_reps"] == 30 and r["real_long_share"] == 1.0            # direction is reproduced (all long)
    assert abs(r["control_trades_mean"] - r["real_trades"]) <= 0.2 * r["real_trades"] + 1   # frequency matched after sub-sampling
    assert sum(r["strata_levels_used"].values()) == r["real_trades"]
    assert r["strata_levels_used"]["year_slot_vol"] + r["strata_levels_used"]["year_slot"] > 0


def test_control_draws_only_from_the_same_time_slot():
    """If the real signals are all at 08:00 the control entries must all be at 08:00 too (exposure timing is matched)."""
    import quantlab.engine as eng
    df = _frame()
    sigs = _sigs_at_slot(df, 8)
    seen = []
    orig = eng.run_backtest

    def spy(d, s, *a, **k):
        seen.extend(x.i for x in s)
        return orig(d, s, *a, **k)
    eng.run_backtest = spy
    try:
        matched_control(df, sigs, CM, df["time"].iloc[0], df["time"].iloc[-1] + pd.Timedelta(hours=4), n_reps=5, seed=2)
    finally:
        eng.run_backtest = orig
    hours = {df["time"].iloc[i].hour for i in seen}
    assert hours == {8}


def test_control_is_not_beaten_by_pure_market_drift():
    """A strategy that is just 'long at 08:00 in an up year' must NOT look special against the matched control."""
    rng = np.random.default_rng(11)
    n = 3000
    t = pd.date_range("2018-01-01", periods=n, freq="4h")
    c = 1000 + np.cumsum(rng.normal(0.4, 3, n))                          # strong drift
    o = np.r_[c[0], c[:-1]]
    df = pd.DataFrame({"time": t, "open": o, "high": np.maximum(o, c) + 1, "low": np.minimum(o, c) - 1, "close": c,
                       "tick_volume": 1, "spread": 0, "real_volume": 0})
    sigs = _sigs_at_slot(df, 8)
    r = matched_control(df, sigs, CM, t[0], t[-1] + pd.Timedelta(hours=4), n_reps=60, seed=4)
    assert r["p_vs_control"] > 0.05                                      # same exposure -> no spurious edge


def test_failed_attempts_are_logged_and_counted(lab):
    _setup(lab)
    registry.register_hypothesis("LEAK", "x", "peeks")
    before = registry.trial_count(("dev", "valid"))
    with pytest.raises(LookaheadError):
        run_trial("LEAK", "XAUUSD", "H4", "dev", {}, leaky)
    assert registry.trial_count(("dev", "valid")) == before + 1          # the failed attempt is in the multiple-testing family
    ab = [e for e in registry.read_events() if e["type"] == "trial" and e["metrics"].get("aborted")]
    assert len(ab) == 1 and "LookaheadError" in ab[0]["metrics"]["reason"]
    assert registry.verify_chain()[0]


def test_valid_contaminated_hypothesis_can_never_reach_hold(lab):
    _setup(lab)
    cfg = [{"symbol": "XAUUSD", "tf": "H4", "params": {"n": 20, "k": 2.0, "rr": 2.0}}]
    registry.register_hypothesis("P1", "breakout", "parent")
    registry.freeze_hypothesis("P1", cfg)
    run_trial("P1", "XAUUSD", "H4", "valid", cfg[0]["params"], donchian, control=False)       # VALID results of the parent are seen
    registry.close_family("test")
    registry.record_verdict("P1", "valid", False)
    registry.register_hypothesis("C1", "breakout", "child tuned after seeing P1 on VALID", derived_from="P1")
    assert registry.valid_contaminated("C1") == ["P1"]
    registry.freeze_hypothesis("C1", cfg)
    registry.record_verdict("C1", "valid", True)
    with pytest.raises(registry.RegistryError, match="contaminated"):
        registry.request_hold("C1")
    registry.register_hypothesis("I1", "breakout", "independent, designed on DEV only")
    assert registry.valid_contaminated("I1") == []
    with pytest.raises(registry.RegistryError):
        registry.register_hypothesis("X", "b", "bad parent", derived_from="NOPE")


def test_classification_unproven_even_if_profitable_when_sample_is_small(lab):
    good = {"n_trades": 12, "expectancy_R_net": 0.9, "profit_factor_net": 3.0, "expectancy_ex_top5_R": 0.5, "p_adjusted_provisional": 0.001,
            "p_vs_control": 0.001, "positive_year_share": 1.0, "max_drawdown_R": 2.0, "total_R_net": 10.8, "m_family": 3,
            "scenarios": {"pessimistic": {"expectancy_R_net": 0.5}, "stress": {"profit_factor_net": 2.0}}}
    from quantlab.config import protocol_params
    small = dict(good, n_trades=protocol_params()["criteria"]["valid"]["min_trades"] - 1)
    FP = dict(neighbor_positive_share=0.9, final_adjusted_p=0.001)
    v = evaluate_valid(small, **FP)
    assert v["classification"] == "UNPROVEN_INSUFFICIENT_SAMPLE" and v["insufficient_sample"] and not v["passed"]
    neg_small = dict(small, expectancy_R_net=-0.3)
    assert evaluate_valid(neg_small, **FP)["classification"] == "UNPROVEN_INSUFFICIENT_SAMPLE"
    big = dict(good, n_trades=protocol_params()["criteria"]["valid"]["min_trades"] + 10)
    assert evaluate_valid(big, neighbor_positive_share=0.9, final_adjusted_p=0.5)["classification"] == "UNPROVEN"
    assert evaluate_valid(dict(big, expectancy_R_net=-0.2), neighbor_positive_share=0.9, final_adjusted_p=0.5)["classification"] == "REJECTED"


def test_neighbour_helpers():
    n = neighbor_configs({"n": 20, "rr": 2.0}, {"n": [10, 20, 30], "rr": [1.0, 2.0, 3.0]})
    assert {"n": 10, "rr": 2.0} in n and {"n": 30, "rr": 2.0} in n and {"n": 20, "rr": 1.0} in n and len(n) == 4
    assert neighbor_positive_share([0.1, -0.1, 0.2, 0.3]) == 0.75 and neighbor_positive_share([]) is None
