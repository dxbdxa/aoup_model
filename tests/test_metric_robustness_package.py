from __future__ import annotations

from src.runners.run_metric_robustness_package import (
    METRIC_COLUMNS,
    build_metric_robustness_table,
    classify_branch,
    load_inputs,
    rank_canonical_points,
)


def test_metric_robustness_table_has_expected_classifications() -> None:
    summary, metric_table, _canonical = load_inputs()
    robustness = build_metric_robustness_table(summary, metric_table).set_index("conclusion_id")

    assert robustness.loc["MR1", "classification"] == "invariant"
    assert robustness.loc["MR2", "classification"] == "invariant"
    assert robustness.loc["MR3", "classification"] == "shifted_but_principle_consistent"
    assert robustness.loc["MR4", "classification"] == "shifted_but_principle_consistent"
    assert robustness.loc["MR5", "classification"] == "invariant"
    assert robustness.loc["MR6", "classification"] == "invariant"
    assert robustness.loc["MR7", "classification"] == "outside_current_bookkeeping"
    assert robustness.loc["MR8", "classification"] == "outside_current_bookkeeping"


def test_winner_branch_shifts_but_ridge_family_survives() -> None:
    summary, metric_table, canonical = load_inputs()

    sigma_winner = summary.loc[summary[METRIC_COLUMNS["eta_sigma"]].idxmax()]
    completion_winner = summary.loc[summary[METRIC_COLUMNS["eta_completion_drag"]].idxmax()]
    trap_winner = summary.loc[summary[METRIC_COLUMNS["eta_trap_drag"]].idxmax()]

    assert classify_branch(float(sigma_winner["Pi_U"])) == "moderate_flow_efficiency_branch"
    assert classify_branch(float(completion_winner["Pi_U"])) == "high_flow_speed_branch"
    assert classify_branch(float(trap_winner["Pi_U"])) == "high_flow_speed_branch"

    ranks = rank_canonical_points(summary, canonical).set_index("canonical_label")
    assert int(ranks.loc["OP_SPEED_TIP", "eta_completion_drag_rank"]) <= 2
    assert int(ranks.loc["OP_SPEED_TIP", "eta_trap_drag_rank"]) <= 2
    assert int(ranks.loc["OP_EFFICIENCY_TIP", "eta_sigma_rank"]) <= 3
