from __future__ import annotations

import pandas as pd

from src.runners.run_intervention_dataset import build_mechanism_aggregate, build_slice_manifest, load_confirmatory_grid, score_slice_ordering


def test_load_confirmatory_grid_keeps_base_ridge_rows() -> None:
    grid = load_confirmatory_grid()

    assert not grid.empty
    assert grid["n_traj"].eq(4096).all()
    assert grid["scan_block"].eq("confirmatory_ridge_grid").all()


def test_build_slice_manifest_has_expected_local_counts() -> None:
    grid = load_confirmatory_grid()

    slice_manifest, point_manifest = build_slice_manifest(grid)
    counts = slice_manifest.groupby("slice_name").size().to_dict()

    assert counts == {"delay_slice": 4, "flow_slice": 5, "memory_slice": 7}
    assert len(point_manifest) == 14
    assert int(point_manifest["slice_count"].max()) == 3


def test_score_slice_ordering_prefers_early_monotone_metric() -> None:
    slice_summary = pd.DataFrame(
        {
            "slice_name": ["flow_slice"] * 5,
            "axis_name": ["Pi_U"] * 5,
            "axis_value": [0.10, 0.15, 0.20, 0.25, 0.30],
            "is_baseline": [False, False, True, False, False],
            "first_gate_commit_delay": [2.3, 1.95, 1.7, 1.45, 1.2],
            "wall_dwell_before_first_commit": [0.80, 0.62, 0.50, 0.40, 0.31],
            "trap_burden_mean": [0.0, 0.0, 0.0, 0.0, 0.0],
            "residence_given_approach": [0.42, 0.48, 0.55, 0.61, 0.66],
            "commit_given_residence": [0.55, 0.55, 0.56, 0.55, 0.55],
            "Psucc_mean": [0.97, 0.96, 0.95, 0.91, 0.86],
            "MFPT_mean": [5.4, 4.7, 4.0, 3.5, 3.0],
            "eta_sigma_mean": [5.8e-5, 6.2e-5, 6.6e-5, 5.6e-5, 4.6e-5],
            "eta_completion_drag": [3.1e-4, 3.6e-4, 4.0e-4, 3.8e-4, 3.5e-4],
            "eta_trap_drag": [3.1e-4, 3.6e-4, 4.0e-4, 3.8e-4, 3.5e-4],
        }
    )

    ordering = score_slice_ordering(slice_summary)
    mechanism = ordering[
        (ordering["slice_name"] == "flow_slice") & (ordering["metric_group"] == "mechanism")
    ].sort_values(["mechanism_rank", "metric_name"])
    aggregate = build_mechanism_aggregate(ordering)

    assert mechanism.iloc[0]["metric_name"] in {
        "first_gate_commit_delay",
        "wall_dwell_before_first_commit",
        "residence_given_approach",
    }
    assert float(mechanism.loc[mechanism["metric_name"] == "commit_given_residence", "early_indicator_score"].iloc[0]) < float(
        mechanism.loc[mechanism["metric_name"] == "first_gate_commit_delay", "early_indicator_score"].iloc[0]
    )
    assert aggregate.iloc[0]["metric_name"] in {
        "first_gate_commit_delay",
        "wall_dwell_before_first_commit",
        "residence_given_approach",
    }
