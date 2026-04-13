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

from src.runners.run_metric_robustness_package import (
    BRANCH_COLORS,
    BRANCH_DISPLAY,
    BRANCH_ORDER,
    CANONICAL_DISPLAY,
    CANONICAL_LABEL_ORDER,
    METRIC_COLUMNS,
    METRIC_DISPLAY,
    METRIC_MARKERS,
    build_metric_robustness_table,
    load_inputs as load_metric_inputs,
    nondominated_indices,
    rank_canonical_points,
    top_k,
)

EFFICIENCY_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "efficiency_metric_comparison.csv"
ROBUSTNESS_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "metric_robustness_table.csv"
ROBUSTNESS_FIGURE_PATH = PROJECT_ROOT / "outputs" / "figures" / "thermodynamics" / "metric_robustness_map.png"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "extended_data"
PNG_PATH = OUTPUT_DIR / "ed_fig6_thermodynamic_upgrade_detail.png"
SVG_PATH = OUTPUT_DIR / "ed_fig6_thermodynamic_upgrade_detail.svg"
MANIFEST_DOC_PATH = PROJECT_ROOT / "docs" / "ed_fig6_panel_manifest.md"

METRIC_ORDER = ["eta_sigma", "eta_completion_drag", "eta_trap_drag"]
METRIC_COLORS = {
    "eta_sigma": "#1f77b4",
    "eta_completion_drag": "#ff7f0e",
    "eta_trap_drag": "#2ca02c",
}
PANEL_TITLES = {
    "A": "Metric-Family Ridge Comparison",
    "B": "Branch Preference Reordering",
    "C": "Canonical Rank Comparison",
    "D": "Non-Dominated Set Comparison",
    "E": "Current Bookkeeping Diagram",
    "F": "Closure Limits and Scope",
}
BOOKKEEPING_INCLUDED = [
    ("Transport numerator", "Psucc/Tmax and Psucc/MFPT style output proxies"),
    ("Explicit cost proxy", "medium or drag dissipation through Sigma_drag"),
    ("Proxy refinement", "trap-time stale-loss penalty in eta_trap_drag"),
]
BOOKKEEPING_MISSING = [
    ("Active propulsion", "no separate propulsion work or fuel-consumption channel"),
    ("Controller work", "steering burden is kinematic only, not energetic"),
    ("Memory bath", "no separate viscoelastic or memory-side dissipation term"),
    ("Information cost", "no update-rate, sensing, or bandwidth bookkeeping"),
    ("Completion split", "no full pre-commit versus post-commit energetic separation"),
    ("Total closure", "no total entropy-production balance"),
]


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
    summary, metric_table, canonical = load_metric_inputs()
    robustness_table = build_metric_robustness_table(summary, metric_table)
    canonical_ranks = rank_canonical_points(summary, canonical)
    return {
        "summary": summary,
        "metric_table": metric_table,
        "canonical": canonical,
        "robustness": robustness_table,
        "canonical_ranks": canonical_ranks,
    }


