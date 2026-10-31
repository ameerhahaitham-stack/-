"""Stats, sizing, charts/replay (no future leakage) and the end-to-end official pipeline."""
import json

import numpy as np
import pandas as pd
import pytest

from quantlab import data, registry, synth
from quantlab.charts import candlestick, example_gallery, trade_charts
from quantlab.config import root
from quantlab.engine import Signal, atr
from quantlab.events import event_study
from quantlab.experiment import LookaheadError, run_trial
from quantlab.replay import Replay
from quantlab.report import evaluate_hold, evaluate_valid, registry_report_md, trial_report_md
from quantlab.sizing import apply_sizing
from quantlab.stats import adjust_p, benjamini_hochberg, bonferroni, cluster_bootstrap, holm, trade_metrics


# ----------------------------------------------------------------- stats
def test_multiple_testing_corrections():
    p = np.array([0.001, 0.01, 0.04, 0.5])
    assert (holm(p) >= p).all() and (bonferroni(p) >= holm(p) - 1e-12).all()
    assert holm(p)[0] == pytest.approx(0.004)
    assert holm(p, m=100)[0] == pytest.approx(0.1)           # other logged trials count against you
    assert (benjamini_hochberg(p) <= bonferroni(p) + 1e-12).all()
    assert adjust_p(0.01, 50) == pytest.approx(0.5)


def _trades(r, start="2020-01-01"):
    t = pd.date_range(start, periods=len(r), freq="7D")
    return pd.DataFrame({"entry_time": t, "exit_time": t + pd.Timedelta(days=1), "net_R": r, "gross_R": np.array(r) + 0.1,
                         "cost_R": 0.1, "cost_pct_of_stop": 0.1, "bars_held": 3})


def test_bootstrap_separates_real_edge_from_noise():
    rng = np.random.default_rng(0)
    strong = cluster_bootstrap(_trades(rng.normal(0.5, 1.0, 300)), n=2000)
    noise = cluster_bootstrap(_trades(rng.normal(0.0, 1.0, 300)), n=2000)
    assert strong["p_raw"] < 0.01 and strong["ci_low"] > 0
    assert noise["p_raw"] > 0.05


def test_metrics_set_is_complete_and_top5_dependence_visible():
    r = np.r_[np.full(5, 10.0), np.full(95, -0.3)]
    m = trade_metrics(_trades(r))
    for k in ["win_rate", "profit_factor_net", "expectancy_R_net", "avg_win_R", "avg_loss_R", "total_R_net", "max_drawdown_R",
              "max_losing_streak", "n_trades", "avg_bars_held", "expectancy_R_gross", "avg_cost_R"]:
        assert k in m
    assert m["expectancy_R_net"] > 0 and m["expectancy_ex_top5_R"] < 0     # profit depends on 5 trades


# ----------------------------------------------------------------- sizing
SPECS = {"XAUUSD": dict(value_per_px_per_lot=100.0, contract_size=100.0, volume_min=0.01, volume_step=0.01, volume_max=100.0)}


def _t(entry, risk_px, pnl_px, price=2000.0):
    e = pd.Timestamp(entry)
    return dict(symbol="XAUUSD", entry_time=e, exit_time=e + pd.Timedelta(hours=5), side=1, entry_fill=price, risk_px=risk_px, pnl_px_net=pnl_px)


def test_sizing_rounds_down_rejects_below_min_and_reports_real_risk():
    tr = pd.DataFrame([_t("2020-01-06 10:00", 10.0, 20.0), _t("2020-01-07 10:00", 5000.0, -5000.0)])
    out, s = apply_sizing(tr, SPECS, risk_pct=0.5, start_equity=10000)
    assert len(out) == 1 and s["rejected"]["below_min_lot"] == 1
    assert out.lots.iloc[0] == pytest.approx(0.05) and out.risk_pct_real.iloc[0] == pytest.approx(0.5)


def test_leverage_cap_is_flagged_with_the_real_risk_not_the_planned_one():
    tr = pd.DataFrame([_t("2020-01-06 10:00", 1.0, -1.0)])           # tight stop -> 0.50 lots wanted, 5x cap allows 0.25
    out, s = apply_sizing(tr, SPECS, risk_pct=0.5, start_equity=10000, max_leverage=5)
    assert bool(out.leverage_capped.iloc[0]) and s["leverage_capped_trades"] == 1
    assert out.lots.iloc[0] == pytest.approx(0.25) and out.risk_pct_real.iloc[0] == pytest.approx(0.25)   # real risk half the plan


def test_daily_loss_limit_blocks_entries():
    tr = pd.DataFrame([_t("2020-01-06 01:00", 10.0, -10.0), _t("2020-01-06 08:00", 10.0, -10.0), _t("2020-01-06 20:00", 10.0, 10.0)])
    out, s = apply_sizing(tr, SPECS, risk_pct=0.5, start_equity=10000, daily_loss_limit_pct=0.8)
    assert s["rejected"]["daily_loss_limit"] >= 1 and len(out) < 3


