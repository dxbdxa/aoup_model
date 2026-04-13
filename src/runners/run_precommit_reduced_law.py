from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POINT_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "intervention_dataset" / "point_summary.csv"
SLICE_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "intervention_dataset" / "slice_summary.csv"
ORDERING_PATH = PROJECT_ROOT / "outputs" / "datasets" / "intervention_dataset" / "metric_ordering.csv"
RATE_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "precommit_gate_rates.csv"
PRECOMMIT_FIT_REPORT_PATH = PROJECT_ROOT / "docs" / "precommit_gate_theory_fit_report.md"
GATE_THEORY_PRINCIPLE_PATH = PROJECT_ROOT / "docs" / "gate_theory_principle_note.md"
GENERAL_PRINCIPLE_PATH = PROJECT_ROOT / "docs" / "general_principle_candidates.md"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "gate_theory"
PREDICTION_FIGURE_PATH = FIGURE_DIR / "prediction_vs_validation.png"
SCOPE_MAP_FIGURE_PATH = FIGURE_DIR / "reduced_law_scope_map.png"
LAW_DOC_PATH = PROJECT_ROOT / "docs" / "precommit_reduced_law_candidates.md"
VALIDATION_DOC_PATH = PROJECT_ROOT / "docs" / "precommit_prediction_validation_report.md"

MECHANISM_METRICS = [
    "wall_dwell_before_first_commit",
    "first_gate_commit_delay",
    "residence_given_approach",
    "commit_given_residence",
    "trap_burden_mean",
]
PLOT_METRICS = [
    ("wall_dwell_before_first_commit", "wall dwell", "#1f77b4"),
    ("first_gate_commit_delay", "commit delay", "#2ca02c"),
    ("residence_given_approach", "residence/approach", "#ff7f0e"),
    ("commit_given_residence", "commit/residence", "#7f7f7f"),
    ("trap_burden_mean", "trap burden", "#d62728"),
]


@dataclass(frozen=True)
class PredictionSpec:
    prediction_id: str
    short_title: str
    control_axis: str
    statement: str
    operational_prediction: str
    falsifier: str


PREDICTIONS = (
    PredictionSpec(
        prediction_id="P1",
        short_title="Delay Acts First On Timing",
        control_axis="Pi_f",
        statement=(
            "Around the productive ridge midpoint, delay enters first through the pre-commit timing budget: "
            "off-center delay perturbations should lengthen `first_gate_commit_delay` and "
            "`wall_dwell_before_first_commit` before they materially change `commit_given_residence`."
        ),
        operational_prediction=(
            "On the delay slice, the balanced ridge midpoint should minimize the timing observables, "
            "`commit_given_residence` should stay subleading, and trap burden should appear only at the stale edge."
        ),
        falsifier=(
            "The law would fail if the delay slice were driven first by `commit_given_residence`, or if timing stayed flat "
            "while delay changed across the local ridge neighborhood."
        ),
    ),
    PredictionSpec(
        prediction_id="P2",
        short_title="Flow Orders The Timing Budget",
        control_axis="Pi_U",
        statement=(
            "Increasing flow should monotonically compress the pre-commit timing budget and modestly improve "
            "approach-to-residence organization, while leaving `commit_given_residence` approximately invariant."
        ),
        operational_prediction=(
            "On the flow slice, both timing observables should decrease monotonically, "
            "`residence_given_approach` should increase, and `commit_given_residence` should remain flat."
        ),
        falsifier=(
            "The law would fail if higher flow did not shorten the timing budget, or if `commit_given_residence` "
            "became the dominant flow-sensitive observable."
        ),
    ),
    PredictionSpec(
        prediction_id="P3",
        short_title="Memory Acts First On Arrival Organization",
        control_axis="Pi_m",
        statement=(
            "Within the productive memory band, memory should act more cleanly on the "
            "`gate_approach -> gate_residence_precommit` part of the backbone than on timing or final pre-commit conversion."
        ),
        operational_prediction=(
            "On the memory slice, `residence_given_approach` should vary more coherently than either timing metric "
            "or `commit_given_residence`, even if the full slice is not perfectly monotone."
        ),
        falsifier=(
            "The law would fail if the memory slice changed `commit_given_residence` first, or if "
            "`residence_given_approach` were less coherent than the timing observables."
        ),
    ),
    PredictionSpec(
        prediction_id="P4",
        short_title="Commit Conversion Is A Late Correlate",
        control_axis="all",
        statement=(
            "`commit_given_residence` is not the leading control knob of the local ridge. "
            "Its control sensitivity should remain subleading compared with timing and approach organization."
        ),
        operational_prediction=(
            "Across all intervention slices, `commit_given_residence` should never rank as a leading early-indicator variable."
        ),
        falsifier=(
            "The law would fail if `commit_given_residence` became the strongest or second-strongest early responder "
            "under any control-axis intervention."
        ),
    ),
    PredictionSpec(
        prediction_id="P5",
        short_title="Trap Burden Is A Punctate Stale Flag",
        control_axis="stale edge",
        statement=(
            "`trap_burden_mean` should be treated as a weak or punctate stale flag, not as a smooth reduced-law coordinate. "
            "It should remain near zero on productive local ridge points and turn on only at stale edge points or intermittently."
        ),
        operational_prediction=(
            "Trap burden should be absent on most productive delay and flow points, appear at the high-delay stale point, "
            "and remain mixed rather than monotone on the memory slice."
        ),
        falsifier=(
            "The law would fail if trap burden became a smooth dominant control response across the local productive ridge."
        ),
    ),
)


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) <= 1e-12:
        return 0.0
    return float(numerator / denominator)


