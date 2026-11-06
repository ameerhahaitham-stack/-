"""The ONE official path from a signal function to a logged, reproducible trial.

signal_fn(df, **params) -> list[Signal]  must use only data up to each signal bar (verified by a truncation test).
Every call: loads data through the guarded loader, checks look-ahead, runs 4 cost scenarios, computes cluster-bootstrap
p-value and matched-control p-value, logs the trial to the hash-chained registry and saves trades/summary to results/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import registry
from .config import protocol_params, root
from .costs import build_scenarios, fallback_spread_px
from .data import TF_MIN, load_specs, load_with_context
from .engine import Signal, check_no_lookahead, matched_control, run_backtest
from .events import event_study
from .stats import adjust_p, by_year, cluster_bootstrap, label_regimes, by_regime, positive_year_share, trade_metrics


NOT_EVALUABLE = "NOT_EVALUABLE_CONTROL_INFEASIBLE"   # stage-1 status when the matched non-overlapping control cannot be built (NOT a rejection)
EVENT_MIN_EVENTS = 30      # pre-declared in docs/HYPOTHESES_DEV_PLAN.md (a property of the definition, not of any outcome)


class LookaheadError(RuntimeError):
    pass


def _log_aborted(hid, symbol, tf, split, params, entry, note, ex) -> None:
    try:
        registry.log_trial(hid, symbol, tf, split, params, {"aborted": True, "reason": f"{type(ex).__name__}: {str(ex)[:300]}"},
                           data_source=entry["source"], note=(note + " | ABORTED").strip(" |"), synthetic=entry["synthetic"])
    except Exception:            # never mask the original error
        pass


def neighbor_configs(params: dict, grids: dict) -> list[dict]:
    """Parameter neighbours: for every parameter that has a grid, one step down and one step up (others unchanged).
    Neighbours are frozen together with the main configuration and each is a VALID trial (all are counted)."""
    out = []
    for k, grid in grids.items():
        g = sorted(grid)
        if params.get(k) not in g:
            continue
        i = g.index(params[k])
        for j in (i - 1, i + 1):
            if 0 <= j < len(g):
                out.append({**params, k: g[j]})
    return out


def neighbor_positive_share(expectancies: list[float]) -> float | None:
    """Share of neighbouring configurations with positive net expectancy (None if there are none: the criterion then FAILS)."""
    e = [x for x in expectancies if x is not None and np.isfinite(x)]
    return float(np.mean([x > 0 for x in e])) if e else None


def run_event_study(hid: str, symbol: str, tf: str, pattern_fn, params: dict | None = None, primary_h: int = 5,
                    n_ctrl: int = 2000, n_ctrl_primary: int = 20000, note: str = "", save: bool = True,
                    lookahead_check: bool = True) -> dict:
    """Stage 1 (gross, cost-free). DEV ONLY. Logged as a trial: it is a statistical test and counts in the multiple-testing family.
    Only the PRIMARY horizon is tested; the other horizons are descriptive. Look-ahead is checked like for strategies.

    Eligibility (one rule for events and control, see events.eligible): an event counts only if its entry bar and its FULL primary
    horizon (bar i+h) lie inside the DEV window. The >= 30 events requirement is applied to those eligible, de-duplicated events."""
    from .events import eligible
    from .patterns import EVENT_MIN_GAP, event_arrays
    params = params or {}
    pp = protocol_params()
    registry.check_lock()
    df, es, ee, entry = load_with_context(symbol, tf, "dev")
    try:
        fn = lambda d: [Signal(e.i, e.side, e.stop) for e in pattern_fn(d, **params)]
        if lookahead_check:
            lc = pp["lookahead_check"]
            bad = check_no_lookahead(fn, df, lc["n_checks"], lc["seed"])
            if bad:
                raise LookaheadError(f"{hid}: pattern changes when future bars are removed: {bad[0]}")
        evs = pattern_fn(df, **params)
        bar_td = pd.Timedelta(minutes=TF_MIN[tf])
        elig = eligible(df, primary_h, es, ee, bar_td)
        evs_ok = [e for e in evs if elig[e.i]]                      # eligibility FIRST, then de-duplication
        idx, side = event_arrays(evs_ok)
        n_eligible = int(len(idx))
        if n_eligible < EVENT_MIN_EVENTS:
            registry.log_not_testable(hid, symbol, tf, params, f"fewer than {EVENT_MIN_EVENTS} eligible de-duplicated DEV events",
                                      {"n_events_raw": int(len(evs)), "n_eligible_dedup": n_eligible, "primary_horizon": primary_h})
            return {"trial_seq": None, "summary": {"kind": "not_testable", "n_events": n_eligible, "min_events": EVENT_MIN_EVENTS}, "table": None}
        tab = event_study(df, idx, side, horizons=(1, 3, primary_h, 10, 20), eval_start=es, eval_end=ee, n_ctrl=n_ctrl,
                          seed=pp["control"]["seed"], primary_h=primary_h, n_ctrl_primary=n_ctrl_primary,
                          bar_td=bar_td, min_gap=EVENT_MIN_GAP)
        row = {k: (None if isinstance(v, float) and not np.isfinite(v) else v)
               for k, v in tab[tab["horizon"] == primary_h].iloc[0].to_dict().items()}        # NaN -> None (control could not be built)
        evaluable = bool(row.get("control_complete")) and row.get("p_vs_random") is not None
        summary = {"kind": "event_study", "evaluation_status": "EVALUATED" if evaluable else NOT_EVALUABLE, "primary_horizon": primary_h, "n_events_raw": int(len(evs)), "n_events": int(row.get("n", 0)),
                   "n_control_candidates": row.get("n_control_candidates"),
                   "edge_ATR": row.get("edge_ATR"), "mean_ATR": row.get("mean_ATR"), "hit_rate": row.get("hit_rate"),
                   "p_vs_random": row.get("p_vs_random") if evaluable else None,
                   "p_raw": row.get("p_vs_random") if evaluable else None,            # None => counted as p = 1 in the family Holm
                   "p_incomplete_control_diagnostic": None if evaluable else row.get("p_vs_random"), "n_ctrl_used": row.get("n_ctrl"),
                   "p_resolution": row.get("p_resolution"), "n_ctrl_requested": row.get("n_ctrl_requested"),
                   "control_coverage": row.get("control_coverage"), "control_placement_success": row.get("control_placement_success"),
                   "control_complete": row.get("control_complete"),
                   "control_warning": row.get("control_warning"), "long_share": float((side == 1).mean()) if len(side) else None,
                   "descriptive_horizons": tab.round(4).to_dict(orient="records")}
    except Exception as ex:
        _log_aborted(hid, symbol, tf, "dev", params, entry, note + " | event_study", ex)
        raise
    ev = registry.log_trial(hid, symbol, tf, "dev", params, summary, data_source=entry["source"], note=(note + " | event_study").strip(" |"),
                            synthetic=entry["synthetic"])
    if save:
        d = root() / "results" / hid
        d.mkdir(parents=True, exist_ok=True)
        (d / f"event_dev_{symbol}_{tf}_{ev['seq']}.json").write_text(json.dumps({"hid": hid, "symbol": symbol, "tf": tf, "params": params,
                                                                               "summary": summary}, indent=2, default=str), encoding="utf-8")
    return {"trial_seq": ev["seq"], "summary": summary, "table": tab}


def run_trial(hid: str, symbol: str, tf: str, split: str, params: dict, signal_fn, note: str = "",
              control: bool = True, lookahead_check: bool = True, save: bool = True) -> dict:
    pp = protocol_params()
    registry.check_lock()
    if split == "hold":
        registry.assert_hold_available(hid, symbol, tf, params)     # fail BEFORE touching the sealed data
    df, es, ee, entry = load_with_context(symbol, tf, split, hid=hid if split == "hold" else None)
    specs = load_specs(symbol)
    try:
        scen = build_scenarios(symbol, specs, pp)
        fb = fallback_spread_px(symbol, pp)
        fn = lambda d: signal_fn(d, **params)
        if lookahead_check:
            lc = pp["lookahead_check"]
            bad = check_no_lookahead(fn, df, lc["n_checks"], lc["seed"])
            if bad:
                raise LookaheadError(f"{hid}: signal function changes when future bars are removed: {bad[0]}")
        sigs = fn(df)
        results = {name: run_backtest(df, sigs, cm, es, ee, fb) for name, cm in scen.items()}
        metrics = {name: trade_metrics(r.trades) for name, r in results.items()}
        base_tr = results["base"].trades
        bs = cluster_bootstrap(base_tr, pp["bootstrap"]["n"], pp["bootstrap"]["seed"], pp["bootstrap"]["cluster"])
        ctrl = matched_control(df, sigs, scen["base"], es, ee, pp["control"]["n_reps"], pp["control"]["seed"], fb) if control else {}
        m_family = max(registry.trial_count(("dev", "valid")) + 1, 1)      # counts aborted attempts too
        summary = {**metrics["base"], **{f"p_raw": bs["p_raw"], "ci_low": bs["ci_low"], "ci_high": bs["ci_high"], "n_clusters": bs.get("n_clusters")},
                   "p_adjusted_provisional": adjust_p(bs["p_raw"], m_family, pp["multiple_testing"]["method"]), "m_family": m_family,   # staged p x m: PROVISIONAL, never a final result (see registry.family_table)
                   "p_vs_control": ctrl.get("p_vs_control"), "edge_vs_control_R": ctrl.get("diff"), "control_diag": ctrl,
                   "scenarios": {k: {"expectancy_R_net": v.get("expectancy_R_net"), "profit_factor_net": v.get("profit_factor_net"),
                                     "n_trades": v.get("n_trades")} for k, v in metrics.items()},
                   "positive_year_share": positive_year_share(base_tr), "rejects": results["base"].rejects,
                   "warnings": results["base"].warnings, "specs_assumed": bool(specs.get("assumed", False))}
    except Exception as ex:      # a failed attempt is still an attempt: it is logged and counted in the multiple-testing family
        _log_aborted(hid, symbol, tf, split, params, entry, note, ex)
        raise
    ev = registry.log_trial(hid, symbol, tf, split, params, summary, data_source=entry["source"], note=note,
                            synthetic=entry["synthetic"])
    out = {"trial_seq": ev["seq"], "summary": summary, "trades": base_tr, "by_year": by_year(base_tr), "results": results,
           "df": df, "eval": (es, ee), "control": ctrl}
    if save:
        d = root() / "results" / hid
        d.mkdir(parents=True, exist_ok=True)
        stem = f"{split}_{symbol}_{tf}_{ev['seq']}"
        base_tr.to_csv(d / f"{stem}_trades.csv", index=False)
        (d / f"{stem}_summary.json").write_text(json.dumps({"hid": hid, "params": params, "summary": summary, "split": split,
                                                             "symbol": symbol, "tf": tf}, indent=2, default=str), encoding="utf-8")
    return out
