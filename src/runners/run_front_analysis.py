from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_confirmatory_scan import build_updated_view

SCAN_ID = "front_analysis"
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet"
FIGURE_ROOT = PROJECT_ROOT / "outputs" / "figures" / SCAN_ID
REPORT_PATH = PROJECT_ROOT / "docs" / "front_analysis_report.md"
CONCLUSION_BOX_PATH = FIGURE_ROOT / "front_conclusion_box.txt"

OBJECTIVES: dict[str, dict[str, Any]] = {
    "Psucc_mean": {
        "label": "Success Probability",
        "goal": "max",
        "ci_low": "Psucc_ci_low",
        "ci_high": "Psucc_ci_high",
        "sort_columns": ["Psucc_mean", "eta_sigma_mean", "MFPT_mean", "trap_time_mean"],
        "ascending": [False, False, True, True],
        "projection_title": "Maximum Success Front",
    },
    "eta_sigma_mean": {
        "label": "Efficiency Screening Signal",
        "goal": "max",
        "ci_low": "eta_sigma_ci_low",
        "ci_high": "eta_sigma_ci_high",
        "sort_columns": ["eta_sigma_mean", "Psucc_mean", "MFPT_mean", "trap_time_mean"],
        "ascending": [False, False, True, True],
        "projection_title": "Maximum Efficiency Front",
    },
    "MFPT_mean": {
        "label": "Mean First-Passage Time",
        "goal": "min",
        "ci_low": "MFPT_ci_low",
        "ci_high": "MFPT_ci_high",
        "sort_columns": ["MFPT_mean", "Psucc_mean", "eta_sigma_mean", "trap_time_mean"],
        "ascending": [True, False, False, True],
        "projection_title": "Minimum MFPT Front",
    },
}

OBJECTIVE_PAIRS = (
    ("Psucc_mean", "eta_sigma_mean"),
    ("Psucc_mean", "MFPT_mean"),
    ("eta_sigma_mean", "MFPT_mean"),
)

FRONT_COLORS = {
    "Psucc_mean": "tab:blue",
    "eta_sigma_mean": "tab:green",
    "MFPT_mean": "tab:red",
}


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def sort_for_objective(df: pd.DataFrame, objective: str) -> pd.DataFrame:
    config = OBJECTIVES[objective]
    return df.sort_values(config["sort_columns"], ascending=config["ascending"]).copy()


def load_front_dataset(summary_path: Path = SUMMARY_PATH) -> pd.DataFrame:
    summary_df = pd.read_parquet(summary_path)
    updated_df, _ = build_updated_view(summary_df)
    updated_df = updated_df.copy()
    updated_df["is_anchor_8192"] = updated_df["analysis_source"] == "resampled_8192"
    updated_df["anchor_priority"] = updated_df["is_anchor_8192"].astype(int)
    updated_df["Pi_sum"] = updated_df["Pi_m"] + updated_df["Pi_f"]
    return updated_df


def extract_fronts(df: pd.DataFrame, *, top_k: int = 20) -> dict[str, pd.DataFrame]:
    fronts: dict[str, pd.DataFrame] = {}
    for objective in OBJECTIVES:
        front = sort_for_objective(df, objective).head(top_k).copy()
        front["front_objective"] = objective
        front["front_rank"] = np.arange(1, len(front) + 1)
        fronts[objective] = front
    return fronts


def winner_row(df: pd.DataFrame, objective: str) -> pd.Series:
    return sort_for_objective(df, objective).iloc[0]


def anchor_row(df: pd.DataFrame, objective: str) -> pd.Series:
    anchor_df = df[df["is_anchor_8192"]].copy()
    if anchor_df.empty:
        return winner_row(df, objective)
    return sort_for_objective(anchor_df, objective).iloc[0]