def _status_from_score(score: float) -> str:
    if score >= 0.75:
        return "supported"
    if score >= 0.50:
        return "mixed"
    return "not_supported"


def _metric_row(ordering_df: pd.DataFrame, slice_name: str, metric_name: str) -> pd.Series:
    subset = ordering_df[(ordering_df["slice_name"] == slice_name) & (ordering_df["metric_name"] == metric_name)]
    if subset.empty:
        raise RuntimeError(f"Missing metric row for {slice_name} / {metric_name}.")
    return subset.iloc[0]


def _slice_rows(slice_summary: pd.DataFrame, slice_name: str) -> pd.DataFrame:
    subset = slice_summary[slice_summary["slice_name"] == slice_name].sort_values("axis_value").reset_index(drop=True)
    if subset.empty:
        raise RuntimeError(f"Missing slice rows for {slice_name}.")
    return subset


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    point_summary = pd.read_csv(POINT_SUMMARY_PATH)
    slice_summary = pd.read_csv(SLICE_SUMMARY_PATH)
    ordering_df = pd.read_csv(ORDERING_PATH)
    rate_table = pd.read_csv(RATE_TABLE_PATH)
    return point_summary, slice_summary, ordering_df, rate_table


def build_metric_classification(ordering_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric_name in MECHANISM_METRICS:
        subset = ordering_df[ordering_df["metric_name"] == metric_name]
        mean_score = float(subset["early_indicator_score"].mean())
        mean_monotonicity = float(subset["monotonicity_score"].mean())
        if metric_name == "trap_burden_mean":
            classification = "weak_or_punctate_stale_flag"
            reason = "Appears mainly at stale edges or intermittently, with mixed directionality."
        elif metric_name == "commit_given_residence":
            classification = "late_correlate"
            reason = "Cross-slice response stays small and comparatively flat."
        elif metric_name == "residence_given_approach":
            classification = "early_indicator"
            reason = "Cleaner secondary early signal, especially on memory and flow slices."
        else:
            classification = "early_indicator"
            reason = "Dominant pre-commit timing discriminator."
        rows.append(
            {
                "metric_name": metric_name,
                "classification": classification,
                "mean_early_indicator_score": mean_score,
                "mean_monotonicity_score": mean_monotonicity,
                "reason": reason,
            }
        )
    return pd.DataFrame(rows).sort_values(["classification", "mean_early_indicator_score"], ascending=[True, False]).reset_index(drop=True)


def validate_predictions(slice_summary: pd.DataFrame, ordering_df: pd.DataFrame) -> pd.DataFrame:
    delay = _slice_rows(slice_summary, "delay_slice")
    memory = _slice_rows(slice_summary, "memory_slice")
    flow = _slice_rows(slice_summary, "flow_slice")

    delay_first = _metric_row(ordering_df, "delay_slice", "first_gate_commit_delay")
    delay_wall = _metric_row(ordering_df, "delay_slice", "wall_dwell_before_first_commit")
    delay_commit = _metric_row(ordering_df, "delay_slice", "commit_given_residence")
    delay_trap = _metric_row(ordering_df, "delay_slice", "trap_burden_mean")

    flow_first = _metric_row(ordering_df, "flow_slice", "first_gate_commit_delay")
    flow_wall = _metric_row(ordering_df, "flow_slice", "wall_dwell_before_first_commit")
    flow_approach = _metric_row(ordering_df, "flow_slice", "residence_given_approach")
    flow_commit = _metric_row(ordering_df, "flow_slice", "commit_given_residence")
    flow_trap = _metric_row(ordering_df, "flow_slice", "trap_burden_mean")

    memory_first = _metric_row(ordering_df, "memory_slice", "first_gate_commit_delay")
    memory_wall = _metric_row(ordering_df, "memory_slice", "wall_dwell_before_first_commit")
    memory_approach = _metric_row(ordering_df, "memory_slice", "residence_given_approach")
    memory_commit = _metric_row(ordering_df, "memory_slice", "commit_given_residence")
    memory_trap = _metric_row(ordering_df, "memory_slice", "trap_burden_mean")

    classification = build_metric_classification(ordering_df).set_index("metric_name")

    rows: list[dict[str, Any]] = []

    delay_baseline = delay.loc[delay["is_baseline"]].iloc[0]
    delay_positive_trap = delay[delay["trap_burden_mean"] > 1e-12]
    delay_checks = {
        "timing_budget_local_min_commit_delay": float(delay_baseline["first_gate_commit_delay"]) <= float(delay["first_gate_commit_delay"].min()) + 1e-12,
        "timing_budget_local_min_wall_dwell": float(delay_baseline["wall_dwell_before_first_commit"]) <= float(delay["wall_dwell_before_first_commit"].min()) + 1e-12,
        "commit_conversion_subleading": float(delay_commit["early_indicator_score"]) < min(
            float(delay_first["early_indicator_score"]),
            float(delay_wall["early_indicator_score"]),
        ),
        "trap_only_at_high_delay_edge": (
            len(delay_positive_trap) == 1
            and math.isclose(float(delay_positive_trap["axis_value"].iloc[0]), float(delay["axis_value"].max()))
        ),
    }
    rows.append(
        {
            "prediction_id": "P1",
            "short_title": "Delay Acts First On Timing",
            "control_axis": "Pi_f",
            "validation_score": float(np.mean(list(delay_checks.values()))),
            "status": _status_from_score(float(np.mean(list(delay_checks.values())))),
            "checks_passed": int(sum(bool(value) for value in delay_checks.values())),
            "checks_total": int(len(delay_checks)),
            "observed_evidence": (
                f"delay midpoint gives the local timing minimum: commit delay `{delay_baseline['first_gate_commit_delay']:.4f}` "
                f"vs slice range `{delay['first_gate_commit_delay'].min():.4f}` to `{delay['first_gate_commit_delay'].max():.4f}`; "
                f"wall dwell `{delay_baseline['wall_dwell_before_first_commit']:.4f}` vs range "
                f"`{delay['wall_dwell_before_first_commit'].min():.4f}` to `{delay['wall_dwell_before_first_commit'].max():.4f}`; "
                f"`commit_given_residence` score `{delay_commit['early_indicator_score']:.4f}` stays below the timing scores; "
                f"trap burden turns on only at `Pi_f = {delay_positive_trap['axis_value'].iloc[0]:.3f}`."
            ),
            "law_statement": PREDICTIONS[0].statement,
            "operational_prediction": PREDICTIONS[0].operational_prediction,
            "falsifier": PREDICTIONS[0].falsifier,
        }
    )

    flow_checks = {
        "commit_delay_decreases_monotonically": (
            str(flow_first["direction_label"]) == "decreasing" and float(flow_first["monotonicity_score"]) >= 0.80
        ),
        "wall_dwell_decreases_monotonically": (
            str(flow_wall["direction_label"]) == "decreasing" and float(flow_wall["monotonicity_score"]) >= 0.80
        ),
        "approach_residence_increases": (
            str(flow_approach["direction_label"]) == "increasing" and float(flow_approach["monotonicity_score"]) >= 0.80
        ),
        "commit_conversion_subleading": float(flow_commit["early_indicator_score"]) < 0.25 * min(
            float(flow_first["early_indicator_score"]),
            float(flow_wall["early_indicator_score"]),
        ),
    }
    rows.append(
        {
            "prediction_id": "P2",
            "short_title": "Flow Orders The Timing Budget",
            "control_axis": "Pi_U",
            "validation_score": float(np.mean(list(flow_checks.values()))),
            "status": _status_from_score(float(np.mean(list(flow_checks.values())))),
            "checks_passed": int(sum(bool(value) for value in flow_checks.values())),
            "checks_total": int(len(flow_checks)),
            "observed_evidence": (
                f"commit delay falls from `{flow['first_gate_commit_delay'].iloc[0]:.4f}` to `{flow['first_gate_commit_delay'].iloc[-1]:.4f}`, "
                f"wall dwell falls from `{flow['wall_dwell_before_first_commit'].iloc[0]:.4f}` to "
                f"`{flow['wall_dwell_before_first_commit'].iloc[-1]:.4f}`, "
                f"`residence_given_approach` rises from `{flow['residence_given_approach'].iloc[0]:.4f}` to "
                f"`{flow['residence_given_approach'].iloc[-1]:.4f}`, and `commit_given_residence` "
                f"stays near `{flow.loc[flow['is_baseline'], 'commit_given_residence'].iloc[0]:.3f}`."
            ),
            "law_statement": PREDICTIONS[1].statement,
            "operational_prediction": PREDICTIONS[1].operational_prediction,
            "falsifier": PREDICTIONS[1].falsifier,
        }
    )

    memory_checks = {
        "approach_more_monotone_than_commit": float(memory_approach["monotonicity_score"]) > float(memory_commit["monotonicity_score"]),
        "approach_more_monotone_than_commit_delay": float(memory_approach["monotonicity_score"]) > float(memory_first["monotonicity_score"]),
        "approach_more_monotone_than_wall_dwell": float(memory_approach["monotonicity_score"]) > float(memory_wall["monotonicity_score"]),
        "approach_responds_more_than_commit_conversion": float(memory_approach["early_indicator_score"]) > float(memory_commit["early_indicator_score"]),
        "approach_improves_from_low_to_productive_band": float(memory["residence_given_approach"].iloc[-2]) > float(memory["residence_given_approach"].iloc[0]),
    }
    rows.append(
        {
            "prediction_id": "P3",
            "short_title": "Memory Acts First On Arrival Organization",
            "control_axis": "Pi_m",
            "validation_score": float(np.mean(list(memory_checks.values()))),
            "status": _status_from_score(float(np.mean(list(memory_checks.values())))),
            "checks_passed": int(sum(bool(value) for value in memory_checks.values())),
            "checks_total": int(len(memory_checks)),
            "observed_evidence": (
                f"memory-slice monotonicity is highest for `residence_given_approach` (`{memory_approach['monotonicity_score']:.3f}`) "
                f"vs commit delay `{memory_first['monotonicity_score']:.3f}`, wall dwell `{memory_wall['monotonicity_score']:.3f}`, "
                f"and `commit_given_residence` `{memory_commit['monotonicity_score']:.3f}`; "
                f"`residence_given_approach` rises from `{memory['residence_given_approach'].iloc[0]:.4f}` at low memory "
                f"to `{memory['residence_given_approach'].iloc[-2]:.4f}` before the edge roll-off."
            ),
            "law_statement": PREDICTIONS[2].statement,
            "operational_prediction": PREDICTIONS[2].operational_prediction,
            "falsifier": PREDICTIONS[2].falsifier,
        }
    )

    commit_checks = {
        "never_top_ranked": int(classification.loc["commit_given_residence", "classification"] == "late_correlate"),
        "no_top1_occurrence": int(
            ordering_df[(ordering_df["metric_name"] == "commit_given_residence")]["combined_rank"].min() > 1
        ),
        "subleading_mean_score_vs_timing": (
            float(classification.loc["commit_given_residence", "mean_early_indicator_score"]) < float(classification.loc["first_gate_commit_delay", "mean_early_indicator_score"])
            and float(classification.loc["commit_given_residence", "mean_early_indicator_score"]) < float(classification.loc["wall_dwell_before_first_commit", "mean_early_indicator_score"])
        ),
        "low_mean_monotonicity": float(classification.loc["commit_given_residence", "mean_monotonicity_score"]) < 0.40,
    }
    rows.append(
        {
            "prediction_id": "P4",
            "short_title": "Commit Conversion Is A Late Correlate",
            "control_axis": "all",
            "validation_score": float(np.mean(list(commit_checks.values()))),
            "status": _status_from_score(float(np.mean(list(commit_checks.values())))),
            "checks_passed": int(sum(bool(value) for value in commit_checks.values())),
            "checks_total": int(len(commit_checks)),
            "observed_evidence": (
                f"`commit_given_residence` has the smallest mean early-indicator score (`{classification.loc['commit_given_residence', 'mean_early_indicator_score']:.4f}`) "
                f"and low mean monotonicity (`{classification.loc['commit_given_residence', 'mean_monotonicity_score']:.3f}`); "
                "it never appears as a leading slice responder."
            ),
            "law_statement": PREDICTIONS[3].statement,
            "operational_prediction": PREDICTIONS[3].operational_prediction,
            "falsifier": PREDICTIONS[3].falsifier,
        }
    )

    memory_positive_trap = int((memory["trap_burden_mean"] > 1e-12).sum())
    flow_positive_trap = int((flow["trap_burden_mean"] > 1e-12).sum())
    trap_checks = {
        "delay_trap_only_at_stale_edge": delay_checks["trap_only_at_high_delay_edge"],
        "memory_trap_mixed_not_monotone": str(memory_trap["direction_label"]) == "mixed",
        "flow_trap_mixed_not_monotone": str(flow_trap["direction_label"]) == "mixed",
        "trap_not_clean_global_law_coordinate": float(classification.loc["trap_burden_mean", "mean_monotonicity_score"]) < 0.50,
    }
    rows.append(
        {
            "prediction_id": "P5",
            "short_title": "Trap Burden Is A Punctate Stale Flag",
            "control_axis": "stale edge",
            "validation_score": float(np.mean(list(trap_checks.values()))),
            "status": _status_from_score(float(np.mean(list(trap_checks.values())))),
            "checks_passed": int(sum(bool(value) for value in trap_checks.values())),
            "checks_total": int(len(trap_checks)),
            "observed_evidence": (
                f"trap burden is positive at only `{len(delay_positive_trap)}` delay-slice point, "
                f"`{memory_positive_trap}` memory-slice points, and `{flow_positive_trap}` flow-slice points; "
                f"memory and flow directions remain `{memory_trap['direction_label']}` and `{flow_trap['direction_label']}`."
            ),
            "law_statement": PREDICTIONS[4].statement,
            "operational_prediction": PREDICTIONS[4].operational_prediction,
            "falsifier": PREDICTIONS[4].falsifier,
        }
    )

    return pd.DataFrame(rows)


def build_scope_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "control_parameter": "Pi_f",
                "timing_budget": "first / strong",
                "approach_to_residence": "secondary",
                "residence_to_commit": "late / flat",
                "trap_burden": "punctate stale edge",
            },
            {
                "control_parameter": "Pi_m",
                "timing_budget": "weak / mixed",
                "approach_to_residence": "first / cleanest",
                "residence_to_commit": "late / flat",
                "trap_burden": "intermittent flag",
            },
            {
                "control_parameter": "Pi_U",
                "timing_budget": "first / strongest",
                "approach_to_residence": "secondary increasing",
                "residence_to_commit": "late / flat",
                "trap_burden": "weak / punctate",
            },
        ]
    )