def build_branch_count_table(summary: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric_name in METRIC_ORDER:
        metric_column = METRIC_COLUMNS[metric_name]
        top = top_k(summary, metric_column, k=k)
        counts = top["branch_name"].value_counts()
        row = {"metric_name": metric_name}
        for branch_name in BRANCH_ORDER:
            row[branch_name] = int(counts.get(branch_name, 0))
        rows.append(row)
    return pd.DataFrame(rows)


def build_nd_overlap_table(summary: pd.DataFrame) -> pd.DataFrame:
    nd_sets = {
        metric_name: set(summary.iloc[nondominated_indices(summary, METRIC_COLUMNS[metric_name])]["state_point_id"])
        for metric_name in METRIC_ORDER
    }
    rows: list[dict[str, Any]] = []
    for metric_a in METRIC_ORDER:
        for metric_b in METRIC_ORDER:
            set_a = nd_sets[metric_a]
            set_b = nd_sets[metric_b]
            overlap = len(set_a & set_b)
            union = len(set_a | set_b)
            rows.append(
                {
                    "metric_a": metric_a,
                    "metric_b": metric_b,
                    "overlap_count": overlap,
                    "jaccard_index": float(overlap / union if union else 0.0),
                }
            )
    return pd.DataFrame(rows)


def draw_panel_a(ax: plt.Axes, summary: pd.DataFrame) -> None:
    ax.scatter(summary["Pi_U"], summary["Pi_m"], color="#d9d9d9", s=15, alpha=0.35, edgecolors="none")
    for metric_name in METRIC_ORDER:
        metric_column = METRIC_COLUMNS[metric_name]
        nd_df = summary.iloc[nondominated_indices(summary, metric_column)].copy()
        ax.scatter(
            nd_df["Pi_U"],
            nd_df["Pi_m"],
            s=58,
            marker=METRIC_MARKERS[metric_name],
            color=METRIC_COLORS[metric_name],
            edgecolor="black",
            linewidth=0.35,
            alpha=0.86,
            label=METRIC_DISPLAY[metric_name],
        )
        winner = summary.loc[summary[metric_column].idxmax()]
        ax.scatter(
            [winner["Pi_U"]],
            [winner["Pi_m"]],
            s=150,
            marker="*",
            color=METRIC_COLORS[metric_name],
            edgecolor="black",
            linewidth=0.5,
            zorder=5,
        )
    ax.set_xlabel("Pi_U")
    ax.set_ylabel("Pi_m")
    ax.grid(alpha=0.18, linewidth=0.6)
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    ax.text(
        0.02,
        0.97,
        "All three metrics retain the same narrow competitive ridge in `Pi_f`, so the metric upgrade strengthens ridge robustness. What changes is the preferred branch along that ridge, not the ridge itself.",
        transform=ax.transAxes,
        va="top",
        fontsize=7.8,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.82"},
    )


def draw_panel_b(ax: plt.Axes, branch_counts: pd.DataFrame) -> None:
    x = np.arange(len(branch_counts))
    bottom = np.zeros(len(branch_counts), dtype=float)
    for branch_name in BRANCH_ORDER:
        heights = branch_counts[branch_name].to_numpy(dtype=float)
        ax.bar(
            x,
            heights,
            bottom=bottom,
            color=BRANCH_COLORS[branch_name],
            label=BRANCH_DISPLAY[branch_name],
        )
        bottom += heights
    ax.set_xticks(x)
    ax.set_xticklabels([METRIC_DISPLAY[name] for name in branch_counts["metric_name"]], rotation=15)
    ax.set_ylim(0, 10)
    ax.set_ylabel("Top-10 count")
    ax.grid(axis="y", alpha=0.18, linewidth=0.6)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.text(
        0.02,
        0.96,
        "Top-10 concentration moves from the moderate-flow ridge branch under `eta_sigma` to the high-flow branch under the stronger completion-aware metrics.",
        transform=ax.transAxes,
        va="top",
        fontsize=7.8,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.82"},
    )


def draw_panel_c(ax: plt.Axes, canonical_ranks: pd.DataFrame) -> None:
    heatmap = canonical_ranks.set_index("canonical_label")[
        [f"{metric_name}_rank" for metric_name in METRIC_ORDER]
    ].loc[CANONICAL_LABEL_ORDER]
    values = heatmap.to_numpy(dtype=float)
    im = ax.imshow(values, aspect="auto", cmap="YlOrRd_r")
    ax.set_xticks(np.arange(len(METRIC_ORDER)))
    ax.set_xticklabels([METRIC_DISPLAY[name] for name in METRIC_ORDER], rotation=15)
    ax.set_yticks(np.arange(len(CANONICAL_LABEL_ORDER)))
    ax.set_yticklabels([CANONICAL_DISPLAY[label] for label in CANONICAL_LABEL_ORDER])
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f"{int(values[i, j])}", ha="center", va="center", fontsize=8)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="global rank")
    ax.text(
        0.02,
        -0.15,
        "The efficiency tip ranks near the top under `eta_sigma`, while the speed tip jumps to the top tier under the completion-aware metrics. The success tip stays thermodynamically secondary across the current metric family.",
        transform=ax.transAxes,
        fontsize=7.8,
        va="top",
    )


