"""Cost-model audit: every cost is charged exactly once, on the right side, and converts to R as documented.
All expected numbers are computed by hand (see docs/COST_MODEL.md)."""
import pytest

from conftest import mk
from quantlab.costs import CostModel
from quantlab.engine import Signal, run_backtest

# point = 1.0 so that "spread points" == price units; commission 7 USD / 100 USD per px = 0.07 px
SP, COMM, SLIP_IN, SLIP_OUT = 0.2, 7.0, 0.05, 0.10


def cm(spread=0.0, comm=0.0, sin=0.0, sout=0.0):
    return CostModel(name="t", spread_mode="fixed" if spread else "none", spread_fixed_px=spread, point=1.0,
                     commission_usd_per_lot_rt=comm, value_per_px_per_lot=100.0, slippage_in_px=sin, slippage_out_px=sout)


def one(df, sig, c):
    r = run_backtest(df, [sig], c)
    assert len(r.trades) == 1
    return r.trades.iloc[0]


# ---------- full hand-computed trades (all costs on) ----------
def test_long_take_profit_all_costs():
    df = mk([(100, 100.2, 99.9, 100), (100, 103.5, 99.6, 103.0), (103, 103.2, 102.8, 103.0)])
    t = one(df, Signal(0, 1, 99.0, rr=2.0), cm(SP, COMM, SLIP_IN, SLIP_OUT))
    assert t.entry_fill == pytest.approx(100.25)                 # ask + slippage
    assert t.risk_px == pytest.approx(1.25)                      # |fill - stop|, spread and slippage are INSIDE the risk
    assert t.tp == pytest.approx(102.75)
    assert t.net_R == pytest.approx((2.5 - 0.07) / 1.25)         # TP is a limit: no exit slippage, commission once
    assert t.gross_R == pytest.approx(2.0)


def test_long_stop_all_costs():
    df = mk([(100, 100.2, 99.9, 100), (100, 100.3, 98.5, 99.0)])
    t = one(df, Signal(0, 1, 99.0, rr=2.0), cm(SP, COMM, SLIP_IN, SLIP_OUT))
    assert t.exit_fill == pytest.approx(98.90)                   # stop level minus exit slippage
    assert t.net_R == pytest.approx((-1.35 - 0.07) / 1.25)
    assert t.gross_R == pytest.approx(-1.0)


def test_short_take_profit_all_costs():
    df = mk([(100, 100.1, 99.9, 100), (100, 100.3, 97.5, 98.0), (98, 98.3, 97.8, 98.0)])
    t = one(df, Signal(0, -1, 101.0, rr=2.0), cm(SP, COMM, SLIP_IN, SLIP_OUT))
    assert t.entry_fill == pytest.approx(99.95)                  # bid minus slippage; spread is paid at the exit side
    assert t.risk_px == pytest.approx(1.05)
    assert t.tp == pytest.approx(97.85)                          # bar low 97.5 + spread 0.2 = 97.7 <= 97.85 -> filled at 97.85
    assert t.net_R == pytest.approx((2.10 - 0.07) / 1.05)


def test_short_stop_all_costs():
    df = mk([(100, 100.1, 99.9, 100), (100, 100.9, 99.8, 100.2)])
    t = one(df, Signal(0, -1, 101.0, rr=2.0), cm(SP, COMM, SLIP_IN, SLIP_OUT))
    assert t.exit_reason == "stop"                               # high 100.9 + spread 0.2 = 101.1 >= 101.0
    assert t.exit_fill == pytest.approx(101.10)
    assert t.net_R == pytest.approx((-1.15 - 0.07) / 1.05)


# ---------- each cost charged exactly once (differences against the zero-cost run, same exit path) ----------
def _time_exit_pair(side):
    df = mk([(100, 100.2, 99.9, 100), (100, 100.6, 99.8, 100.3), (100.3, 100.7, 100.0, 100.4)])
    stop = 90.0 if side == 1 else 110.0
    return df, Signal(0, side, stop, rr=None, max_hold=2)


@pytest.mark.parametrize("side", [1, -1])
def test_spread_is_charged_exactly_once_per_round_trip(side):
    df, sg = _time_exit_pair(side)
    z, s = one(df, sg, cm()), one(df, sg, cm(spread=SP))
    assert z.pnl_px_net - s.pnl_px_net == pytest.approx(SP)      # long pays it at entry (ask), short at exit (ask)