# ----------------------------------------------------------------- charts / replay
def _df():
    m15 = synth.make_m15("EURUSD", "2018-01-01", "2018-03-31", seed=2)
    return synth.aggregate(m15, "H1")


def test_replay_never_exposes_future_bars(tmp_path):
    df = _df()
    r = Replay(df, start=df.time.iloc[300], window=80)
    for _ in range(25):
        assert r.visible().time.max() == r.now and len(r.visible()) == r.cursor + 1
        assert r.visible_window().time.max() == r.now
        r.step(7)
    r.set_speed(3)
    r.step()
    assert r.cursor == 300 + 25 * 7 + 3
    r.render(tmp_path / "f.png")
    assert (tmp_path / "f.png").stat().st_size > 5000
    full_last = df.time.iloc[-1]
    r.jump_to(df.time.iloc[10])
    assert r.visible().time.max() < full_last and len(r.visible()) == 11


def test_replay_hides_exit_and_shows_stop_only_while_open(tmp_path):
    df = _df()
    e, x = 400, 420
    trades = pd.DataFrame([{"entry_time": df.time[e], "exit_time": df.time[x], "side": 1, "entry_fill": df.close[e], "stop": df.close[e] * 0.99,
                            "tp": df.close[e] * 1.02, "exit_fill": df.close[x], "net_R": 1.5}])
    r = Replay(df, start=df.time[e + 3], window=60, trades=trades)
    m, lines = r._overlays(r.visible_window())
    assert any(k["kind"] == "exit" for k in m) is False and len(lines) == 2          # open position: stop/target visible, no exit yet
    r.jump_to(df.time[x + 2])
    m, lines = r._overlays(r.visible_window())
    assert any(k["kind"] == "exit" for k in m) and lines == []


def test_replay_video_export_uses_only_past_bars(tmp_path):
    df = _df()
    r = Replay(df, start=df.time.iloc[200], window=50)
    out = r.export_video(tmp_path / "clip.gif", n_frames=4, fps=4, stride=5)
    assert out.endswith(".gif") and (tmp_path / "clip.gif").stat().st_size > 1000
    assert r.cursor == 200                       # export does not move the cursor


def test_gallery_samples_losers_as_well_as_winners(tmp_path):
    df = _df()
    a = atr(df)
    sigs = [Signal(i, 1, df.close[i] - a[i], 1.0, 20) for i in range(30, len(df) - 40, 15)]
    from quantlab.costs import ZERO
    from quantlab.engine import run_backtest
    tr = run_backtest(df, sigs, ZERO).trades
    g = example_gallery(df, tr, "demo", tmp_path, n_each=2, seed=4)
    assert len(g["wins"]) == 2 and len(g["losses"]) == 2
    for item in g["wins"] + g["losses"]:
        assert (tmp_path / item["before"].split("/")[-1]).exists() and (tmp_path / item["after"].split("/")[-1]).exists()


def test_event_study_finds_nothing_in_noise_and_something_in_planted_effect():
    m15 = synth.make_m15("EURUSD", "2018-01-01", "2019-12-31", seed=8)
    df = synth.aggregate(m15, "H1").reset_index(drop=True)
    rng = np.random.default_rng(1)
    idx = np.sort(rng.choice(np.arange(50, len(df) - 30), 400, replace=False))
    noise = event_study(df, idx, 1, horizons=(5,), n_ctrl=500)
    assert noise.loc[0, "p_vs_random"] > 0.02
    # planted effect: for the marked events, bar i+5 closes 1 ATR above bar i+1's open
    a = atr(df)
    d3 = df.copy()
    for i in idx:
        d3.loc[i + 5, "close"] = d3.loc[i + 1, "open"] + 1.0 * a[i]
        d3.loc[i + 5, "high"] = max(d3.loc[i + 5, "high"], d3.loc[i + 5, "close"])
    planted = event_study(d3, idx, 1, horizons=(5,), n_ctrl=500)
    assert planted.loc[0, "p_vs_random"] < 0.01 and planted.loc[0, "edge_ATR"] > 0.3


# ----------------------------------------------------------------- end-to-end official pipeline
def donchian(df, n=20, k=2.0, rr=2.0):
    a = atr(df, 14)
    hh = df["high"].rolling(n).max().shift(1).to_numpy()
    c = df["close"].to_numpy()
    return [Signal(i, 1, c[i] - k * a[i], rr, 30) for i in range(n + 1, len(df)) if c[i] > hh[i] and np.isfinite(a[i])]


def leaky(df, **kw):
    nxt = df["close"].shift(-1)
    return [Signal(i, 1, df["close"].iloc[i] * 0.99, 1.0, 10) for i in range(40, len(df) - 1) if nxt.iloc[i] > df["close"].iloc[i]]