def draw_panel_d(ax: plt.Axes, metric_table: pd.DataFrame, overlap_df: pd.DataFrame) -> None:
    ax.set_axis_off()

    count_ax = ax.inset_axes([0.06, 0.58, 0.88, 0.33])
    plot_df = metric_table[metric_table["is_computed"]].copy()
    count_ax.bar(
        np.arange(len(plot_df)),
        plot_df["pareto_candidate_count"].to_numpy(dtype=float),
        color=[METRIC_COLORS[name] for name in METRIC_ORDER],
    )
    count_ax.set_xticks(np.arange(len(plot_df)))
    count_ax.set_xticklabels(plot_df["metric_name"], rotation=15)
    count_ax.set_ylabel("count")
    count_ax.set_title("non-dominated counts", fontsize=9)
    count_ax.grid(axis="y", alpha=0.18, linewidth=0.6)

    overlap_ax = ax.inset_axes([0.11, 0.06, 0.64, 0.38])
    pivot = overlap_df.pivot(index="metric_a", columns="metric_b", values="jaccard_index").loc[METRIC_ORDER, METRIC_ORDER]
    values = pivot.to_numpy(dtype=float)
    im = overlap_ax.imshow(values, cmap="YlGnBu", vmin=0.0, vmax=1.0, aspect="auto")
    overlap_ax.set_xticks(np.arange(len(METRIC_ORDER)))
    overlap_ax.set_xticklabels([METRIC_DISPLAY[name] for name in METRIC_ORDER], rotation=15, fontsize=7)
    overlap_ax.set_yticks(np.arange(len(METRIC_ORDER)))
    overlap_ax.set_yticklabels([METRIC_DISPLAY[name] for name in METRIC_ORDER], fontsize=7)
    overlap_ax.set_title("set overlap (Jaccard)", fontsize=9)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            overlap_count = int(
                overlap_df[
                    (overlap_df["metric_a"] == METRIC_ORDER[i]) & (overlap_df["metric_b"] == METRIC_ORDER[j])
                ]["overlap_count"].iloc[0]
            )
            overlap_ax.text(j, i, f"{values[i, j]:.2f}\n{overlap_count}", ha="center", va="center", fontsize=7)
    ax.figure.colorbar(im, ax=overlap_ax, fraction=0.08, pad=0.03)
    ax.text(0.79, 0.12, "cell text:\nJaccard\ncount", transform=ax.transAxes, fontsize=7.5, va="bottom")
    ax.text(
        0.02,
        0.97,
        "The non-dominated sets remain large for all three metrics. The completion-aware and trap-aware sets overlap strongly, which is why the trap proxy sharpens the story without creating a new leading thermodynamic branch.",
        transform=ax.transAxes,
        va="top",
        fontsize=7.8,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.82"},
    )


def draw_panel_e(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.add_patch(
        patches.FancyBboxPatch((0.04, 0.10), 0.40, 0.80, boxstyle="round,pad=0.02", facecolor="#e5f5e0", edgecolor="0.80")
    )
    ax.add_patch(
        patches.FancyBboxPatch((0.56, 0.10), 0.40, 0.80, boxstyle="round,pad=0.02", facecolor="#fee0d2", edgecolor="0.80")
    )
    ax.text(0.24, 0.87, "Included now", fontsize=10, fontweight="bold", ha="center")
    ax.text(0.76, 0.87, "Missing now", fontsize=10, fontweight="bold", ha="center")

    for index, (title, description) in enumerate(BOOKKEEPING_INCLUDED):
        y = 0.75 - index * 0.19
        ax.add_patch(
            patches.FancyBboxPatch((0.08, y - 0.08), 0.32, 0.12, boxstyle="round,pad=0.01", facecolor="white", edgecolor="0.82")
        )
        ax.text(0.24, y, title, fontsize=8.5, fontweight="bold", ha="center", va="center")
        ax.text(0.24, y - 0.055, description, fontsize=7.3, ha="center", va="center", wrap=True)

    for index, (title, description) in enumerate(BOOKKEEPING_MISSING):
        y = 0.77 - index * 0.12
        ax.add_patch(
            patches.FancyBboxPatch((0.60, y - 0.05), 0.32, 0.08, boxstyle="round,pad=0.01", facecolor="white", edgecolor="0.82")
        )
        ax.text(0.76, y + 0.012, title, fontsize=8.1, fontweight="bold", ha="center", va="center")
        ax.text(0.76, y - 0.020, description, fontsize=6.9, ha="center", va="center", wrap=True)

    ax.annotate("", xy=(0.56, 0.50), xytext=(0.44, 0.50), arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "0.35"})
    ax.text(0.50, 0.54, "closure gap", fontsize=8, ha="center")


