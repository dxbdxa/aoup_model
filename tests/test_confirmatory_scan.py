from __future__ import annotations

import pandas as pd

from src.runners.run_confirmatory_scan import (
    analyze_front_distinctness,
    bootstrap_trap_time_ci,
    rank_candidates,
    select_resample_candidates,
)


def test_bootstrap_trap_time_ci_handles_empty_and_singleton_inputs() -> None:
    empty_low, empty_high = bootstrap_trap_time_ci(pd.DataFrame(columns=["trap_duration"]), resamples=32, seed=1)
    assert empty_low == 0.0
    assert empty_high == 0.0

    single = pd.DataFrame({"trap_duration": [0.75]})
    single_low, single_high = bootstrap_trap_time_ci(single, resamples=32, seed=1)
    assert single_low == 0.75
    assert single_high == 0.75


def test_select_resample_candidates_returns_six_unique_points() -> None:
    df = pd.DataFrame(
        [
            {
                "state_point_id": f"id_{index}",
                "scan_label": f"point_{index}",
                "n_traj": 4096,
                "Pi_m": 0.1 + 0.01 * index,
                "Pi_f": 0.02,
                "Pi_U": 0.1 + 0.01 * index,
                "Psucc_mean": 0.99 - 0.01 * index,
                "eta_sigma_mean": 1.0 + 0.02 * (10 - index),
                "MFPT_mean": 2.0 + 0.1 * index,
                "trap_time_mean": 0.1 * index,
            }
            for index in range(10)
        ]
    )
    ranked = rank_candidates(df)
    selected = select_resample_candidates(ranked, n_candidates=6)

    assert len(selected) == 6
    assert selected["state_point_id"].nunique() == 6
    assert {"success", "efficiency", "speed"} <= set(selected["selection_reason"])


def test_analyze_front_distinctness_detects_three_distinct_winners() -> None:
    df = pd.DataFrame(
        [
            {
                "scan_label": "success_point",
                "state_point_id": "s",
                "Pi_m": 0.1,
                "Pi_f": 0.02,
                "Pi_U": 0.1,
                "analysis_n_traj": 8192,
                "analysis_source": "resampled_8192",
                "Psucc_mean": 0.98,
                "Psucc_ci_low": 0.97,
                "Psucc_ci_high": 0.99,
                "eta_sigma_mean": 5.5e-5,
                "eta_sigma_ci_low": 5.2e-5,
                "eta_sigma_ci_high": 5.8e-5,
                "MFPT_mean": 5.6,
                "MFPT_ci_low": 5.3,
                "MFPT_ci_high": 5.9,
                "trap_time_mean": 0.4,
            },
            {
                "scan_label": "efficiency_point",
                "state_point_id": "e",
                "Pi_m": 0.2,
                "Pi_f": 0.02,
                "Pi_U": 0.2,
                "analysis_n_traj": 8192,
                "analysis_source": "resampled_8192",
                "Psucc_mean": 0.95,
                "Psucc_ci_low": 0.94,
                "Psucc_ci_high": 0.96,
                "eta_sigma_mean": 6.8e-5,
                "eta_sigma_ci_low": 6.6e-5,
                "eta_sigma_ci_high": 7.0e-5,
                "MFPT_mean": 4.0,
                "MFPT_ci_low": 3.8,
                "MFPT_ci_high": 4.2,
                "trap_time_mean": 0.3,
            },
            {
                "scan_label": "speed_point",
                "state_point_id": "f",
                "Pi_m": 0.1,
                "Pi_f": 0.02,
                "Pi_U": 0.3,
                "analysis_n_traj": 8192,
                "analysis_source": "resampled_8192",
                "Psucc_mean": 0.88,
                "Psucc_ci_low": 0.86,
                "Psucc_ci_high": 0.9,
                "eta_sigma_mean": 5.1e-5,
                "eta_sigma_ci_low": 4.9e-5,
                "eta_sigma_ci_high": 5.3e-5,
                "MFPT_mean": 2.8,
                "MFPT_ci_low": 2.7,
                "MFPT_ci_high": 2.9,
                "trap_time_mean": 0.2,
            },
        ]
    )

    analysis = analyze_front_distinctness(df)

    assert analysis["distinct_locations"] is True
    assert analysis["winner_locations"]["Psucc_mean"]["scan_label"] == "success_point"
    assert analysis["winner_locations"]["eta_sigma_mean"]["scan_label"] == "efficiency_point"
    assert analysis["winner_locations"]["MFPT_mean"]["scan_label"] == "speed_point"