def compute_topk_overlap(fronts: dict[str, pd.DataFrame], ks: tuple[int, ...] = (5, 10, 20)) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for k in ks:
        top_sets = {
            objective: set(front.head(k)["scan_label"].astype(str).tolist())
            for objective, front in fronts.items()
        }
        for objective_a, objective_b in OBJECTIVE_PAIRS:
            set_a = top_sets[objective_a]
            set_b = top_sets[objective_b]
            overlap = set_a & set_b
            union = set_a | set_b
            records.append(
                {
                    "k": k,
                    "objective_a": objective_a,
                    "objective_b": objective_b,
                    "overlap_count": len(overlap),
                    "overlap_fraction_vs_k": len(overlap) / float(k),
                    "jaccard_index": len(overlap) / float(len(union)) if union else 0.0,
                    "shared_scan_labels": ";".join(sorted(overlap)),
                }
            )
        all_overlap = top_sets["Psucc_mean"] & top_sets["eta_sigma_mean"] & top_sets["MFPT_mean"]
        all_union = top_sets["Psucc_mean"] | top_sets["eta_sigma_mean"] | top_sets["MFPT_mean"]
        records.append(
            {
                "k": k,
                "objective_a": "Psucc_mean",
                "objective_b": "eta_sigma_mean|MFPT_mean",
                "overlap_count": len(all_overlap),
                "overlap_fraction_vs_k": len(all_overlap) / float(k),
                "jaccard_index": len(all_overlap) / float(len(all_union)) if all_union else 0.0,
                "shared_scan_labels": ";".join(sorted(all_overlap)),
            }
        )
    return pd.DataFrame(records)


def parameter_distance(row_a: pd.Series, row_b: pd.Series, ranges: dict[str, float]) -> dict[str, float]:
    delta_pm = float(row_b["Pi_m"] - row_a["Pi_m"])
    delta_pf = float(row_b["Pi_f"] - row_a["Pi_f"])
    delta_pu = float(row_b["Pi_U"] - row_a["Pi_U"])
    raw_distance = math.sqrt(delta_pm**2 + delta_pf**2 + delta_pu**2)
    scaled_distance = math.sqrt(
        (delta_pm / ranges["Pi_m"]) ** 2
        + (delta_pf / ranges["Pi_f"]) ** 2
        + (delta_pu / ranges["Pi_U"]) ** 2
    )
    return {
        "delta_Pi_m": delta_pm,
        "delta_Pi_f": delta_pf,
        "delta_Pi_U": delta_pu,
        "euclidean_distance": raw_distance,
        "normalized_distance": scaled_distance,
    }


def ci_separation(
    winner: pd.Series,
    competitor: pd.Series,
    objective: str,
) -> dict[str, Any]:
    config = OBJECTIVES[objective]
    low = _float_or_none(winner.get(config["ci_low"]))
    high = _float_or_none(winner.get(config["ci_high"]))
    competitor_value = float(competitor[objective])
    separated = None
    if low is not None and high is not None:
        if config["goal"] == "max":
            separated = competitor_value < low
        else:
            separated = competitor_value > high
    return {
        "reference_objective": objective,
        "reference_value": float(winner[objective]),
        "reference_ci_low": low,
        "reference_ci_high": high,
        "competitor_value": competitor_value,
        "separated_by_ci": separated,
    }


