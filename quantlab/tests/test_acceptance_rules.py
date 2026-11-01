"""The locked acceptance rules: every criterion is mandatory, uncomputed criteria fail, one failure blocks acceptance."""
import copy

import pytest

from quantlab.config import protocol_params
from quantlab.report import evaluate_dev_screen, evaluate_hold, evaluate_valid

GOOD = {"n_trades": 120, "expectancy_R_net": 0.18, "profit_factor_net": 1.4, "expectancy_ex_top5_R": 0.10, "p_adjusted": 0.04,
        "m_family": 30, "p_vs_control": 0.03, "positive_year_share": 0.75, "max_drawdown_R": 9.0, "total_R_net": 21.6,
        "scenarios": {"pessimistic": {"expectancy_R_net": 0.08, "profit_factor_net": 1.15}, "stress": {"expectancy_R_net": 0.02, "profit_factor_net": 1.05}}}


def verdict(**over):
    s = copy.deepcopy(GOOD)
    for k, v in over.items():
        s[k] = v
    return evaluate_valid(s, dev_summary={"expectancy_R_net": 0.12}, neighbor_positive_share=over.pop("_nb", 0.85) if False else 0.85)


def test_a_strategy_meeting_every_rule_is_accepted_for_hold(lab):
    v = verdict()
    assert v["passed"] and v["classification"] == "ACCEPTED_FOR_HOLD"


@pytest.mark.parametrize("field,bad,rule", [
    ("n_trades", 2, "min_trades"), ("expectancy_R_net", 0.05, "expectancy_net"), ("profit_factor_net", 1.1, "profit_factor_net"),
    ("expectancy_ex_top5_R", -0.01, "not_few_trades_luck"), ("p_adjusted", 0.25, "adjusted_p"), ("p_vs_control", 0.3, "beats_random_control"),
    ("positive_year_share", 0.25, "year_stability"), ("max_drawdown_R", 25.0, "max_drawdown")])
def test_each_single_failure_blocks_acceptance(lab, field, bad, rule):
    v = verdict(**{field: bad})
    assert not v["passed"] and not v["checks"][rule]["ok"]
    assert v["classification"] != "ACCEPTED_FOR_HOLD"


def test_cost_robustness_rules(lab):
    s = copy.deepcopy(GOOD)
    s["scenarios"]["pessimistic"]["expectancy_R_net"] = -0.01
    assert not evaluate_valid(s, neighbor_positive_share=0.9)["checks"]["pessimistic_costs"]["ok"]
    s = copy.deepcopy(GOOD)
    s["scenarios"]["stress"]["profit_factor_net"] = 0.95
    assert not evaluate_valid(s, neighbor_positive_share=0.9)["checks"]["stress_costs"]["ok"]
    s = copy.deepcopy(GOOD)
    s["scenarios"]["stress_tickvalue"] = {"profit_factor_net": 0.9}
    assert not evaluate_valid(s, neighbor_positive_share=0.9)["checks"]["stress_tickvalue"]["ok"]


def test_parameter_stability_is_mandatory_and_uncomputed_fails(lab):
    assert not evaluate_valid(copy.deepcopy(GOOD), neighbor_positive_share=None)["passed"]
    assert not evaluate_valid(copy.deepcopy(GOOD), neighbor_positive_share=0.5)["checks"]["parameter_stability"]["ok"]


def test_return_to_drawdown_rule(lab):
    s = copy.deepcopy(GOOD)
    s["total_R_net"], s["max_drawdown_R"] = 8.0, 12.0
    assert not evaluate_valid(s, neighbor_positive_share=0.9)["checks"]["return_to_drawdown"]["ok"]


def test_dev_screen_is_only_permission_to_freeze(lab):
    assert evaluate_dev_screen({"n_trades": 50, "expectancy_R_net": 0.02}, gross_event_edge_p=0.04)["classification"] == "MAY_FREEZE"
    assert evaluate_dev_screen({"n_trades": 20, "expectancy_R_net": 0.5})["classification"] == "DO_NOT_FREEZE"
    assert evaluate_dev_screen({"n_trades": 50, "expectancy_R_net": 0.02}, gross_event_edge_p=0.5)["classification"] == "DO_NOT_FREEZE"


def test_hold_rules_include_drawdown(lab):
    ok = {"n_trades": 40, "expectancy_R_net": 0.12, "profit_factor_net": 1.25, "max_drawdown_R": 10}
    assert evaluate_hold(ok)["classification"] == "CONFIRMED_OUT_OF_SAMPLE"
    assert evaluate_hold({**ok, "max_drawdown_R": 30})["classification"] == "NOT_CONFIRMED"
    assert evaluate_hold({**ok, "n_trades": protocol_params()["criteria"]["hold"]["min_trades"] - 1})["classification"] == "NOT_CONFIRMED"
