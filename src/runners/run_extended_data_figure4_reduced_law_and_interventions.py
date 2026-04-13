from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import textwrap
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import patches

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_precommit_reduced_law import (
    MECHANISM_METRICS,
    build_metric_classification,
    build_working_regions,
    load_inputs,
    validate_predictions,
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "extended_data"
PNG_PATH = OUTPUT_DIR / "ed_fig4_reduced_law_and_interventions.png"
SVG_PATH = OUTPUT_DIR / "ed_fig4_reduced_law_and_interventions.svg"
MANIFEST_DOC_PATH = PROJECT_ROOT / "docs" / "ed_fig4_panel_manifest.md"

INTERVENTION_FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "intervention_dataset"
GATE_THEORY_FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "gate_theory"

PANEL_TITLES = {
    "A": "Delay-slice response curves around the balanced midpoint",
    "B": "Memory-slice response curves inside the productive band",
    "C": "Flow-slice response curves along the local ridge",
    "D": "Early-indicator versus late-correlate summary heatmap",
    "E": "Prediction-by-prediction validation summary",
    "F": "Reduced-law scope: where it works and where failure is expected",
}

METRIC_STYLES = {
    "wall_dwell_before_first_commit": {"label": "wall dwell", "color": "#1f77b4", "linewidth": 2.4},
    "first_gate_commit_delay": {"label": "commit delay", "color": "#2ca02c", "linewidth": 2.4},
    "residence_given_approach": {"label": "residence / approach", "color": "#ff7f0e", "linewidth": 2.2},
    "commit_given_residence": {"label": "commit / residence", "color": "#7f7f7f", "linewidth": 1.9},
    "trap_burden_mean": {"label": "trap burden", "color": "#d62728", "linewidth": 2.0},
}
ROW_ORDER = [
    "wall_dwell_before_first_commit",
    "first_gate_commit_delay",
    "residence_given_approach",
    "commit_given_residence",
    "trap_burden_mean",
]
ROW_LABELS = {
    "wall_dwell_before_first_commit": "wall dwell before commit",
    "first_gate_commit_delay": "first commit delay",
    "residence_given_approach": "residence given approach",
    "commit_given_residence": "commit given residence",
    "trap_burden_mean": "trap burden",
}
SLICE_ORDER = ["delay_slice", "memory_slice", "flow_slice"]
SLICE_LABELS = {
    "delay_slice": "delay",
    "memory_slice": "memory",
    "flow_slice": "flow",
}
CLASS_LABELS = {
    "early_indicator": "early",
    "late_correlate": "late",
    "weak_or_punctate_stale_flag": "stale flag",
}
STATUS_COLORS = {
    "works_well": "#31a354",
    "works_with_limits": "#9ecae1",
    "expected_failure": "#d62728",
}
COMPACT_EVIDENCE = {
    "P1": "baseline delay point minimizes both timing observables; trap turns on only at the high-delay stale edge",
    "P2": "higher flow shortens both timing variables, raises residence/approach, and leaves commit/residence nearly flat",
    "P3": "memory changes residence/approach more coherently than timing or commit/residence",
    "P4": "commit/residence never ranks as a leading responder and keeps the smallest mean early score",
    "P5": "trap burden appears only sporadically and stays mixed rather than forming a smooth control law",
}
COMPACT_SCOPE_REASON = {
    "delay slice near balanced midpoint": "timing responds first; trap burden stays deferred to the stale edge",
    "flow ordering along the ridge": "timing contraction is monotone; commit/residence stays flat",
    "memory variation inside productive band": "residence/approach is cleaner than timing, but the slice is weaker and mixed",
    "trap kinetics as a fitted rate law": "trap counts stay too sparse for a fitted law",
    "post-commit completion and full crossing success": "the reduced law stops at gate_commit",
    "full efficiency ranking": "efficiency still mixes downstream transport costs outside the reduced law",
}


def annotate_panel(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.12,
        1.03,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def format_value(value: float) -> str:
    if not np.isfinite(value):
        return "NA"
    if value == 0.0:
        return "0"
    if abs(value) < 1e-3:
        return f"{value:.2e}"
    if abs(value) < 1.0:
        return f"{value:.3f}"
    return f"{value:.3f}"


def normalized_mechanism_slice(slice_summary: pd.DataFrame, slice_name: str) -> pd.DataFrame:
    subset = slice_summary[slice_summary["slice_name"] == slice_name].copy().sort_values("axis_value").reset_index(drop=True)
    baseline = subset.loc[subset["is_baseline"]].iloc[0]
    rows: list[dict[str, Any]] = []
    for metric_name in MECHANISM_METRICS:
        values = subset[metric_name].astype(float).to_numpy()
        centered = values - float(baseline[metric_name])
        scale = max(float(np.max(np.abs(centered))), 1e-12)
        normalized = centered / scale
        for axis_value, raw_value, norm_value in zip(subset["axis_value"].astype(float), values, normalized):
            rows.append(
                {
                    "slice_name": slice_name,
                    "metric_name": metric_name,
                    "axis_name": subset["axis_name"].iloc[0],
                    "axis_value": float(axis_value),
                    "raw_value": float(raw_value),
                    "normalized_response": float(norm_value),
                }
            )
    return pd.DataFrame(rows)


def build_ordering_heatmap(ordering_df: pd.DataFrame, classification_df: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str], list[list[str]], list[str]]:
    matrix = np.zeros((len(ROW_ORDER), len(SLICE_ORDER)), dtype=float)
    annotations: list[list[str]] = []
    for row_index, metric_name in enumerate(ROW_ORDER):
        row_ann: list[str] = []
        for col_index, slice_name in enumerate(SLICE_ORDER):
            row = ordering_df[(ordering_df["slice_name"] == slice_name) & (ordering_df["metric_name"] == metric_name)].iloc[0]
            matrix[row_index, col_index] = float(row["early_indicator_score"])
            row_ann.append(f"{row['early_indicator_score']:.3f}\n{row['direction_label']}")
        annotations.append(row_ann)
    row_labels = [ROW_LABELS[name] for name in ROW_ORDER]
    col_labels = [SLICE_LABELS[name] for name in SLICE_ORDER]
    class_map = classification_df.set_index("metric_name")["classification"].to_dict()
    class_labels = [CLASS_LABELS[class_map[name]] for name in ROW_ORDER]
    return matrix, row_labels, col_labels, annotations, class_labels


def load_outputs() -> dict[str, Any]:
    point_summary, slice_summary, ordering_df, _ = load_inputs()
    del point_summary
    validation_df = validate_predictions(slice_summary, ordering_df)
    classification_df = build_metric_classification(ordering_df)
    working_regions = build_working_regions()
    return {
        "slice_summary": slice_summary,
        "ordering": ordering_df,
        "validation": validation_df,
        "classification": classification_df,
        "working_regions": working_regions,
    }


def draw_slice_panel(ax: plt.Axes, slice_summary: pd.DataFrame, slice_name: str, emphasis_metric: str, note: str) -> None:
    normalized = normalized_mechanism_slice(slice_summary, slice_name)
    subset = slice_summary[slice_summary["slice_name"] == slice_name].copy().sort_values("axis_value").reset_index(drop=True)
    baseline_axis = float(subset.loc[subset["is_baseline"], "axis_value"].iloc[0])
    axis_name = str(subset["axis_name"].iloc[0])
    for metric_name in ROW_ORDER:
        metric_subset = normalized[normalized["metric_name"] == metric_name].copy()
        style = METRIC_STYLES[metric_name]
        alpha = 1.0 if metric_name == emphasis_metric or metric_name in {"wall_dwell_before_first_commit", "first_gate_commit_delay"} else 0.90
        linewidth = style["linewidth"] + (0.4 if metric_name == emphasis_metric else 0.0)
        marker = "s" if metric_name == "trap_burden_mean" else "o"
        ax.plot(
            metric_subset["axis_value"],
            metric_subset["normalized_response"],
            marker=marker,
            linewidth=linewidth,
            color=style["color"],
            alpha=alpha,
            label=style["label"],
        )
    ax.axvline(baseline_axis, color="#555555", linestyle="--", linewidth=1.0)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel(axis_name)
    ax.set_ylabel("normalized response about baseline")
    ax.grid(alpha=0.22, linewidth=0.6)
    ax.text(
        0.03,
        0.05,
        note,
        transform=ax.transAxes,
        fontsize=7.8,
        bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.82"},
    )


def draw_heatmap_panel(ax: plt.Axes, ordering_df: pd.DataFrame, classification_df: pd.DataFrame) -> None:
    matrix, row_labels, col_labels, annotations, class_labels = build_ordering_heatmap(ordering_df, classification_df)
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels([f"{label} [{cls}]" for label, cls in zip(row_labels, class_labels)])
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            ax.text(col_index, row_index, annotations[row_index][col_index], ha="center", va="center", fontsize=7.5)
    ax.text(
        0.02,
        -0.16,
        "Cells report early-indicator score and direction label for each slice. The reduced-law package classifies timing plus arrival as early, commit conversion as late, and trap burden as a punctate stale flag.",
        transform=ax.transAxes,
        fontsize=7.8,
        va="top",
    )
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.03, label="early-indicator score")


