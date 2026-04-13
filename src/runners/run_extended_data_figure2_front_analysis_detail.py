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
from matplotlib.ticker import FormatStrFormatter

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_front_analysis import (
    FRONT_COLORS,
    extract_fronts,
    load_front_dataset,
    objective_summary_rows,
)

FRONT_ANALYSIS_ROOT = PROJECT_ROOT / "outputs" / "figures" / "front_analysis"
OVERLAP_PATH = FRONT_ANALYSIS_ROOT / "front_overlap_summary.csv"
DISTANCE_PATH = FRONT_ANALYSIS_ROOT / "front_distance_summary.csv"
PARETO_PATH = FRONT_ANALYSIS_ROOT / "pareto_candidates.csv"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "extended_data"
PNG_PATH = OUTPUT_DIR / "ed_fig2_front_analysis_detail.png"
SVG_PATH = OUTPUT_DIR / "ed_fig2_front_analysis_detail.svg"
MANIFEST_DOC_PATH = PROJECT_ROOT / "docs" / "ed_fig2_panel_manifest.md"

OBJECTIVE_ORDER = ["Psucc_mean", "eta_sigma_mean", "MFPT_mean"]
OBJECTIVE_DISPLAY = {
    "Psucc_mean": "success",
    "eta_sigma_mean": "efficiency",
    "MFPT_mean": "speed",
}
PAIR_DISPLAY = {
    ("Psucc_mean", "eta_sigma_mean"): "success vs efficiency",
    ("Psucc_mean", "MFPT_mean"): "success vs speed",
    ("eta_sigma_mean", "MFPT_mean"): "efficiency vs speed",
    ("Psucc_mean", "eta_sigma_mean|MFPT_mean"): "all three fronts",
}
PARAMETER_DISPLAY = {
    "Pi_m": "Pi_m",
    "Pi_f": "Pi_f",
    "Pi_U": "Pi_U",
}
PANEL_TITLES = {
    "A": "Front projection in Pi_m",
    "B": "Front projection in Pi_f",
    "C": "Front projection in Pi_U",
    "D": "Top-k overlap for ranked front sets",
    "E": "Winner-distance summary in parameter space",
    "F": "CI-aware winner callout and anchor support",
}


def load_inputs() -> dict[str, Any]:
    confirmatory = load_front_dataset().copy()
    fronts = extract_fronts(confirmatory, top_k=20)
    overlap_df = pd.read_csv(OVERLAP_PATH).copy()
    distance_df = pd.read_csv(DISTANCE_PATH).copy()
    pareto_df = pd.read_csv(PARETO_PATH).copy()
    summary_rows = objective_summary_rows(confirmatory).copy()
    return {
        "confirmatory": confirmatory,
        "fronts": fronts,
        "overlap": overlap_df,
        "distance": distance_df,
        "pareto": pareto_df,
        "summary_rows": summary_rows,
    }


def format_ci(low: float, high: float) -> str:
    if max(abs(low), abs(high)) < 1e-3:
        return f"[{low:.2e}, {high:.2e}]"
    return f"[{low:.3f}, {high:.3f}]"