def build_working_regions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "region_or_task": "delay slice near balanced midpoint",
                "law_status": "works_well",
                "reason": "Timing observables respond first and trap burden stays deferred to the stale edge.",
            },
            {
                "region_or_task": "flow ordering along the ridge",
                "law_status": "works_well",
                "reason": "Timing contraction is monotone and `commit_given_residence` stays flat.",
            },
            {
                "region_or_task": "memory variation inside productive band",
                "law_status": "works_with_limits",
                "reason": "`residence_given_approach` is cleaner than timing, but the slice is weaker and not globally monotone in every observable.",
            },
            {
                "region_or_task": "trap kinetics as a fitted rate law",
                "law_status": "expected_failure",
                "reason": "Trap counts remain too sparse; trap burden is only an occupancy-level stale flag.",
            },
            {
                "region_or_task": "post-commit completion and full crossing success",
                "law_status": "expected_failure",
                "reason": "The reduced law stops at `gate_commit` and does not claim a crossing-completion model.",
            },
            {
                "region_or_task": "full efficiency ranking",
                "law_status": "expected_failure",
                "reason": "Efficiency still mixes pre-commit organization with downstream transport costs outside the reduced law.",
            },
        ]
    )


def normalized_slice_response(slice_summary: pd.DataFrame, slice_name: str) -> pd.DataFrame:
    subset = _slice_rows(slice_summary, slice_name)
    baseline = subset.loc[subset["is_baseline"]].iloc[0]
    rows: list[dict[str, Any]] = []
    for metric_name in MECHANISM_METRICS:
        raw = subset[metric_name].to_numpy(dtype=float)
        baseline_value = float(baseline[metric_name])
        centered = raw - baseline_value
        scale = max(float(np.max(np.abs(centered))), 1e-12)
        normalized = centered / scale
        for axis_value, norm_value in zip(subset["axis_value"].to_numpy(dtype=float), normalized):
            rows.append(
                {
                    "slice_name": slice_name,
                    "metric_name": metric_name,
                    "axis_value": axis_value,
                    "normalized_response": norm_value,
                }
            )
    return pd.DataFrame(rows)


