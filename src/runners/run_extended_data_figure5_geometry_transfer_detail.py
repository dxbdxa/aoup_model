from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.colors import ListedColormap

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CANONICAL_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "canonical_transfer_summary.csv"
REFERENCE_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "reference_extraction_summary.csv"
INVARIANT_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "geometry_transfer_invariant_table.csv"
STRESS_FIGURE_PATH = PROJECT_ROOT / "outputs" / "figures" / "geometry_transfer" / "transfer_stress_figure.png"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "extended_data"
PNG_PATH = OUTPUT_DIR / "ed_fig5_geometry_transfer_detail.png"
SVG_PATH = OUTPUT_DIR / "ed_fig5_geometry_transfer_detail.svg"
MANIFEST_DOC_PATH = PROJECT_ROOT / "docs" / "ed_fig5_panel_manifest.md"

FAMILY_ORDER = [
    "GF0_REF_NESTED_MAZE",
    "GF1_SINGLE_BOTTLENECK_CHANNEL",
    "GF2_PORE_ARRAY_STRIP",
]
FAMILY_SHORT = {
    "GF0_REF_NESTED_MAZE": "GF0",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "GF1",
    "GF2_PORE_ARRAY_STRIP": "GF2",
}
FAMILY_DISPLAY = {
    "GF0_REF_NESTED_MAZE": "GF0 nested maze",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "GF1 single bottleneck",
    "GF2_PORE_ARRAY_STRIP": "GF2 pore array",
}
FAMILY_COLORS = {
    "GF0_REF_NESTED_MAZE": "#1f77b4",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "#ff7f0e",
    "GF2_PORE_ARRAY_STRIP": "#2ca02c",
}
CANONICAL_ORDER = [
    "OP_SPEED_TIP",
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
    "OP_EFFICIENCY_TIP",
    "OP_SUCCESS_TIP",
]
CANONICAL_SHORT = {
    "OP_SPEED_TIP": "speed",
    "OP_BALANCED_RIDGE_MID": "balanced",
    "OP_STALE_CONTROL_OFF_RIDGE": "stale",
    "OP_EFFICIENCY_TIP": "efficiency",
    "OP_SUCCESS_TIP": "success",
}
CLASSIFICATION_ORDER = ["survives", "renormalizes", "weakens", "fails"]
CLASSIFICATION_TO_VALUE = {label: index for index, label in enumerate(CLASSIFICATION_ORDER)}
CLASSIFICATION_COLORS = {
    "survives": "#31a354",
    "renormalizes": "#3182bd",
    "weakens": "#f0ad4e",
    "fails": "#d62728",
}
METRIC_SPECS = [
    ("first_gate_commit_delay", "commit delay", True),
    ("wall_dwell_before_first_commit", "wall dwell", True),
    ("residence_given_approach", "arrival", False),
]
PANEL_TITLES = {
    "A": "Geometry Gallery and Matched Transfer Object",
    "B": "Family-Specific Backbone Ordering Comparison",
    "C": "Invariant Table: Survives, Renormalizes, Weakens, Fails",
    "D": "Coefficient-Renormalization Detail",
    "E": "Weaker Transfer Signals Kept Secondary",
    "F": "Tested-Family Scope Boundary",
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


def load_inputs() -> dict[str, pd.DataFrame]:
    canonical = pd.read_csv(CANONICAL_SUMMARY_PATH).copy()
    reference = pd.read_csv(REFERENCE_SUMMARY_PATH).copy()
    invariant = pd.read_csv(INVARIANT_TABLE_PATH).copy()
    canonical["geometry_family"] = pd.Categorical(canonical["geometry_family"], FAMILY_ORDER, ordered=True)
    canonical["canonical_label"] = pd.Categorical(canonical["canonical_label"], CANONICAL_ORDER, ordered=True)
    canonical = canonical.sort_values(["geometry_family", "canonical_label"]).reset_index(drop=True)
    reference["geometry_family"] = pd.Categorical(reference["geometry_family"], FAMILY_ORDER, ordered=True)
    reference = reference.sort_values("geometry_family").reset_index(drop=True)
    return {"canonical": canonical, "reference": reference, "invariant": invariant}


def normalize_profile(values: np.ndarray, ascending: bool) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if not ascending:
        values = -values
    value_min = float(np.min(values))
    value_max = float(np.max(values))
    if value_max <= value_min:
        return np.full_like(values, 0.5, dtype=float)
    return (values - value_min) / (value_max - value_min)


def build_backbone_profile_table(canonical_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family in FAMILY_ORDER:
        family_df = canonical_summary[canonical_summary["geometry_family"] == family].copy()
        family_df = family_df.set_index("canonical_label").loc[CANONICAL_ORDER].reset_index()
        for metric_name, metric_label, ascending in METRIC_SPECS:
            normalized = normalize_profile(family_df[metric_name].to_numpy(dtype=float), ascending=ascending)
            for canonical_label, raw_value, normalized_value in zip(
                family_df["canonical_label"].astype(str),
                family_df[metric_name].astype(float),
                normalized,
            ):
                rows.append(
                    {
                        "geometry_family": family,
                        "metric_name": metric_name,
                        "metric_label": metric_label,
                        "canonical_label": canonical_label,
                        "raw_value": float(raw_value),
                        "normalized_value": float(normalized_value),
                    }
                )
    return pd.DataFrame(rows)


def build_coefficient_ratio_table(reference_summary: pd.DataFrame) -> pd.DataFrame:
    reference = reference_summary.set_index("geometry_family")
    gf0 = reference.loc["GF0_REF_NESTED_MAZE"]
    rows: list[dict[str, Any]] = []
    metric_specs = [
        ("ell_g", "ell_g"),
        ("tau_g", "tau_g"),
        ("baseline_wall_fraction", "wall fraction"),
        ("baseline_commit_events_per_traj", "commit events"),
        ("baseline_approach_events_per_traj", "approach events"),
    ]
    for family in FAMILY_ORDER[1:]:
        for source_name, display_name in metric_specs:
            rows.append(
                {
                    "geometry_family": family,
                    "metric_name": source_name,
                    "metric_label": display_name,
                    "ratio_to_gf0": float(reference.loc[family, source_name] / gf0[source_name]),
                }
            )
    return pd.DataFrame(rows)


def build_weak_signal_summary(canonical_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family in FAMILY_ORDER:
        family_df = canonical_summary[canonical_summary["geometry_family"] == family].copy()
        balanced = family_df[family_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
        stale = family_df[family_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
        p_reach_max = float(family_df["p_reach_commit"].max())
        commit_max = float(family_df["commit_given_residence"].max())
        p_reach_winners = family_df[np.isclose(family_df["p_reach_commit"], p_reach_max)]["canonical_label"].astype(str).tolist()
        commit_winners = family_df[np.isclose(family_df["commit_given_residence"], commit_max)]["canonical_label"].astype(str).tolist()
        rows.append(
            {
                "geometry_family": family,
                "trap_balanced": float(balanced["trap_burden_mean"]),
                "trap_stale": float(stale["trap_burden_mean"]),
                "trap_delta": float(stale["trap_burden_mean"] - balanced["trap_burden_mean"]),
                "p_reach_winner": "tie" if len(p_reach_winners) != 1 else CANONICAL_SHORT[p_reach_winners[0]],
                "commit_winner": "tie" if len(commit_winners) != 1 else CANONICAL_SHORT[commit_winners[0]],
            }
        )
    return pd.DataFrame(rows)


def draw_backbone_sequence(ax: plt.Axes, x0: float, y0: float, scale: float = 1.0) -> None:
    labels = ["bulk", "wall", "approach", "residence", "commit"]
    colors = ["#f0f0f0", "#d9d9d9", "#9ecae1", "#6baed6", "#3182bd"]
    for index, (label, color) in enumerate(zip(labels, colors)):
        cx = x0 + index * 0.12 * scale
        circle = patches.Circle((cx, y0), 0.035 * scale, facecolor=color, edgecolor="0.35")
        ax.add_patch(circle)
        ax.text(cx, y0 - 0.06 * scale, label, ha="center", va="top", fontsize=7)
        if index < len(labels) - 1:
            ax.annotate(
                "",
                xy=(cx + 0.07 * scale, y0),
                xytext=(cx + 0.04 * scale, y0),
                arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "0.35"},
            )


def draw_geometry_cartoon(ax: plt.Axes, family: str, x0: float, y0: float, width: float, height: float) -> None:
    ax.add_patch(
        patches.FancyBboxPatch(
            (x0, y0),
            width,
            height,
            boxstyle="round,pad=0.02",
            facecolor="#fbfbfb",
            edgecolor="0.78",
        )
    )
    inner_x = x0 + 0.04 * width
    inner_y = y0 + 0.12 * height
    inner_w = 0.92 * width
    inner_h = 0.64 * height
    ax.add_patch(patches.Rectangle((inner_x, inner_y), inner_w, inner_h, fill=False, edgecolor="0.35", linewidth=1.2))

    if family == "GF0_REF_NESTED_MAZE":
        barriers = [(0.38, 0.55), (0.63, 0.45)]
    elif family == "GF1_SINGLE_BOTTLENECK_CHANNEL":
        barriers = [(0.52, 0.50)]
    else:
        barriers = [(0.34, 0.62), (0.58, 0.38)]

    for barrier_x_rel, gap_y_rel in barriers:
        bx = inner_x + barrier_x_rel * inner_w
        gap_y = inner_y + gap_y_rel * inner_h
        wall_half = 0.02 * width
        gap_half = 0.11 * height
        ax.add_patch(patches.Rectangle((bx - wall_half, inner_y), 2 * wall_half, gap_y - gap_half - inner_y, color="0.65"))
        ax.add_patch(
            patches.Rectangle(
                (bx - wall_half, gap_y + gap_half),
                2 * wall_half,
                inner_y + inner_h - (gap_y + gap_half),
                color="0.65",
            )
        )
        # Highlight the matched pre-commit doorway neighborhood, not post-commit completion.
        ax.add_patch(
            patches.FancyBboxPatch(
                (bx - 0.06 * width, gap_y - 0.16 * height),
                0.12 * width,
                0.32 * height,
                boxstyle="round,pad=0.01",
                facecolor="#fee391",
                edgecolor="#d95f0e",
                linewidth=1.0,
                alpha=0.85,
            )
        )
    ax.annotate(
        "",
        xy=(inner_x + 0.18 * inner_w, inner_y + 0.50 * inner_h),
        xytext=(inner_x + 0.05 * inner_w, inner_y + 0.50 * inner_h),
        arrowprops={"arrowstyle": "->", "lw": 1.4, "color": FAMILY_COLORS[family]},
    )
    ax.text(x0 + width / 2, y0 + 0.87 * height, FAMILY_SHORT[family], fontsize=10, fontweight="bold", ha="center")
    ax.text(x0 + width / 2, y0 + 0.80 * height, FAMILY_DISPLAY[family].replace("GF0 ", "").replace("GF1 ", "").replace("GF2 ", ""), fontsize=7.8, ha="center")
    draw_backbone_sequence(ax, x0 + 0.07 * width, y0 + 0.08 * height, scale=0.85)


def draw_panel_a(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    width = 0.29
    for index, family in enumerate(FAMILY_ORDER):
        draw_geometry_cartoon(ax, family, 0.03 + index * 0.32, 0.16, width, 0.70)
    ax.text(
        0.5,
        0.04,
        "The matched transfer object is the same pre-commit backbone in all three tested families; the highlighted doorway neighborhood marks the approach-residence-commit structure rather than post-commit completion.",
        ha="center",
        fontsize=8,
    )


def draw_panel_b(ax: plt.Axes, profile_df: pd.DataFrame) -> None:
    ax.set_axis_off()
    inset_positions = [(0.05, 0.66, 0.90, 0.25), (0.05, 0.36, 0.90, 0.25), (0.05, 0.06, 0.90, 0.25)]
    for (metric_name, metric_label, _ascending), (x0, y0, width, height) in zip(METRIC_SPECS, inset_positions):
        inset = ax.inset_axes([x0, y0, width, height])
        subset = profile_df[profile_df["metric_name"] == metric_name].copy()
        for family in FAMILY_ORDER:
            family_subset = subset[subset["geometry_family"] == family].set_index("canonical_label").loc[CANONICAL_ORDER].reset_index()
            inset.plot(
                np.arange(len(CANONICAL_ORDER)),
                family_subset["normalized_value"].to_numpy(dtype=float),
                marker="o",
                linewidth=2.0,
                color=FAMILY_COLORS[family],
                label=FAMILY_SHORT[family],
            )
        inset.set_xlim(-0.1, len(CANONICAL_ORDER) - 0.9)
        inset.set_ylim(-0.05, 1.05)
        inset.set_xticks(np.arange(len(CANONICAL_ORDER)))
        inset.set_xticklabels([CANONICAL_SHORT[label] for label in CANONICAL_ORDER], fontsize=7)
        if y0 > 0.1:
            inset.tick_params(labelbottom=False)
        inset.set_yticks([0.0, 0.5, 1.0])
        inset.set_yticklabels(["low", "mid", "high"], fontsize=7)
        inset.grid(alpha=0.22, linewidth=0.6)
        inset.text(0.01, 0.85, metric_label, transform=inset.transAxes, fontsize=8, fontweight="bold")
    ax.text(
        0.02,
        0.98,
        "Within-family normalization makes shape survival visible: timing and wall-dwell retain the same canonical order, while the arrival branch preserves the same discriminator ordering across GF0, GF1, and GF2.",
        transform=ax.transAxes,
        va="top",
        fontsize=7.8,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.82"},
    )
    legend_handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[family], marker="o", linewidth=2.0, label=FAMILY_SHORT[family]) for family in FAMILY_ORDER
    ]
    ax.legend(handles=legend_handles, loc="lower right", frameon=False, fontsize=7.5)


def draw_panel_c(ax: plt.Axes, invariant_df: pd.DataFrame) -> None:
    display = invariant_df.copy()
    display["classification_value"] = display["classification"].map(CLASSIFICATION_TO_VALUE)
    matrix = display[["classification_value"]].to_numpy(dtype=float)
    image = ax.imshow(matrix, cmap=ListedColormap([CLASSIFICATION_COLORS[label] for label in CLASSIFICATION_ORDER]), aspect="auto", vmin=0, vmax=len(CLASSIFICATION_ORDER) - 1)
    del image
    ax.set_xticks([0])
    ax.set_xticklabels(["status"])
    ax.set_yticks(np.arange(len(display)))
    ax.set_yticklabels([f"{row.invariant_id} {row.invariant_name}" for row in display.itertuples()], fontsize=7.6)
    for row_index, row in enumerate(display.itertuples()):
        ax.text(0, row_index, row.classification, ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        ax.text(0.58, row_index, row.invariant_group, transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color="0.30")
    ax.set_xlim(-0.45, 0.95)
    ax.text(
        0.02,
        -0.15,
        "Full invariant package: three rows survive at shape level, coefficients renormalize, coefficient-exact identity fails, and trap/selectivity stay weaker candidate-level signals.",
        transform=ax.transAxes,
        fontsize=7.8,
        va="top",
    )
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=CLASSIFICATION_COLORS[label], label=label) for label in CLASSIFICATION_ORDER
    ]
    ax.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.33), ncol=2, frameon=False, fontsize=7.5)