def annotate_panel(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.16,
        1.03,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def build_overlap_display_tables(overlap_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered_pairs = list(PAIR_DISPLAY.keys())
    overlap = overlap_df.copy()
    overlap["pair_label"] = overlap.apply(
        lambda row: PAIR_DISPLAY[(row["objective_a"], row["objective_b"])],
        axis=1,
    )
    counts = (
        overlap.pivot(index="pair_label", columns="k", values="overlap_count")
        .reindex([PAIR_DISPLAY[pair] for pair in ordered_pairs])
        .reindex(columns=[5, 10, 20])
    )
    jaccard = (
        overlap.pivot(index="pair_label", columns="k", values="jaccard_index")
        .reindex([PAIR_DISPLAY[pair] for pair in ordered_pairs])
        .reindex(columns=[5, 10, 20])
    )
    return counts, jaccard


def directional_ci_check_count(distance_df: pd.DataFrame) -> tuple[int, int]:
    checks = pd.concat(
        [
            distance_df["b_separated_from_a_by_ci"].fillna(False).astype(bool),
            distance_df["a_separated_from_b_by_ci"].fillna(False).astype(bool),
        ],
        ignore_index=True,
    )
    return int(checks.sum()), int(len(checks))


def projection_panel(
    ax: plt.Axes,
    *,
    parameter: str,
    confirmatory: pd.DataFrame,
    fronts: dict[str, pd.DataFrame],
) -> None:
    row_positions = {"Psucc_mean": 2.0, "eta_sigma_mean": 1.0, "MFPT_mean": 0.0}
    param_values = confirmatory[parameter].astype(float)
    span = float(param_values.max() - param_values.min())
    pad = span * 0.08 if span > 0 else 0.02
    xmin = float(param_values.min() - pad)
    xmax = float(param_values.max() + pad)

    ax.vlines(param_values, -0.55, -0.38, color="0.86", linewidth=0.7, alpha=0.8, zorder=1)
    ax.text(
        0.02,
        0.02,
        f"all confirmatory points: {len(confirmatory)}",
        transform=ax.transAxes,
        fontsize=8,
        color="0.40",
    )

    winner_lines: list[str] = []
    for objective in OBJECTIVE_ORDER:
        front = fronts[objective].sort_values([parameter, "front_rank"]).reset_index(drop=True).copy()
        offsets = np.linspace(-0.18, 0.18, len(front))
        yvals = row_positions[objective] + offsets
        front["plot_y"] = yvals
        ax.scatter(
            front[parameter],
            front["plot_y"],
            color=FRONT_COLORS[objective],
            s=34,
            alpha=0.80,
            edgecolors="none",
            zorder=3,
        )
        anchors = front[front["is_anchor_8192"]].copy()
        if not anchors.empty:
            ax.scatter(
                anchors[parameter],
                anchors["plot_y"],
                facecolors="none",
                edgecolors="black",
                linewidths=0.9,
                s=72,
                zorder=4,
            )
        winner = front.iloc[0]
        ax.scatter(
            [winner[parameter]],
            [row_positions[objective]],
            marker="D",
            s=95,
            color=FRONT_COLORS[objective],
            edgecolors="black",
            linewidths=0.8,
            zorder=5,
        )
        winner_lines.append(f"{OBJECTIVE_DISPLAY[objective]} {float(winner[parameter]):.3g}")

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.72, 2.42)
    ax.set_yticks([2.0, 1.0, 0.0])
    ax.set_yticklabels(["success front", "efficiency front", "speed front"])
    ax.set_xlabel(PARAMETER_DISPLAY[parameter])
    if parameter == "Pi_f":
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    else:
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    ax.grid(axis="x", alpha=0.22, linewidth=0.6)
    ax.text(
        0.98,
        0.97,
        "winner positions:\n" + "\n".join(winner_lines),
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.82"},
    )


def overlap_panel(ax: plt.Axes, overlap_df: pd.DataFrame) -> None:
    counts, jaccard = build_overlap_display_tables(overlap_df)
    image = ax.imshow(counts.to_numpy(dtype=float), cmap="Blues", vmin=0.0, vmax=max(1.0, float(counts.to_numpy().max())))
    ax.set_xticks(np.arange(len(counts.columns)))
    ax.set_xticklabels([f"top-{int(col)}" for col in counts.columns])
    ax.set_yticks(np.arange(len(counts.index)))
    ax.set_yticklabels(counts.index)
    for row_index, row_label in enumerate(counts.index):
        for col_index, col_label in enumerate(counts.columns):
            value = int(counts.loc[row_label, col_label])
            j_value = float(jaccard.loc[row_label, col_label])
            ax.text(
                col_index,
                row_index,
                f"{value}\nJ={j_value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="black",
            )
    ax.text(
        0.98,
        -0.16,
        "all front pairs keep zero overlap at top-10",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
    )
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.03, label="overlap count")