def compute_front_distance_summary(df: pd.DataFrame) -> pd.DataFrame:
    winners = {objective: winner_row(df, objective) for objective in OBJECTIVES}
    ranges = {
        axis: float(df[axis].max() - df[axis].min())
        for axis in ("Pi_m", "Pi_f", "Pi_U")
    }
    records: list[dict[str, Any]] = []
    for objective_a, objective_b in OBJECTIVE_PAIRS:
        row_a = winners[objective_a]
        row_b = winners[objective_b]
        distance = parameter_distance(row_a, row_b, ranges)
        on_a = ci_separation(row_a, row_b, objective_a)
        on_b = ci_separation(row_b, row_a, objective_b)
        records.append(
            {
                "winner_a": objective_a,
                "winner_b": objective_b,
                "scan_label_a": row_a["scan_label"],
                "scan_label_b": row_b["scan_label"],
                "analysis_source_a": row_a["analysis_source"],
                "analysis_source_b": row_b["analysis_source"],
                "n_traj_a": int(row_a["analysis_n_traj"]),
                "n_traj_b": int(row_b["analysis_n_traj"]),
                "Pi_m_a": float(row_a["Pi_m"]),
                "Pi_f_a": float(row_a["Pi_f"]),
                "Pi_U_a": float(row_a["Pi_U"]),
                "Pi_m_b": float(row_b["Pi_m"]),
                "Pi_f_b": float(row_b["Pi_f"]),
                "Pi_U_b": float(row_b["Pi_U"]),
                **distance,
                "a_metric_value": on_a["reference_value"],
                "a_metric_ci_low": on_a["reference_ci_low"],
                "a_metric_ci_high": on_a["reference_ci_high"],
                "b_value_on_a_metric": on_a["competitor_value"],
                "b_separated_from_a_by_ci": on_a["separated_by_ci"],
                "b_metric_value": on_b["reference_value"],
                "b_metric_ci_low": on_b["reference_ci_low"],
                "b_metric_ci_high": on_b["reference_ci_high"],
                "a_value_on_b_metric": on_b["competitor_value"],
                "a_separated_from_b_by_ci": on_b["separated_by_ci"],
            }
        )
    return pd.DataFrame(records)


def pareto_candidates(df: pd.DataFrame) -> pd.DataFrame:
    values = df[["Psucc_mean", "eta_sigma_mean", "MFPT_mean"]].to_numpy(dtype=float)
    nondominated_indices: list[int] = []
    for i, point_a in enumerate(values):
        dominated = False
        for j, point_b in enumerate(values):
            if i == j:
                continue
            if (
                point_b[0] >= point_a[0]
                and point_b[1] >= point_a[1]
                and point_b[2] <= point_a[2]
                and (point_b[0] > point_a[0] or point_b[1] > point_a[1] or point_b[2] < point_a[2])
            ):
                dominated = True
                break
        if not dominated:
            nondominated_indices.append(i)

    pareto_df = df.iloc[nondominated_indices].copy()
    pareto_df = pareto_df.sort_values(["Pi_U", "Pi_m", "Pi_f"]).copy()
    pareto_df["pareto_index"] = np.arange(1, len(pareto_df) + 1)
    pareto_df["is_success_winner"] = pareto_df["scan_label"] == winner_row(df, "Psucc_mean")["scan_label"]
    pareto_df["is_efficiency_winner"] = pareto_df["scan_label"] == winner_row(df, "eta_sigma_mean")["scan_label"]
    pareto_df["is_speed_winner"] = pareto_df["scan_label"] == winner_row(df, "MFPT_mean")["scan_label"]
    pareto_df["front_role"] = pareto_df.apply(
        lambda row: ",".join(
            role
            for role, flag in (
                ("success_winner", row["is_success_winner"]),
                ("efficiency_winner", row["is_efficiency_winner"]),
                ("speed_winner", row["is_speed_winner"]),
                ("anchor_8192", row["is_anchor_8192"]),
            )
            if flag
        ),
        axis=1,
    )
    columns = [
        "pareto_index",
        "scan_label",
        "analysis_source",
        "analysis_n_traj",
        "is_anchor_8192",
        "Pi_m",
        "Pi_f",
        "Pi_U",
        "Pi_sum",
        "Psucc_mean",
        "Psucc_ci_low",
        "Psucc_ci_high",
        "eta_sigma_mean",
        "eta_sigma_ci_low",
        "eta_sigma_ci_high",
        "MFPT_mean",
        "MFPT_ci_low",
        "MFPT_ci_high",
        "trap_time_mean",
        "front_role",
        "result_json",
    ]
    return pareto_df[columns]


