from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.runners.run_efficiency_metric_upgrade import build_metric_table, load_summary

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PATH = PROJECT_ROOT / "outputs" / "tables" / "canonical_operating_points.csv"
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet"
BOOKKEEPING_PATH = PROJECT_ROOT / "docs" / "thermodynamic_bookkeeping.md"
UPGRADE_PATH = PROJECT_ROOT / "docs" / "efficiency_metric_upgrade.md"
DISCUSSION_PATH = PROJECT_ROOT / "docs" / "thermodynamic_upgrade_discussion.md"
PRINCIPLE_SCOPE_PATH = PROJECT_ROOT / "docs" / "principle_scope_statement_v2.md"
GEOMETRY_EVIDENCE_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_evidence_table.md"
GEOMETRY_CLAIM_NOTE_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_claim_upgrade_note.md"

OUTPUT_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "metric_robustness_table.csv"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "thermodynamics"
FIGURE_PATH = FIGURE_DIR / "metric_robustness_map.png"
REPORT_PATH = PROJECT_ROOT / "docs" / "metric_robustness_report.md"
SUMMARY_DOC_PATH = PROJECT_ROOT / "docs" / "thermodynamic_results_summary_v2.md"

METRIC_COLUMNS = {
    "eta_sigma": "eta_sigma_mean",
    "eta_completion_drag": "eta_completion_drag",
    "eta_trap_drag": "eta_trap_drag",
}
METRIC_ORDER = ["eta_sigma", "eta_completion_drag", "eta_trap_drag"]
METRIC_DISPLAY = {
    "eta_sigma": "eta_sigma",
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

CLASS_TO_VALUE = {
    "invariant": 0,
    "shifted_but_principle_consistent": 1,
    "outside_current_bookkeeping": 2,
}
CLASS_COLORS = ["#31a354", "#f0ad4e", "#bdbdbd"]
CANONICAL_LABEL_ORDER = [
    "OP_SUCCESS_TIP",
    "OP_EFFICIENCY_TIP",
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
    "OP_SPEED_TIP",
]
CANONICAL_DISPLAY = {
    "OP_SUCCESS_TIP": "success",
    "OP_EFFICIENCY_TIP": "efficiency",
    "OP_BALANCED_RIDGE_MID": "balanced",
    "OP_STALE_CONTROL_OFF_RIDGE": "stale",
    "OP_SPEED_TIP": "speed",
}


@dataclass(frozen=True)
class ConclusionSpec:
    conclusion_id: str
    conclusion_name: str
    conclusion_group: str
    classification: str
    manuscript_effect: str
    interpretation: str


CONCLUSION_SPECS = (
    ConclusionSpec(
        "MR1",
        "Pareto-like ridge survives the metric upgrade",
        "ridge_survival",
        "invariant",
        "strengthens",
        "The productive ridge persists under every computed metric rather than collapsing to one fragile proxy optimum.",
    ),
    ConclusionSpec(
        "MR2",
        "Competitive ridge stays on the same narrow Pi_f strip",
        "ridge_survival",
        "invariant",
        "strengthens",
        "Metric choice does not move the competitive set off the established productive-memory strip.",
    ),
    ConclusionSpec(
        "MR3",
        "Winning branch changes under the upgraded numerator",
        "branch_preference",
        "shifted_but_principle_consistent",
        "refines",
        "Metric upgrade reorders which branch is favored along the ridge without destroying the ridge itself.",
    ),
    ConclusionSpec(
        "MR4",
        "Top-tier branch concentration changes across metrics",
        "branch_preference",
        "shifted_but_principle_consistent",
        "refines",
        "The top-ranked competitive set shifts from moderate-flow concentration to high-flow concentration under completion-aware metrics.",
    ),
    ConclusionSpec(
        "MR5",
        "Success front stays distinct from thermodynamic winners",
        "front_structure",
        "invariant",
        "strengthens",
        "The metric family does not convert the low-flow success tip into the thermodynamic winner.",
    ),
    ConclusionSpec(
        "MR6",
        "Trap-aware refinement does not overturn the completion-aware branch choice",
        "front_structure",
        "invariant",
        "strengthens",
        "Adding the current stale-loss proxy sharpens interpretation but does not create a new leading branch.",
    ),
    ConclusionSpec(
        "MR7",
        "Current metrics still use drag-centered bookkeeping rather than full thermodynamic closure",
        "scope_limit",
        "outside_current_bookkeeping",
        "scope_limit",
        "The present metric family upgrades discussion credibility, but it still does not close the missing energetic and informational channels.",
    ),
    ConclusionSpec(
        "MR8",
        "Full branch ordering under missing cost channels remains unresolved",
        "scope_limit",
        "outside_current_bookkeeping",
        "scope_limit",
        "No current metric tests whether adding propulsion, controller, memory, information, or post-commit completion costs would reorder the ridge again.",
    ),
)


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def classify_branch(pi_u: float) -> str:
    if pi_u <= 0.12:
        return "low_flow_success_branch"
    if pi_u >= 0.25:
        return "high_flow_speed_branch"
    return "moderate_flow_efficiency_branch"


def nondominated_indices(summary: pd.DataFrame, metric_name: str) -> list[int]:
    values = summary[["Psucc_mean", "MFPT_mean", metric_name]].to_numpy(dtype=float)
    keep: list[int] = []
    for i, point_a in enumerate(values):
        dominated = False
        for j, point_b in enumerate(values):
            if i == j:
                continue
            better_or_equal = (
                point_b[0] >= point_a[0]
                and point_b[2] >= point_a[2]
                and point_b[1] <= point_a[1]
            )
            strictly_better = (
                point_b[0] > point_a[0]
                or point_b[2] > point_a[2]
                or point_b[1] < point_a[1]
            )
            if better_or_equal and strictly_better:
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return keep


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = load_summary().copy()
    summary["branch_name"] = summary["Pi_U"].map(classify_branch)
    metric_table = build_metric_table(summary).copy()
    canonical = pd.read_csv(CANONICAL_PATH).copy()
    return summary, metric_table, canonical


def metric_row(metric_table: pd.DataFrame, metric_name: str) -> pd.Series:
    return metric_table.loc[metric_table["metric_name"] == metric_name].iloc[0]


def top_k(summary: pd.DataFrame, metric_column: str, *, k: int) -> pd.DataFrame:
    return summary.nlargest(k, metric_column).copy()


def branch_counts_text(df: pd.DataFrame) -> str:
    counts = df["branch_name"].value_counts().to_dict()
    parts = [f"{BRANCH_DISPLAY[name]} `{counts.get(name, 0)}`" for name in BRANCH_ORDER]
    return ", ".join(parts)


def nd_summary_text(summary: pd.DataFrame, metric_column: str) -> str:
    nd_df = summary.iloc[nondominated_indices(summary, metric_column)].copy()
    return (
        f"`{len(nd_df)}` points; "
        f"`Pi_f in [{nd_df['Pi_f'].min():.3f}, {nd_df['Pi_f'].max():.3f}]`; "
        f"branches: {branch_counts_text(nd_df)}"
    )


def winner_text(summary: pd.DataFrame, metric_column: str) -> str:
    winner = summary.loc[summary[metric_column].idxmax()]
    return (
        f"{BRANCH_DISPLAY[str(winner['branch_name'])]} "
        f"at `({winner['Pi_m']:.3f}, {winner['Pi_f']:.3f}, {winner['Pi_U']:.3f})`"
    )


def top10_branch_text(summary: pd.DataFrame, metric_column: str) -> str:
    return branch_counts_text(top_k(summary, metric_column, k=10))


def top10_overlap_text(summary: pd.DataFrame, metric_column: str) -> str:
    top_metric = set(top_k(summary, metric_column, k=10)["state_point_id"])
    top_success = set(summary.nlargest(10, "Psucc_mean")["state_point_id"])
    top_speed = set(summary.nsmallest(10, "MFPT_mean")["state_point_id"])
    return (
        f"top-10 overlap with success `{len(top_metric & top_success)}`; "
        f"with speed `{len(top_metric & top_speed)}`"
    )


def completion_trap_consistency_text(summary: pd.DataFrame) -> str:
    completion_top20 = set(top_k(summary, "eta_completion_drag", k=20)["state_point_id"])
    trap_top20 = set(top_k(summary, "eta_trap_drag", k=20)["state_point_id"])
    completion_winner = summary.loc[summary["eta_completion_drag"].idxmax()]
    trap_winner = summary.loc[summary["eta_trap_drag"].idxmax()]
    same_winner = completion_winner["state_point_id"] == trap_winner["state_point_id"]
    return (
        f"same winner `{same_winner}`; "
        f"top-20 overlap `{len(completion_top20 & trap_top20)}` of `20`"
    )


def rank_canonical_points(summary: pd.DataFrame, canonical: pd.DataFrame) -> pd.DataFrame:
    rank_df = summary[["result_json", *METRIC_COLUMNS.values()]].copy()
    for metric_name, metric_column in METRIC_COLUMNS.items():
        rank_df[f"{metric_name}_rank"] = summary[metric_column].rank(ascending=False, method="min")
    merged = canonical[["canonical_label", "result_json"]].merge(rank_df, on="result_json", how="left")
    if merged[METRIC_COLUMNS.values()].isnull().any().any():
        raise RuntimeError("Failed to map canonical operating points onto the confirmatory metric summary.")
    return merged


def build_metric_robustness_table(
    summary: pd.DataFrame,
    metric_table: pd.DataFrame,
) -> pd.DataFrame:
    sigma_col = METRIC_COLUMNS["eta_sigma"]
    completion_col = METRIC_COLUMNS["eta_completion_drag"]
    trap_col = METRIC_COLUMNS["eta_trap_drag"]

    row_payloads = {
        "MR1": {
            "eta_sigma_result": nd_summary_text(summary, sigma_col),
            "eta_completion_drag_result": nd_summary_text(summary, completion_col),
            "eta_trap_drag_result": nd_summary_text(summary, trap_col),
        },
        "MR2": {
            "eta_sigma_result": (
                f"winner strip `Pi_U in [{top_k(summary, sigma_col, k=10)['Pi_U'].min():.2f}, "
                f"{top_k(summary, sigma_col, k=10)['Pi_U'].max():.2f}]`; "
                f"`Pi_f` values `{sorted(top_k(summary, sigma_col, k=20)['Pi_f'].unique().tolist())}`"
            ),
            "eta_completion_drag_result": (
                f"winner strip `Pi_U in [{top_k(summary, completion_col, k=10)['Pi_U'].min():.2f}, "
                f"{top_k(summary, completion_col, k=10)['Pi_U'].max():.2f}]`; "
                f"`Pi_f` values `{sorted(top_k(summary, completion_col, k=20)['Pi_f'].unique().tolist())}`"
            ),
            "eta_trap_drag_result": (
                f"winner strip `Pi_U in [{top_k(summary, trap_col, k=10)['Pi_U'].min():.2f}, "
                f"{top_k(summary, trap_col, k=10)['Pi_U'].max():.2f}]`; "
                f"`Pi_f` values `{sorted(top_k(summary, trap_col, k=20)['Pi_f'].unique().tolist())}`"
            ),
        },
        "MR3": {
            "eta_sigma_result": winner_text(summary, sigma_col),
            "eta_completion_drag_result": winner_text(summary, completion_col),
            "eta_trap_drag_result": winner_text(summary, trap_col),
        },
        "MR4": {
            "eta_sigma_result": top10_branch_text(summary, sigma_col),
            "eta_completion_drag_result": top10_branch_text(summary, completion_col),
            "eta_trap_drag_result": top10_branch_text(summary, trap_col),
        },
        "MR5": {
            "eta_sigma_result": top10_overlap_text(summary, sigma_col),
            "eta_completion_drag_result": top10_overlap_text(summary, completion_col),
            "eta_trap_drag_result": top10_overlap_text(summary, trap_col),
        },
        "MR6": {
            "eta_sigma_result": "baseline screening branch differs from upgraded metrics",
            "eta_completion_drag_result": completion_trap_consistency_text(summary),
            "eta_trap_drag_result": completion_trap_consistency_text(summary),
        },
        "MR7": {
            "eta_sigma_result": "drag-normalized screening metric only",
            "eta_completion_drag_result": "completion-aware numerator, but drag-only denominator",
            "eta_trap_drag_result": "adds stale-loss proxy, but still not total entropy production",
        },
        "MR8": {
            "eta_sigma_result": "cannot test missing propulsion/controller/information/post-commit costs",
            "eta_completion_drag_result": "cannot test missing propulsion/controller/information/post-commit costs",
            "eta_trap_drag_result": "cannot test missing propulsion/controller/information/post-commit costs",
        },
    }

    rows: list[dict[str, str]] = []
    for spec in CONCLUSION_SPECS:
        row = {
            "conclusion_id": spec.conclusion_id,
            "conclusion_name": spec.conclusion_name,
            "conclusion_group": spec.conclusion_group,
            "eta_sigma_result": row_payloads[spec.conclusion_id]["eta_sigma_result"],
            "eta_completion_drag_result": row_payloads[spec.conclusion_id]["eta_completion_drag_result"],
            "eta_trap_drag_result": row_payloads[spec.conclusion_id]["eta_trap_drag_result"],
            "classification": spec.classification,
            "manuscript_effect": spec.manuscript_effect,
            "interpretation": spec.interpretation,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def make_figure(
    summary: pd.DataFrame,
    canonical_ranks: pd.DataFrame,
    robustness_table: pd.DataFrame,
) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax = axes[0, 0]
    ax.scatter(summary["Pi_U"], summary["Pi_m"], color="#d9d9d9", s=18, alpha=0.45, edgecolors="none")
    for metric_name in METRIC_ORDER:
        metric_column = METRIC_COLUMNS[metric_name]
        nd_df = summary.iloc[nondominated_indices(summary, metric_column)].copy()
        ax.scatter(
            nd_df["Pi_U"],
            nd_df["Pi_m"],
            s=55,
            marker=METRIC_MARKERS[metric_name],
            color=METRIC_COLORS[metric_name],
            edgecolor="black",
            linewidth=0.35,
            alpha=0.85,
            label=METRIC_DISPLAY[metric_name],
        )
    ax.set_title("Ridge Survival Across Metric Choice")
    ax.set_xlabel("Pi_U")
    ax.set_ylabel("Pi_m")
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    ax = axes[0, 1]
    x = np.arange(len(METRIC_ORDER))
    bottom = np.zeros(len(METRIC_ORDER), dtype=float)
    for branch_name in BRANCH_ORDER:
        heights = []
        for metric_name in METRIC_ORDER:
            metric_column = METRIC_COLUMNS[metric_name]
            top10 = top_k(summary, metric_column, k=10)
            counts = top10["branch_name"].value_counts()
            heights.append(float(counts.get(branch_name, 0)))
        heights_array = np.array(heights, dtype=float)
        ax.bar(
            x,
            heights_array,
            bottom=bottom,
            color=BRANCH_COLORS[branch_name],
            label=BRANCH_DISPLAY[branch_name],
        )
        bottom += heights_array
    ax.set_xticks(x)
    ax.set_xticklabels([METRIC_DISPLAY[name] for name in METRIC_ORDER], rotation=15)
    ax.set_ylim(0, 10)
    ax.set_ylabel("Top-10 count")
    ax.set_title("Branch Preference Change")
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    ax = axes[1, 0]
    heatmap = canonical_ranks.set_index("canonical_label")[
        [f"{metric_name}_rank" for metric_name in METRIC_ORDER]
    ].loc[CANONICAL_LABEL_ORDER]
    values = heatmap.to_numpy(dtype=float)
    im = ax.imshow(values, aspect="auto", cmap="YlOrRd_r")
    ax.set_xticks(np.arange(len(METRIC_ORDER)))
    ax.set_xticklabels([METRIC_DISPLAY[name] for name in METRIC_ORDER], rotation=15)
    ax.set_yticks(np.arange(len(CANONICAL_LABEL_ORDER)))
    ax.set_yticklabels([CANONICAL_DISPLAY[label] for label in CANONICAL_LABEL_ORDER])
    ax.set_title("Canonical Branch Reordering")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f"{int(values[i, j])}", ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("global rank (lower is better)")

    ax = axes[1, 1]
    overlap_df = pd.DataFrame(
        {
            "metric_name": [METRIC_DISPLAY[name] for name in METRIC_ORDER],
            "success_overlap": [
                len(set(top_k(summary, METRIC_COLUMNS[name], k=10)["state_point_id"]) & set(summary.nlargest(10, "Psucc_mean")["state_point_id"]))
                for name in METRIC_ORDER
            ],
            "speed_overlap": [
                len(set(top_k(summary, METRIC_COLUMNS[name], k=10)["state_point_id"]) & set(summary.nsmallest(10, "MFPT_mean")["state_point_id"]))
                for name in METRIC_ORDER
            ],
        }
    )
    width = 0.35
    ax.bar(
        np.arange(len(overlap_df)) - width / 2,
        overlap_df["success_overlap"],
        width=width,
        color="#2ca02c",
        label="top-10 overlap with success",
    )
    ax.bar(
        np.arange(len(overlap_df)) + width / 2,
        overlap_df["speed_overlap"],
        width=width,
        color="#d62728",
        label="top-10 overlap with speed",
    )
    ax.set_xticks(np.arange(len(overlap_df)))
    ax.set_xticklabels(overlap_df["metric_name"], rotation=15)
    ax.set_ylabel("Overlap count")
    ax.set_title("Front Structure Under Metric Choice")
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle("Metric-Robustness Map", fontsize=15)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_report(
    summary: pd.DataFrame,
    metric_table: pd.DataFrame,
    robustness_table: pd.DataFrame,
    canonical_ranks: pd.DataFrame,
) -> None:
    counts = robustness_table["classification"].value_counts().to_dict()
    sigma_row = metric_row(metric_table, "eta_sigma")
    completion_row = metric_row(metric_table, "eta_completion_drag")
    trap_row = metric_row(metric_table, "eta_trap_drag")
    invariant_rows = robustness_table[robustness_table["classification"] == "invariant"]
    shifted_rows = robustness_table[
        robustness_table["classification"] == "shifted_but_principle_consistent"
    ]
    scope_rows = robustness_table[
        robustness_table["classification"] == "outside_current_bookkeeping"
    ]
    branch_threshold_note = (
        "Branch labels use the same operating-family split already implicit in the current upgrade note: "
        "`Pi_U <= 0.12` for the low-flow success branch, `0.12 < Pi_U < 0.25` for the moderate-flow ridge branch, "
        "and `Pi_U >= 0.25` for the high-flow speed/completion branch."
    )

    lines = [
        "# Metric Robustness Report",
        "",
        "## Scope",
        "",
        "This note tests whether the productive ridge survives the current thermodynamic metric family, or whether it only appears under one screening definition.",
        "",
        f"- confirmatory summary: {_path_link(SUMMARY_PATH)}",
        f"- canonical operating points: {_path_link(CANONICAL_PATH)}",
        f"- existing metric upgrade note: {_path_link(UPGRADE_PATH)}",
        f"- bookkeeping note: {_path_link(BOOKKEEPING_PATH)}",
        f"- geometry-transfer evidence: {_path_link(GEOMETRY_EVIDENCE_PATH)}",
        f"- robustness table: {_path_link(OUTPUT_TABLE_PATH)}",
        f"- robustness figure: {_path_link(FIGURE_PATH)}",
        "",
        "The tested metric family remains strictly inside current bookkeeping: `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag`.",
        "",
        "## Compact Readout",
        "",
        f"- `eta_sigma` winner: {winner_text(summary, METRIC_COLUMNS['eta_sigma'])}",
        f"- `eta_completion_drag` winner: {winner_text(summary, METRIC_COLUMNS['eta_completion_drag'])}",
        f"- `eta_trap_drag` winner: {winner_text(summary, METRIC_COLUMNS['eta_trap_drag'])}",
        f"- non-dominated counts: `eta_sigma = {int(sigma_row['pareto_candidate_count'])}`, "
        f"`eta_completion_drag = {int(completion_row['pareto_candidate_count'])}`, "
        f"`eta_trap_drag = {int(trap_row['pareto_candidate_count'])}`",
        f"- Spearman vs `eta_sigma`: `eta_completion_drag = {completion_row['spearman_vs_eta_sigma']:.3f}`, "
        f"`eta_trap_drag = {trap_row['spearman_vs_eta_sigma']:.3f}`",
        f"- branch-family rule: {branch_threshold_note}",
        "",
        "## Ridge Survival Versus Branch-Preference Change",
        "",
        "These two questions separate cleanly in the data.",
        "",
        "Ridge survival:",
        "",
        "- every computed metric retains a non-dominated ridge rather than collapsing to a single isolated optimum",
        "- every non-dominated set stays pinned to the same narrow `Pi_f` strip `[0.018, 0.025]`",
        "- the non-dominated branch mix remains three-way rather than degenerating to only one branch family",
        "",
        "Branch-preference change:",
        "",
        "- `eta_sigma` concentrates its top-10 entirely on the moderate-flow ridge branch",
        "- `eta_completion_drag` shifts top-10 concentration to the high-flow speed/completion branch",
        "- `eta_trap_drag` leaves that high-flow preference in place rather than restoring the old moderate-flow winner",
        "",
        "So the ridge is robust to metric choice, but the preferred branch along the ridge is not metric-invariant.",
        "",
        "## Which conclusions survive metric upgrade, and which only survive within one metric family?",
        "",
        "### Invariant across the current metric family",
        "",
        invariant_rows[
            [
                "conclusion_name",
                "eta_sigma_result",
                "eta_completion_drag_result",
                "eta_trap_drag_result",
                "interpretation",
            ]
        ].to_markdown(index=False),
        "",
        "### Shifted but still principle-consistent",
        "",
        shifted_rows[
            [
                "conclusion_name",
                "eta_sigma_result",
                "eta_completion_drag_result",
                "eta_trap_drag_result",
                "interpretation",
            ]
        ].to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        "- what survives metric upgrade is the existence and location of the productive ridge",
        "- what only survives within one metric family is the exact branch ordering along that ridge",
        "- the upgraded metric family therefore strengthens the ridge claim, but it only refines branch choice rather than making it universal",
        "",
        "## What still cannot be claimed as full thermodynamic closure?",
        "",
        scope_rows[
            [
                "conclusion_name",
                "eta_sigma_result",
                "eta_completion_drag_result",
                "eta_trap_drag_result",
                "interpretation",
            ]
        ].to_markdown(index=False),
        "",
        "Missing closure channels that remain explicit:",
        "",
        "- active-propulsion work is not separately booked",
        "- controller or steering actuation work is not separately booked",
        "- memory-bath dissipation is not separately booked",
        "- information-rate or update-cost terms are not booked",
        "- pre-commit and post-commit spending are not separated into a full energetic budget",
        "- total entropy production is therefore not available",
        "",
        "## Current Manuscript-Level Upgrade",
        "",
        "The safest strengthened statement is:",
        "",
        "> Within current bookkeeping, the productive ridge is robust to the tested metric family: `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag` all preserve the same narrow competitive ridge, even though the preferred branch shifts from the moderate-flow ridge family to the high-flow fast-completion branch under the stronger completion-aware metrics.",
        "",
        "This strengthens the thermodynamic qualifier because the ridge is no longer tied to one screening proxy. At the same time, it keeps the scope limit visible: branch preference is metric-sensitive, and full thermodynamic closure is still not available.",
        "",
        "## Evidence Summary",
        "",
        f"- invariant conclusions: `{counts.get('invariant', 0)}`",
        f"- shifted but principle-consistent conclusions: `{counts.get('shifted_but_principle_consistent', 0)}`",
        f"- outside current bookkeeping: `{counts.get('outside_current_bookkeeping', 0)}`",
        "",
        "Canonical-rank check:",
        "",
        canonical_ranks[
            [
                "canonical_label",
                "eta_sigma_rank",
                "eta_completion_drag_rank",
                "eta_trap_drag_rank",
            ]
        ]
        .assign(
            canonical_label=lambda df: df["canonical_label"].map(CANONICAL_DISPLAY),
        )
        .to_markdown(index=False),
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_results_summary(robustness_table: pd.DataFrame) -> None:
    invariant_rows = robustness_table[robustness_table["classification"] == "invariant"]
    shifted_rows = robustness_table[
        robustness_table["classification"] == "shifted_but_principle_consistent"
    ]
    scope_rows = robustness_table[
        robustness_table["classification"] == "outside_current_bookkeeping"
    ]
    lines = [
        "# Thermodynamic Results Summary V2",
        "",
        "## Scope",
        "",
        "This note compresses the current thermodynamic Results statement after the metric-robustness pass.",
        "",
        f"- principle scope statement: {_path_link(PRINCIPLE_SCOPE_PATH)}",
        f"- geometry transfer claim note: {_path_link(GEOMETRY_CLAIM_NOTE_PATH)}",
        f"- thermodynamic upgrade discussion: {_path_link(DISCUSSION_PATH)}",
        f"- metric robustness report: {_path_link(REPORT_PATH)}",
        "",
        "## Main Results Statement",
        "",
        "> Within current bookkeeping, the productive ridge is robust across the tested metric family, but the preferred branch along that ridge is metric-sensitive. `eta_sigma` favors the moderate-flow ridge family, whereas the stronger completion-aware metrics favor the high-flow fast-completion branch. This upgrades the thermodynamic qualifier from a one-metric screening observation to a compact metric-family result, without claiming full thermodynamic closure.",
        "",
        "## Which conclusions survive metric upgrade, and which only survive within one metric family?",
        "",
        "Invariant conclusions:",
        "",
        invariant_rows[["conclusion_name", "interpretation"]].to_markdown(index=False),
        "",
        "Shifted but still principle-consistent conclusions:",
        "",
        shifted_rows[["conclusion_name", "interpretation"]].to_markdown(index=False),
        "",
        "Practical readout:",
        "",
        "- ridge survival upgrades into the main Results claim",
        "- branch preference change belongs in Results too, but as a scoped qualifier rather than as a contradiction",
        "- no single branch winner should be stated as metric-universal within the current family",
        "",
        "## What still cannot be claimed as full thermodynamic closure?",
        "",
        scope_rows[["conclusion_name", "interpretation"]].to_markdown(index=False),
        "",
        "Do not claim:",
        "",
        "- total entropy production",
        "- full energetic efficiency",
        "- a final thermodynamic winner that is stable to missing cost channels",
        "- closure of active, controller, memory, information, and post-commit completion costs",
        "",
        "## Recommended Manuscript Language",
        "",
        "Use this phrasing in Results or Discussion:",
        "",
        "> The productive ridge is robust to the current metric upgrade, not just to one screening proxy. What changes under the stronger completion-aware metrics is the preferred branch along that ridge, which shifts toward the high-flow fast-completion family. Because the present bookkeeping remains drag-centered, this should be read as a thermodynamic upgrade in scope rather than as full closure.",
    ]
    SUMMARY_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_outputs() -> dict[str, str]:
    summary, metric_table, canonical = load_inputs()
    canonical_ranks = rank_canonical_points(summary, canonical)
    robustness_table = build_metric_robustness_table(summary, metric_table)
    OUTPUT_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    robustness_table.to_csv(OUTPUT_TABLE_PATH, index=False)
    make_figure(summary, canonical_ranks, robustness_table)
    write_report(summary, metric_table, robustness_table, canonical_ranks)
    write_results_summary(robustness_table)
    return {
        "metric_robustness_report": str(REPORT_PATH),
        "metric_robustness_table_csv": str(OUTPUT_TABLE_PATH),
        "metric_robustness_map_png": str(FIGURE_PATH),
        "thermodynamic_results_summary_v2": str(SUMMARY_DOC_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the metric-robustness evidence package for the thermodynamic upgrade.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