def draw_panel_f(ax: plt.Axes, robustness: pd.DataFrame, metric_table: pd.DataFrame) -> None:
    ax.set_axis_off()
    invariant_count = int((robustness["classification"] == "invariant").sum())
    shifted_count = int((robustness["classification"] == "shifted_but_principle_consistent").sum())
    scope_count = int((robustness["classification"] == "outside_current_bookkeeping").sum())
    completion_row = metric_table.loc[metric_table["metric_name"] == "eta_completion_drag"].iloc[0]
    trap_row = metric_table.loc[metric_table["metric_name"] == "eta_trap_drag"].iloc[0]

    sections = [
        (
            0.03,
            0.60,
            0.28,
            0.29,
            "#e5f5e0",
            "Strengthened now",
            [
                f"{invariant_count} conclusions are invariant across the metric family",
                "The ridge stays on the same narrow `Pi_f` strip",
                "The metric upgrade therefore strengthens robustness",
            ],
        ),
        (
            0.36,
            0.60,
            0.28,
            0.29,
            "#fff7bc",
            "Shifted, not contradicted",
            [
                f"{shifted_count} conclusions refine branch preference",
                "The winner shifts from the moderate-flow branch to the high-flow branch",
                "This is a scoped reordering, not a collapse of the ridge",
            ],
        ),
        (
            0.69,
            0.60,
            0.28,
            0.29,
            "#fee0d2",
            "Still outside closure",
            [
                f"{scope_count} conclusions remain explicit scope limits",
                "Drag-centered bookkeeping is not full thermodynamic closure",
                "A final thermodynamic winner is still unresolved under missing channels",
            ],
        ),
    ]
    for x0, y0, width, height, color, title, bullets in sections:
        ax.add_patch(
            patches.FancyBboxPatch((x0, y0), width, height, boxstyle="round,pad=0.02", facecolor=color, edgecolor="0.82")
        )
        ax.text(x0 + 0.02, y0 + height - 0.04, title, fontsize=9.2, fontweight="bold", va="top")
        for index, bullet in enumerate(bullets):
            ax.text(x0 + 0.02, y0 + height - 0.10 - index * 0.07, bullet, fontsize=7.9, va="top")

    ax.add_patch(
        patches.FancyBboxPatch((0.03, 0.10), 0.94, 0.37, boxstyle="round,pad=0.02", facecolor="#f7f7f7", edgecolor="0.82")
    )
    ax.text(0.05, 0.43, "Compact scope note", fontsize=9.2, fontweight="bold", va="top")
    ax.text(
        0.05,
        0.33,
        f"`eta_completion_drag` and `eta_trap_drag` share the same winner and overlap strongly at top-20 depth (`{int(completion_row['top20_overlap_with_speed'])}` and `{int(trap_row['top20_overlap_with_speed'])}` speed-front overlaps, with trap-aware keeping the same winner), which strengthens the metric-family result. But the bookkeeping remains drag-centered, so this is a robustness upgrade in scope rather than full thermodynamic closure.",
        fontsize=8.0,
        va="top",
        wrap=True,
    )
    ax.text(
        0.05,
        0.18,
        "Do not read this figure as a claim about total entropy production, full energetic efficiency, or a branch winner stable to propulsion, controller, memory, information, and post-commit completion costs.",
        fontsize=8.0,
        va="top",
        wrap=True,
    )


