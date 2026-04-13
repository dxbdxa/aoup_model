from __future__ import annotations

from src.runners.run_precommit_reduced_law import build_metric_classification, build_scope_table, load_inputs, validate_predictions


def test_validate_predictions_supports_core_precommit_laws() -> None:
    _, slice_summary, ordering_df, _ = load_inputs()

    validation_df = validate_predictions(slice_summary, ordering_df)
    status_map = validation_df.set_index("prediction_id")["status"].to_dict()

    assert status_map["P1"] == "supported"
    assert status_map["P2"] == "supported"
    assert status_map["P3"] == "supported"
    assert status_map["P4"] == "supported"
    assert status_map["P5"] == "supported"


def test_metric_classification_preserves_early_vs_late_roles() -> None:
    _, _, ordering_df, _ = load_inputs()

    classification = build_metric_classification(ordering_df).set_index("metric_name")

    assert classification.loc["wall_dwell_before_first_commit", "classification"] == "early_indicator"
    assert classification.loc["first_gate_commit_delay", "classification"] == "early_indicator"
    assert classification.loc["residence_given_approach", "classification"] == "early_indicator"
    assert classification.loc["commit_given_residence", "classification"] == "late_correlate"
    assert classification.loc["trap_burden_mean", "classification"] == "weak_or_punctate_stale_flag"


def test_scope_table_keeps_expected_backbone_map() -> None:
    scope = build_scope_table().set_index("control_parameter")

    assert scope.loc["Pi_f", "timing_budget"] == "first / strong"
    assert scope.loc["Pi_m", "approach_to_residence"] == "first / cleanest"
    assert scope.loc["Pi_U", "residence_to_commit"] == "late / flat"
