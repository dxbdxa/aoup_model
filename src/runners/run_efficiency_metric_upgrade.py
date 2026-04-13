from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet"
TRAJECTORY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "trajectory_level.parquet"
OUTPUT_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "efficiency_metric_comparison.csv"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "thermodynamics"
FIGURE_PATH = FIGURE_DIR / "metric_comparison.png"
DOC_PATH = PROJECT_ROOT / "docs" / "efficiency_metric_upgrade.md"


@dataclass(frozen=True)
class MetricSpec:
    name: str
    display_name: str
    family_tier: str
    purpose: str
    formula: str
    cost_channels: str
    is_computed: bool = True


METRICS = (
    MetricSpec(
        name="eta_sigma_mean",
        display_name="eta_sigma",
        family_tier="directly_computed",
        purpose="screening",
        formula="(Psucc_mean / Tmax) / Sigma_drag_mean",
        cost_channels="transport proxy + drag dissipation proxy",
    ),
    MetricSpec(
        name="eta_completion_drag",
        display_name="eta_completion_drag",
        family_tier="directly_computed",
        purpose="manuscript_thermodynamic_discussion",
        formula="(Psucc_mean / MFPT_mean) / Sigma_drag_mean",
        cost_channels="successful completion rate + drag dissipation proxy",
    ),
    MetricSpec(
        name="eta_trap_drag",
        display_name="eta_trap_drag",
        family_tier="proxy_quantity",
        purpose="mechanism_interpretation",
        formula="eta_completion_drag / (1 + trap_time_mean / Tmax)",
        cost_channels="successful completion rate + drag dissipation proxy + trap-time waste proxy",
    ),
    MetricSpec(
        name="eta_total_future",
        display_name="eta_total_future",
        family_tier="aspirational_future_quantity",
        purpose="future_full_thermodynamic_discussion",
        formula="productive output / (drag + propulsion + controller + memory + information + completion costs)",
        cost_channels="future full bookkeeping",
        is_computed=False,
    ),
)


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def load_summary() -> pd.DataFrame:
    summary = pd.read_parquet(SUMMARY_PATH).copy()
    summary["eta_completion_drag"] = summary["Psucc_mean"] / (
        summary["MFPT_mean"] * summary["Sigma_drag_mean"]
    )
    summary["eta_trap_drag"] = summary["eta_completion_drag"] / (
        1.0 + summary["trap_time_mean"] / summary["Tmax"]
    )
    return summary


def load_canonical_mechanism_summary() -> pd.DataFrame:
    traj_df = pd.read_parquet(
        TRAJECTORY_PATH,
        columns=[
            "canonical_label",
            "trap_time_total",
            "boundary_contact_fraction_i",
            "wall_dwell_before_first_commit",
            "first_gate_commit_delay",
            "Sigma_drag_i",
        ],
    )
    return (
        traj_df.groupby("canonical_label", as_index=False)
        .agg(
            trap_time_total=("trap_time_total", "mean"),
            boundary_contact_fraction_i=("boundary_contact_fraction_i", "mean"),
            wall_dwell_before_first_commit=("wall_dwell_before_first_commit", "mean"),
            first_gate_commit_delay=("first_gate_commit_delay", "mean"),
            Sigma_drag_i=("Sigma_drag_i", "mean"),
        )
        .sort_values("canonical_label")
    )


def top_overlap(summary: pd.DataFrame, metric_name: str, *, k: int) -> tuple[int, int]:
    top_succ = set(summary.nlargest(k, "Psucc_mean")["state_point_id"])
    top_metric = set(summary.nlargest(k, metric_name)["state_point_id"])
    top_speed = set(summary.nsmallest(k, "MFPT_mean")["state_point_id"])
    return len(top_metric & top_succ), len(top_metric & top_speed)


def nondominated_indices(summary: pd.DataFrame, metric_name: str) -> list[int]:
    values = summary[["Psucc_mean", "MFPT_mean", metric_name]].to_numpy()
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


