from __future__ import annotations

import pandas as pd

from src.runners.run_extended_data_figure4_reduced_law_and_interventions import (
    build_ordering_heatmap,
    normalized_mechanism_slice,
)
from src.runners.run_precommit_reduced_law import build_metric_classification, load_inputs


def test_normalized_mechanism_slice_centers_baseline_at_zero() -> None:
    _, slice_summary, _, _ = load_inputs()

    normalized = normalized_mechanism_slice(slice_summary, "flow_slice")

    baseline = normalized[normalized["axis_value"] == 0.20]
    assert not baseline.empty
    assert (baseline["normalized_response"].abs() < 1e-12).all()


def test_build_ordering_heatmap_preserves_metric_and_slice_order() -> None:
    _, _, ordering_df, _ = load_inputs()
    classification_df = build_metric_classification(ordering_df)

    matrix, row_labels, col_labels, annotations, class_labels = build_ordering_heatmap(ordering_df, classification_df)

    assert matrix.shape == (5, 3)
    assert row_labels[0] == "wall dwell before commit"
    assert row_labels[-1] == "trap burden"
    assert col_labels == ["delay", "memory", "flow"]
    assert class_labels[3] == "late"
    assert class_labels[4] == "stale flag"
    assert "increasing" in annotations[0][0] or "decreasing" in annotations[0][0] or "mixed" in annotations[0][0]