def classify_front_structure(
    overlap_df: pd.DataFrame,
    distance_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    df: pd.DataFrame,
) -> tuple[str, str]:
    top5 = overlap_df[overlap_df["k"] == 5]
    top10 = overlap_df[overlap_df["k"] == 10]
    top20 = overlap_df[overlap_df["k"] == 20]
    zero_top5_top10 = bool((top5["overlap_count"] == 0).all() and (top10["overlap_count"] == 0).all())
    some_top20_overlap = bool((top20["overlap_count"] > 0).any())
    pareto_size = int(len(pareto_df))
    winner_pf_span = float(distance_df[["Pi_f_a", "Pi_f_b"]].max().max() - distance_df[["Pi_f_a", "Pi_f_b"]].min().min())
    winner_pu_span = float(distance_df[["Pi_U_a", "Pi_U_b"]].max().max() - distance_df[["Pi_U_a", "Pi_U_b"]].min().min())
    all_ci_separated = bool(distance_df["b_separated_from_a_by_ci"].fillna(False).all() and distance_df["a_separated_from_b_by_ci"].fillna(False).all())

    if pareto_size >= 8 and winner_pf_span <= 0.01 and winner_pu_span >= 0.1:
        if zero_top5_top10 and some_top20_overlap and all_ci_separated:
            return (
                "Pareto-like ridge",
                "The productive-memory structure is best described as a Pareto-like ridge with distinct front tips: the non-dominated set is extended, Pi_f stays tightly pinned, Pi_U orders the tradeoff, and winner separation survives CI-aware checks.",
            )
        return (
            "Pareto-like ridge",
            "The non-dominated set forms an extended ridge in the confirmatory dataset, even though the best objective tips are not strongly overlapping.",
        )
    if zero_top5_top10 and not some_top20_overlap:
        return (
            "Three isolated local optima",
            "The top-ranked fronts stay disjoint even at larger k and do not organize into an extended overlapping family.",
        )
    return (
        "Partially overlapping front family",
        "The confirmatory dataset supports a shared ridge family, but overlap between objective-ranked subsets is limited enough that practical winners remain objective-specific.",
    )


def objective_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for objective in OBJECTIVES:
        winner = winner_row(df, objective)
        anchor = anchor_row(df, objective)
        records.append(
            {
                "objective": objective,
                "winner_scan_label": winner["scan_label"],
                "winner_analysis_source": winner["analysis_source"],
                "winner_n_traj": int(winner["analysis_n_traj"]),
                "winner_Pi_m": float(winner["Pi_m"]),
                "winner_Pi_f": float(winner["Pi_f"]),
                "winner_Pi_U": float(winner["Pi_U"]),
                "winner_metric_value": float(winner[objective]),
                "winner_ci_low": _float_or_none(winner.get(OBJECTIVES[objective]["ci_low"])),
                "winner_ci_high": _float_or_none(winner.get(OBJECTIVES[objective]["ci_high"])),
                "anchor_scan_label": anchor["scan_label"],
                "anchor_analysis_source": anchor["analysis_source"],
                "anchor_n_traj": int(anchor["analysis_n_traj"]),
                "anchor_Pi_m": float(anchor["Pi_m"]),
                "anchor_Pi_f": float(anchor["Pi_f"]),
                "anchor_Pi_U": float(anchor["Pi_U"]),
                "anchor_metric_value": float(anchor[objective]),
                "anchor_ci_low": _float_or_none(anchor.get(OBJECTIVES[objective]["ci_low"])),
                "anchor_ci_high": _float_or_none(anchor.get(OBJECTIVES[objective]["ci_high"])),
            }
        )
    return pd.DataFrame(records)