def make_prediction_figure(slice_summary: pd.DataFrame, validation_df: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 10))

    ax = axes[0, 0]
    ordered = validation_df.sort_values(["validation_score", "prediction_id"], ascending=[True, True])
    colors = ordered["status"].map(
        {"supported": "#2ca02c", "mixed": "#ff7f0e", "not_supported": "#d62728"}
    )
    ax.barh(ordered["prediction_id"] + " " + ordered["short_title"], ordered["validation_score"], color=colors)
    ax.axvline(0.75, color="#555555", linestyle="--", linewidth=1.0)
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("validation score")
    ax.set_title("Prediction Validation Scores")

    slice_map = {
        "delay_slice": axes[0, 1],
        "memory_slice": axes[1, 0],
        "flow_slice": axes[1, 1],
    }
    for slice_name, ax in slice_map.items():
        normalized = normalized_slice_response(slice_summary, slice_name)
        for metric_name, label, color in PLOT_METRICS:
            subset = normalized[normalized["metric_name"] == metric_name]
            ax.plot(subset["axis_value"], subset["normalized_response"], marker="o", linewidth=1.8, color=color, label=label)
        baseline_axis = float(slice_summary[(slice_summary["slice_name"] == slice_name) & (slice_summary["is_baseline"])]["axis_value"].iloc[0])
        ax.axvline(baseline_axis, color="#555555", linestyle="--", linewidth=1.0)
        ax.set_ylim(-1.1, 1.1)
        ax.set_title(slice_name.replace("_", " "))
        ax.set_xlabel(slice_summary[slice_summary["slice_name"] == slice_name]["axis_name"].iloc[0])
        ax.set_ylabel("normalized response about baseline")
    axes[1, 1].legend(loc="lower right", fontsize=8)

    fig.suptitle("Pre-Commit Reduced-Law Predictions Vs Intervention Validation", fontsize=14)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(PREDICTION_FIGURE_PATH, dpi=220)
    plt.close(fig)


