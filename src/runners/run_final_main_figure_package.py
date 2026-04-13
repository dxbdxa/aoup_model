from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_efficiency_metric_upgrade import load_summary
from src.runners.run_front_analysis import (
    compute_front_distance_summary,
    compute_topk_overlap,
    extract_fronts,
    pareto_candidates,
    winner_row,
)
from src.runners.run_metric_robustness_package import classify_branch, nondominated_indices

SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet"
CANONICAL_OPERATING_POINTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "canonical_operating_points.csv"
POINT_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "intervention_dataset" / "point_summary.csv"
MECHANISM_ORDERING_PATH = PROJECT_ROOT / "outputs" / "datasets" / "intervention_dataset" / "mechanism_ordering_aggregate.csv"
CANONICAL_TRANSFER_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "canonical_transfer_summary.csv"
REFERENCE_TRANSFER_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "reference_extraction_summary.csv"
REFERENCE_SCALES_PATH = PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "figures" / "main_figures" / "final"

FIGURE_PATHS = {
    "figure1": OUTPUT_ROOT / "figure1_problem_setup_precommit_object.png",
    "figure2": OUTPUT_ROOT / "figure2_quantitative_ridge_discovery.png",
    "figure3": OUTPUT_ROOT / "figure3_central_precommit_principle.png",
    "figure4": OUTPUT_ROOT / "figure4_scope_transfer_metric_robustness.png",
    "manifest": OUTPUT_ROOT / "panel_sources_manifest.json",
}

OBJECTIVE_COLORS = {
    "Psucc_mean": "#1f77b4",
    "eta_sigma_mean": "#2ca02c",
    "MFPT_mean": "#d62728",
}
OBJECTIVE_DISPLAY = {
    "Psucc_mean": "success",
    "eta_sigma_mean": "efficiency",
    "MFPT_mean": "speed",
}
CANONICAL_COLORS = {
    "OP_SUCCESS_TIP": "#1f77b4",
    "OP_EFFICIENCY_TIP": "#2ca02c",
    "OP_SPEED_TIP": "#d62728",
    "OP_BALANCED_RIDGE_MID": "#4d4d4d",
    "OP_STALE_CONTROL_OFF_RIDGE": "#ff7f0e",
}
CANONICAL_DISPLAY = {
    "OP_SUCCESS_TIP": "success",
    "OP_EFFICIENCY_TIP": "efficiency",
    "OP_SPEED_TIP": "speed",
    "OP_BALANCED_RIDGE_MID": "balanced",
    "OP_STALE_CONTROL_OFF_RIDGE": "stale",
}
GEOMETRY_ORDER = [
    "GF0_REF_NESTED_MAZE",
    "GF1_SINGLE_BOTTLENECK_CHANNEL",
    "GF2_PORE_ARRAY_STRIP",
]
GEOMETRY_DISPLAY = {
    "GF0_REF_NESTED_MAZE": "GF0",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "GF1",
    "GF2_PORE_ARRAY_STRIP": "GF2",
}
GEOMETRY_COLORS = {
    "GF0_REF_NESTED_MAZE": "#1f77b4",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "#ff7f0e",
    "GF2_PORE_ARRAY_STRIP": "#2ca02c",
}
CANONICAL_TIMING_ORDER = [
    "OP_SPEED_TIP",
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
    "OP_EFFICIENCY_TIP",
    "OP_SUCCESS_TIP",
]
FIRST_HIT_COLORS = {
    "first / strong": "#31a354",
    "first / strongest": "#31a354",
    "first / cleanest": "#31a354",
    "secondary": "#9ecae1",
    "secondary increasing": "#9ecae1",
    "weak / mixed": "#d2b48c",
    "late / flat": "#bdbdbd",
    "punctate stale edge": "#de2d26",
    "intermittent flag": "#de2d26",
    "weak / punctate": "#de2d26",
}
SCOPE_COLORS = {
    "supported": "#31a354",
    "supported_with_qualifier": "#9ecae1",
    "candidate": "#f0ad4e",
    "ruled_out": "#d62728",
    "out_of_scope": "#bdbdbd",
}
METRIC_COLUMNS = {
    "eta_sigma": "eta_sigma_mean",
    "eta_completion_drag": "eta_completion_drag",
    "eta_trap_drag": "eta_trap_drag",
}
METRIC_COLORS = {
    "eta_sigma": "#1f77b4",
    "eta_completion_drag": "#ff7f0e",
    "eta_trap_drag": "#2ca02c",
}
METRIC_MARKERS = {
    "eta_sigma": "o",
    "eta_completion_drag": "s",
    "eta_trap_drag": "^",
}
BRANCH_ORDER = [
    "low_flow_success_branch",
    "moderate_flow_efficiency_branch",
    "high_flow_speed_branch",
]
BRANCH_DISPLAY = {
    "low_flow_success_branch": "low-flow success",
    "moderate_flow_efficiency_branch": "moderate-flow ridge",
    "high_flow_speed_branch": "high-flow speed",
}
BRANCH_COLORS = {
    "low_flow_success_branch": "#2ca02c",
    "moderate_flow_efficiency_branch": "#1f77b4",
    "high_flow_speed_branch": "#d62728",
}


