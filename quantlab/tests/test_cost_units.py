"""Cost UNIT audit (2026-11-05). Every number below was computed by hand and written as a literal.

Units: costs live in PRICE units per unit of the instrument (XAUUSD: USD per ounce; EURUSD: USD per EUR... i.e. quote units).
USD = price_cost x value_per_px_per_lot x lots.   R = price_cost / risk_px (independent of lots).
"""
import pandas as pd
import pytest

from conftest import mk
from quantlab.config import protocol_params
from quantlab.costs import build_scenarios
from quantlab.engine import Signal, run_backtest
from quantlab.sizing import apply_sizing

SPEC = {
    "XAUUSD": {"point": 0.01, "value_per_px_per_lot": 100.0, "contract_size": 100.0, "volume_min": 0.01, "volume_step": 0.01,
               "volume_max": 100.0, "verified": True, "tick_basis_conflict": False},
    "EURUSD": {"point": 1e-5, "value_per_px_per_lot": 100000.0, "contract_size": 100000.0, "volume_min": 0.01, "volume_step": 0.01,
               "volume_max": 100.0, "verified": True, "tick_basis_conflict": False},
}
LOTS = [0.01, 0.10, 1.00]


def base(sym):
    return build_scenarios(sym, SPEC[sym], protocol_params())["base"]


def run(sym, bars, sig):
    r = run_backtest(mk(bars, spread=0.0), [sig], base(sym))      # spread column 0 -> the research floor drives the spread
    assert len(r.trades) == 1
    return r.trades.iloc[0]


# (symbol, side, bars, stop, rr, max_hold) -> expected price-unit components and R, all hand-computed
# XAU long time-exit: fill 2000+0.10+0.05=2000.15, risk 10.15; exit close 2005 -0.10 slip = 2004.90; gross pnl 4.75+... see below
CASES = {
    "XAU_long_time": dict(sym="XAUUSD", side=1, bars=[(2000, 2001, 1999, 2000), (2000, 2006, 1999, 2005)], stop=1990.0, rr=None, hold=1,
                          risk=10.15, spread=0.10, comm=0.07, slip=0.15, net_px=4.68, gross_R=0.5, net_R=4.68 / 10.15),
    "XAU_short_time": dict(sym="XAUUSD", side=-1, bars=[(2000, 2001, 1999, 2000), (2000, 2001, 1994, 1995)], stop=2010.0, rr=None, hold=1,
                           risk=10.05, spread=0.10, comm=0.07, slip=0.15, net_px=4.68, gross_R=0.5, net_R=4.68 / 10.05),
    "EUR_long_time": dict(sym="EURUSD", side=1, bars=[(1.1, 1.1005, 1.0995, 1.1), (1.1, 1.1055, 1.0995, 1.105)], stop=1.09, rr=None, hold=1,
                          risk=0.01006, spread=0.00005, comm=0.00007, slip=0.00003, net_px=0.00485, gross_R=0.5, net_R=0.00485 / 0.01006),
    # EURUSD SELL (independent hand computation, symmetric to the long case):
    #   signal bar close 1.1000, entry = next open 1.1000; short sells at the BID: slippage in = -0.00001 -> fill 1.09999
    #   risk = |1.09999 - 1.11000| = 0.01001
    #   time exit at close 1.0950; a short is closed by BUYING at the ask: + spread 0.00005 -> 1.09505, + exit slippage 0.00002 -> 1.09507
    #   gross pnl (fill-to-fill) = 1.09999 - 1.09507 = 0.00492 ; commission 0.00007 -> net 0.00485 ; costs charged once each:
    #   spread 0.00005 + commission 0.00007 + slippage (0.00001 + 0.00002) 0.00003 = 0.00015 (identical to the long case)
    "EUR_short_time": dict(sym="EURUSD", side=-1, bars=[(1.1, 1.1005, 1.0995, 1.1), (1.1, 1.1005, 1.0945, 1.095)], stop=1.11, rr=None, hold=1,
                           risk=0.01001, spread=0.00005, comm=0.00007, slip=0.00003, net_px=0.00485, gross_R=0.5, net_R=0.00485 / 0.01001),
}


@pytest.mark.parametrize("name", list(CASES))
def test_trade_record_matches_hand_computation(name):
    c = CASES[name]
    t = run(c["sym"], c["bars"], Signal(0, c["side"], c["stop"], c["rr"], c["hold"]))
    assert t.risk_px == pytest.approx(c["risk"], abs=1e-9)
    assert t.spread_px == pytest.approx(c["spread"], abs=1e-12)
    assert t.commission_px == pytest.approx(c["comm"], abs=1e-12)
    assert t.slippage_px == pytest.approx(c["slip"], abs=1e-12)
    assert t.pnl_px_net == pytest.approx(c["net_px"], abs=1e-9)
    assert t.gross_R == pytest.approx(c["gross_R"], abs=1e-9)
    assert t.net_R == pytest.approx(c["net_R"], abs=1e-9)
    # cost (price units) = spread + commission + slippage, each charged once: XAU 0.10+0.07+0.15 = 0.32 ; EUR 0.00005+0.00007+0.00003 = 0.00015
    assert (c["spread"] + c["comm"] + c["slip"]) == pytest.approx(0.32 if c["sym"] == "XAUUSD" else 0.00015, abs=1e-12)


# USD per lot size, hand-computed:  XAU 0.32 px x 100 = 32 USD/lot (spread 10, slippage 15, commission 7);  EUR 0.00015 x 100000 = 15 USD/lot (5, 3, 7)
USD_PER_LOT = {"XAUUSD": dict(spread=10.0, slip=15.0, comm=7.0, total=32.0), "EURUSD": dict(spread=5.0, slip=3.0, comm=7.0, total=15.0)}


