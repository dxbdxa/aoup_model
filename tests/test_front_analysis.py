from __future__ import annotations

import pandas as pd

from src.runners.run_front_analysis import (
    classify_front_structure,
    compute_topk_overlap,
    extract_fronts,
    pareto_candidates,
)


def _sample_front_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "scan_label": "success_tip",
                "analysis_source": "resampled_8192",
                "analysis_n_traj": 8192,
                "is_anchor_8192": True,
                "Pi_m": 0.08,
                "Pi_f": 0.025,
                "Pi_U": 0.10,
                "Pi_sum": 0.105,
                "Psucc_mean": 0.974,
                "Psucc_ci_low": 0.970,
                "Psucc_ci_high": 0.977,
                "eta_sigma_mean": 5.4e-5,
                "eta_sigma_ci_low": 5.3e-5,
                "eta_sigma_ci_high": 5.5e-5,
                "MFPT_mean": 6.1,
                "MFPT_ci_low": 6.0,
                "MFPT_ci_high": 6.2,
                "trap_time_mean": 0.5,
                "result_json": "success.json",
            },
            {
                "scan_label": "efficiency_tip",
                "analysis_source": "base_4096",
                "analysis_n_traj": 4096,
                "is_anchor_8192": False,
                "Pi_m": 0.18,
                "Pi_f": 0.018,
                "Pi_U": 0.15,
                "Pi_sum": 0.198,
                "Psucc_mean": 0.959,
                "Psucc_ci_low": 0.953,
                "Psucc_ci_high": 0.965,
                "eta_sigma_mean": 6.7e-5,
                "eta_sigma_ci_low": 6.4e-5,
                "eta_sigma_ci_high": 7.0e-5,
                "MFPT_mean": 4.24,
                "MFPT_ci_low": 4.15,
                "MFPT_ci_high": 4.34,
                "trap_time_mean": 0.3,
                "result_json": "efficiency.json",
            },
            {
                "scan_label": "speed_tip",
                "analysis_source": "resampled_8192",
                "analysis_n_traj": 8192,
                "is_anchor_8192": True,
                "Pi_m": 0.10,
                "Pi_f": 0.018,
                "Pi_U": 0.30,
                "Pi_sum": 0.118,
                "Psucc_mean": 0.869,
                "Psucc_ci_low": 0.861,
                "Psucc_ci_high": 0.876,
                "eta_sigma_mean": 4.9e-5,
                "eta_sigma_ci_low": 4.7e-5,
                "eta_sigma_ci_high": 5.1e-5,
                "MFPT_mean": 2.82,
                "MFPT_ci_low": 2.76,
                "MFPT_ci_high": 2.87,
                "trap_time_mean": 0.0,
                "result_json": "speed.json",
            },
            {
                "scan_label": "ridge_mid",
                "analysis_source": "base_4096",
                "analysis_n_traj": 4096,
                "is_anchor_8192": False,
                "Pi_m": 0.15,
                "Pi_f": 0.020,
                "Pi_U": 0.20,
                "Pi_sum": 0.17,
                "Psucc_mean": 0.952,
                "Psucc_ci_low": 0.945,
                "Psucc_ci_high": 0.959,
                "eta_sigma_mean": 6.65e-5,
                "eta_sigma_ci_low": 6.4e-5,
                "eta_sigma_ci_high": 6.9e-5,
                "MFPT_mean": 4.05,
                "MFPT_ci_low": 3.93,
                "MFPT_ci_high": 4.16,
                "trap_time_mean": 0.2,
                "result_json": "mid.json",
            },
            {
                "scan_label": "dominated",
                "analysis_source": "base_4096",
                "analysis_n_traj": 4096,
                "is_anchor_8192": False,
                "Pi_m": 0.12,
                "Pi_f": 0.025,
                "Pi_U": 0.25,
                "Pi_sum": 0.145,
                "Psucc_mean": 0.90,
                "Psucc_ci_low": 0.89,
                "Psucc_ci_high": 0.91,
                "eta_sigma_mean": 4.6e-5,
                "eta_sigma_ci_low": 4.4e-5,
                "eta_sigma_ci_high": 4.8e-5,
                "MFPT_mean": 4.8,
                "MFPT_ci_low": 4.7,
                "MFPT_ci_high": 4.9,
                "trap_time_mean": 0.6,
                "result_json": "dominated.json",
            },
        ]
    )


def test_compute_topk_overlap_captures_small_example_structure() -> None:
    df = _sample_front_df()
    fronts = extract_fronts(df, top_k=3)
    overlap = compute_topk_overlap(fronts, ks=(1, 2))

    assert int(overlap[(overlap["k"] == 1) & (overlap["objective_a"] == "Psucc_mean")]["overlap_count"].iloc[0]) == 0
    assert int(overlap[(overlap["k"] == 2) & (overlap["objective_a"] == "Psucc_mean")]["overlap_count"].iloc[0]) == 1


def test_pareto_candidates_filters_dominated_points() -> None:
    df = _sample_front_df()
    pareto = pareto_candidates(df)

    assert "dominated" not in set(pareto["scan_label"])
    assert {"success_tip", "efficiency_tip", "speed_tip"} <= set(pareto["scan_label"])


def test_classify_front_structure_prefers_pareto_like_ridge() -> None:
    df = _sample_front_df()
    fronts = extract_fronts(df, top_k=4)
    overlap = compute_topk_overlap(fronts, ks=(5, 10, 20))
    distance_df = pd.DataFrame(
        [
            {
                "winner_a": "Psucc_mean",
                "winner_b": "eta_sigma_mean",
                "Pi_f_a": 0.025,
                "Pi_f_b": 0.018,
                "Pi_U_a": 0.10,
                "Pi_U_b": 0.15,
                "b_separated_from_a_by_ci": True,
                "a_separated_from_b_by_ci": True,
            },
            {
                "winner_a": "Psucc_mean",
                "winner_b": "MFPT_mean",
                "Pi_f_a": 0.025,
                "Pi_f_b": 0.018,
                "Pi_U_a": 0.10,
                "Pi_U_b": 0.30,
                "b_separated_from_a_by_ci": True,
                "a_separated_from_b_by_ci": True,
            },
            {
                "winner_a": "eta_sigma_mean",
                "winner_b": "MFPT_mean",
                "Pi_f_a": 0.018,
                "Pi_f_b": 0.018,
                "Pi_U_a": 0.15,
                "Pi_U_b": 0.30,
                "b_separated_from_a_by_ci": True,
                "a_separated_from_b_by_ci": True,
            },
        ]
    )
    pareto = pd.concat([df] * 3, ignore_index=True).head(9)

    label, explanation = classify_front_structure(overlap, distance_df, pareto, df)

    assert label == "Pareto-like ridge"
    assert "Pi_U" in explanation or "ridge" in explanation