def _setup(lab, tfs=("H4",)):
    synth.make_all(root() / "data" / "incoming", symbols=("XAUUSD",), start="2018-01-01", end="2019-12-31", tfs=tfs, seed=5)
    for tf in tfs:
        data.ingest(root() / "data" / "incoming" / f"SYNTH_XAUUSD_{tf}.csv", "XAUUSD", tf, "synthetic test data", synthetic=True)
    registry.lock_protocol()


def test_end_to_end_pipeline_and_gates(lab):
    _setup(lab)
    registry.register_hypothesis("DON1", "breakout", "20-bar high breakout, ATR stop")
    with pytest.raises(registry.RegistryError):                        # cannot touch VALID before freezing
        run_trial("DON1", "XAUUSD", "H4", "valid", {"n": 20}, donchian)
    with pytest.raises(data.HoldLockedError):
        data.load_with_context("XAUUSD", "H4", "hold")
    run = run_trial("DON1", "XAUUSD", "H4", "dev", {"n": 20, "k": 2.0, "rr": 2.0}, donchian)
    s = run["summary"]
    assert s["n_trades"] > 20 and "p_adjusted" in s and set(s["scenarios"]) == {"optimistic", "base", "pessimistic", "stress"}
    assert s["scenarios"]["optimistic"]["expectancy_R_net"] >= s["scenarios"]["stress"]["expectancy_R_net"]
    assert s["avg_cost_R"] > 0 and s["m_family"] == 1
    assert list((root() / "results" / "DON1").glob("dev_*_trades.csv"))
    with pytest.raises(LookaheadError):
        registry.register_hypothesis("LEAK", "x", "peeks")
        run_trial("LEAK", "XAUUSD", "H4", "dev", {}, leaky)
    registry.freeze_hypothesis("DON1", [{"symbol": "XAUUSD", "tf": "H4", "params": {"n": 20, "k": 2.0, "rr": 2.0}}])
    with pytest.raises(registry.RegistryError):
        run_trial("DON1", "XAUUSD", "H4", "valid", {"n": 25, "k": 2.0, "rr": 2.0}, donchian)   # changed params
    v = run_trial("DON1", "XAUUSD", "H4", "valid", {"n": 20, "k": 2.0, "rr": 2.0}, donchian)
    assert v["eval"][0] == pd.Timestamp("2019-01-01")
    assert v["trades"]["entry_time"].min() >= pd.Timestamp("2019-01-01") and v["trades"]["entry_time"].max() < pd.Timestamp("2019-07-01")
    verdict = evaluate_valid(v["summary"], dev_summary=s)
    assert verdict["classification"] in ("REJECTED", "PROMISING_UNPROVEN", "ACCEPTED_FOR_HOLD")
    md = trial_report_md("DON1", "XAUUSD", "H4", "valid", v, verdict)
    assert "Verdict" in md and "Cost scenarios" in md
    registry.record_verdict("DON1", "valid", verdict["passed"], verdict)
    if not verdict["passed"]:                                          # a failure must permanently close HOLD
        with pytest.raises(registry.RegistryError):
            run_trial("DON1", "XAUUSD", "H4", "hold", {"n": 20, "k": 2.0, "rr": 2.0}, donchian)
    assert registry.verify_chain()[0]
    assert "Registry report" in registry_report_md()


def test_hold_flow_opens_once_and_only_after_valid_pass(lab):
    _setup(lab)
    registry.register_hypothesis("DON2", "breakout", "d")
    p = {"n": 20, "k": 2.0, "rr": 2.0}
    run_trial("DON2", "XAUUSD", "H4", "dev", p, donchian)
    registry.freeze_hypothesis("DON2", [{"symbol": "XAUUSD", "tf": "H4", "params": p}])
    run_trial("DON2", "XAUUSD", "H4", "valid", p, donchian)
    registry.record_verdict("DON2", "valid", True, {"note": "forced pass to test the HOLD gate"})
    registry.request_hold("DON2")
    h = run_trial("DON2", "XAUUSD", "H4", "hold", p, donchian)
    assert h["eval"][0] == pd.Timestamp("2019-07-01") and h["trades"]["entry_time"].min() >= pd.Timestamp("2019-07-01")
    assert evaluate_hold(h["summary"])["classification"] in ("CONFIRMED_OUT_OF_SAMPLE", "NOT_CONFIRMED")
    with pytest.raises(registry.RegistryError):
        run_trial("DON2", "XAUUSD", "H4", "hold", p, donchian)          # same config can never be re-run on HOLD
    with pytest.raises(registry.RegistryError):
        registry.request_hold("DON2")                                   # and HOLD cannot be re-opened
    ev =[e for e in registry.read_events() if e["type"] == "hold_access"]
    assert len(ev) == 1
