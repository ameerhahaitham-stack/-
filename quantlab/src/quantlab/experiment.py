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
from .data import load_specs, load_with_context
from .engine import check_no_lookahead, matched_control, run_backtest
from .stats import adjust_p, by_year, cluster_bootstrap, label_regimes, by_regime, positive_year_share, trade_metrics


class LookaheadError(RuntimeError):
    pass


def run_trial(hid: str, symbol: str, tf: str, split: str, params: dict, signal_fn, note: str = "",
              control: bool = True, lookahead_check: bool = True, save: bool = True) -> dict:
    pp = protocol_params()
    registry.check_lock()
    if split == "hold":
        registry.assert_hold_available(hid, symbol, tf, params)     # fail BEFORE touching the sealed data
    df, es, ee, entry = load_with_context(symbol, tf, split, hid=hid if split == "hold" else None)
    specs = load_specs(symbol)
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
    m_family = max(registry.trial_count(("dev", "valid")) + 1, 1)
    summary = {**metrics["base"], **{f"p_raw": bs["p_raw"], "ci_low": bs["ci_low"], "ci_high": bs["ci_high"]},
               "p_adjusted": adjust_p(bs["p_raw"], m_family, pp["multiple_testing"]["method"]), "m_family": m_family,
               "p_vs_control": ctrl.get("p_vs_control"), "edge_vs_control_R": ctrl.get("diff"),
               "scenarios": {k: {"expectancy_R_net": v.get("expectancy_R_net"), "profit_factor_net": v.get("profit_factor_net"),
                                 "n_trades": v.get("n_trades")} for k, v in metrics.items()},
               "positive_year_share": positive_year_share(base_tr), "rejects": results["base"].rejects,
               "warnings": results["base"].warnings, "specs_assumed": bool(specs.get("assumed", False))}
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