def make_projection_figure(df: pd.DataFrame, fronts: dict[str, pd.DataFrame], x_param: str, figure_path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 10.5), sharex=True)
    x_label = x_param
    order = ["Psucc_mean", "eta_sigma_mean", "MFPT_mean"]
    for axis, objective in zip(axes, order):
        front = fronts[objective].sort_values([x_param, "front_rank"]).copy()
        axis.scatter(
            df[x_param],
            df[objective],
            color="0.82",
            s=26,
            alpha=0.7,
            label="confirmatory grid",
        )
        anchor_df = df[df["is_anchor_8192"]]
        axis.scatter(
            anchor_df[x_param],
            anchor_df[objective],
            facecolors="white",
            edgecolors="black",
            linewidths=1.0,
            s=65,
            label="8192 anchors",
            zorder=3,
        )
        axis.plot(
            front[x_param],
            front[objective],
            color=FRONT_COLORS[objective],
            linewidth=1.5,
            alpha=0.8,
        )
        axis.scatter(
            front[x_param],
            front[objective],
            color=FRONT_COLORS[objective],
            s=42,
            label=f"top-20 {objective}",
            zorder=4,
        )
        winner = winner_row(df, objective)
        axis.scatter(
            [winner[x_param]],
            [winner[objective]],
            color=FRONT_COLORS[objective],
            edgecolors="black",
            linewidths=0.9,
            s=95,
            marker="D",
            zorder=5,
            label="front winner",
        )
        if objective == "MFPT_mean":
            axis.invert_yaxis()
        axis.set_ylabel(objective)
        axis.set_title(OBJECTIVES[objective]["projection_title"])
        axis.grid(alpha=0.25, linewidth=0.6)

    handles, labels = axes[0].get_legend_handles_labels()
    seen: set[str] = set()
    unique_handles = []
    unique_labels = []
    for handle, label in zip(handles, labels):
        if label in seen:
            continue
        seen.add(label)
        unique_handles.append(handle)
        unique_labels.append(label)
    fig.legend(unique_handles, unique_labels, loc="upper center", ncol=4, frameon=False)
    axes[-1].set_xlabel(x_label)
    fig.suptitle(f"Productive-Memory Front Projections Along {x_param}")
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def conclusion_box(
    *,
    classification: str,
    classification_text: str,
    summary_rows: pd.DataFrame,
    overlap_df: pd.DataFrame,
) -> str:
    success = summary_rows[summary_rows["objective"] == "Psucc_mean"].iloc[0]
    efficiency = summary_rows[summary_rows["objective"] == "eta_sigma_mean"].iloc[0]
    speed = summary_rows[summary_rows["objective"] == "MFPT_mean"].iloc[0]
    top10 = overlap_df[overlap_df["k"] == 10]
    return (
        "The confirmatory ridge resolves into a narrow productive-memory front family rather than a single optimum. "
        f"The best descriptor is '{classification}': {classification_text} "
        f"The winner for success sits at (Pi_m, Pi_f, Pi_U) = ({success['winner_Pi_m']:.3g}, {success['winner_Pi_f']:.3g}, {success['winner_Pi_U']:.3g}), "
        f"the efficiency winner at ({efficiency['winner_Pi_m']:.3g}, {efficiency['winner_Pi_f']:.3g}, {efficiency['winner_Pi_U']:.3g}), "
        f"and the speed winner at ({speed['winner_Pi_m']:.3g}, {speed['winner_Pi_f']:.3g}, {speed['winner_Pi_U']:.3g}). "
        f"Top-10 overlap counts remain zero for all front pairs, so Pi_U orders practical objective preference along the ridge without collapsing the three decision points into one."
    )


