"""Verdicts against the pre-registered criteria and markdown reports. Failures are reported exactly like successes."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import registry
from .config import protocol_params, root


def _g(d: dict, k: str, default=float("nan")):
    v = d.get(k, default)
    return default if v is None else v


def evaluate_dev_screen(summary: dict, gross_event_edge_p: float | None = None) -> dict:
    """DEV screen: permission to FREEZE a configuration. It is never evidence of an edge."""
    c = protocol_params()["criteria"]["dev_screen"]
    checks = {
        "min_trades": (_g(summary, "n_trades", 0) >= c["min_trades"], f"{_g(summary, 'n_trades', 0)} >= {c['min_trades']}"),
        "expectancy_net_positive": (_g(summary, "expectancy_R_net") > c["min_expectancy_R_net"], f"{_g(summary, 'expectancy_R_net'):.3f}R"),
    }
    if gross_event_edge_p is not None:
        checks["gross_event_edge"] = (gross_event_edge_p <= c["min_gross_event_edge_p"], f"event-study p {gross_event_edge_p:.3f} <= {c['min_gross_event_edge_p']}")
    ok = all(v[0] for v in checks.values())
    return {"classification": "MAY_FREEZE" if ok else "DO_NOT_FREEZE", "passed": ok,
            "checks": {k: {"ok": bool(v[0]), "detail": v[1]} for k, v in checks.items()}}


def evaluate_valid(summary: dict, dev_summary: dict | None = None, neighbor_positive_share: float | None = None) -> dict:
    """Apply the locked VALID criteria to a base-scenario summary (output of experiment.run_trial).
    Every criterion is mandatory. A criterion that could not be computed FAILS (it is never skipped)."""
    c = protocol_params()["criteria"]["valid"]
    sc = summary.get("scenarios", {})
    dd, tot = _g(summary, "max_drawdown_R"), _g(summary, "total_R_net")
    checks = {
        "min_trades": (_g(summary, "n_trades", 0) >= c["min_trades"], f"{_g(summary, 'n_trades', 0)} >= {c['min_trades']}"),
        "expectancy_net": (_g(summary, "expectancy_R_net") >= c["min_expectancy_R_net"], f"{_g(summary, 'expectancy_R_net'):.3f}R >= {c['min_expectancy_R_net']}R"),
        "profit_factor_net": (_g(summary, "profit_factor_net") >= c["min_profit_factor_net"], f"{_g(summary, 'profit_factor_net'):.2f} >= {c['min_profit_factor_net']}"),
        "not_few_trades_luck": ((_g(summary, "expectancy_ex_top5_R") > 0) if c["expectancy_ex_top5_positive"] else True, f"expectancy without 5 best trades {_g(summary, 'expectancy_ex_top5_R'):.3f}R"),
        "adjusted_p": (_g(summary, "p_adjusted") <= c["max_adjusted_p"], f"p_adj {_g(summary, 'p_adjusted'):.3f} (m={summary.get('m_family')}) <= {c['max_adjusted_p']}"),
        "beats_random_control": (_g(summary, "p_vs_control") <= c["max_p_vs_control"], f"p_vs_control {_g(summary, 'p_vs_control'):.3f} <= {c['max_p_vs_control']}"),
        "pessimistic_costs": (_g(sc.get("pessimistic", {}), "expectancy_R_net") > c["pessimistic_expectancy_min"], f"pessimistic expectancy {_g(sc.get('pessimistic', {}), 'expectancy_R_net'):.3f}R"),
        "stress_costs": (_g(sc.get("stress", {}), "profit_factor_net") >= c["stress_profit_factor_min"], f"stress PF {_g(sc.get('stress', {}), 'profit_factor_net'):.2f}"),
        "year_stability": (_g(summary, "positive_year_share") >= c["min_positive_years_share"], f"positive years {_g(summary, 'positive_year_share'):.0%}"),
        "max_drawdown": (dd <= c["max_drawdown_R"], f"max drawdown {dd:.1f}R <= {c['max_drawdown_R']}R"),
        "return_to_drawdown": ((tot > 0) if dd == 0 else (tot / dd >= c["min_return_to_drawdown"]), f"total {tot:.1f}R / drawdown {dd:.1f}R >= {c['min_return_to_drawdown']}"),
        "parameter_stability": ((neighbor_positive_share is not None and neighbor_positive_share >= c["min_neighbor_positive_share"]),
                                "not computed (FAILS by rule)" if neighbor_positive_share is None else
                                f"{neighbor_positive_share:.0%} of neighbouring parameter sets positive >= {c['min_neighbor_positive_share']:.0%}"),
    }
    if "stress_tickvalue" in sc:      # present only while a symbol's tick value is unverified (see COST_MODEL.md)
        checks["stress_tickvalue"] = (_g(sc["stress_tickvalue"], "profit_factor_net") >= c["stress_tickvalue_pf_min"],
                                      f"tick-value stress PF {_g(sc['stress_tickvalue'], 'profit_factor_net'):.2f}")
    if dev_summary is not None:
        checks["dev_positive"] = (_g(dev_summary, "expectancy_R_net") > 0, f"DEV expectancy {_g(dev_summary, 'expectancy_R_net'):.3f}R")
    passed = all(ok for ok, _ in checks.values())
    positive = _g(summary, "expectancy_R_net") > 0
    cls = "ACCEPTED_FOR_HOLD" if passed else ("PROMISING_UNPROVEN" if positive and _g(summary, "n_trades", 0) > 0 else "REJECTED")
    return {"classification": cls, "passed": passed, "checks": {k: {"ok": bool(v[0]), "detail": v[1]} for k, v in checks.items()}}


def evaluate_hold(summary: dict) -> dict:
    c = protocol_params()["criteria"]["hold"]
    dd = _g(summary, "max_drawdown_R")
    ok = (_g(summary, "n_trades", 0) >= c["min_trades"] and _g(summary, "expectancy_R_net") >= c["min_expectancy_R_net"]
          and _g(summary, "profit_factor_net") >= c["min_profit_factor_net"] and dd <= c["max_drawdown_R"])
    return {"classification": "CONFIRMED_OUT_OF_SAMPLE" if ok else "NOT_CONFIRMED", "passed": bool(ok),
            "detail": f"n={_g(summary, 'n_trades', 0)}, expectancy {_g(summary, 'expectancy_R_net'):.3f}R, PF {_g(summary, 'profit_factor_net'):.2f}, max drawdown {dd:.1f}R"}


def trial_report_md(hid: str, symbol: str, tf: str, split: str, run: dict, verdict: dict | None = None) -> str:
    s = run["summary"]
    L = [f"# {hid} - {symbol} {tf} - {split.upper()}", "",
         f"Trial #{run['trial_seq']} | trades {s.get('n_trades', 0)} | assumptions: costs placeholder={'YES' if s.get('specs_assumed') else 'no (specs from MT5)'}", ""]
    if verdict:
        L += [f"## Verdict: **{verdict['classification']}**", ""]
        for k, v in verdict.get("checks", {}).items():
            L.append(f"- {'PASS' if v['ok'] else 'FAIL'} {k}: {v['detail']}")
        if "detail" in verdict:
            L.append(f"- {verdict['detail']}")
        L.append("")
    keys = ["win_rate", "profit_factor_net", "expectancy_R_net", "expectancy_R_gross", "avg_win_R", "avg_loss_R", "total_R_net",
            "max_drawdown_R", "max_losing_streak", "avg_bars_held", "avg_cost_R", "median_cost_pct_of_stop", "p90_cost_pct_of_stop",
            "p_raw", "p_adjusted", "p_vs_control", "ci_low", "ci_high"]
    L += ["## Metrics (net of costs, base scenario)", "", "| metric | value |", "|---|---|"]
    for k in keys:
        if k in s and s[k] is not None:
            L.append(f"| {k} | {s[k]:.4f} |" if isinstance(s[k], (int, float)) else f"| {k} | {s[k]} |")
    L += ["", "## Cost scenarios", "", "| scenario | trades | expectancy R | PF |", "|---|---|---|---|"]
    for k, v in s.get("scenarios", {}).items():
        L.append(f"| {k} | {v.get('n_trades')} | {_g(v, 'expectancy_R_net'):.3f} | {_g(v, 'profit_factor_net'):.2f} |")
    if len(run["by_year"]):
        L += ["", "## By year", "", run["by_year"].round(3).to_markdown()]
    L += ["", "## Rejected / skipped signals", "", str(s.get("rejects"))]
    if s.get("warnings"):
        L += ["", "## Warnings", ""] + [f"- {w}" for w in s["warnings"]]
    L += ["", f"_Multiple-testing: p_adjusted uses all {s.get('m_family')} logged DEV+VALID trials. Past performance does not guarantee future results._"]
    return "\n".join(L)


def registry_report_md() -> str:
    th = registry.trials_df()
    hy = registry.hypotheses_df()
    ok, msg = registry.verify_chain()
    L = ["# Registry report", "", f"Chain integrity: **{msg}** | protocol: {registry.lock_status()}", "",
         f"Total DEV+VALID trials logged: {registry.trial_count(('dev', 'valid'))}  (this is the multiple-testing family size)", ""]
    L += ["## Hypotheses", "", hy.to_markdown(index=False) if len(hy) else "none", "", "## Trials", "",
          th.drop(columns=["params"]).round(4).to_markdown(index=False) if len(th) else "none"]
    return "\n".join(L)


def write_text(path, text: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return str(p)
