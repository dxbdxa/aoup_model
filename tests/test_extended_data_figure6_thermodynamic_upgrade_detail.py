from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_extended_data_figure6_thermodynamic_upgrade_detail import (
    BOOKKEEPING_MISSING,
    build_branch_count_table,
    build_nd_overlap_table,
    load_inputs,
)


def test_branch_counts_capture_expected_reordering() -> None:
    inputs = load_inputs()

    branch_counts = build_branch_count_table(inputs["summary"]).set_index("metric_name")

    assert int(branch_counts.loc["eta_sigma", "moderate_flow_efficiency_branch"]) == 10
    assert int(branch_counts.loc["eta_completion_drag", "high_flow_speed_branch"]) == 8
    assert int(branch_counts.loc["eta_trap_drag", "high_flow_speed_branch"]) == 8


def test_nd_overlap_table_shows_strong_completion_trap_agreement() -> None:
    inputs = load_inputs()

    overlap_df = build_nd_overlap_table(inputs["summary"])
    row = overlap_df[
        (overlap_df["metric_a"] == "eta_completion_drag") & (overlap_df["metric_b"] == "eta_trap_drag")
    ].iloc[0]

    assert int(row["overlap_count"]) == 18
    assert round(float(row["jaccard_index"]), 2) == 0.90


def test_bookkeeping_missing_list_keeps_closure_channels_explicit() -> None:
    missing_titles = {title for title, _description in BOOKKEEPING_MISSING}

    assert "Active propulsion" in missing_titles
    assert "Controller work" in missing_titles
    assert "Memory bath" in missing_titles
    assert "Information cost" in missing_titles
    assert "Total closure" in missing_titles
