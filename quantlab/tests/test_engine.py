"""Engine verification on hand-computed cases and on a fair-coin random walk."""
import numpy as np
import pandas as pd
import pytest

from conftest import mk
from quantlab.costs import CostModel
from quantlab.engine import Signal, atr, check_no_lookahead, matched_control, run_backtest
from quantlab.stats import cluster_bootstrap

NOCOST = CostModel(name="t", spread_mode="none")


def one(df, sig, cm=NOCOST):
    r = run_backtest(df, [sig], cm)
    assert len(r.trades) == 1, r.rejects
    return r.trades.iloc[0]


def test_long_hits_target_exactly_2R():
    df = mk([(100, 100.2, 99.9, 100), (100, 103, 99.5, 102.5), (102.5, 103, 102, 102.8)])
    t = one(df, Signal(0, 1, 99.0, rr=2.0))
    assert t.exit_reason == "tp" and t.net_R == pytest.approx(2.0) and t.gross_R == pytest.approx(2.0)


def test_stop_assumed_first_when_both_touched():
    df = mk([(100, 100.2, 99.9, 100), (100, 103, 98.9, 101), (101, 102, 100, 101)])
    t = one(df, Signal(0, 1, 99.0, rr=2.0))
    assert t.exit_reason == "stop" and t.net_R == pytest.approx(-1.0)


def test_gap_through_stop_fills_at_open_not_stop():
    df = mk([(100, 100.2, 99.9, 100), (100, 100.5, 99.6, 99.8), (98, 98.5, 97, 97.5)])
    t = one(df, Signal(0, 1, 99.0, rr=3.0))
    assert t.exit_reason == "stop" and t.exit_fill == pytest.approx(98.0) and t.net_R == pytest.approx(-2.0)


def test_short_stop_triggers_on_ask_side():
    df = mk([(100, 100.1, 99.9, 100), (100, 100.9, 99.8, 100.2), (100.2, 100.5, 99.9, 100.1)], spread=0.2)
    cm = CostModel(name="t", spread_mode="measured", point=1.0)
    t = one(df, Signal(0, -1, 101.0, rr=None, max_hold=5), cm)
    assert t.exit_reason == "stop"          # high 100.9 + spread 0.2 = 101.1 >= 101
    assert t.net_R == pytest.approx(-1.0)


def test_commission_is_charged_in_R_of_this_trade():
    df = mk([(100, 100.2, 99.9, 100), (100, 103, 99.5, 102.5)])
    cm = CostModel(name="t", spread_mode="none", commission_usd_per_lot_rt=7.0, value_per_px_per_lot=100.0)
    t = one(df, Signal(0, 1, 99.0, rr=2.0), cm)
    assert t.net_R == pytest.approx(2.0 - 0.07) and t.cost_R == pytest.approx(0.07)


def test_cost_in_R_scales_inversely_with_stop_distance():
    cm = CostModel(name="t", spread_mode="none", commission_usd_per_lot_rt=7.0, value_per_px_per_lot=100.0, slippage_out_px=0.0)
    tight = mk([(100, 100.1, 99.95, 100), (100, 100.6, 99.9, 100.4)])
    wide = mk([(100, 100.1, 99.95, 100), (100, 105, 99.9, 104)])
    t1 = one(tight, Signal(0, 1, 99.5, rr=1.0), cm)    # risk 0.5
    t2 = one(wide, Signal(0, 1, 95.0, rr=1.0), cm)     # risk 5
    assert t1.cost_R == pytest.approx(0.07 / 0.5) and t2.cost_R == pytest.approx(0.07 / 5.0)


def test_spread_widens_actual_risk():
    df = mk([(100, 100.2, 99.9, 100), (100, 102, 99.5, 101.5)], spread=0.1)
    cm = CostModel(name="t", spread_mode="measured", point=1.0)
    t = one(df, Signal(0, 1, 99.0, rr=1.0), cm)
    assert t.risk_px == pytest.approx(1.1) and t.entry_fill == pytest.approx(100.1)