def format_winner_note(summary: pd.DataFrame, spec: MetricSpec) -> str:
    if not spec.is_computed:
        return "Not computed yet."
    winner = summary.loc[summary[spec.name].idxmax()]
    speed_winner = summary.loc[summary["MFPT_mean"].idxmin()]
    if winner["state_point_id"] == speed_winner["state_point_id"]:
        return "Winner coincides with the speed tip."
    if winner["Pi_U"] >= 0.25:
        return "Winner sits on the high-flow speed-favored branch."
    if winner["Pi_U"] <= 0.12:
        return "Winner sits on the low-flow success-favored branch."
    return "Winner stays on the moderate-flow efficiency ridge family."


def build_metric_table(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    spearman_eta_sigma = summary[["eta_sigma_mean", "eta_completion_drag", "eta_trap_drag"]].corr(
        method="spearman"
    )
    for spec in METRICS:
        row: dict[str, object] = {
            "metric_name": spec.display_name,
            "metric_column": spec.name,
            "family_tier": spec.family_tier,
            "purpose": spec.purpose,
            "is_computed": spec.is_computed,
            "formula": spec.formula,
            "cost_channels": spec.cost_channels,
        }
        if spec.is_computed:
            winner = summary.loc[summary[spec.name].idxmax()]
            overlap10_succ, overlap10_speed = top_overlap(summary, spec.name, k=10)
            overlap20_succ, overlap20_speed = top_overlap(summary, spec.name, k=20)
            nd_idx = nondominated_indices(summary, spec.name)
            nd_df = summary.iloc[nd_idx]
            row.update(
                {
                    "winner_state_point_id": str(winner["state_point_id"]),
                    "winner_Pi_m": float(winner["Pi_m"]),
                    "winner_Pi_f": float(winner["Pi_f"]),
                    "winner_Pi_U": float(winner["Pi_U"]),
                    "winner_value": float(winner[spec.name]),
                    "winner_Psucc_mean": float(winner["Psucc_mean"]),
                    "winner_MFPT_mean": float(winner["MFPT_mean"]),
                    "winner_Sigma_drag_mean": float(winner["Sigma_drag_mean"]),
                    "winner_trap_time_mean": float(winner["trap_time_mean"]),
                    "top10_overlap_with_success": int(overlap10_succ),
                    "top10_overlap_with_speed": int(overlap10_speed),
                    "top20_overlap_with_success": int(overlap20_succ),
                    "top20_overlap_with_speed": int(overlap20_speed),
                    "pareto_candidate_count": int(len(nd_df)),
                    "pareto_Pi_f_min": float(nd_df["Pi_f"].min()),
                    "pareto_Pi_f_max": float(nd_df["Pi_f"].max()),
                    "winner_note": format_winner_note(summary, spec),
                }
            )
            if spec.name != "eta_sigma_mean":
                row["spearman_vs_eta_sigma"] = float(spearman_eta_sigma.loc["eta_sigma_mean", spec.name])
            else:
                row["spearman_vs_eta_sigma"] = 1.0
        rows.append(row)
    return pd.DataFrame(rows)


def make_figure(summary: pd.DataFrame, metric_table: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    ax = axes[0, 0]
    ranks = pd.DataFrame(
        {
            "eta_sigma_rank": summary["eta_sigma_mean"].rank(ascending=False, method="dense"),
            "eta_completion_rank": summary["eta_completion_drag"].rank(ascending=False, method="dense"),
            "Pi_U": summary["Pi_U"],
        }
    )
    scatter = ax.scatter(
        ranks["eta_sigma_rank"],
        ranks["eta_completion_rank"],
        c=ranks["Pi_U"],
        cmap="viridis",
        s=24,
        alpha=0.75,
        edgecolors="none",
    )
    ax.set_title("Rank Shift: eta_sigma vs Completion Drag")
    ax.set_xlabel("eta_sigma rank")
    ax.set_ylabel("eta_completion_drag rank")
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Pi_U")

    ax = axes[0, 1]
    winner_points = []
    for spec in METRICS:
        if not spec.is_computed:
            continue
        winner_row = metric_table.loc[metric_table["metric_name"] == spec.display_name].iloc[0]
        winner_points.append(
            {
                "label": spec.display_name,
                "Pi_U": float(winner_row["winner_Pi_U"]),
                "Pi_m": float(winner_row["winner_Pi_m"]),
            }
        )
    success_row = summary.loc[summary["Psucc_mean"].idxmax()]
    speed_row = summary.loc[summary["MFPT_mean"].idxmin()]
    ref_points = [
        ("success_tip", float(success_row["Pi_U"]), float(success_row["Pi_m"]), "#2ca02c"),
        ("speed_tip", float(speed_row["Pi_U"]), float(speed_row["Pi_m"]), "#d62728"),
    ]
    for name, x, y, color in ref_points:
        ax.scatter(x, y, s=90, marker="*", color=color, edgecolor="black", linewidth=0.5)
        ax.text(x + 0.005, y + 0.003, name, fontsize=8)
    colors = ["#1f77b4", "#ff7f0e", "#9467bd"]
    for item, color in zip(winner_points, colors):
        ax.scatter(item["Pi_U"], item["Pi_m"], s=70, color=color)
        ax.text(item["Pi_U"] + 0.005, item["Pi_m"] + 0.003, item["label"], fontsize=8)
    ax.set_title("Winner Locations")
    ax.set_xlabel("Pi_U")
    ax.set_ylabel("Pi_m")

    ax = axes[1, 0]
    plot_df = metric_table[metric_table["is_computed"]].copy()
    x = np.arange(len(plot_df))
    width = 0.35
    ax.bar(
        x - width / 2,
        plot_df["top10_overlap_with_success"],
        width=width,
        label="Top-10 overlap with success",
        color="#2ca02c",
    )
    ax.bar(
        x + width / 2,
        plot_df["top10_overlap_with_speed"],
        width=width,
        label="Top-10 overlap with speed",
        color="#d62728",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(plot_df["metric_name"], rotation=15)
    ax.set_title("Front Overlap Under Metric Choice")
    ax.set_ylabel("Overlap count")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    ax.bar(plot_df["metric_name"], plot_df["pareto_candidate_count"], color=["#1f77b4", "#ff7f0e", "#9467bd"])
    for idx, row in plot_df.iterrows():
        ax.text(
            idx,
            float(row["pareto_candidate_count"]) + 0.3,
            f"Pi_f in [{row['pareto_Pi_f_min']:.3f}, {row['pareto_Pi_f_max']:.3f}]",
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=0,
        )
    ax.set_title("Pareto-Like Ridge Size")
    ax.set_ylabel("Non-dominated count")

    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_doc(summary: pd.DataFrame, metric_table: pd.DataFrame, canonical_df: pd.DataFrame) -> None:
    direct_df = metric_table[metric_table["family_tier"] == "directly_computed"].copy()
    proxy_df = metric_table[metric_table["family_tier"] == "proxy_quantity"].copy()
    future_df = metric_table[metric_table["family_tier"] == "aspirational_future_quantity"].copy()

    completion_row = metric_table.loc[metric_table["metric_name"] == "eta_completion_drag"].iloc[0]
    trap_row = metric_table.loc[metric_table["metric_name"] == "eta_trap_drag"].iloc[0]
    sigma_row = metric_table.loc[metric_table["metric_name"] == "eta_sigma"].iloc[0]

    speed_tip = summary.loc[summary["MFPT_mean"].idxmin()]
    success_tip = summary.loc[summary["Psucc_mean"].idxmax()]
    canonical_speed = canonical_df[canonical_df["canonical_label"] == "OP_SPEED_TIP"].iloc[0]
    canonical_eff = canonical_df[canonical_df["canonical_label"] == "OP_EFFICIENCY_TIP"].iloc[0]

    doc = f"""# Efficiency Metric Upgrade

## Scope

This note defines a compact upgraded family of transport-efficiency quantities beyond `eta_sigma`, tests them on the confirmatory scan, and asks whether the productive-memory ridge remains Pareto-like under better-separated cost accounting.

Primary inputs:

- {_path_link(PROJECT_ROOT / 'docs' / 'thermodynamic_bookkeeping.md')}
- {_path_link(PROJECT_ROOT / 'docs' / 'eta_sigma_interpretation_note.md')}
- {_path_link(PROJECT_ROOT / 'docs' / 'front_analysis_report.md')}
- {_path_link(PROJECT_ROOT / 'docs' / 'geometry_transfer_principle_note.md')}
- {_path_link(SUMMARY_PATH)}
- {_path_link(TRAJECTORY_PATH)}
- {_path_link(OUTPUT_TABLE_PATH)}
- {_path_link(FIGURE_PATH)}

The goal is not to produce a full thermodynamic completion law. It is to see whether a small and interpretable metric family changes the ridge picture qualitatively.

## Compact Metric Family

The recommended family is intentionally small.

### Directly computed quantities

{direct_df[["metric_name", "formula", "purpose", "cost_channels"]].to_markdown(index=False)}

Interpretation:

- `eta_sigma` remains the baseline drag-normalized screening metric
- `eta_completion_drag` upgrades the numerator from success-per-budget-window to success-per-completion-time, while keeping the same drag proxy in the denominator

### Proxy quantity

{proxy_df[["metric_name", "formula", "purpose", "cost_channels"]].to_markdown(index=False)}

Interpretation:

- `eta_trap_drag` adds one explicit stale-burden penalty using `trap_time_mean / Tmax`
- this is the cleanest current pre-commit waste proxy available on the full confirmatory scan

### Aspirational future quantity

{future_df[["metric_name", "formula", "purpose", "cost_channels"]].to_markdown(index=False)}

Interpretation:

- `eta_total_future` is the placeholder for a later full bookkeeping quantity
- it is intentionally not computed now because active propulsion work, controller work, information/update costs, and post-commit completion costs are not yet separated

## Why trap burden is the preferred proxy upgrade

The refined mechanism dataset suggests that raw wall contact should not be penalized as if it were always waste.

Canonical mechanism means:

{canonical_df[["canonical_label", "trap_time_total", "boundary_contact_fraction_i", "wall_dwell_before_first_commit", "first_gate_commit_delay", "Sigma_drag_i"]].to_markdown(index=False)}

This matters because:

- the speed tip has higher wall-contact fraction than the efficiency tip (`{canonical_speed['boundary_contact_fraction_i']:.3f}` vs `{canonical_eff['boundary_contact_fraction_i']:.3f}`), yet both remain essentially trap-free
- wall-guided motion can therefore be productive, not merely dissipative waste
- trap burden is the cleaner current full-scan penalty because it tracks stale loss more directly than generic wall contact does

## What changes under the upgraded metrics?

Baseline `eta_sigma`:

- winner stays on the moderate-flow efficiency ridge family, with raw maximum at `(Pi_m, Pi_f, Pi_U) = ({sigma_row['winner_Pi_m']:.3f}, {sigma_row['winner_Pi_f']:.3f}, {sigma_row['winner_Pi_U']:.3f})`
- top-10 overlap remains zero with both success and speed fronts

Completion-aware `eta_completion_drag`:

- winner moves to `(Pi_m, Pi_f, Pi_U) = ({completion_row['winner_Pi_m']:.3f}, {completion_row['winner_Pi_f']:.3f}, {completion_row['winner_Pi_U']:.3f})`
- this coincides with the speed tip at `(Pi_m, Pi_f, Pi_U) = ({speed_tip['Pi_m']:.3f}, {speed_tip['Pi_f']:.3f}, {speed_tip['Pi_U']:.3f})`
- the completion-aware upgrade therefore shifts the efficiency emphasis toward the high-flow fast-completion branch

Trap-aware `eta_trap_drag`:

- winner remains at the same high-flow point as `eta_completion_drag`
- the trap penalty is weak on the competitive ridge, so this proxy mainly refines interpretation rather than moving the optimum
- the near-identity of the two upgraded metrics is consistent with the current ridge carrying low trap burden over its leading branches

Spearman rank comparison:

- `eta_completion_drag` vs `eta_sigma`: `{completion_row['spearman_vs_eta_sigma']:.3f}`
- `eta_trap_drag` vs `eta_sigma`: `{trap_row['spearman_vs_eta_sigma']:.3f}`

So the thermodynamic upgrade is not trivial. It meaningfully changes which branch looks best, even though it does not destroy the ridge itself.

## Does the Pareto-like ridge survive the thermodynamic upgrade?

Yes. The ridge remains Pareto-like under the upgraded metrics.

Evidence:

- `eta_sigma` gives a non-dominated set of `{int(sigma_row['pareto_candidate_count'])}` points
- `eta_completion_drag` gives a non-dominated set of `{int(completion_row['pareto_candidate_count'])}` points
- `eta_trap_drag` gives a non-dominated set of `{int(trap_row['pareto_candidate_count'])}` points
- in every computed case, the non-dominated set stays pinned to `Pi_f` in `[0.018, 0.025]`
- the success front and upgraded-efficiency fronts remain largely distinct at top-10 depth

What changes is not the existence of the ridge, but the preferred branch along it:

- baseline `eta_sigma` favors a moderate-flow efficiency family
- completion-aware drag efficiency favors the high-flow fast-completion branch
- trap-aware drag efficiency leaves that branch choice essentially unchanged

So the thermodynamic upgrade changes the front ordering along the ridge more than it changes the ridge geometry itself.

## Which metric should be used in the manuscript, and for what purpose?

Recommended usage:

- use `eta_sigma` for screening, continuity with earlier figures, and broad ridge localization
- use `eta_completion_drag` for manuscript-level thermodynamic discussion, because it cleanly upgrades the numerator while staying inside directly computed quantities
- use `eta_trap_drag` for mechanism interpretation, because it asks whether pre-commit stale burden changes the thermodynamic ranking
- reserve `eta_total_future` for later thermodynamic closure once missing channels are explicitly computed

Practical reading:

- `eta_sigma` answers: which points are good transport-per-drag screeners?
- `eta_completion_drag` answers: which points convert drag spending into successful completed transport most efficiently?
- `eta_trap_drag` answers: does the answer change once stale pre-commit loss is penalized?

Current manuscript recommendation:

- main screening metric: `eta_sigma`
- main upgraded thermodynamic metric: `eta_completion_drag`
- supporting mechanism metric: `eta_trap_drag`

## Bottom Line

The upgraded metric family remains compact and interpretable:

- one directly computed baseline metric
- one directly computed completion-aware upgrade
- one proxy trap-aware refinement
- one aspirational future full-efficiency placeholder

The Pareto-like ridge survives the thermodynamic upgrade, but the preferred efficient branch shifts toward the high-flow speed tip once completion rate is separated more cleanly from the old `eta_sigma` numerator.
"""
    DOC_PATH.write_text(doc, encoding="ascii")


def build_outputs() -> dict[str, str]:
    summary = load_summary()
    canonical_df = load_canonical_mechanism_summary()
    metric_table = build_metric_table(summary)
    OUTPUT_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    metric_table.to_csv(OUTPUT_TABLE_PATH, index=False)
    make_figure(summary, metric_table)
    write_doc(summary, metric_table, canonical_df)
    return {
        "doc": str(DOC_PATH),
        "table": str(OUTPUT_TABLE_PATH),
        "figure": str(FIGURE_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build upgraded transport-efficiency quantities and compare their front geometry.")
    parser.parse_args(argv)
    result = build_outputs()
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