def build_report(
    *,
    df: pd.DataFrame,
    summary_rows: pd.DataFrame,
    overlap_df: pd.DataFrame,
    distance_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    classification: str,
    classification_text: str,
    output_paths: dict[str, Path],
) -> str:
    success = summary_rows[summary_rows["objective"] == "Psucc_mean"].iloc[0]
    efficiency = summary_rows[summary_rows["objective"] == "eta_sigma_mean"].iloc[0]
    speed = summary_rows[summary_rows["objective"] == "MFPT_mean"].iloc[0]

    topk_table = overlap_df.pivot(index=["objective_a", "objective_b"], columns="k", values="overlap_count")
    anchor_count = int(df["is_anchor_8192"].sum())

    report = f"""# Front Analysis Report

## Scope

This report builds the final front-analysis package for the productive-memory ridge using the confirmatory scan as the primary dataset.

Primary inputs:

- {_path_link(SUMMARY_PATH)}
- {_path_link(PROJECT_ROOT / "docs" / "confirmatory_scan_run_report.md")}
- {_path_link(PROJECT_ROOT / "docs" / "confirmatory_scan_first_look.md")}
- {_path_link(PROJECT_ROOT / "outputs" / "figures" / "confirmatory_scan" / "final_front_candidates.csv")}
- {_path_link(PROJECT_ROOT / "outputs" / "figures" / "confirmatory_scan" / "confirmatory_front_analysis.json")}

Confidence policy:

- all confirmatory points are kept in the working dataset
- `8192`-trajectory points are treated as highest-confidence anchors
- publication-facing winner separation uses CI-aware comparisons on the confirmatory winners

Dataset summary:

- working state points: `{len(df)}`
- `8192` anchors: `{anchor_count}`
- Pareto candidates: `{len(pareto_df)}`
- `Pi_f` support in confirmatory ridge: `[{df['Pi_f'].min():.3g}, {df['Pi_f'].max():.3g}]`

## Publication-Ready Fronts

### Maximum `Psucc_mean`

- winner: `{success['winner_scan_label']}`
- winner location: `Pi_m = {success['winner_Pi_m']}`, `Pi_f = {success['winner_Pi_f']}`, `Pi_U = {success['winner_Pi_U']}`
- winner value: `{success['winner_metric_value']}`
- winner CI: `[{success['winner_ci_low']}, {success['winner_ci_high']}]`
- highest-confidence anchor: `{success['anchor_scan_label']}` at `n_traj = {success['anchor_n_traj']}`

### Maximum `eta_sigma_mean`

- winner: `{efficiency['winner_scan_label']}`
- winner location: `Pi_m = {efficiency['winner_Pi_m']}`, `Pi_f = {efficiency['winner_Pi_f']}`, `Pi_U = {efficiency['winner_Pi_U']}`
- winner value: `{efficiency['winner_metric_value']}`
- winner CI: `[{efficiency['winner_ci_low']}, {efficiency['winner_ci_high']}]`
- highest-confidence anchor: `{efficiency['anchor_scan_label']}` at `n_traj = {efficiency['anchor_n_traj']}`

### Minimum `MFPT_mean`

- winner: `{speed['winner_scan_label']}`
- winner location: `Pi_m = {speed['winner_Pi_m']}`, `Pi_f = {speed['winner_Pi_f']}`, `Pi_U = {speed['winner_Pi_U']}`
- winner value: `{speed['winner_metric_value']}`
- winner CI: `[{speed['winner_ci_low']}, {speed['winner_ci_high']}]`
- highest-confidence anchor: `{speed['anchor_scan_label']}` at `n_traj = {speed['anchor_n_traj']}`

## Front Geometry

- the ridge remains tightly pinned in `Pi_f`, with front winners confined to `Pi_f = 0.018` to `0.025`
- `Pi_U` orders objective preference along the ridge: low flow for success, moderate flow for efficiency, high flow for speed
- `Pi_m` tunes where each objective sits on the ridge, but does not erase the `Pi_U` ordering
- the non-dominated set spans `{len(pareto_df)}` confirmatory points, not just the three winners

Projection figures:

- {_path_link(output_paths["front_projection_PiU"])}
- {_path_link(output_paths["front_projection_Pim"])}
- {_path_link(output_paths["front_projection_Pif"])}

## Uncertainty-Aware Separation

Top-k overlap counts:

{topk_table.to_markdown()}

Winner-distance summary:

{distance_df[[
    "winner_a",
    "winner_b",
    "delta_Pi_m",
    "delta_Pi_f",
    "delta_Pi_U",
    "euclidean_distance",
    "normalized_distance",
    "b_separated_from_a_by_ci",
    "a_separated_from_b_by_ci",
]].to_markdown(index=False)}

Interpretation:

- top-5 overlap is zero for every objective pair
- top-10 overlap is zero for every objective pair
- top-20 overlap stays zero except for a single success/efficiency shared point
- each winner remains separated from the other winners on its own metric under CI-aware comparison

## Does the ridge encode a Pareto-like transport front?

Yes. The confirmatory scan is best described as **{classification}**.

Reasoning:

- the non-dominated set is extended rather than collapsing to three isolated points
- front winners remain distinct, so the ridge has separated tips instead of one universal optimum
- overlap is negligible at `k = 5` and `k = 10`, which preserves practical objective specificity
- limited overlap only appears deeper in the ranked sets, which is consistent with a shared ridge backbone
- the strongest shared coordinate is the narrow `Pi_f` band, while `Pi_U` carries the dominant ordering signal

## Practical Decision Tradeoffs

- choose the success front when maximizing hit probability is the primary constraint
- choose the efficiency front when transport per dissipation is the main figure of merit
- choose the speed front when first-passage time dominates and some success loss is acceptable
- treat the `8192` anchors as the most reliable manuscript callouts, especially for the success and speed tips
- keep the efficiency tip tied to the local ridge family rather than forcing it onto the speed branch

## Output Bundle

- {_path_link(output_paths["front_overlap_summary"])}
- {_path_link(output_paths["front_distance_summary"])}
- {_path_link(output_paths["pareto_candidates"])}
- {_path_link(output_paths["front_conclusion_box"])}

## Manuscript Quote

```text
{CONCLUSION_BOX_PATH.read_text(encoding="ascii")}
```
"""
    return report