def winner_distance_panel(ax: plt.Axes, summary_rows: pd.DataFrame, distance_df: pd.DataFrame) -> None:
    winners = summary_rows[["objective", "winner_Pi_m", "winner_Pi_f", "winner_Pi_U"]].copy()
    winners = winners.rename(
        columns={
            "winner_Pi_m": "Pi_m",
            "winner_Pi_f": "Pi_f",
            "winner_Pi_U": "Pi_U",
        }
    )
    positions = {
        row["objective"]: (float(row["Pi_U"]), float(row["Pi_m"]))
        for _, row in winners.iterrows()
    }
    for _, row in distance_df.iterrows():
        x0, y0 = positions[row["winner_a"]]
        x1, y1 = positions[row["winner_b"]]
        ax.plot([x0, x1], [y0, y1], color="0.55", linestyle="--", linewidth=1.1, zorder=1)
        mid_x = (x0 + x1) / 2.0
        mid_y = (y0 + y1) / 2.0
        ax.text(
            mid_x,
            mid_y,
            f"d*={float(row['normalized_distance']):.2f}",
            fontsize=8,
            ha="center",
            va="center",
            bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.85"},
        )
    for _, row in winners.iterrows():
        objective = row["objective"]
        ax.scatter(
            float(row["Pi_U"]),
            float(row["Pi_m"]),
            color=FRONT_COLORS[objective],
            marker="D",
            s=130,
            edgecolors="black",
            linewidths=0.9,
            zorder=3,
        )
        ax.annotate(
            f"{OBJECTIVE_DISPLAY[objective]}\nPi_f={float(row['Pi_f']):.3f}",
            (float(row["Pi_U"]), float(row["Pi_m"])),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xlabel("Pi_U")
    ax.set_ylabel("Pi_m")
    ax.grid(alpha=0.22, linewidth=0.6)
    ax.set_xlim(0.085, 0.315)
    ax.set_ylim(0.06, 0.205)
    ax.text(
        0.02,
        0.04,
        "three distinct winner locations\nprojected in (Pi_U, Pi_m)",
        transform=ax.transAxes,
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.82"},
    )


def uncertainty_panel(ax: plt.Axes, summary_rows: pd.DataFrame, confirmatory: pd.DataFrame, distance_df: pd.DataFrame) -> None:
    ax.set_axis_off()
    true_checks, total_checks = directional_ci_check_count(distance_df)
    anchor_count = int(confirmatory["is_anchor_8192"].sum())
    ax.text(
        0.00,
        0.98,
        f"directional CI checks passed: {true_checks}/{total_checks}\n8192 anchors in confirmatory set: {anchor_count}",
        fontsize=9,
        va="top",
    )
    y_positions = [0.75, 0.49, 0.23]
    for y, (_, row) in zip(y_positions, summary_rows.iterrows()):
        objective = row["objective"]
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.00, y - 0.12),
                0.98,
                0.18,
                boxstyle="round,pad=0.02",
                facecolor="#f7f7f7",
                edgecolor="0.80",
            )
        )
        ax.text(
            0.03,
            y + 0.03,
            OBJECTIVE_DISPLAY[objective],
            color=FRONT_COLORS[objective],
            fontsize=10,
            fontweight="bold",
            va="center",
        )
        ax.text(
            0.25,
            y + 0.04,
            f"winner: {row['winner_analysis_source']} | n={int(row['winner_n_traj'])}",
            fontsize=8,
            va="center",
        )
        ax.text(
            0.25,
            y - 0.01,
            f"CI on own metric: {format_ci(float(row['winner_ci_low']), float(row['winner_ci_high']))}",
            fontsize=8,
            va="center",
        )
        ax.text(
            0.25,
            y - 0.06,
            f"best 8192 anchor: ({float(row['anchor_Pi_m']):.2f}, {float(row['anchor_Pi_f']):.3f}, {float(row['anchor_Pi_U']):.2f})",
            fontsize=8,
            va="center",
        )
    ax.text(
        0.00,
        0.02,
        "This panel only reports the completed front-analysis confidence checks: winner CI spans, anchor coverage, and pairwise CI-aware separation.",
        fontsize=8,
        va="bottom",
    )


