from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_extended_data_figure5_geometry_transfer_detail import (
    build_backbone_profile_table,
    build_coefficient_ratio_table,
    build_weak_signal_summary,
    load_inputs,
)


def test_build_backbone_profile_table_contains_expected_family_metric_grid() -> None:
    inputs = load_inputs()

    profile_df = build_backbone_profile_table(inputs["canonical"])

    assert set(profile_df["geometry_family"].unique()) == {
        "GF0_REF_NESTED_MAZE",
        "GF1_SINGLE_BOTTLENECK_CHANNEL",
        "GF2_PORE_ARRAY_STRIP",
    }
    assert set(profile_df["metric_name"].unique()) == {
        "first_gate_commit_delay",
        "wall_dwell_before_first_commit",
        "residence_given_approach",
    }
    assert profile_df["normalized_value"].between(0.0, 1.0).all()
    assert len(profile_df) == 3 * 3 * 5


def test_build_coefficient_ratio_table_captures_expected_renormalization_ratios() -> None:
    inputs = load_inputs()

    ratio_df = build_coefficient_ratio_table(inputs["reference"])

    gf1_tau = ratio_df[
        (ratio_df["geometry_family"] == "GF1_SINGLE_BOTTLENECK_CHANNEL") & (ratio_df["metric_name"] == "tau_g")
    ]["ratio_to_gf0"].iloc[0]
    gf2_wall = ratio_df[
        (ratio_df["geometry_family"] == "GF2_PORE_ARRAY_STRIP") & (ratio_df["metric_name"] == "baseline_wall_fraction")
    ]["ratio_to_gf0"].iloc[0]

    assert round(float(gf1_tau), 2) == 2.73
    assert round(float(gf2_wall), 2) == 1.78


def test_build_weak_signal_summary_marks_non_universal_selectivity_and_mixed_traps() -> None:
    inputs = load_inputs()

    weak_df = build_weak_signal_summary(inputs["canonical"]).set_index("geometry_family")

    assert weak_df.loc["GF1_SINGLE_BOTTLENECK_CHANNEL", "p_reach_winner"] == "tie"
    assert weak_df.loc["GF1_SINGLE_BOTTLENECK_CHANNEL", "commit_winner"] == "stale"
    assert weak_df.loc["GF2_PORE_ARRAY_STRIP", "trap_delta"] < 0.0