def draw_panel_d(ax: plt.Axes, ratio_df: pd.DataFrame) -> None:
    metric_order = ["ell_g", "tau_g", "baseline_wall_fraction", "baseline_commit_events_per_traj", "baseline_approach_events_per_traj"]
    metric_labels = {
        "ell_g": "ell_g",
        "tau_g": "tau_g",
        "baseline_wall_fraction": "wall fraction",
        "baseline_commit_events_per_traj": "commit events",
        "baseline_approach_events_per_traj": "approach events",
    }
    x = np.arange(len(metric_order))
    width = 0.32
    for offset, family in [(-width / 2, "GF1_SINGLE_BOTTLENECK_CHANNEL"), (width / 2, "GF2_PORE_ARRAY_STRIP")]:
        subset = ratio_df[ratio_df["geometry_family"] == family].set_index("metric_name").loc[metric_order].reset_index()
        ax.bar(
            x + offset,
            subset["ratio_to_gf0"].to_numpy(dtype=float),
            width=width,
            color=FAMILY_COLORS[family],
            label=FAMILY_SHORT[family],
        )
    ax.axhline(1.0, color="#555555", linestyle="--", linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([metric_labels[name] for name in metric_order], rotation=18)
    ax.set_ylabel("ratio to GF0")
    ax.grid(axis="y", alpha=0.22, linewidth=0.6)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    ax.text(
        0.02,
        0.96,
        "Shape survives, coefficients do not. GF1 and GF2 both require strong renormalization in `ell_g`, `tau_g`, and local encounter statistics, which rules out coefficient identity while supporting the shape-level transfer reading.",
        transform=ax.transAxes,
        va="top",
        fontsize=7.7,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.82"},
    )


def draw_panel_e(ax: plt.Axes, weak_df: pd.DataFrame) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.add_patch(
        patches.FancyBboxPatch((0.02, 0.54), 0.96, 0.42, boxstyle="round,pad=0.02", facecolor="#f7f7f7", edgecolor="0.82")
    )
    ax.text(0.04, 0.92, "Selectivity scalar winners", fontsize=9.2, fontweight="bold", va="top")
    ax.text(0.56, 0.92, "top p_reach_commit", fontsize=8, fontweight="bold", va="top", ha="right")
    ax.text(0.94, 0.92, "top commit_given_residence", fontsize=8, fontweight="bold", va="top", ha="right")
    for index, row in enumerate(weak_df.itertuples()):
        y = 0.82 - index * 0.11
        ax.text(0.04, y, FAMILY_SHORT[row.geometry_family], fontsize=8.5, fontweight="bold", va="center")
        ax.text(0.56, y, str(row.p_reach_winner), fontsize=8, va="center", ha="right")
        ax.text(0.94, y, str(row.commit_winner), fontsize=8, va="center", ha="right")

    trap_ax = ax.inset_axes([0.06, 0.10, 0.88, 0.28])
    trap_y = np.arange(len(weak_df))[::-1]
    for family_y, row in zip(trap_y, weak_df.itertuples()):
        trap_ax.plot([row.trap_balanced, row.trap_stale], [family_y, family_y], color="0.70", linewidth=2.0)
        trap_ax.scatter(row.trap_balanced, family_y, color="#31a354", s=55, zorder=3, label="balanced" if family_y == trap_y[0] else None)
        trap_ax.scatter(row.trap_stale, family_y, color="#de2d26", s=55, zorder=3, label="stale" if family_y == trap_y[0] else None)
        trap_ax.text(max(row.trap_balanced, row.trap_stale) + 8e-05, family_y, format_value(row.trap_delta), fontsize=7.5, va="center")
    trap_ax.set_yticks(trap_y)
    trap_ax.set_yticklabels([FAMILY_SHORT[family] for family in weak_df["geometry_family"]])
    trap_ax.set_xlabel("trap burden")
    trap_ax.grid(axis="x", alpha=0.22, linewidth=0.6)
    trap_ax.legend(frameon=False, fontsize=7, loc="lower right")
    trap_ax.text(0.02, 0.90, "delta shown at right", transform=trap_ax.transAxes, fontsize=7)

    ax.text(
        0.02,
        0.01,
        "Weaker signals stay visible but subordinate: the success branch is not isolated by one universal scalar across GF1/GF2, and trap burden changes are geometry-sensitive rather than a clean transfer invariant.",
        fontsize=7.7,
        va="bottom",
    )


def draw_panel_f(ax: plt.Axes, invariant_df: pd.DataFrame, ratio_df: pd.DataFrame) -> None:
    ax.set_axis_off()
    survives_count = int((invariant_df["classification"] == "survives").sum())
    weakens_count = int((invariant_df["classification"] == "weakens").sum())
    ratio_max = float(ratio_df["ratio_to_gf0"].max())
    boxes = [
        (
            0.02,
            0.62,
            0.29,
            0.28,
            "#e5f5e0",
            "Supported now",
            [
                "GF0/GF1/GF2 preserve the pre-commit backbone shape",
                f"{survives_count} invariant rows survive cleanly",
                "Main verdict: shape survives before crossing detail",
            ],
        ),
        (
            0.35,
            0.62,
            0.29,
            0.28,
            "#deebf7",
            "Renormalizes",
            [
                "Absolute scales and encounter coefficients shift strongly",
                f"largest displayed ratio is {ratio_max:.2f}x GF0",
                "Correct reading: same shape, geometry-specific coefficients",
            ],
        ),
        (
            0.68,
            0.62,
            0.30,
            0.28,
            "#fee0d2",
            "Not implied here",
            [
                "No GF3 stress upgrade",
                "No unrestricted universality claim",
                "No post-commit completion transfer claim",
            ],
        ),
    ]
    for x0, y0, width, height, color, title, bullets in boxes:
        ax.add_patch(
            patches.FancyBboxPatch((x0, y0), width, height, boxstyle="round,pad=0.02", facecolor=color, edgecolor="0.82")
        )
        ax.text(x0 + 0.02, y0 + height - 0.04, title, fontsize=9.2, fontweight="bold", va="top")
        for index, bullet in enumerate(bullets):
            ax.text(x0 + 0.02, y0 + height - 0.10 - index * 0.07, bullet, fontsize=8, va="top")

    ax.add_patch(
        patches.FancyBboxPatch((0.02, 0.10), 0.96, 0.40, boxstyle="round,pad=0.02", facecolor="#f7f7f7", edgecolor="0.82")
    )
    ax.text(0.04, 0.46, "Scope note", fontsize=9.2, fontweight="bold", va="top")
    ax.text(
        0.04,
        0.37,
        f"This extended-data figure strengthens the tested-family transfer verdict without expanding the claim ceiling. Weak signals appear in {weakens_count} rows, but they do not overturn the backbone result. GF3 remains a deferred stress test, so broader irregular-labyrinth universality is still outside scope.",
        fontsize=8.1,
        va="top",
        wrap=True,
    )
    ax.text(
        0.04,
        0.20,
        "Use this figure as family-specific support for the main-text statement: the transferable object is the pre-commit backbone, shape survives across GF0/GF1/GF2, and coefficient identity is neither expected nor supported.",
        fontsize=8.1,
        va="top",
        wrap=True,
    )


def build_figure(inputs: dict[str, pd.DataFrame]) -> None:
    profile_df = build_backbone_profile_table(inputs["canonical"])
    ratio_df = build_coefficient_ratio_table(inputs["reference"])
    weak_df = build_weak_signal_summary(inputs["canonical"])

    fig, axes = plt.subplots(2, 3, figsize=(17, 10.6))
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.08, top=0.88, wspace=0.32, hspace=0.42)
    axes = axes.flatten()

    draw_panel_a(axes[0])
    draw_panel_b(axes[1], profile_df)
    draw_panel_c(axes[2], inputs["invariant"])
    draw_panel_d(axes[3], ratio_df)
    draw_panel_e(axes[4], weak_df)
    draw_panel_f(axes[5], inputs["invariant"], ratio_df)

    for ax, panel_letter in zip(axes, ["A", "B", "C", "D", "E", "F"]):
        annotate_panel(ax, panel_letter)
        ax.set_title(PANEL_TITLES[panel_letter], fontsize=12)

    fig.suptitle("Extended Data Figure 5. Geometry-Transfer Detail and Family-Specific Comparison", fontsize=17, fontweight="bold")
    fig.text(
        0.5,
        0.93,
        "Detailed support for the main-text transfer verdict. The transferable object stays centered on the pre-commit backbone: shape survives across GF0/GF1/GF2, coefficients renormalize, weaker signals stay secondary, and GF3-style universality is not implied.",
        ha="center",
        fontsize=10,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_manifest(inputs: dict[str, pd.DataFrame]) -> None:
    ratio_df = build_coefficient_ratio_table(inputs["reference"])
    weak_df = build_weak_signal_summary(inputs["canonical"])
    invariant_df = inputs["invariant"].copy()
    counts = invariant_df["classification"].value_counts().to_dict()
    largest_ratio = float(ratio_df["ratio_to_gf0"].max())
    gf1_commit_ratio = float(
        ratio_df[(ratio_df["geometry_family"] == "GF1_SINGLE_BOTTLENECK_CHANNEL") & (ratio_df["metric_name"] == "baseline_commit_events_per_traj")]["ratio_to_gf0"].iloc[0]
    )
    gf2_wall_ratio = float(
        ratio_df[(ratio_df["geometry_family"] == "GF2_PORE_ARRAY_STRIP") & (ratio_df["metric_name"] == "baseline_wall_fraction")]["ratio_to_gf0"].iloc[0]
    )
    lines = [
        "# Extended Data Figure 5 Panel Manifest",
        "",
        "## Scope",
        "",
        "This note documents the panel logic for Extended Data Figure 5, which provides the family-specific support behind the main-text geometry-transfer verdict while keeping the claim ceiling at shape-level transfer plus coefficient renormalization.",
        "",
        "Primary data sources:",
        "",
        f"- [extended_data_plan.md](file://{PROJECT_ROOT / 'docs' / 'extended_data_plan.md'})",
        f"- [geometry_family_spec.md](file://{PROJECT_ROOT / 'docs' / 'geometry_family_spec.md'})",
        f"- [geometry_transfer_plan.md](file://{PROJECT_ROOT / 'docs' / 'geometry_transfer_plan.md'})",
        f"- [geometry_transfer_run_report.md](file://{PROJECT_ROOT / 'docs' / 'geometry_transfer_run_report.md'})",
        f"- [geometry_transfer_first_look.md](file://{PROJECT_ROOT / 'docs' / 'geometry_transfer_first_look.md'})",
        f"- [geometry_transfer_evidence_table.md](file://{PROJECT_ROOT / 'docs' / 'geometry_transfer_evidence_table.md'})",
        f"- [geometry_transfer_claim_upgrade_note.md](file://{PROJECT_ROOT / 'docs' / 'geometry_transfer_claim_upgrade_note.md'})",
        f"- [canonical_transfer_summary.csv](file://{CANONICAL_SUMMARY_PATH})",
        f"- [reference_extraction_summary.csv](file://{REFERENCE_SUMMARY_PATH})",
        f"- [geometry_transfer_invariant_table.csv](file://{INVARIANT_TABLE_PATH})",
        f"- [transfer_stress_figure.png](file://{STRESS_FIGURE_PATH})",
        f"- [ED Figure 5 PNG](file://{PNG_PATH})",
        f"- [ED Figure 5 SVG](file://{SVG_PATH})",
        "",
        "## Figure-Level Message",
        "",
        "- this figure exists to show family-specific support for the transfer verdict, not to expand the verdict beyond the tested GF0/GF1/GF2 family",
        "- the transferable object remains the pre-commit backbone rather than full crossing completion",
        "- shape survival and coefficient renormalization are both made explicit, so the reader can see why coefficient identity is not the right claim",
        "- weaker transfer signals are kept visible but secondary",
        "",
        "## Panel Logic",
        "",
        "### Panel A",
        "",
        "- title: `Compact geometry gallery for GF0, GF1, and GF2 with matched transfer object highlighted`",
        "- purpose: show the three tested families and keep attention on the shared approach-residence-commit object rather than downstream completion",
        "- quantitative note: all gallery cartoons carry the same five-state backbone `bulk -> wall -> approach -> residence -> commit`",
        "",
        "### Panel B",
        "",
        "- title: `Family-specific backbone ordering comparison`",
        "- purpose: compare within-family shape profiles for commit delay, wall dwell, and arrival organization across the canonical operating-point order",
        "- quantitative note: timing and wall-dwell retain the same canonical order in all three tested families, while arrival preserves the same discriminator ordering",
        "",
        "### Panel C",
        "",
        "- title: `Full invariant table visualization, including survives / renormalizes / weakens / fails`",
        "- purpose: show the whole verdict package rather than only the strengthened rows",
        f"- quantitative note: counts are survives `{counts.get('survives', 0)}`, renormalizes `{counts.get('renormalizes', 0)}`, weakens `{counts.get('weakens', 0)}`, fails `{counts.get('fails', 0)}`",
        "",
        "### Panel D",
        "",
        "- title: `Coefficient-renormalization detail panel`",
        "- purpose: make the difference between shape survival and coefficient identity visually explicit",
        f"- quantitative note: the largest displayed GF1/GF2 to GF0 ratio is `{largest_ratio:.2f}`, with `GF1` commit events at `{gf1_commit_ratio:.2f}` and `GF2` wall fraction at `{gf2_wall_ratio:.2f}`",
        "",
        "### Panel E",
        "",
        "- title: `Weaker transfer signals such as trap burden and selectivity scalar behavior`",
        "- purpose: retain weaker signals without allowing them to dominate the figure-level verdict",
        f"- quantitative note: trap matched-pair deltas are `{format_value(float(weak_df.loc[weak_df['geometry_family'] == 'GF0_REF_NESTED_MAZE', 'trap_delta'].iloc[0]))}`, `{format_value(float(weak_df.loc[weak_df['geometry_family'] == 'GF1_SINGLE_BOTTLENECK_CHANNEL', 'trap_delta'].iloc[0]))}`, and `{format_value(float(weak_df.loc[weak_df['geometry_family'] == 'GF2_PORE_ARRAY_STRIP', 'trap_delta'].iloc[0]))}` for GF0, GF1, and GF2 respectively",
        "",
        "### Panel F",
        "",
        "- title: `Optional scope note panel explicitly separating tested-family support from broader GF3-style stress claims`",
        "- purpose: mark the boundary between what the tested family supports now and what remains deferred",
        "- quantitative note: GF3 remains deferred and no unrestricted universality claim is upgraded by this figure",
        "",
        "## Trusted Transfer Layer",
        "",
        "- strongest support: canonical timing order, stale-vs-balanced timing penalty, and arrival-order backbone shape",
        "- strengthened but renormalized: reference scales and local encounter coefficients",
        "- weaker and kept secondary: single-scalar selectivity and trap burden as matched transfer signals",
        "",
        "## Why this stays scoped",
        "",
        "- the figure is centered on GF0/GF1/GF2 and the pre-commit backbone only",
        "- coefficient-exact identity is shown as failed rather than quietly folded into the transfer claim",
        "- GF3-style irregular-labyrinth universality remains explicitly outside the upgraded claim",
        "- post-commit completion transfer is not promoted here",
        "",
        "## Bottom Line",
        "",
        "Extended Data Figure 5 is the detailed support layer behind the main-text geometry-transfer verdict. It shows that the pre-commit backbone survives across the tested family at the level of shape, that the absolute coefficients renormalize rather than match exactly, and that weaker signals stay visibly secondary while broader universality remains out of scope.",
        "",
    ]
    MANIFEST_DOC_PATH.write_text("\n".join(lines), encoding="ascii")


def build_outputs() -> dict[str, str]:
    inputs = load_inputs()
    build_figure(inputs)
    write_manifest(inputs)
    return {
        "png": str(PNG_PATH),
        "svg": str(SVG_PATH),
        "manifest_doc": str(MANIFEST_DOC_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Extended Data Figure 5: geometry-transfer detail and family-specific comparison.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