@pytest.mark.parametrize("side", [1, -1])
def test_commission_is_charged_exactly_once(side):
    df, sg = _time_exit_pair(side)
    z, c = one(df, sg, cm()), one(df, sg, cm(comm=COMM))
    assert z.pnl_px_net - c.pnl_px_net == pytest.approx(0.07)


@pytest.mark.parametrize("side", [1, -1])
def test_slippage_is_charged_once_on_entry_and_once_on_a_market_exit(side):
    df, sg = _time_exit_pair(side)
    z, s = one(df, sg, cm()), one(df, sg, cm(sin=SLIP_IN, sout=SLIP_OUT))
    assert z.pnl_px_net - s.pnl_px_net == pytest.approx(SLIP_IN + SLIP_OUT)


def test_take_profit_limit_has_no_exit_slippage():
    df = mk([(100, 100.2, 99.9, 100), (100, 103.5, 99.6, 103.0)])
    sg = Signal(0, 1, 99.0, rr=2.0)
    a, b = one(df, sg, cm(sin=SLIP_IN)), one(df, sg, cm(sin=SLIP_IN, sout=5.0))
    assert a.pnl_px_net == pytest.approx(b.pnl_px_net)


def test_spread_stop_out_is_minus_one_R_and_cost_shows_up_in_distance_not_in_r():
    """Documented property: because R uses the real (spread-inclusive) risk, a pure-spread stop-out is exactly -1R.
    The spread's cost appears as a wider stop/target geometry (lower hit-rate) and smaller lots, not as a worse stop R."""
    df = mk([(100, 100.2, 99.9, 100), (100, 100.3, 98.5, 99.0)])
    t = one(df, Signal(0, 1, 99.0, rr=2.0), cm(spread=SP))
    assert t.net_R == pytest.approx(-1.0) and t.risk_px == pytest.approx(1.2) and t.cost_R == pytest.approx(0.0)


def test_cost_pct_of_stop_is_the_planned_R_view_of_cost():
    df = mk([(100, 100.2, 99.9, 100), (100, 103.5, 99.6, 103.0)])
    t = one(df, Signal(0, 1, 99.0, rr=2.0), cm(SP, COMM, SLIP_IN, SLIP_OUT))
    expected = (SP + 0.07 + SLIP_IN + 0.0) / 1.25               # TP exit: no exit slippage
    assert t.cost_pct_of_stop == pytest.approx(expected)


# ---------- XAUUSD tick-value contradiction: effect on sizing and on commission-in-price ----------
from quantlab.costs import build_scenarios
from quantlab.config import protocol_params
from quantlab.sizing import real_risk_under_truth


def test_assuming_the_larger_value_per_px_errs_on_the_safe_side():
    safe = real_risk_under_truth(10000, 0.5, 20.0, assumed_vpp=100, true_vpp=10)      # assume 100, truth 10
    danger = real_risk_under_truth(10000, 0.5, 20.0, assumed_vpp=10, true_vpp=100)    # assume 10, truth 100
    ok = real_risk_under_truth(10000, 0.5, 20.0, assumed_vpp=100, true_vpp=100)
    assert safe["real_risk_pct"] < ok["real_risk_pct"] < danger["real_risk_pct"]
    assert danger["real_risk_pct"] == pytest.approx(5.0) and safe["real_risk_pct"] == pytest.approx(0.04)   # 10x over-risk vs 10x under-risk


def test_min_lot_rejects_wide_gold_stops_on_a_small_account():
    r = real_risk_under_truth(10000, 0.5, 60.0, assumed_vpp=100, true_vpp=100)         # 0.01 lot would risk 60 USD > 50 USD
    assert r["rejected_below_min_lot"]


def test_commission_in_price_is_10x_larger_if_tick_value_is_the_true_basis():
    pp = protocol_params()
    specs = {"point": 0.01, "value_per_px_per_lot": 100.0, "tick_basis_conflict": True, "verified": False}
    sc = build_scenarios("XAUUSD", specs, pp)
    assert "stress_tickvalue" in sc
    assert sc["base"].commission_px == pytest.approx(0.07)
    assert sc["stress_tickvalue"].commission_px == pytest.approx(7.0 * 1.5 / 10.0)      # 1.05 px: 15x the base commission in price
    sc2 = build_scenarios("XAUUSD", {**specs, "verified": True}, pp)                  # after OrderCalcProfit check the scenario disappears
    assert "stress_tickvalue" not in sc2
    sc3 = build_scenarios("EURUSD", {"point": 0.00001, "value_per_px_per_lot": 100000.0, "tick_basis_conflict": False}, pp)
    assert "stress_tickvalue" not in sc3
