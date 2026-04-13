from __future__ import annotations

import pandas as pd

from src.runners.run_extended_data_figure2_front_analysis_detail import (
    build_overlap_display_tables,
    directional_ci_check_count,
    format_ci,
)


def test_format_ci_switches_between_decimal_and_scientific() -> None:
    assert format_ci(0.970454, 0.977343) == "[0.970, 0.977]"
    assert format_ci(6.4e-05, 7.0e-05) == "[6.40e-05, 7.00e-05]"


def test_build_overlap_display_tables_orders_pairs_and_k_values() -> None:
    overlap_df = pd.DataFrame(
        [
            {"k": 20, "objective_a": "Psucc_mean", "objective_b": "eta_sigma_mean", "overlap_count": 1, "jaccard_index": 0.03},
            {"k": 10, "objective_a": "Psucc_mean", "objective_b": "eta_sigma_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 5, "objective_a": "Psucc_mean", "objective_b": "eta_sigma_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 20, "objective_a": "Psucc_mean", "objective_b": "MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 10, "objective_a": "Psucc_mean", "objective_b": "MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 5, "objective_a": "Psucc_mean", "objective_b": "MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 20, "objective_a": "eta_sigma_mean", "objective_b": "MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 10, "objective_a": "eta_sigma_mean", "objective_b": "MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 5, "objective_a": "eta_sigma_mean", "objective_b": "MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 20, "objective_a": "Psucc_mean", "objective_b": "eta_sigma_mean|MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 10, "objective_a": "Psucc_mean", "objective_b": "eta_sigma_mean|MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
            {"k": 5, "objective_a": "Psucc_mean", "objective_b": "eta_sigma_mean|MFPT_mean", "overlap_count": 0, "jaccard_index": 0.0},
        ]
    )

    counts, jaccard = build_overlap_display_tables(overlap_df)

    assert list(counts.columns) == [5, 10, 20]
    assert list(counts.index) == [
        "success vs efficiency",
        "success vs speed",
        "efficiency vs speed",
        "all three fronts",
    ]
    assert int(counts.loc["success vs efficiency", 20]) == 1
    assert float(jaccard.loc["success vs efficiency", 20]) == 0.03


def test_directional_ci_check_count_counts_both_columns() -> None:
    distance_df = pd.DataFrame(
        [
            {"b_separated_from_a_by_ci": True, "a_separated_from_b_by_ci": True},
            {"b_separated_from_a_by_ci": True, "a_separated_from_b_by_ci": False},
            {"b_separated_from_a_by_ci": False, "a_separated_from_b_by_ci": True},
        ]
    )

    true_checks, total_checks = directional_ci_check_count(distance_df)

    assert (true_checks, total_checks) == (4, 6)