def load_inputs() -> dict[str, Any]:
    reference_scales = json.loads(REFERENCE_SCALES_PATH.read_text(encoding="ascii"))
    confirmatory = load_summary().copy()
    if "scan_label" not in confirmatory.columns:
        confirmatory["scan_label"] = confirmatory["state_point_id"].astype(str)
    if "is_anchor_8192" not in confirmatory.columns:
        confirmatory["is_anchor_8192"] = confirmatory["n_traj"].astype(float) >= 8192
    if "analysis_source" not in confirmatory.columns:
        confirmatory["analysis_source"] = np.where(
            confirmatory["is_anchor_8192"],
            "resampled_8192",
            "base_4096",
        )
    if "analysis_n_traj" not in confirmatory.columns:
        confirmatory["analysis_n_traj"] = confirmatory["n_traj"].astype(int)
    if "Pi_sum" not in confirmatory.columns:
        confirmatory["Pi_sum"] = confirmatory["Pi_m"] + confirmatory["Pi_f"]
    canonical_ops = pd.read_csv(CANONICAL_OPERATING_POINTS_PATH).copy()
    point_summary = pd.read_csv(POINT_SUMMARY_PATH).copy()
    mechanism_ordering = pd.read_csv(MECHANISM_ORDERING_PATH).copy()
    canonical_transfer = pd.read_csv(CANONICAL_TRANSFER_SUMMARY_PATH).copy()
    reference_transfer = pd.read_csv(REFERENCE_TRANSFER_SUMMARY_PATH).copy()
    return {
        "reference_scales": reference_scales,
        "confirmatory": confirmatory,
        "canonical_ops": canonical_ops,
        "point_summary": point_summary,
        "mechanism_ordering": mechanism_ordering,
        "canonical_transfer": canonical_transfer,
        "reference_transfer": reference_transfer,
    }