def build_figure(inputs: dict[str, Any]) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(16, 9.8))
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.08, top=0.88, wspace=0.34, hspace=0.38)
    axes = axes.flatten()

    projection_parameters = [("A", "Pi_m"), ("B", "Pi_f"), ("C", "Pi_U")]
    for index, (panel_letter, parameter) in enumerate(projection_parameters):
        ax = axes[index]
        annotate_panel(ax, panel_letter)
        ax.set_title(PANEL_TITLES[panel_letter], fontsize=12)
        projection_panel(
            ax,
            parameter=parameter,
            confirmatory=inputs["confirmatory"],
            fronts=inputs["fronts"],
        )

    annotate_panel(axes[3], "D")
    axes[3].set_title(PANEL_TITLES["D"], fontsize=12)
    overlap_panel(axes[3], inputs["overlap"])

    annotate_panel(axes[4], "E")
    axes[4].set_title(PANEL_TITLES["E"], fontsize=12)
    winner_distance_panel(axes[4], inputs["summary_rows"], inputs["distance"])

    annotate_panel(axes[5], "F")
    axes[5].set_title(PANEL_TITLES["F"], fontsize=12, loc="left")
    uncertainty_panel(axes[5], inputs["summary_rows"], inputs["confirmatory"], inputs["distance"])

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", label="success front members", markerfacecolor=FRONT_COLORS["Psucc_mean"], markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", label="efficiency front members", markerfacecolor=FRONT_COLORS["eta_sigma_mean"], markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", label="speed front members", markerfacecolor=FRONT_COLORS["MFPT_mean"], markersize=7),
        plt.Line2D([0], [0], marker="D", color="w", label="front winner", markerfacecolor="#666666", markeredgecolor="black", markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", label="8192 anchor", markerfacecolor="none", markeredgecolor="black", markersize=8),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.02), fontsize=8)

    fig.suptitle("Extended Data Figure 2. Front-Analysis Details and Uncertainty-Aware Separation", fontsize=17, fontweight="bold")
    fig.text(
        0.5,
        0.93,
        "Detailed support for the main-text front-tip claim: axis projections, overlap counts, parameter-space winner distances, and CI-aware anchor checks.",
        ha="center",
        fontsize=10,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_manifest(inputs: dict[str, Any]) -> None:
    true_checks, total_checks = directional_ci_check_count(inputs["distance"])
    counts, _ = build_overlap_display_tables(inputs["overlap"])
    lines = [
        "# Extended Data Figure 2 Panel Manifest",
        "",
        "## Scope",
        "",
        "This note documents the panel logic for Extended Data Figure 2, which provides detailed support for the main-text claim that the productive region forms a Pareto-like ridge with distinct success, efficiency, and speed tips.",
        "",
        "Primary data sources:",
        "",
        f"- [front_analysis_report.md](file://{PROJECT_ROOT / 'docs' / 'front_analysis_report.md'})",
        f"- [front_overlap_summary.csv](file://{OVERLAP_PATH})",
        f"- [front_distance_summary.csv](file://{DISTANCE_PATH})",
        f"- [pareto_candidates.csv](file://{PARETO_PATH})",
        f"- [ED Figure 2 PNG](file://{PNG_PATH})",
        f"- [ED Figure 2 SVG](file://{SVG_PATH})",
        "",
        "## Visual Language",
        "",
        "- blue, green, and red retain the `success`, `efficiency`, and `speed` front naming from the completed front-analysis package",
        "- top-row panels project the top-20 front members onto `Pi_m`, `Pi_f`, and `Pi_U` while keeping all confirmatory points as a light reference rug",
        "- diamonds mark the front winners and open black circles mark `8192` anchors that lie on the plotted front",
        "- lower-row panels report overlap counts, parameter-space winner distances, and CI-aware confidence callouts without adding new interpretation",
        "",
        "## Panel Logic",
        "",
        "### Panel A",
        "",
        "- title: `Front projection in Pi_m`",
        "- purpose: show where the success, efficiency, and speed fronts sit along `Pi_m`",
        "- quantitative note: the three winners sit at `Pi_m = 0.08`, `0.18`, and `0.10`",
        "",
        "### Panel B",
        "",
        "- title: `Front projection in Pi_f`",
        "- purpose: show the tight `Pi_f` pinning of the front family",
        "- quantitative note: the front remains concentrated on `Pi_f = 0.018` to `0.025`",
        "",
        "### Panel C",
        "",
        "- title: `Front projection in Pi_U`",
        "- purpose: show that `Pi_U` orders objective preference along the ridge",
        "- quantitative note: the winners sit at `Pi_U = 0.10`, `0.15`, and `0.30`",
        "",
        "### Panel D",
        "",
        "- title: `Top-k overlap for ranked front sets`",
        "- purpose: report overlap counts and Jaccard indices for `k = 5`, `10`, and `20`",
        f"- quantitative note: the only nonzero pairwise overlap count is `{int(counts.loc['success vs efficiency', 20])}` at `top-20` for `success vs efficiency`",
        "",
        "### Panel E",
        "",
        "- title: `Winner-distance summary in parameter space`",
        "- purpose: show the three winner locations in `(Pi_U, Pi_m)` with `Pi_f` labels and pairwise normalized distances",
        "- quantitative note: pairwise normalized distances span `0.94` to `1.42`",
        "",
        "### Panel F",
        "",
        "- title: `CI-aware winner callout and anchor support`",
        "- purpose: report the completed uncertainty-aware checks already used in the front-analysis package",
        f"- quantitative note: directional CI checks pass in `{true_checks}/{total_checks}` cases and the confirmatory set contains `{int(inputs['confirmatory']['is_anchor_8192'].sum())}` anchors",
        "",
        "## Why this supports rather than replaces Main Figure 2",
        "",
        "- the main text keeps the cleaner claim-bearing view of ridge structure and front-tip separation",
        "- Extended Data Figure 2 carries the denser front-analysis detail: per-axis projections, top-k overlap bookkeeping, parameter-distance bookkeeping, and confidence callouts",
        "- this figure therefore supports the main-text claim quantitatively without becoming the primary interpretive figure",
        "",
        "## Bottom Line",
        "",
        "Extended Data Figure 2 is the detailed numerical support layer for the front-analysis package. It keeps the separation structure explicit, quantitative, and uncertainty-aware while staying within the already completed front-analysis outputs.",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Figure 2: front-analysis details and uncertainty-aware separation.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
