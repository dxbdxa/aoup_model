from __future__ import annotations

import pandas as pd

from src.runners.run_main_figure_package import best_by_axis, build_panel_manifest, normalize_series


def test_normalize_series_handles_constant_values() -> None:
    values = pd.Series([2.0, 2.0, 2.0])
    normalized = normalize_series(values)
    assert normalized.tolist() == [0.5, 0.5, 0.5]


def test_best_by_axis_picks_correct_rows_for_max_and_min() -> None:
    df = pd.DataFrame(
        [
            {"Pi_f": 0.018, "Pi_m": 0.1, "Pi_U": 0.1, "Psucc_mean": 0.95, "MFPT_mean": 5.0, "analysis_source": "a"},
            {"Pi_f": 0.018, "Pi_m": 0.2, "Pi_U": 0.2, "Psucc_mean": 0.97, "MFPT_mean": 4.8, "analysis_source": "b"},
            {"Pi_f": 0.025, "Pi_m": 0.1, "Pi_U": 0.1, "Psucc_mean": 0.96, "MFPT_mean": 4.2, "analysis_source": "c"},
            {"Pi_f": 0.025, "Pi_m": 0.2, "Pi_U": 0.3, "Psucc_mean": 0.91, "MFPT_mean": 3.7, "analysis_source": "d"},
        ]
    )

    best_success = best_by_axis(df, "Pi_f", "Psucc_mean", "max")
    best_speed = best_by_axis(df, "Pi_f", "MFPT_mean", "min")

    assert list(best_success["Psucc_mean"]) == [0.97, 0.96]
    assert list(best_speed["MFPT_mean"]) == [4.8, 3.7]


def test_build_panel_manifest_exposes_standardized_notation_and_outputs() -> None:
    manifest = build_panel_manifest()

    assert manifest["notation"]["Pi_m"] == "tau_mem / tau_g"
    assert manifest["notation"]["Pi_f"] == "tau_f / tau_g"
    assert manifest["notation"]["Pi_U"] == "U / v0"
    assert "figure3_pareto_like_ridge" in manifest["figures"]
    assert "panels" in manifest["figures"]["figure4_mechanism_tradeoff"]