def build_figure(inputs: dict[str, pd.DataFrame]) -> None:
    branch_counts = build_branch_count_table(inputs["summary"])
    overlap_df = build_nd_overlap_table(inputs["summary"])

    fig, axes = plt.subplots(2, 3, figsize=(17, 10.6))
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.08, top=0.88, wspace=0.34, hspace=0.40)
    axes = axes.flatten()

    draw_panel_a(axes[0], inputs["summary"])
    draw_panel_b(axes[1], branch_counts)
    draw_panel_c(axes[2], inputs["canonical_ranks"])
    draw_panel_d(axes[3], inputs["metric_table"], overlap_df)
    draw_panel_e(axes[4])
    draw_panel_f(axes[5], inputs["robustness"], inputs["metric_table"])

    for ax, panel_letter in zip(axes, ["A", "B", "C", "D", "E", "F"]):
        annotate_panel(ax, panel_letter)
        ax.set_title(PANEL_TITLES[panel_letter], fontsize=12)

    fig.suptitle("Extended Data Figure 6. Thermodynamic-Upgrade Detail and Bookkeeping Limits", fontsize=17, fontweight="bold")
    fig.text(
        0.5,
        0.93,
        "Detailed support for the main-text thermodynamic qualifier. The tested metric family strengthens ridge robustness and shows a branch-preference shift, while the bookkeeping limits remain explicit and rule out any claim of full thermodynamic closure.",
        ha="center",
        fontsize=10,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_manifest(inputs: dict[str, pd.DataFrame]) -> None:
    branch_counts = build_branch_count_table(inputs["summary"])
    overlap_df = build_nd_overlap_table(inputs["summary"])
    counts = inputs["robustness"]["classification"].value_counts().to_dict()
    completion_row = inputs["metric_table"].loc[inputs["metric_table"]["metric_name"] == "eta_completion_drag"].iloc[0]
    trap_row = inputs["metric_table"].loc[inputs["metric_table"]["metric_name"] == "eta_trap_drag"].iloc[0]
    speed_rank = int(
        inputs["canonical_ranks"].set_index("canonical_label").loc["OP_SPEED_TIP", "eta_completion_drag_rank"]
    )
    efficiency_rank = int(
        inputs["canonical_ranks"].set_index("canonical_label").loc["OP_EFFICIENCY_TIP", "eta_sigma_rank"]
    )
    lines = [
        "# Extended Data Figure 6 Panel Manifest",
        "",
        "## Scope",
        "",
        "This note documents the panel logic for Extended Data Figure 6, which gives the detailed metric-family comparison and bookkeeping boundaries behind the main-text thermodynamic qualifier.",
        "",
        "Primary data sources:",
        "",
        f"- [extended_data_plan.md](file://{PROJECT_ROOT / 'docs' / 'extended_data_plan.md'})",
        f"- [thermodynamic_bookkeeping.md](file://{PROJECT_ROOT / 'docs' / 'thermodynamic_bookkeeping.md'})",
        f"- [efficiency_metric_upgrade.md](file://{PROJECT_ROOT / 'docs' / 'efficiency_metric_upgrade.md'})",
        f"- [metric_robustness_report.md](file://{PROJECT_ROOT / 'docs' / 'metric_robustness_report.md'})",
        f"- [thermodynamic_results_summary_v2.md](file://{PROJECT_ROOT / 'docs' / 'thermodynamic_results_summary_v2.md'})",
        f"- [efficiency_metric_comparison.csv](file://{EFFICIENCY_TABLE_PATH})",
        f"- [metric_robustness_table.csv](file://{ROBUSTNESS_TABLE_PATH})",
        f"- [metric_robustness_map.png](file://{ROBUSTNESS_FIGURE_PATH})",
        f"- [canonical_operating_points.csv](file://{PROJECT_ROOT / 'outputs' / 'tables' / 'canonical_operating_points.csv'})",
        f"- [ED Figure 6 PNG](file://{PNG_PATH})",
        f"- [ED Figure 6 SVG](file://{SVG_PATH})",
        "",
        "## Figure-Level Message",
        "",
        "- this figure exists to support the main-text thermodynamic qualifier with the full current metric family rather than a single screening metric",
        "- the central message is ridge survival plus branch-preference shift under the stronger completion-aware metrics",
        "- the bookkeeping remains drag-centered, so the figure strengthens robustness without implying full thermodynamic closure",
        "- bookkeeping limits remain visible and compact rather than hidden in footnotes",
        "",
        "## Panel Logic",
        "",
        "### Panel A",
        "",
        "- title: `Metric-family ridge comparison: eta_sigma, eta_completion_drag, eta_trap_drag`",
        "- purpose: overlay the three non-dominated ridge sets and their winners to show ridge survival under metric choice",
        "- quantitative note: non-dominated counts are `18`, `18`, and `20` for `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag`",
        "",
        "### Panel B",
        "",
        "- title: `Branch-preference reordering across metrics`",
        "- purpose: show the top-tier concentration shift from the moderate-flow ridge branch to the high-flow branch",
        f"- quantitative note: top-10 counts move from `{int(branch_counts.loc[branch_counts['metric_name'] == 'eta_sigma', 'moderate_flow_efficiency_branch'].iloc[0])}` moderate-flow points under `eta_sigma` to `{int(branch_counts.loc[branch_counts['metric_name'] == 'eta_completion_drag', 'high_flow_speed_branch'].iloc[0])}` high-flow points under `eta_completion_drag`",
        "",
        "### Panel C",
        "",
        "- title: `Canonical-point rank comparison across metrics`",
        "- purpose: show which canonical representatives move up or down when the metric numerator is upgraded",
        f"- quantitative note: the efficiency tip is rank `{efficiency_rank}` under `eta_sigma`, while the speed tip is rank `{speed_rank}` under `eta_completion_drag`",
        "",
        "### Panel D",
        "",
        "- title: `Non-dominated-set comparison across the metric family`",
        "- purpose: compare set size and pairwise overlap for the current competitive ridge family",
        f"- quantitative note: the completion-aware and trap-aware sets share Jaccard `{overlap_df[(overlap_df['metric_a'] == 'eta_completion_drag') & (overlap_df['metric_b'] == 'eta_trap_drag')]['jaccard_index'].iloc[0]:.2f}` with overlap count `{int(overlap_df[(overlap_df['metric_a'] == 'eta_completion_drag') & (overlap_df['metric_b'] == 'eta_trap_drag')]['overlap_count'].iloc[0])}`",
        "",
        "### Panel E",
        "",
        "- title: `Compact bookkeeping diagram showing what is included versus missing`",
        "- purpose: show the current bookkeeping boundary at a glance",
        "- quantitative note: explicit current bookkeeping contains one drag-centered cost channel plus the trap proxy refinement, while the remaining active, controller, memory, information, and completion channels stay outside the denominator",
        "",
        "### Panel F",
        "",
        "- title: `Explicit closure-limit panel summarizing which energetic or informational channels remain outside current bookkeeping`",
        "- purpose: state clearly why the metric upgrade improves robustness but does not produce full closure",
        f"- quantitative note: robustness-table counts are invariant `{counts.get('invariant', 0)}`, shifted-but-principle-consistent `{counts.get('shifted_but_principle_consistent', 0)}`, and outside-current-bookkeeping `{counts.get('outside_current_bookkeeping', 0)}`",
        "",
        "## Supported Now",
        "",
        "- ridge survival is robust across the current metric family",
        "- branch preference shifts from the moderate-flow ridge family to the high-flow fast-completion family under the stronger completion-aware metrics",
        f"- the trap-aware proxy keeps the same winner as `eta_completion_drag` and preserves strong top-20 agreement (`{int(completion_row['top20_overlap_with_speed'])}` and `{int(trap_row['top20_overlap_with_speed'])}` speed-front overlaps remain secondary to the same branch winner)",
        "",
        "## Not Supported Now",
        "",
        "- total entropy production",
        "- full energetic efficiency",
        "- a branch winner guaranteed to remain stable after missing cost channels are added",
        "- full closure of active, controller, memory, information, and post-commit completion costs",
        "",
        "## Bottom Line",
        "",
        "Extended Data Figure 6 is the detailed support layer behind the thermodynamic qualifier: the productive ridge survives the tested metric family, the preferred branch along that ridge shifts under the stronger completion-aware metrics, and the current bookkeeping remains explicitly incomplete rather than thermodynamically closed.",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Figure 6: thermodynamic-upgrade detail and bookkeeping limits.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