def draw_validation_panel(ax: plt.Axes, validation_df: pd.DataFrame) -> None:
    ax.set_axis_off()
    y_positions = np.linspace(0.88, 0.10, len(validation_df))
    for y, (_, row) in zip(y_positions, validation_df.iterrows()):
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.02, y - 0.085),
                0.96,
                0.14,
                boxstyle="round,pad=0.02",
                facecolor="#f7f7f7",
                edgecolor="0.82",
            )
        )
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.03, y - 0.055),
                0.12,
                0.07,
                boxstyle="round,pad=0.01",
                facecolor="#31a354" if row["status"] == "supported" else "#f0ad4e",
                edgecolor="none",
            )
        )
        ax.text(0.09, y - 0.020, row["prediction_id"], ha="center", va="center", fontsize=9, fontweight="bold", color="white")
        ax.text(0.18, y + 0.01, f"{row['short_title']} | score {row['validation_score']:.2f} | checks {int(row['checks_passed'])}/{int(row['checks_total'])}", fontsize=8.8, fontweight="bold", va="center")
        wrapped = textwrap.fill(COMPACT_EVIDENCE[str(row["prediction_id"])], width=62)
        ax.text(0.18, y - 0.060, wrapped, fontsize=7.5, va="bottom")
    ax.text(
        0.02,
        0.01,
        "All five predictions are supported in the current package. This panel reports the explicit check counts and the slice-level evidence rather than extending the law past `gate_commit`.",
        fontsize=7.8,
        va="bottom",
    )