def annotate_panel(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.10,
        1.02,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def build_figure1(reference_scales: dict[str, float]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax_geom, ax_graph, ax_refs, ax_controls = axes.flatten()
    for ax in axes.flatten():
        ax.set_axis_off()

    chamber_y = 0.43
    chamber_h = 0.22
    chambers = [(0.05, 0.24), (0.34, 0.24), (0.63, 0.24)]
    for x0, width in chambers:
        ax_geom.add_patch(
            patches.FancyBboxPatch(
                (x0, chamber_y),
                width,
                chamber_h,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=1.8,
                edgecolor="#222222",
                facecolor="#f7f7f7",
            )
        )
    for gate_x in (0.30, 0.59):
        ax_geom.add_patch(
            patches.Rectangle((gate_x, 0.51), 0.04, 0.08, facecolor="#d9edf7", edgecolor="#222222")
        )
    ax_geom.annotate(
        "",
        xy=(0.93, 0.55),
        xytext=(0.12, 0.55),
        arrowprops={"arrowstyle": "->", "lw": 2.0, "color": "#ff7f0e"},
    )
    ax_geom.text(0.45, 0.63, "background flow", color="#ff7f0e", fontsize=11, ha="center")
    ax_geom.annotate(
        "",
        xy=(0.40, 0.47),
        xytext=(0.26, 0.38),
        arrowprops={"arrowstyle": "->", "lw": 2.0, "color": "#1f77b4"},
    )
    ax_geom.text(0.23, 0.34, "active heading", color="#1f77b4", fontsize=10)
    ax_geom.annotate(
        "",
        xy=(0.50, 0.80),
        xytext=(0.50, 0.60),
        arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#d62728", "linestyle": "--"},
    )
    ax_geom.text(0.52, 0.80, "delayed steering", color="#d62728", fontsize=10, va="bottom")
    ax_geom.text(0.05, 0.14, "Narrow gates define the reference search length and crossing time.", fontsize=10)
    ax_geom.set_xlim(0, 1)
    ax_geom.set_ylim(0, 1)
    annotate_panel(ax_geom, "A")
    ax_geom.set_title("Gated transport problem", fontsize=13, pad=8)

    nodes = [
        ("bulk", 0.10, 0.58, "#f7f7f7"),
        ("wall\nsliding", 0.32, 0.58, "#e8f1fa"),
        ("gate\napproach", 0.54, 0.58, "#e8f1fa"),
        ("gate residence\n(pre-commit)", 0.76, 0.58, "#e8f1fa"),
        ("gate\ncommit", 0.76, 0.26, "#d9edf7"),
    ]
    for label, x0, y0, color in nodes:
        ax_graph.add_patch(
            patches.FancyBboxPatch(
                (x0, y0),
                0.14,
                0.14,
                boxstyle="round,pad=0.02",
                linewidth=1.4,
                edgecolor="#333333",
                facecolor=color,
            )
        )
        ax_graph.text(x0 + 0.07, y0 + 0.07, label, ha="center", va="center", fontsize=10)
    arrows = [
        ((0.24, 0.65), (0.32, 0.65)),
        ((0.46, 0.65), (0.54, 0.65)),
        ((0.68, 0.65), (0.76, 0.65)),
        ((0.83, 0.58), (0.83, 0.40)),
    ]
    for start, end in arrows:
        ax_graph.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#333333"})
    ax_graph.annotate(
        "",
        xy=(0.36, 0.74),
        xytext=(0.24, 0.74),
        arrowprops={"arrowstyle": "<->", "lw": 1.4, "color": "#888888"},
    )
    ax_graph.text(0.30, 0.78, "search / recycle", fontsize=9, color="#666666", ha="center")
    ax_graph.annotate(
        "",
        xy=(0.93, 0.26),
        xytext=(0.90, 0.26),
        arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#999999", "linestyle": "--"},
    )
    ax_graph.text(0.94, 0.26, "post-commit crossing\n(deferred)", fontsize=9, color="#666666", va="center")
    ax_graph.set_xlim(0, 1)
    ax_graph.set_ylim(0, 1)
    annotate_panel(ax_graph, "B")
    ax_graph.set_title("Pre-commit transport object", fontsize=13, pad=8)

    bars = [
        ("tau_g", float(reference_scales["tau_g"]), "#6baed6"),
        ("l_g", float(reference_scales["ell_g"]), "#9ecae1"),
        ("tau_p", float(reference_scales["tau_p"]), "#c6dbef"),
    ]
    max_value = max(value for _, value, _ in bars)
    for idx, (label, value, color) in enumerate(bars):
        y = 0.70 - 0.18 * idx
        width = 0.62 * value / max_value
        ax_refs.add_patch(patches.Rectangle((0.12, y), width, 0.08, facecolor=color, edgecolor="#333333"))
        ax_refs.text(0.05, y + 0.04, label, va="center", fontsize=10)
        ax_refs.text(0.78, y + 0.04, f"{value:.3f}", va="center", fontsize=10)
    ax_refs.text(0.12, 0.23, "Reference extraction uses the no-memory, no-feedback, U = 0 baseline.", fontsize=10)
    ax_refs.text(0.12, 0.14, "These scales anchor the nondimensional control coordinates.", fontsize=10)
    ax_refs.set_xlim(0, 1)
    ax_refs.set_ylim(0, 1)
    annotate_panel(ax_refs, "C")
    ax_refs.set_title("Reference scales", fontsize=13, pad=8)

    control_boxes = [
        ("Pi_m", "tau_mem / tau_g", "memory smooths or stales guidance"),
        ("Pi_f", "tau_f / tau_g", "delay sets pre-commit admissibility"),
        ("Pi_U", "U / v0", "flow orders branch preference"),
    ]
    for idx, (name, formula, role) in enumerate(control_boxes):
        y = 0.70 - 0.20 * idx
        ax_controls.add_patch(
            patches.FancyBboxPatch(
                (0.05, y - 0.08),
                0.88,
                0.14,
                boxstyle="round,pad=0.02",
                linewidth=1.0,
                edgecolor="#bcbcbc",
                facecolor="#fafafa",
            )
        )
        ax_controls.text(0.10, y, name, fontsize=12, fontweight="bold")
        ax_controls.text(0.28, y, formula, fontsize=11, family="monospace")
        ax_controls.text(0.62, y, role, fontsize=10)
    ax_controls.text(0.05, 0.16, "Main-text claim object:", fontsize=10, fontweight="bold")
    ax_controls.text(
        0.05,
        0.08,
        "productive transport is organized before crossing on the pre-commit backbone",
        fontsize=10,
    )
    ax_controls.set_xlim(0, 1)
    ax_controls.set_ylim(0, 1)
    annotate_panel(ax_controls, "D")
    ax_controls.set_title("Controls and organizing roles", fontsize=13, pad=8)

    fig.suptitle("Figure 1. Problem Setup, Reference Scales, and the Pre-Commit Transport Object", fontsize=17, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATHS["figure1"], dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_figure2(confirmatory: pd.DataFrame) -> None:
    pareto_df = pareto_candidates(confirmatory)
    fronts = extract_fronts(confirmatory, top_k=20)
    overlap_df = compute_topk_overlap(fronts, ks=(5, 10, 20))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax_ridge, ax_strip, ax_overlap, ax_tradeoff = axes.flatten()

    ax_ridge.scatter(confirmatory["Pi_U"], confirmatory["Pi_m"], color="0.85", s=22, alpha=0.75)
    ax_ridge.plot(pareto_df["Pi_U"], pareto_df["Pi_m"], color="#444444", linewidth=1.4, alpha=0.9)
    ridge_scatter = ax_ridge.scatter(
        pareto_df["Pi_U"],
        pareto_df["Pi_m"],
        c=pareto_df["Pi_f"],
        cmap="plasma",
        s=82,
        edgecolors="black",
        linewidths=0.4,
        zorder=3,
    )
    for objective in OBJECTIVE_COLORS:
        row = winner_row(confirmatory, objective)
        ax_ridge.scatter(
            row["Pi_U"],
            row["Pi_m"],
            color=OBJECTIVE_COLORS[objective],
            marker="D",
            s=135,
            edgecolors="black",
            linewidths=0.8,
            zorder=4,
        )
        ax_ridge.annotate(
            OBJECTIVE_DISPLAY[objective],
            (row["Pi_U"], row["Pi_m"]),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=9,
        )
    ax_ridge.set_xlabel("Pi_U")
    ax_ridge.set_ylabel("Pi_m")
    ax_ridge.set_title("Pareto-like ridge ordered by flow", fontsize=13)
    ax_ridge.grid(alpha=0.25, linewidth=0.6)
    ax_ridge.text(
        0.03,
        0.05,
        "20 non-dominated points\nthree distinct front tips",
        transform=ax_ridge.transAxes,
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.8"},
    )
    annotate_panel(ax_ridge, "A")

    strip_scatter = ax_strip.scatter(
        confirmatory["Pi_m"],
        confirmatory["Pi_f"],
        c=confirmatory["Pi_U"],
        cmap="viridis",
        s=34,
        alpha=0.55,
        edgecolors="none",
    )
    ax_strip.scatter(
        pareto_df["Pi_m"],
        pareto_df["Pi_f"],
        facecolors="none",
        edgecolors="black",
        s=80,
        linewidths=1.0,
    )
    for objective in OBJECTIVE_COLORS:
        row = winner_row(confirmatory, objective)
        ax_strip.scatter(
            row["Pi_m"],
            row["Pi_f"],
            color=OBJECTIVE_COLORS[objective],
            marker="D",
            s=120,
            edgecolors="black",
            linewidths=0.8,
        )
    ax_strip.axhspan(0.018, 0.025, color="#fee391", alpha=0.20)
    ax_strip.set_xlabel("Pi_m")
    ax_strip.set_ylabel("Pi_f")
    ax_strip.set_title("The productive ridge is confined to a thin delay strip", fontsize=13)
    ax_strip.grid(alpha=0.25, linewidth=0.6)
    ax_strip.text(
        0.04,
        0.93,
        "Pareto family stays inside Pi_f = 0.018 to 0.025",
        transform=ax_strip.transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "0.8"},
    )
    annotate_panel(ax_strip, "B")
    fig.colorbar(strip_scatter, ax=ax_strip, shrink=0.85, label="Pi_U")

    pair_order = [("Psucc_mean", "eta_sigma_mean"), ("Psucc_mean", "MFPT_mean"), ("eta_sigma_mean", "MFPT_mean")]
    ks = [5, 10, 20]
    overlap_matrix = np.zeros((len(pair_order), len(ks)), dtype=float)
    for i, pair in enumerate(pair_order):
        for j, k in enumerate(ks):
            row = overlap_df[
                (overlap_df["objective_a"] == pair[0])
                & (overlap_df["objective_b"] == pair[1])
                & (overlap_df["k"] == k)
            ].iloc[0]
            overlap_matrix[i, j] = float(row["overlap_count"])
    im = ax_overlap.imshow(overlap_matrix, cmap="Blues_r", vmin=0, vmax=max(1, overlap_matrix.max()))
    ax_overlap.set_xticks(np.arange(len(ks)))
    ax_overlap.set_xticklabels([f"top-{k}" for k in ks])
    ax_overlap.set_yticks(np.arange(len(pair_order)))
    ax_overlap.set_yticklabels(["success / efficiency", "success / speed", "efficiency / speed"])
    ax_overlap.set_title("Front-tip overlap remains negligible", fontsize=13)
    for i in range(overlap_matrix.shape[0]):
        for j in range(overlap_matrix.shape[1]):
            ax_overlap.text(j, i, f"{int(overlap_matrix[i, j])}", ha="center", va="center", fontsize=11)
    ax_overlap.text(
        0.02,
        -0.22,
        "CI-aware winner checks remain separated for all three front tips.",
        transform=ax_overlap.transAxes,
        fontsize=9,
    )
    annotate_panel(ax_overlap, "C")
    fig.colorbar(im, ax=ax_overlap, shrink=0.82, label="overlap count")

    tradeoff_scatter = ax_tradeoff.scatter(
        pareto_df["MFPT_mean"],
        pareto_df["Psucc_mean"],
        c=pareto_df["Pi_U"],
        cmap="viridis",
        s=70,
        edgecolors="black",
        linewidths=0.35,
    )
    for objective in OBJECTIVE_COLORS:
        row = winner_row(confirmatory, objective)
        ax_tradeoff.scatter(
            row["MFPT_mean"],
            row["Psucc_mean"],
            color=OBJECTIVE_COLORS[objective],
            marker="D",
            s=140,
            edgecolors="black",
            linewidths=0.8,
        )
        ax_tradeoff.annotate(
            OBJECTIVE_DISPLAY[objective],
            (row["MFPT_mean"], row["Psucc_mean"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=9,
        )
    ax_tradeoff.set_xlabel("MFPT_mean")
    ax_tradeoff.set_ylabel("Psucc_mean")
    ax_tradeoff.set_title("Distinct tips live on a common Pareto family", fontsize=13)
    ax_tradeoff.grid(alpha=0.25, linewidth=0.6)
    annotate_panel(ax_tradeoff, "D")
    fig.colorbar(tradeoff_scatter, ax=ax_tradeoff, shrink=0.85, label="Pi_U")

    fig.suptitle("Figure 2. Quantitative Discovery of the Pareto-Like Productive Ridge", fontsize=17, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(FIGURE_PATHS["figure2"], dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_figure3(
    confirmatory: pd.DataFrame,
    canonical_ops: pd.DataFrame,
    point_summary: pd.DataFrame,
    mechanism_ordering: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax_canonical, ax_heatmap, ax_early, ax_matched = axes.flatten()

    ax_canonical.scatter(confirmatory["Pi_U"], confirmatory["Pi_f"], color="0.86", s=20, alpha=0.65)
    pareto_df = pareto_candidates(confirmatory)
    ax_canonical.scatter(
        pareto_df["Pi_U"],
        pareto_df["Pi_f"],
        facecolors="none",
        edgecolors="#666666",
        s=75,
        linewidths=0.9,
    )
    for _, row in canonical_ops.iterrows():
        label = str(row["canonical_label"])
        ax_canonical.scatter(
            float(row["Pi_U"]),
            float(row["Pi_f"]),
            color=CANONICAL_COLORS[label],
            s=150 if label in ("OP_SUCCESS_TIP", "OP_EFFICIENCY_TIP", "OP_SPEED_TIP") else 110,
            marker="D" if label != "OP_STALE_CONTROL_OFF_RIDGE" else "s",
            edgecolors="black",
            linewidths=0.9,
            zorder=3,
        )
        ax_canonical.annotate(
            CANONICAL_DISPLAY[label],
            (float(row["Pi_U"]), float(row["Pi_f"])),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=9,
        )
    ax_canonical.axhspan(0.018, 0.025, color="#fee391", alpha=0.18)
    ax_canonical.set_xlabel("Pi_U")
    ax_canonical.set_ylabel("Pi_f")
    ax_canonical.set_title("Canonical ridge branches and the stale comparator", fontsize=13)
    ax_canonical.grid(alpha=0.25, linewidth=0.6)
    ax_canonical.text(
        0.03,
        0.05,
        "success, efficiency, speed, balanced, and stale\nbecome the named operating points for mechanism tests",
        transform=ax_canonical.transAxes,
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.8"},
    )
    annotate_panel(ax_canonical, "A")

    row_labels = ["Pi_f", "Pi_m", "Pi_U"]
    col_labels = ["timing budget", "approach -> residence", "residence -> commit", "trap burden"]
    cell_text = np.array(
        [
            ["first / strong", "secondary", "late / flat", "punctate stale edge"],
            ["weak / mixed", "first / cleanest", "late / flat", "intermittent flag"],
            ["first / strongest", "secondary increasing", "late / flat", "weak / punctate"],
        ],
        dtype=object,
    )
    category_order = list(FIRST_HIT_COLORS.keys())
    category_to_int = {name: idx for idx, name in enumerate(category_order)}
    cell_values = np.vectorize(category_to_int.get)(cell_text)
    cmap = matplotlib.colors.ListedColormap([FIRST_HIT_COLORS[name] for name in category_order])
    ax_heatmap.imshow(cell_values, cmap=cmap, aspect="auto", vmin=0, vmax=len(category_order) - 1)
    ax_heatmap.set_xticks(np.arange(len(col_labels)))
    ax_heatmap.set_xticklabels(col_labels, rotation=15)
    ax_heatmap.set_yticks(np.arange(len(row_labels)))
    ax_heatmap.set_yticklabels(row_labels)
    ax_heatmap.set_title("Which control parameter acts on which backbone part first?", fontsize=13)
    for i in range(cell_text.shape[0]):
        for j in range(cell_text.shape[1]):
            ax_heatmap.text(j, i, str(cell_text[i, j]), ha="center", va="center", fontsize=9)
    ax_heatmap.text(
        0.02,
        -0.18,
        "Reduced-law validation: 5 / 5 explicit predictions supported.",
        transform=ax_heatmap.transAxes,
        fontsize=9,
    )
    annotate_panel(ax_heatmap, "B")

    classification = {
        "wall_dwell_before_first_commit": "early_indicator",
        "first_gate_commit_delay": "early_indicator",
        "residence_given_approach": "early_indicator",
        "commit_given_residence": "late_correlate",
        "trap_burden_mean": "weak_or_punctate_stale_flag",
    }
    class_color = {
        "early_indicator": "#31a354",
        "late_correlate": "#bdbdbd",
        "weak_or_punctate_stale_flag": "#de2d26",
    }
    display_names = {
        "wall_dwell_before_first_commit": "wall dwell",
        "first_gate_commit_delay": "commit delay",
        "residence_given_approach": "residence / approach",
        "commit_given_residence": "commit / residence",
        "trap_burden_mean": "trap burden",
    }
    plot_df = mechanism_ordering.copy()
    plot_df["classification"] = plot_df["metric_name"].map(classification)
    plot_df["display_name"] = plot_df["metric_name"].map(display_names)
    for _, row in plot_df.iterrows():
        ax_early.scatter(
            float(row["mean_early_indicator_score"]),
            float(row["mean_monotonicity_score"]),
            s=150,
            color=class_color[str(row["classification"])],
            edgecolors="black",
            linewidths=0.7,
        )
        ax_early.annotate(
            str(row["display_name"]),
            (float(row["mean_early_indicator_score"]), float(row["mean_monotonicity_score"])),
            textcoords="offset points",
            xytext=(7, 4),
            fontsize=9,
        )
    ax_early.set_xlabel("mean early-indicator score")
    ax_early.set_ylabel("mean monotonicity score")
    ax_early.set_title("Early indicators separate from late correlates", fontsize=13)
    ax_early.grid(alpha=0.25, linewidth=0.6)
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", label=label.replace("_", " "), markerfacecolor=color, markeredgecolor="black", markersize=9)
        for label, color in class_color.items()
    ]
    ax_early.legend(handles=legend_handles, frameon=False, fontsize=8, loc="lower right")
    annotate_panel(ax_early, "C")

    matched = point_summary[
        point_summary["result_json"].isin(canonical_ops["result_json"])
    ].copy()
    label_to_result = canonical_ops.set_index("canonical_label")["result_json"].to_dict()
    balanced = matched.loc[matched["result_json"] == label_to_result["OP_BALANCED_RIDGE_MID"]].iloc[0]
    stale = matched.loc[matched["result_json"] == label_to_result["OP_STALE_CONTROL_OFF_RIDGE"]].iloc[0]
    matched_metrics = [
        ("first_gate_commit_delay", "commit delay"),
        ("wall_dwell_before_first_commit", "wall dwell"),
        ("residence_given_approach", "residence / approach"),
        ("commit_given_residence", "commit / residence"),
        ("trap_burden_mean", "trap burden"),
    ]
    x = np.arange(len(matched_metrics))
    width = 0.36
    balanced_values = []
    stale_values = []
    stale_delta_labels: list[str] = []
    for metric_name, _ in matched_metrics:
        pair = np.array([float(balanced[metric_name]), float(stale[metric_name])], dtype=float)
        scale = max(pair.max(), 1e-12)
        balanced_values.append(pair[0] / scale)
        stale_values.append(pair[1] / scale)
        if metric_name == "trap_burden_mean":
            stale_delta_labels.append("onset")
        else:
            delta = 100.0 * (pair[1] - pair[0]) / max(pair[0], 1e-12)
            stale_delta_labels.append(f"{delta:+.1f}%")
    ax_matched.bar(x - width / 2, balanced_values, width=width, color="#74c476", label="balanced ridge")
    ax_matched.bar(x + width / 2, stale_values, width=width, color="#fb6a4a", label="stale control")
    ax_matched.set_xticks(x)
    ax_matched.set_xticklabels([label for _, label in matched_metrics], rotation=15)
    ax_matched.set_ylim(0, 1.15)
    ax_matched.set_ylabel("within-metric normalized value")
    ax_matched.set_title("Matched ridge-versus-stale comparator", fontsize=13)
    ax_matched.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax_matched.legend(frameon=False, fontsize=8, loc="upper right")
    ax_matched.text(
        0.03,
        0.92,
        "stale rises first in timing and trap burden;\ncommit / residence stays comparatively flat",
        transform=ax_matched.transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.8"},
    )
    for idx, label in enumerate(stale_delta_labels):
        ax_matched.text(idx + width / 2, min(1.08, stale_values[idx] + 0.04), label, ha="center", fontsize=8)
    annotate_panel(ax_matched, "D")

    fig.suptitle("Figure 3. Central Evidence for the Pareto-Like Ridge and the Pre-Commit Principle", fontsize=17, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(FIGURE_PATHS["figure3"], dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_figure4(
    confirmatory: pd.DataFrame,
    canonical_transfer: pd.DataFrame,
    reference_transfer: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 10.5))
    ax_transfer, ax_coeffs, ax_metric, ax_scope = axes.flatten()

    timing_metrics = [
        ("first_gate_commit_delay", "-"),
        ("wall_dwell_before_first_commit", "--"),
    ]
    x = np.arange(len(CANONICAL_TIMING_ORDER))
    for family in GEOMETRY_ORDER:
        subset = canonical_transfer[canonical_transfer["geometry_family"] == family].set_index("canonical_label").loc[CANONICAL_TIMING_ORDER]
        for metric_name, linestyle in timing_metrics:
            raw = subset[metric_name].to_numpy(dtype=float)
            normalized = (raw - raw.min()) / max(raw.max() - raw.min(), 1e-12)
            ax_transfer.plot(
                x,
                normalized,
                linestyle=linestyle,
                marker="o",
                linewidth=2.0,
                color=GEOMETRY_COLORS[family],
                alpha=0.95,
            )
    geometry_handles = [
        plt.Line2D([0], [0], color=GEOMETRY_COLORS[family], lw=2.2, marker="o", label=GEOMETRY_DISPLAY[family])
        for family in GEOMETRY_ORDER
    ]
    metric_handles = [
        plt.Line2D([0], [0], color="#555555", lw=2.0, linestyle=style, label=label)
        for label, style in [("commit delay", "-"), ("wall dwell", "--")]
    ]
    ax_transfer.legend(handles=geometry_handles + metric_handles, frameon=False, fontsize=8, loc="upper left")
    ax_transfer.set_xticks(x)
    ax_transfer.set_xticklabels([CANONICAL_DISPLAY[label] for label in CANONICAL_TIMING_ORDER], rotation=15)
    ax_transfer.set_ylabel("within-geometry normalized value")
    ax_transfer.set_title("Backbone shape transfers across GF0 / GF1 / GF2", fontsize=13)
    ax_transfer.grid(alpha=0.25, linewidth=0.6)
    annotate_panel(ax_transfer, "A")

    ref = reference_transfer.set_index("geometry_family")
    gf0 = ref.loc["GF0_REF_NESTED_MAZE"]
    coeffs = [
        ("ell_g", "ell_g"),
        ("tau_g", "tau_g"),
        ("baseline_wall_fraction", "wall fraction"),
        ("baseline_commit_events_per_traj", "commit events"),
    ]
    x = np.arange(len(coeffs))
    width = 0.34
    for offset, family in [(-width / 2, "GF1_SINGLE_BOTTLENECK_CHANNEL"), (width / 2, "GF2_PORE_ARRAY_STRIP")]:
        ratios = [float(ref.loc[family, source] / gf0[source]) for source, _ in coeffs]
        ax_coeffs.bar(
            x + offset,
            ratios,
            width=width,
            color=GEOMETRY_COLORS[family],
            label=GEOMETRY_DISPLAY[family],
            edgecolor="black",
            linewidth=0.4,
        )
    ax_coeffs.axhline(1.0, color="#666666", linestyle="--", linewidth=1.0)
    ax_coeffs.set_xticks(x)
    ax_coeffs.set_xticklabels([label for _, label in coeffs], rotation=15)
    ax_coeffs.set_ylabel("ratio to GF0")
    ax_coeffs.set_title("Coefficients renormalize rather than collapse exactly", fontsize=13)
    ax_coeffs.legend(frameon=False, fontsize=8)
    ax_coeffs.grid(axis="y", alpha=0.25, linewidth=0.6)
    annotate_panel(ax_coeffs, "B")

    confirmatory = confirmatory.copy()
    confirmatory["branch_name"] = confirmatory["Pi_U"].map(classify_branch)
    ax_metric.scatter(confirmatory["Pi_U"], confirmatory["Pi_m"], color="0.88", s=18, alpha=0.55, edgecolors="none")
    for metric_name, metric_column in METRIC_COLUMNS.items():
        nd_df = confirmatory.iloc[nondominated_indices(confirmatory, metric_column)].copy()
        ax_metric.scatter(
            nd_df["Pi_U"],
            nd_df["Pi_m"],
            color=METRIC_COLORS[metric_name],
            marker=METRIC_MARKERS[metric_name],
            s=58,
            edgecolors="black",
            linewidths=0.35,
            alpha=0.88,
            label=metric_name,
        )
    ax_metric.set_xlabel("Pi_U")
    ax_metric.set_ylabel("Pi_m")
    ax_metric.set_title("The ridge survives metric refinement", fontsize=13)
    ax_metric.grid(alpha=0.25, linewidth=0.6)
    ax_metric.legend(frameon=False, fontsize=8, loc="lower right")
    ax_metric.text(
        0.03,
        0.05,
        "all non-dominated sets stay in Pi_f = 0.018 to 0.025;\nwinners shift from moderate-flow to high-flow branches",
        transform=ax_metric.transAxes,
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.8"},
    )
    inset = inset_axes(ax_metric, width="44%", height="44%", loc="upper left", borderpad=1.0)
    for idx, metric_name in enumerate(METRIC_COLUMNS):
        top10 = confirmatory.nlargest(10, METRIC_COLUMNS[metric_name])
        counts = top10["branch_name"].value_counts()
        bottom = 0.0
        for branch_name in BRANCH_ORDER:
            value = float(counts.get(branch_name, 0))
            inset.bar(
                idx,
                value,
                bottom=bottom,
                color=BRANCH_COLORS[branch_name],
                width=0.75,
            )
            bottom += value
    inset.set_ylim(0, 10)
    inset.set_xticks(np.arange(len(METRIC_COLUMNS)))
    inset.set_xticklabels(["eta_sigma", "eta_completion", "eta_trap"], rotation=15, fontsize=7)
    inset.set_yticks([0, 5, 10])
    inset.tick_params(axis="y", labelsize=7)
    inset.set_title("Top-10 branch mix", fontsize=8)
    annotate_panel(ax_metric, "C")

    scope_rows = [
        ("Pareto-like ridge and front-tip separation", "supported"),
        ("Pre-commit backbone reduced principle", "supported"),
        ("Shape transfer with coefficient renormalization", "supported_with_qualifier"),
        ("Metric-robust ridge survival", "supported_with_qualifier"),
        ("Coefficient-exact universality", "ruled_out"),
        ("Full crossing-completion law", "out_of_scope"),
        ("GF3 / broader stress-test universality", "candidate"),
        ("Full thermodynamic closure", "out_of_scope"),
    ]
    status_order = list(SCOPE_COLORS.keys())
    status_to_int = {name: idx for idx, name in enumerate(status_order)}
    scope_matrix = np.array([[status_to_int[status]] for _, status in scope_rows], dtype=float)
    scope_cmap = matplotlib.colors.ListedColormap([SCOPE_COLORS[name] for name in status_order])
    ax_scope.imshow(scope_matrix, cmap=scope_cmap, aspect="auto", vmin=0, vmax=len(status_order) - 1)
    ax_scope.set_xticks([0])
    ax_scope.set_xticklabels(["status"])
    ax_scope.set_yticks(np.arange(len(scope_rows)))
    ax_scope.set_yticklabels([label for label, _ in scope_rows])
    ax_scope.set_title("Across the tested family and within current bookkeeping", fontsize=13)
    for i, (_, status) in enumerate(scope_rows):
        ax_scope.text(0, i, status.replace("_", " "), ha="center", va="center", fontsize=8)
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=SCOPE_COLORS[name], label=name.replace("_", " "))
        for name in status_order
    ]
    ax_scope.legend(handles=legend_handles, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2)
    annotate_panel(ax_scope, "D")

    fig.suptitle("Figure 4. Scope Figure: Geometry-Tested Transfer, Metric-Robust Ridge Survival, and Explicit Limits", fontsize=17, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(FIGURE_PATHS["figure4"], dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_manifest() -> None:
    manifest = {
        "claim_hierarchy_anchor": "Across the tested family and within current bookkeeping",
        "outputs": {name: str(path) for name, path in FIGURE_PATHS.items() if name != "manifest"},
        "main_text_priority": {
            "figure3": "central evidence figure",
            "figure4": "scope figure",
        },
        "demoted_to_extended_data": [
            "full localization chronology",
            "threshold sensitivity and mechanism-audit detail",
            "full geometry gallery and family-specific supplementary comparisons",
            "full metric-family comparison tables beyond the main ridge-survival result",
        ],
        "source_files": [
            str(SUMMARY_PATH),
            str(CANONICAL_OPERATING_POINTS_PATH),
            str(POINT_SUMMARY_PATH),
            str(MECHANISM_ORDERING_PATH),
            str(CANONICAL_TRANSFER_SUMMARY_PATH),
            str(REFERENCE_TRANSFER_SUMMARY_PATH),
        ],
    }
    FIGURE_PATHS["manifest"].write_text(json.dumps(manifest, indent=2), encoding="ascii")


def build_outputs() -> dict[str, str]:
    data = load_inputs()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    build_figure1(data["reference_scales"])
    build_figure2(data["confirmatory"])
    build_figure3(data["confirmatory"], data["canonical_ops"], data["point_summary"], data["mechanism_ordering"])
    build_figure4(data["confirmatory"], data["canonical_transfer"], data["reference_transfer"])
    build_manifest()
    return {name: str(path) for name, path in FIGURE_PATHS.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the final main-figure manuscript package under the finalized claim hierarchy.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