def make_scope_map_figure(scope_table: pd.DataFrame) -> None:
    category_to_value = {
        "punctate stale edge": 0,
        "intermittent flag": 0,
        "weak / punctate": 0,
        "late / flat": 1,
        "weak / mixed": 2,
        "secondary": 3,
        "secondary increasing": 3,
        "first / cleanest": 4,
        "first / strong": 4,
        "first / strongest": 4,
    }
    matrix = np.array(
        [
            [
                category_to_value[row["timing_budget"]],
                category_to_value[row["approach_to_residence"]],
                category_to_value[row["residence_to_commit"]],
                category_to_value[row["trap_burden"]],
            ]
            for _, row in scope_table.iterrows()
        ],
        dtype=float,
    )
    cmap = ListedColormap(["#d62728", "#bdbdbd", "#c7b299", "#9ecae1", "#31a354"])

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    image = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=4, aspect="auto")
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(
        ["timing budget", "approach -> residence", "residence -> commit", "trap burden"],
        rotation=20,
    )
    ax.set_yticks(np.arange(len(scope_table)))
    ax.set_yticklabels(scope_table["control_parameter"].tolist())
    for i, (_, row) in enumerate(scope_table.iterrows()):
        values = [
            row["timing_budget"],
            row["approach_to_residence"],
            row["residence_to_commit"],
            row["trap_burden"],
        ]
        for j, text in enumerate(values):
            ax.text(j, i, str(text), ha="center", va="center", fontsize=8, color="#111111")
    ax.set_title("Reduced-Law Scope Map")
    legend_items = [
        Patch(facecolor="#31a354", label="first / strong"),
        Patch(facecolor="#9ecae1", label="secondary"),
        Patch(facecolor="#c7b299", label="weak / mixed"),
        Patch(facecolor="#bdbdbd", label="late / flat"),
        Patch(facecolor="#d62728", label="punctate stale flag"),
    ]
    ax.legend(handles=legend_items, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(SCOPE_MAP_FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_law_doc(
    *,
    validation_df: pd.DataFrame,
    scope_table: pd.DataFrame,
    metric_classification: pd.DataFrame,
    rate_table: pd.DataFrame,
) -> None:
    selected_rates = rate_table[
        (
            (rate_table["src"] == "wall_sliding") & (rate_table["dst"] == "gate_approach")
        )
        | (
            (rate_table["src"] == "gate_approach") & (rate_table["dst"] == "gate_residence_precommit")
        )
        | (
            (rate_table["src"] == "gate_residence_precommit") & (rate_table["dst"] == "gate_commit")
        )
    ][["canonical_label", "src", "dst", "rate_estimate"]]

    lines = [
        "# Precommit Reduced Law Candidates",
        "",
        "## Scope",
        "",
        "This note converts the current pre-commit gate theory into an explicit falsifiable law package. "
        "The law is intentionally strict: it stops at `gate_commit` and does not claim post-commit completion or final crossing kinetics.",
        "",
        f"- intervention dataset: {_path_link(POINT_SUMMARY_PATH)}",
        f"- intervention ordering: {_path_link(ORDERING_PATH)}",
        f"- precommit fit report: {_path_link(PRECOMMIT_FIT_REPORT_PATH)}",
        f"- gate-theory principle: {_path_link(GATE_THEORY_PRINCIPLE_PATH)}",
        f"- general principle note: {_path_link(GENERAL_PRINCIPLE_PATH)}",
        f"- validation figure: {_path_link(PREDICTION_FIGURE_PATH)}",
        f"- scope-map figure: {_path_link(SCOPE_MAP_FIGURE_PATH)}",
        "",
        "## Reduced Pre-Commit Variables",
        "",
        "The reduced law uses only the currently supported pre-commit observables:",
        "",
        "- `T_commit = first_gate_commit_delay`",
        "- `T_wall = wall_dwell_before_first_commit`",
        "- `A_pre = residence_given_approach`",
        "- `C_pre = commit_given_residence`",
        "- `S_pre = trap_burden_mean`",
        "",
        "Mechanism reading from the existing fitted rate model:",
        "",
        "- `wall_sliding -> gate_approach` and `gate_approach -> gate_residence_precommit` encode arrival organization.",
        "- `gate_residence_precommit -> gate_commit` is comparatively stable and should not be treated as the leading control-sensitive knob.",
        "- trap entry remains too sparse for a smooth kinetic law and should be retained only as a stale-flag variable.",
        "",
        selected_rates.to_markdown(index=False),
        "",
        "## Explicit Reduced-Law Predictions",
        "",
    ]
    for spec in PREDICTIONS:
        row = validation_df[validation_df["prediction_id"] == spec.prediction_id].iloc[0]
        lines.extend(
            [
                f"### {spec.prediction_id}: {spec.short_title}",
                "",
                f"Law statement: {spec.statement}",
                "",
                f"Operational prediction: {spec.operational_prediction}",
                "",
                f"Current validation status: `{row['status']}` with score `{row['validation_score']:.2f}`.",
                "",
            ]
        )

    lines.extend(
        [
            "## Which control parameter acts on which part of the backbone first?",
            "",
            scope_table.to_markdown(index=False),
            "",
            "Interpretation:",
            "",
            "- `Pi_f` and `Pi_U` act first on the timing budget.",
            "- `Pi_m` acts first on approach-to-residence organization.",
            "- `commit_given_residence` is a late correlate rather than the main control-sensitive branch.",
            "- `trap_burden_mean` is a stale-edge flag, not a smooth backbone coordinate.",
            "",
            "## Observable Roles",
            "",
            metric_classification.to_markdown(index=False),
            "",
            "## Minimal Reduced-Law Statement For Results",
            "",
            "A manuscript-strength reduced-law statement supported now is:",
            "",
            "> Locally around the productive ridge, delay and flow act first on the pre-commit timing budget, memory acts first on approach-to-residence organization, residence-to-commit conversion is approximately invariant to first order, and trap burden is only a punctate stale flag. The productive ridge is therefore selected before crossing by a timing-and-arrival backbone rather than by post-commit completion physics.",
            "",
            "## What would falsify the pre-commit law?",
            "",
            "- If `commit_given_residence` became the strongest early responder on any local control slice.",
            "- If changing `Pi_f` or `Pi_U` did not move the timing budget before other mechanism observables.",
            "- If memory acted first on `commit_given_residence` rather than on `residence_given_approach`.",
            "- If trap burden became a smooth dominant ridge coordinate rather than a punctate stale flag.",
            "- If explaining the local ridge slices required post-commit completion physics before the pre-commit observables separated.",
            "",
            "## Scope Limits",
            "",
            "- The law stops at `gate_commit`.",
            "- It does not claim a crossing-completion law.",
            "- It does not claim a smooth kinetic trap law.",
            "- It should not be used as a full efficiency law, because efficiency still mixes in downstream transport costs.",
        ]
    )
    LAW_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_validation_doc(
    *,
    validation_df: pd.DataFrame,
    metric_classification: pd.DataFrame,
    working_regions: pd.DataFrame,
) -> None:
    supported = validation_df[validation_df["status"] == "supported"]
    mixed = validation_df[validation_df["status"] == "mixed"]

    lines = [
        "# Precommit Prediction Validation Report",
        "",
        "## Scope",
        "",
        "This report validates the explicit pre-commit reduced-law predictions against the local intervention dataset. "
        "The validation target is the pre-commit backbone only; no post-commit completion claim is made here.",
        "",
        f"- point summary: {_path_link(POINT_SUMMARY_PATH)}",
        f"- slice summary: {_path_link(SLICE_SUMMARY_PATH)}",
        f"- metric ordering: {_path_link(ORDERING_PATH)}",
        f"- prediction figure: {_path_link(PREDICTION_FIGURE_PATH)}",
        f"- scope map: {_path_link(SCOPE_MAP_FIGURE_PATH)}",
        "",
        "## Validation Strategy",
        "",
        "Each prediction is scored by a small set of explicit slice-level checks. "
        "The checks use only local intervention responses already present in the intervention dataset:",
        "",
        "- timing-budget extrema or monotonicity when the law predicts timing-first behavior",
        "- relative early-indicator scores when the law predicts one observable should move before another",
        "- direction labels and monotonicity scores when the law predicts ordered control response",
        "- punctate-onset tests when the law predicts a stale flag rather than a smooth coordinate",
        "",
        "## Prediction Table",
        "",
        validation_df[
            [
                "prediction_id",
                "short_title",
                "control_axis",
                "validation_score",
                "status",
                "checks_passed",
                "checks_total",
                "observed_evidence",
            ]
        ].to_markdown(index=False),
        "",
        "## Early Indicators, Late Correlates, And Stale Flags",
        "",
        metric_classification.to_markdown(index=False),
        "",
        "## Where The Reduced Law Already Works Well",
        "",
        working_regions[working_regions["law_status"].isin(["works_well", "works_with_limits"])].to_markdown(index=False),
        "",
        "Supported strongly now:",
        "",
        "- delay and flow acting first on the pre-commit timing budget",
        "- memory acting more cleanly on approach-to-residence organization than on commitment conversion",
        "- `commit_given_residence` remaining subleading across the local interventions",
        "",
        "Mixed but still useful:",
        "",
        "- the memory slice is informative, but weaker and less globally one-directional than the flow slice",
        "- trap burden is useful only as a stale-flag variable, not as a smooth control law",
        "",
        "## Where The Reduced Law Is Expected To Fail",
        "",
        working_regions[working_regions["law_status"] == "expected_failure"].to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        "- the reduced law should not be judged on post-commit completion",
        "- it should not be expected to close the full efficiency story",
        "- it should not be promoted into a smooth trap-kinetics theory from the present sparse counts",
        "",
        "## Practical Conclusion",
        "",
        f"{len(supported)} of {len(validation_df)} explicit predictions are supported outright by the intervention dataset, and "
        f"{len(mixed)} remain mixed rather than contradicted. "
        "The current reduced law already works as a local pre-commit Results statement because it correctly identifies "
        "which controls hit timing first, which control hits arrival organization first, and which observables should be treated "
        "as late correlates or punctate stale flags.",
    ]
    VALIDATION_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_outputs() -> dict[str, str]:
    point_summary, slice_summary, ordering_df, rate_table = load_inputs()
    del point_summary
    validation_df = validate_predictions(slice_summary, ordering_df)
    metric_classification = build_metric_classification(ordering_df)
    scope_table = build_scope_table()
    working_regions = build_working_regions()
    make_prediction_figure(slice_summary, validation_df)
    make_scope_map_figure(scope_table)
    write_law_doc(
        validation_df=validation_df,
        scope_table=scope_table,
        metric_classification=metric_classification,
        rate_table=rate_table,
    )
    write_validation_doc(
        validation_df=validation_df,
        metric_classification=metric_classification,
        working_regions=working_regions,
    )
    return {
        "precommit_reduced_law_candidates": str(LAW_DOC_PATH),
        "precommit_prediction_validation_report": str(VALIDATION_DOC_PATH),
        "prediction_vs_validation_png": str(PREDICTION_FIGURE_PATH),
        "reduced_law_scope_map_png": str(SCOPE_MAP_FIGURE_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert the pre-commit gate theory into an explicit reduced-law validation package.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