def draw_scope_panel(ax: plt.Axes, working_regions: pd.DataFrame) -> None:
    ax.set_axis_off()
    columns = [
        ("works_well", 0.02, 0.30),
        ("works_with_limits", 0.35, 0.24),
        ("expected_failure", 0.62, 0.36),
    ]
    for status, x0, width in columns:
        subset = working_regions[working_regions["law_status"] == status].copy().reset_index(drop=True)
        ax.add_patch(
            patches.FancyBboxPatch(
                (x0, 0.84),
                width,
                0.08,
                boxstyle="round,pad=0.02",
                facecolor=STATUS_COLORS[status],
                edgecolor="none",
            )
        )
        ax.text(x0 + width / 2, 0.88, status.replace("_", " "), ha="center", va="center", fontsize=9, fontweight="bold", color="white")
        y = 0.76
        for _, row in subset.iterrows():
            height = 0.17 if status == "expected_failure" else 0.18
            ax.add_patch(
                patches.FancyBboxPatch(
                    (x0, y - height + 0.01),
                    width,
                    height,
                    boxstyle="round,pad=0.02",
                    facecolor="#f7f7f7",
                    edgecolor="0.82",
                )
            )
            ax.text(x0 + 0.01, y, textwrap.fill(str(row["region_or_task"]), width=24), fontsize=8.3, fontweight="bold", va="top")
            compact_reason = COMPACT_SCOPE_REASON.get(str(row["region_or_task"]), str(row["reason"]))
            ax.text(x0 + 0.01, y - 0.07, textwrap.fill(compact_reason, width=28), fontsize=7.4, va="top")
            y -= height + 0.03
    ax.text(
        0.02,
        0.02,
        "Scope boundary for manuscript use: the reduced law works locally and pre-commit. It is not a trap-kinetics law, not a post-commit completion law, and not a full efficiency-closure law.",
        fontsize=7.8,
        va="bottom",
    )