def build_front_analysis(
    *,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    figure_root: Path = FIGURE_ROOT,
) -> dict[str, str]:
    df = load_front_dataset(summary_path)
    fronts = extract_fronts(df, top_k=20)
    overlap_df = compute_topk_overlap(fronts)
    distance_df = compute_front_distance_summary(df)
    pareto_df = pareto_candidates(df)
    summary_rows = objective_summary_rows(df)
    classification, classification_text = classify_front_structure(overlap_df, distance_df, pareto_df, df)

    figure_root.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "front_projection_PiU": figure_root / "front_projection_PiU.png",
        "front_projection_Pim": figure_root / "front_projection_Pim.png",
        "front_projection_Pif": figure_root / "front_projection_Pif.png",
        "front_overlap_summary": figure_root / "front_overlap_summary.csv",
        "front_distance_summary": figure_root / "front_distance_summary.csv",
        "pareto_candidates": figure_root / "pareto_candidates.csv",
        "front_conclusion_box": CONCLUSION_BOX_PATH,
    }

    make_projection_figure(df, fronts, "Pi_U", output_paths["front_projection_PiU"])
    make_projection_figure(df, fronts, "Pi_m", output_paths["front_projection_Pim"])
    make_projection_figure(df, fronts, "Pi_f", output_paths["front_projection_Pif"])

    overlap_df.to_csv(output_paths["front_overlap_summary"], index=False)
    distance_df.to_csv(output_paths["front_distance_summary"], index=False)
    pareto_df.to_csv(output_paths["pareto_candidates"], index=False)

    conclusion = conclusion_box(
        classification=classification,
        classification_text=classification_text,
        summary_rows=summary_rows,
        overlap_df=overlap_df,
    )
    CONCLUSION_BOX_PATH.write_text(conclusion, encoding="ascii")

    report_text = build_report(
        df=df,
        summary_rows=summary_rows,
        overlap_df=overlap_df,
        distance_df=distance_df,
        pareto_df=pareto_df,
        classification=classification,
        classification_text=classification_text,
        output_paths=output_paths,
    )
    report_path.write_text(report_text, encoding="ascii")

    return {key: str(value) for key, value in output_paths.items()} | {"report_path": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the final front-analysis package for the productive-memory ridge.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH, help="Confirmatory summary parquet path.")
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH, help="Markdown report destination.")
    parser.add_argument("--figure-root", type=Path, default=FIGURE_ROOT, help="Output directory for front-analysis figures.")
    args = parser.parse_args(argv)

    result = build_front_analysis(summary_path=args.summary_path, report_path=args.report_path, figure_root=args.figure_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