def test_time_exit_and_data_end_flag():
    df = mk([(100, 100.2, 99.9, 100), (100, 100.4, 99.8, 100.3), (100.3, 100.5, 100.0, 100.4), (100.4, 100.6, 100.1, 100.5)])
    t = one(df, Signal(0, 1, 99.0, rr=5.0, max_hold=2))
    assert t.exit_reason == "time" and t.bars_held == 2
    t2 = one(df, Signal(0, 1, 99.0, rr=5.0))
    assert t2.exit_reason == "data_end" and bool(t2.forced_close)


def test_concurrent_signal_is_skipped_and_counted():
    df = mk([(100, 100.2, 99.9, 100)] + [(100, 100.3, 99.8, 100.1)] * 10)
    r = run_backtest(df, [Signal(0, 1, 90.0, rr=50.0, max_hold=6), Signal(2, 1, 90.0, rr=50.0, max_hold=6)], NOCOST)
    assert len(r.trades) == 1 and r.rejects["skipped_concurrent"] == 1


def test_wrong_side_stop_is_rejected():
    df = mk([(100, 100.2, 99.9, 100), (100, 100.3, 99.8, 100.1)])
    r = run_backtest(df, [Signal(0, 1, 101.0, rr=1.0)], NOCOST)
    assert len(r.trades) == 0 and r.rejects["stop_wrong_side"] == 1


def _walk(n=6000, seed=3, sigma=0.002):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.standard_normal(n) * sigma))
    o = np.r_[100.0, c[:-1]]
    w = np.abs(rng.standard_normal(n)) * sigma * 100 * 0.4
    return mk(list(zip(o, np.maximum(o, c) + w, np.minimum(o, c) - w, c)), start="2018-01-01")


def test_fair_walk_has_zero_expectancy_without_costs_and_negative_with_costs():
    df = _walk()
    a = atr(df)
    sigs = [Signal(i, 1 if (i // 10) % 2 == 0 else -1, df.close[i] - (1 if (i // 10) % 2 == 0 else -1) * 1.0 * a[i], 1.0, 40)
            for i in range(30, len(df) - 50, 17)]
    r0 = run_backtest(df, sigs, NOCOST).trades
    ci = cluster_bootstrap(r0, n=2000, kind="month")
    assert ci["ci_low"] < 0 < ci["ci_high"], "no edge must not appear on a random walk with zero costs"
    cm = CostModel(name="c", spread_mode="fixed", spread_fixed_px=0.05, point=1.0, commission_usd_per_lot_rt=0.0)
    rc = run_backtest(df, sigs, cm).trades
    assert rc["net_R"].mean() < r0["net_R"].mean()
    assert rc["cost_R"].mean() > 0


def test_matched_control_does_not_flatter_a_random_signal():
    df = _walk(seed=11)
    a = atr(df)
    sigs = [Signal(i, 1, df.close[i] - 1.0 * a[i], 1.0, 40) for i in range(30, len(df) - 50, 25)]
    res = matched_control(df, sigs, NOCOST, df.time.min(), df.time.max() + pd.Timedelta(days=1), n_reps=100, seed=5)
    assert res["p_vs_control"] > 0.05


def test_lookahead_detector_flags_a_leaking_signal_and_passes_a_clean_one():
    df = _walk(n=1500, seed=5)

    def clean(d):
        sma = d.close.rolling(20).mean()
        return [Signal(i, 1, d.close.iloc[i] * 0.99, 1.0, 20) for i in range(21, len(d)) if d.close.iloc[i] > sma.iloc[i] and d.close.iloc[i - 1] <= sma.iloc[i - 1]]

    def leaky(d):
        nxt = d.close.shift(-1)  # uses the FUTURE bar
        return [Signal(i, 1, d.close.iloc[i] * 0.99, 1.0, 20) for i in range(len(d) - 1) if nxt.iloc[i] > d.close.iloc[i] * 1.001]

    assert check_no_lookahead(clean, df, n_checks=6) == []
    assert len(check_no_lookahead(leaky, df, n_checks=6)) > 0