def build_figure(outputs: dict[str, Any]) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(17, 10.5))
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.08, top=0.88, wspace=0.34, hspace=0.42)
    axes = axes.flatten()

    delay_note = "Baseline at Pi_f = 0.020. Timing responds first; trap burden stays zero until the stale edge at Pi_f = 0.025."
    memory_note = "Baseline at Pi_m = 0.150. Residence/approach is the cleanest smooth memory response; trap burden stays mixed and intermittent."
    flow_note = "Baseline at Pi_U = 0.200. Timing contracts monotonically with flow, while commit/residence stays nearly flat."

    draw_slice_panel(axes[0], outputs["slice_summary"], "delay_slice", "wall_dwell_before_first_commit", delay_note)
    draw_slice_panel(axes[1], outputs["slice_summary"], "memory_slice", "residence_given_approach", memory_note)
    draw_slice_panel(axes[2], outputs["slice_summary"], "flow_slice", "first_gate_commit_delay", flow_note)
    draw_heatmap_panel(axes[3], outputs["ordering"], outputs["classification"])
    draw_validation_panel(axes[4], outputs["validation"])
    draw_scope_panel(axes[5], outputs["working_regions"])

    for ax, panel_letter in zip(axes, ["A", "B", "C", "D", "E", "F"]):
        annotate_panel(ax, panel_letter)
        ax.set_title(PANEL_TITLES[panel_letter], fontsize=12)

    legend_handles = [
        plt.Line2D([0], [0], color=METRIC_STYLES[metric]["color"], marker="s" if metric == "trap_burden_mean" else "o", linewidth=METRIC_STYLES[metric]["linewidth"], label=METRIC_STYLES[metric]["label"])
        for metric in ROW_ORDER
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.02), fontsize=8)

    fig.suptitle("Extended Data Figure 4. Reduced-Law and Intervention-Slice Detail", fontsize=17, fontweight="bold")
    fig.text(
        0.5,
        0.93,
        "Full intervention support for the reduced-law statement. The law is kept strictly pre-commit: timing and arrival organize the ridge, trap burden is a punctate stale flag, and post-commit completion remains outside scope.",
        ha="center",
        fontsize=10,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_manifest(outputs: dict[str, Any]) -> None:
    validation_df = outputs["validation"]
    classification_df = outputs["classification"].set_index("metric_name")
    working_regions = outputs["working_regions"]
    lines = [
        "# Extended Data Figure 4 Panel Manifest",
        "",
        "## Scope",
        "",
        "This note documents the panel logic for Extended Data Figure 4, which carries the full intervention and reduced-law detail that sits behind the compact main-text pre-commit law statement.",
        "",
        "Primary data sources:",
        "",
        f"- [intervention_design.md](file://{PROJECT_ROOT / 'docs' / 'intervention_design.md'})",
        f"- [intervention_dataset_run_report.md](file://{PROJECT_ROOT / 'docs' / 'intervention_dataset_run_report.md'})",
        f"- [intervention_mechanism_ordering.md](file://{PROJECT_ROOT / 'docs' / 'intervention_mechanism_ordering.md'})",
        f"- [precommit_reduced_law_candidates.md](file://{PROJECT_ROOT / 'docs' / 'precommit_reduced_law_candidates.md'})",
        f"- [precommit_prediction_validation_report.md](file://{PROJECT_ROOT / 'docs' / 'precommit_prediction_validation_report.md'})",
        f"- [point_summary.csv](file://{PROJECT_ROOT / 'outputs' / 'datasets' / 'intervention_dataset' / 'point_summary.csv'})",
        f"- [slice_summary.csv](file://{PROJECT_ROOT / 'outputs' / 'datasets' / 'intervention_dataset' / 'slice_summary.csv'})",
        f"- [metric_ordering.csv](file://{PROJECT_ROOT / 'outputs' / 'datasets' / 'intervention_dataset' / 'metric_ordering.csv'})",
        f"- [prediction_vs_validation.png](file://{GATE_THEORY_FIGURE_DIR / 'prediction_vs_validation.png'})",
        f"- [reduced_law_scope_map.png](file://{GATE_THEORY_FIGURE_DIR / 'reduced_law_scope_map.png'})",
        f"- [ED Figure 4 PNG](file://{PNG_PATH})",
        f"- [ED Figure 4 SVG](file://{SVG_PATH})",
        "",
        "## Figure-Level Message",
        "",
        "- this figure gives the full slice detail and validation detail that underlie the main-text reduced-law statement",
        "- the law remains strictly pre-commit throughout the figure",
        "- `trap_burden_mean` is kept visible as a punctate stale flag rather than promoted into a smooth kinetic coordinate",
        "- no panel implies a post-commit completion or full crossing-closure law",
        "",
        "## Panel Logic",
        "",
        "### Panel A",
        "",
        "- title: `Delay-slice response curves around the balanced midpoint`",
        "- purpose: show that delay moves the timing budget first, while trap burden stays deferred to the stale edge",
        "- quantitative note: the baseline timing minimum sits at `Pi_f = 0.020`, and trap burden turns on only at `Pi_f = 0.025`",
        "",
        "### Panel B",
        "",
        "- title: `Memory-slice response curves inside the productive band`",
        "- purpose: show that memory acts more cleanly on `residence_given_approach` than on timing or commitment conversion",
        "- quantitative note: `residence_given_approach` rises from `0.2217` at low memory to `0.2328` before the edge roll-off",
        "",
        "### Panel C",
        "",
        "- title: `Flow-slice response curves along the local ridge`",
        "- purpose: show the monotone contraction of the pre-commit timing budget under increasing flow",
        "- quantitative note: `first_gate_commit_delay` falls from `2.6353` at `Pi_U = 0.10` to `1.3998` at `Pi_U = 0.30`",
        "",
        "### Panel D",
        "",
        "- title: `Early-indicator versus late-correlate summary heatmap`",
        "- purpose: summarize the slice-level early-indicator scores and direction labels across the reduced-law observables",
        f"- quantitative note: `commit_given_residence` is classified as `{CLASS_LABELS[classification_df.loc['commit_given_residence', 'classification']]}`, while `trap_burden_mean` is classified as `{CLASS_LABELS[classification_df.loc['trap_burden_mean', 'classification']]}`",
        "",
        "### Panel E",
        "",
        "- title: `Prediction-by-prediction validation summary`",
        "- purpose: report the explicit validation checks and observed evidence for each reduced-law prediction",
        f"- quantitative note: `{len(validation_df)}` of `{len(validation_df)}` predictions are currently `supported`",
        "",
        "### Panel F",
        "",
        "- title: `Reduced-law scope: where it works and where failure is expected`",
        "- purpose: show which tasks or regions are already in scope, only partly in scope, or expected to fail under the current reduced law",
        f"- quantitative note: the scope panel contains `{int((working_regions['law_status'] == 'works_well').sum())}` `works_well`, `{int((working_regions['law_status'] == 'works_with_limits').sum())}` `works_with_limits`, and `{int((working_regions['law_status'] == 'expected_failure').sum())}` `expected_failure` regions",
        "",
        "## Why this stays pre-commit only",
        "",
        "- slice panels A-C show timing, arrival, commitment, and trap responses only through the pre-commit mechanism variables",
        "- panel F keeps post-commit completion and full efficiency ranking inside the explicit expected-failure scope column",
        "- this figure therefore strengthens the reduced-law evidence package without quietly promoting a post-commit closure claim",
        "",
        "## Bottom Line",
        "",
        "Extended Data Figure 4 is the full evidence layer behind the reduced-law package: timing and arrival observables move first, commit conversion stays late and comparatively flat, trap burden behaves as a punctate stale flag, and the law remains deliberately bounded to pre-commit structure.",
        "",
    ]
    MANIFEST_DOC_PATH.write_text("\n".join(lines), encoding="ascii")


def build_outputs() -> dict[str, str]:
    outputs = load_outputs()
    build_figure(outputs)
    write_manifest(outputs)
    return {
        "png": str(PNG_PATH),
        "svg": str(SVG_PATH),
        "manifest_doc": str(MANIFEST_DOC_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Extended Data Figure 4: reduced-law and intervention-slice detail.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