@pytest.mark.parametrize("lots", LOTS)
@pytest.mark.parametrize("name", list(CASES))
def test_usd_costs_scale_linearly_with_lots_and_r_does_not(name, lots):
    c = CASES[name]
    sym = c["sym"]
    t = run(sym, c["bars"], Signal(0, c["side"], c["stop"], c["rr"], c["hold"]))
    vpp = SPEC[sym]["value_per_px_per_lot"]
    usd = USD_PER_LOT[sym]
    assert t.spread_px * vpp * lots == pytest.approx(usd["spread"] * lots)
    assert t.slippage_px * vpp * lots == pytest.approx(usd["slip"] * lots)
    assert t.commission_px * vpp * lots == pytest.approx(usd["comm"] * lots)           # 7 USD per lot round trip, always
    assert (t.spread_px + t.slippage_px + t.commission_px) * vpp * lots == pytest.approx(usd["total"] * lots)
    # R = net USD pnl / USD risk, whatever the lot size
    assert (t.pnl_px_net * vpp * lots) / (t.risk_px * vpp * lots) == pytest.approx(t.net_R)


# end-to-end through the sizing module: choose equity so that the 0.5% planned risk gives exactly 0.01 / 0.10 / 1.00 lots
@pytest.mark.parametrize("lots", LOTS)
@pytest.mark.parametrize("name", list(CASES))
def test_sizing_pnl_usd_equals_hand_numbers(name, lots):
    c = CASES[name]
    sym = c["sym"]
    t = run(sym, c["bars"], Signal(0, c["side"], c["stop"], c["rr"], c["hold"]))
    vpp = SPEC[sym]["value_per_px_per_lot"]
    equity = lots * vpp * t.risk_px / 0.005                                          # 0.5% of equity == lots x USD-risk-per-lot
    df = pd.DataFrame([{**t.to_dict(), "symbol": sym}])
    out, summ = apply_sizing(df, SPEC, risk_pct=0.5, start_equity=equity)
    assert len(out) == 1 and out["lots"].iloc[0] == pytest.approx(lots)
    assert out["risk_pct_real"].iloc[0] == pytest.approx(0.5)
    assert out["pnl_usd"].iloc[0] == pytest.approx(c["net_px"] * vpp * lots)         # e.g. XAU long: 4.68 x 100 x lots
    assert out["pnl_usd"].iloc[0] / out["risk_usd_real"].iloc[0] == pytest.approx(c["net_R"])


def test_take_profit_exit_has_no_exit_slippage_in_usd():
    # XAU long, rr 2: fill 2000.15, risk 10.15, TP 2020.45 filled at the TP price; costs = spread 0.10 + slip_in 0.05 + comm 0.07 = 0.22 px
    t = run("XAUUSD", [(2000, 2001, 1999, 2000), (2000, 2021, 1999, 2020)], Signal(0, 1, 1990.0, 2.0, None))
    assert t.exit_reason == "tp" and t.tp == pytest.approx(2020.45)
    assert t.slippage_px == pytest.approx(0.05) and t.net_R == pytest.approx((20.30 - 0.07) / 10.15)
    assert (t.spread_px + t.slippage_px + t.commission_px) * 100 * 1.00 == pytest.approx(22.0)       # 22 USD per 1.00 lot


def test_documented_dev_mean_vs_floor_only_totals():
    """docs/COST_MODEL.md quotes 0.34 (XAU) with the DEV-mean effective spread 0.12; with the pure floor 0.10 it is 0.32."""
    cm = base("XAUUSD")
    assert cm.spread_floor_px == 0.10 and cm.commission_px == pytest.approx(0.07) and cm.slippage_in_px + cm.slippage_out_px == pytest.approx(0.15)
    e = base("EURUSD")
    assert e.spread_floor_px == pytest.approx(5e-5) and e.commission_px == pytest.approx(7e-5)
    assert (e.slippage_in_px + e.slippage_out_px) == pytest.approx(3e-5)


def test_eurusd_buy_and_sell_costs_are_symmetric_and_fills_are_on_the_correct_side():
    """Same price path mirrored: both directions pay exactly the same price-unit costs; the long fills ABOVE the open (ask side),
    the short fills BELOW it (bid side); exits are on the opposite sides."""
    buy = run("EURUSD", CASES["EUR_long_time"]["bars"], Signal(0, 1, 1.09, None, 1))
    sell = run("EURUSD", CASES["EUR_short_time"]["bars"], Signal(0, -1, 1.11, None, 1))
    assert buy.entry_fill == pytest.approx(1.10006, abs=1e-12)        # open + spread 0.00005 + slippage 0.00001 (ask side)
    assert sell.entry_fill == pytest.approx(1.09999, abs=1e-12)       # open - slippage 0.00001 (bid side, spread paid once on exit)
    assert buy.exit_fill == pytest.approx(1.10498, abs=1e-12)         # bid close 1.105 - exit slippage 0.00002
    assert sell.exit_fill == pytest.approx(1.09507, abs=1e-12)        # close 1.095 + spread 0.00005 + slippage 0.00002 (ask side)
    for k in ("spread_px", "commission_px", "slippage_px"):
        assert getattr(buy, k) == pytest.approx(getattr(sell, k), abs=1e-12)
    assert buy.pnl_px_net == pytest.approx(sell.pnl_px_net, abs=1e-12)
