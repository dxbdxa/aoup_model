from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from matplotlib import patches
from matplotlib.colors import Normalize

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

THRESHOLD_SENSITIVITY_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset" / "threshold_sensitivity_summary.csv"
TRAP_ALIGNMENT_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_audit" / "trap_metric_alignment.csv"
CONDITIONING_ALIGNMENT_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_audit" / "conditioning_alignment.csv"
OLD_REFINED_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "old_vs_refined_summary.csv"
REFINED_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "refined_summary_by_point.csv"
EVENT_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "event_level.parquet"

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "extended_data"
PNG_PATH = OUTPUT_DIR / "ed_fig3_mechanism_audit_and_thresholds.png"
SVG_PATH = OUTPUT_DIR / "ed_fig3_mechanism_audit_and_thresholds.svg"
MANIFEST_DOC_PATH = PROJECT_ROOT / "docs" / "ed_fig3_panel_manifest.md"

CANONICAL_ORDER = [
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
    "OP_SPEED_TIP",
    "OP_EFFICIENCY_TIP",
    "OP_SUCCESS_TIP",
]
SHORT_LABELS = {
    "OP_BALANCED_RIDGE_MID": "balanced",
    "OP_STALE_CONTROL_OFF_RIDGE": "stale",
    "OP_SPEED_TIP": "speed",
    "OP_EFFICIENCY_TIP": "efficiency",
    "OP_SUCCESS_TIP": "success",
}
PANEL_TITLES = {
    "A": "Event-classification thresholds and refined state graph",
    "B": "Trap metric alignment: source-compatible and raw event durations",
    "C": "Old and refined gate-state definitions on the matched pair",
    "D": "Threshold sensitivity of classifier-near event shares",
    "E": "Trusted ridge-versus-stale observables in the refined audit",
    "F": "Proxy-conditioned gate-local observables and compatibility",
}
REFINED_THRESHOLDS = [
    "wall sliding: |u . t_wall| >= 0.70",
    "residence lane: |t_gate| <= 0.060, |n_gate| <= 0.030",
    "commit lane: |t_gate| <= 0.034, n in [-0.018, 0.020]",
    "commit alignment: u . n_gate >= 0.60",
    "commit progress: v . n_gate >= 0.075",
    "crossing margin: sign change > 0.010",
    "trap confirmation: dwell >= 0.500",
]
STATE_DISPLAY = {
    "bulk_motion": "bulk",
    "wall_sliding": "wall",
    "gate_approach": "approach",
    "gate_residence_precommit": "precommit\nresidence",
    "gate_commit": "commit",
    "gate_crossing": "crossing",
    "trap_episode": "trap",
}
SELECTED_TRANSITIONS = [
    ("bulk_motion", "wall_sliding"),
    ("wall_sliding", "gate_approach"),
    ("gate_approach", "gate_residence_precommit"),
    ("gate_residence_precommit", "gate_commit"),
    ("gate_commit", "gate_crossing"),
    ("trap_episode", "trap_escape"),
]
TRUSTED_OBSERVABLES = [
    ("first_gate_commit_delay", "First commit delay"),
    ("wall_dwell_before_first_commit", "Wall dwell before commit"),
    ("trap_burden_mean", "Trap burden"),
]


def short_label(canonical_label: str) -> str:
    return SHORT_LABELS.get(canonical_label, canonical_label.replace("OP_", "").lower())


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


def normalize_rows(values: np.ndarray) -> np.ndarray:
    normalized = np.zeros_like(values, dtype=float)
    for row_index, row in enumerate(values):
        finite = np.isfinite(row)
        if not finite.any():
            normalized[row_index, :] = np.nan
            continue
        row_min = float(np.nanmin(row))
        row_max = float(np.nanmax(row))
        if row_max <= row_min:
            normalized[row_index, finite] = 0.5
        else:
            normalized[row_index, finite] = (row[finite] - row_min) / (row_max - row_min)
        normalized[row_index, ~finite] = np.nan
    return normalized


def summarize_event_counters(
    event_counts: Counter[str],
    exit_counts: Counter[tuple[str, str]],
) -> dict[str, Any]:
    total_events = int(sum(event_counts.values()))
    state_fractions = {
        state: (event_counts[state] / total_events if total_events > 0 else np.nan)
        for state in STATE_DISPLAY
    }
    transition_shares = {}
    for state, dest in SELECTED_TRANSITIONS:
        denom = event_counts[state]
        transition_shares[(state, dest)] = exit_counts[(state, dest)] / denom if denom > 0 else np.nan
    return {
        "total_events": total_events,
        "event_counts": dict(event_counts),
        "state_fractions": state_fractions,
        "transition_shares": transition_shares,
    }


def summarize_event_parquet(event_path: Path = EVENT_PATH) -> dict[str, Any]:
    event_counts: Counter[str] = Counter()
    exit_counts: Counter[tuple[str, str]] = Counter()
    parquet = pq.ParquetFile(event_path)
    for batch in parquet.iter_batches(columns=["event_type", "exited_to_event_type"], batch_size=500_000):
        frame = batch.to_pandas()
        event_series = frame["event_type"].fillna("terminated").astype(str)
        exit_series = frame["exited_to_event_type"].fillna("terminated").astype(str)
        event_counts.update(event_series.tolist())
        exit_counts.update(zip(event_series.tolist(), exit_series.tolist()))
    return summarize_event_counters(event_counts, exit_counts)


def build_old_refined_matrix(compare_df: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str], list[list[str]]]:
    matched = compare_df[compare_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    matched = matched.set_index("canonical_label")
    rows = [
        ("Delay to capture / commit", "old_gate_capture_delay", "first_gate_commit_delay"),
        ("Wall dwell to capture / commit", "old_wall_dwell_before_capture", "wall_dwell_before_first_commit"),
        ("Capture / residence fraction", "old_gate_capture_probability", "commit_given_residence"),
        ("Return-to-wall fraction", "old_return_to_wall_after_capture_rate", "return_to_wall_after_commit_rate"),
    ]
    columns = [
        ("OP_BALANCED_RIDGE_MID", "old"),
        ("OP_BALANCED_RIDGE_MID", "refined"),
        ("OP_STALE_CONTROL_OFF_RIDGE", "old"),
        ("OP_STALE_CONTROL_OFF_RIDGE", "refined"),
    ]
    values = np.zeros((len(rows), len(columns)), dtype=float)
    annotations: list[list[str]] = []
    for row_index, (_, old_col, refined_col) in enumerate(rows):
        row_annotations: list[str] = []
        for col_index, (canonical_label, kind) in enumerate(columns):
            value = float(matched.loc[canonical_label, old_col if kind == "old" else refined_col])
            values[row_index, col_index] = value
            row_annotations.append(format_value(value))
        annotations.append(row_annotations)
    row_labels = [row[0] for row in rows]
    column_labels = ["ridge old", "ridge refined", "stale old", "stale refined"]
    return values, row_labels, column_labels, annotations


def build_trusted_comparison_rows(refined_summary_df: pd.DataFrame) -> list[dict[str, Any]]:
    summary = refined_summary_df.set_index("canonical_label")
    balanced = summary.loc["OP_BALANCED_RIDGE_MID"]
    stale = summary.loc["OP_STALE_CONTROL_OFF_RIDGE"]
    rows: list[dict[str, Any]] = []
    for column, label in TRUSTED_OBSERVABLES:
        series = summary[column].astype(float)
        value_min = float(series.min())
        value_max = float(series.max())
        spread = value_max - value_min
        if spread <= 0.0:
            balanced_norm = 0.5
            stale_norm = 0.5
        else:
            balanced_norm = (float(balanced[column]) - value_min) / spread
            stale_norm = (float(stale[column]) - value_min) / spread
        rows.append(
            {
                "label": label,
                "balanced_value": float(balanced[column]),
                "stale_value": float(stale[column]),
                "balanced_norm": balanced_norm,
                "stale_norm": stale_norm,
            }
        )
    return rows


def load_inputs() -> dict[str, Any]:
    threshold_df = pd.read_csv(THRESHOLD_SENSITIVITY_PATH).copy()
    trap_df = pd.read_csv(TRAP_ALIGNMENT_PATH).copy()
    conditioning_df = pd.read_csv(CONDITIONING_ALIGNMENT_PATH).copy()
    compare_df = pd.read_csv(OLD_REFINED_PATH).copy()
    refined_summary_df = pd.read_csv(REFINED_SUMMARY_PATH).copy()

    threshold_df["canonical_label"] = pd.Categorical(threshold_df["canonical_label"], CANONICAL_ORDER, ordered=True)
    threshold_df = threshold_df.sort_values("canonical_label").reset_index(drop=True)
    trap_df["canonical_label"] = pd.Categorical(trap_df["canonical_label"], CANONICAL_ORDER, ordered=True)
    trap_df = trap_df.sort_values("canonical_label").reset_index(drop=True)
    conditioning_df["canonical_label"] = pd.Categorical(conditioning_df["canonical_label"], CANONICAL_ORDER, ordered=True)
    conditioning_df = conditioning_df.sort_values("canonical_label").reset_index(drop=True)
    refined_summary_df["canonical_label"] = pd.Categorical(refined_summary_df["canonical_label"], CANONICAL_ORDER, ordered=True)
    refined_summary_df = refined_summary_df.sort_values("canonical_label").reset_index(drop=True)

    event_summary = summarize_event_parquet()
    return {
        "threshold": threshold_df,
        "trap": trap_df,
        "conditioning": conditioning_df,
        "compare": compare_df,
        "refined": refined_summary_df,
        "event_summary": event_summary,
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


def draw_panel_a(ax: plt.Axes, event_summary: dict[str, Any]) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.add_patch(
        patches.FancyBboxPatch(
            (0.02, 0.12),
            0.34,
            0.76,
            boxstyle="round,pad=0.02",
            facecolor="#f7f7f7",
            edgecolor="0.75",
        )
    )
    ax.text(0.04, 0.85, "Refined thresholds", fontsize=10, fontweight="bold", va="top")
    for index, line in enumerate(REFINED_THRESHOLDS):
        ax.text(0.04, 0.80 - 0.09 * index, line, fontsize=7.8, va="top")

    node_specs = {
        "bulk_motion": (0.50, 0.76, 0.16, 0.10, "#f0f0f0"),
        "wall_sliding": (0.50, 0.54, 0.16, 0.10, "#e6e6e6"),
        "gate_approach": (0.72, 0.54, 0.16, 0.10, "#c6dbef"),
        "gate_residence_precommit": (0.72, 0.33, 0.18, 0.10, "#9ecae1"),
        "gate_commit": (0.90, 0.33, 0.12, 0.10, "#6baed6"),
        "gate_crossing": (0.90, 0.15, 0.12, 0.10, "#fdd0a2"),
        "trap_episode": (0.50, 0.15, 0.16, 0.10, "#fcbba1"),
    }
    for state, (x0, y0, width, height, color) in node_specs.items():
        count = int(event_summary["event_counts"].get(state, 0))
        frac = float(event_summary["state_fractions"].get(state, np.nan))
        if count >= 1000:
            stat_text = f"{frac * 100:.1f}% rows"
        else:
            stat_text = f"{count} rows"
        ax.add_patch(
            patches.FancyBboxPatch(
                (x0, y0),
                width,
                height,
                boxstyle="round,pad=0.02",
                facecolor=color,
                edgecolor="0.35",
            )
        )
        ax.text(x0 + width / 2, y0 + 0.065, STATE_DISPLAY[state], ha="center", va="center", fontsize=8.5, fontweight="bold")
        ax.text(x0 + width / 2, y0 + 0.025, stat_text, ha="center", va="center", fontsize=7.5)

    arrow_specs = [
        ((0.58, 0.54), (0.58, 0.66), ("bulk_motion", "wall_sliding"), "bulk -> wall"),
        ((0.66, 0.59), (0.72, 0.59), ("wall_sliding", "gate_approach"), "wall -> approach"),
        ((0.80, 0.51), (0.80, 0.43), ("gate_approach", "gate_residence_precommit"), "approach -> residence"),
        ((0.90, 0.38), (0.90, 0.38), ("gate_residence_precommit", "gate_commit"), "residence -> commit"),
        ((0.96, 0.31), (0.96, 0.25), ("gate_commit", "gate_crossing"), "commit -> crossing"),
        ((0.58, 0.24), (0.58, 0.24), ("trap_episode", "trap_escape"), "trap -> escape"),
    ]
    for start, end, key, label in arrow_specs:
        if key == ("gate_residence_precommit", "gate_commit"):
            ax.annotate("", xy=(0.90, 0.38), xytext=(0.84, 0.38), arrowprops={"arrowstyle": "->", "lw": 1.6, "color": "0.35"})
            text_x, text_y = 0.865, 0.41
        elif key == ("trap_episode", "trap_escape"):
            ax.annotate("", xy=(0.66, 0.20), xytext=(0.58, 0.20), arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#b30000"})
            text_x, text_y = 0.62, 0.23
        else:
            ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.6, "color": "0.35"})
            text_x = (start[0] + end[0]) / 2.0
            text_y = (start[1] + end[1]) / 2.0 + 0.03
        share = float(event_summary["transition_shares"].get(key, np.nan))
        share_text = f"{share * 100:.2f}%" if share >= 1e-3 else f"{share * 100:.4f}%"
        ax.text(
            text_x,
            text_y,
            f"{label}\n{share_text} exits",
            ha="center",
            va="bottom",
            fontsize=7.2,
            bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.85"},
        )
    search_share = event_summary["state_fractions"]["bulk_motion"] + event_summary["state_fractions"]["wall_sliding"]
    ax.text(
        0.50,
        0.04,
        f"Search-basin states (`bulk` + `wall`) occupy {search_share * 100:.1f}% of event rows; `commit -> crossing` stays sparse at {event_summary['transition_shares'][('gate_commit', 'gate_crossing')] * 100:.4f}% exits.",
        fontsize=8,
        ha="center",
    )


def draw_panel_b(ax: plt.Axes, trap_df: pd.DataFrame) -> None:
    ordered = trap_df.copy()
    ordered["label_short"] = ordered["canonical_label"].astype(str).map(short_label)
    y = np.arange(len(ordered))[::-1]
    ax.set_yticks(y)
    ax.set_yticklabels(ordered["label_short"])
    markers = [
        ("source_trap_time_mean", "source", "o", "#222222"),
        ("trajectory_episode_mean_from_totals", "trajectory episode mean", "s", "#3182bd"),
        ("event_duration_raw_mean", "raw event duration", "X", "#e6550d"),
        ("event_duration_aligned_mean", "aligned event duration", "D", "#31a354"),
    ]
    for offset_index, (column, label, marker, color) in enumerate(markers):
        ax.scatter(
            ordered[column],
            y + (offset_index - 1.5) * 0.06,
            s=48,
            marker=marker,
            color=color,
            edgecolors="black" if marker != "X" else "none",
            linewidths=0.5,
            label=label,
            zorder=3,
        )
    for row_y, (_, row) in zip(y, ordered.iterrows()):
        if float(row["n_trap_events"]) > 0:
            ax.plot(
                [float(row["event_duration_raw_mean"]), float(row["event_duration_aligned_mean"])],
                [row_y, row_y],
                color="#bdbdbd",
                linewidth=1.5,
                zorder=1,
            )
            ax.text(float(row["event_duration_aligned_mean"]) + 0.012, row_y, f"n={int(row['n_trap_events'])}", fontsize=8, va="center")
    ax.set_xlabel("trap duration")
    ax.grid(axis="x", alpha=0.22, linewidth=0.6)
    ax.set_xlim(-0.01, max(0.56, float(ordered["event_duration_aligned_mean"].max()) * 1.14))
    ax.legend(fontsize=7, loc="lower right", frameon=False)
    ax.text(
        0.02,
        0.96,
        "Aligned event duration and episode-conditioned totals coincide with the source metric; the raw event duration keeps only the post-confirmation tail.",
        transform=ax.transAxes,
        va="top",
        fontsize=7.6,
        bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.82"},
    )


def draw_panel_c(ax: plt.Axes, compare_df: pd.DataFrame) -> None:
    values, row_labels, col_labels, annotations = build_old_refined_matrix(compare_df)
    normalized = normalize_rows(values)
    image = ax.imshow(normalized, cmap="YlGnBu", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    for row_index in range(values.shape[0]):
        for col_index in range(values.shape[1]):
            ax.text(col_index, row_index, annotations[row_index][col_index], ha="center", va="center", fontsize=7.5)
    ax.text(
        0.02,
        -0.14,
        "Row-normalized color; values shown in each cell. The refined definitions shift timing slightly, sharpen precommit residence vs commit, and isolate a much smaller post-commit return fraction.",
        transform=ax.transAxes,
        fontsize=7.7,
        va="top",
    )
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.03, label="row-normalized magnitude")


def draw_panel_d(ax: plt.Axes, threshold_df: pd.DataFrame) -> None:
    ordered = threshold_df.copy()
    row_labels = [short_label(str(label)) for label in ordered["canonical_label"].astype(str)]
    columns = [
        "wall_sliding_near_alignment_threshold_share",
        "gate_capture_near_depth_threshold_share",
        "trap_episode_near_duration_threshold_share",
    ]
    col_labels = ["wall align", "capture depth", "trap duration"]
    values = ordered[columns].to_numpy(dtype=float)
    masked = np.ma.masked_invalid(values)
    cmap = plt.cm.Oranges.copy()
    cmap.set_bad("#f0f0f0")
    image = ax.imshow(masked, cmap=cmap, vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    for row_index in range(values.shape[0]):
        for col_index in range(values.shape[1]):
            value = values[row_index, col_index]
            text = "—" if not np.isfinite(value) else f"{value:.2f}"
            ax.text(col_index, row_index, text, ha="center", va="center", fontsize=8)
    ax.text(
        0.02,
        -0.14,
        "These shares report how much of each event class sits close to the operative threshold. Trap-duration values only appear where confirmed trap episodes exist.",
        transform=ax.transAxes,
        fontsize=7.7,
        va="top",
    )
    ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.03, label="near-threshold share")


def draw_panel_e(ax: plt.Axes, refined_summary_df: pd.DataFrame) -> None:
    rows = build_trusted_comparison_rows(refined_summary_df)
    y_positions = np.arange(len(rows))[::-1]
    ax.axvspan(0.0, 1.0, color="#f7f7f7", zorder=0)
    for y, row in zip(y_positions, rows):
        ax.plot([row["balanced_norm"], row["stale_norm"]], [y, y], color="0.65", linewidth=2.0, zorder=1)
        ax.scatter(row["balanced_norm"], y, color="#31a354", s=70, zorder=3, label="balanced ridge" if y == y_positions[0] else None)
        ax.scatter(row["stale_norm"], y, color="#de2d26", s=70, zorder=3, label="stale control" if y == y_positions[0] else None)
        ax.text(1.05, y, f"{format_value(row['balanced_value'])} -> {format_value(row['stale_value'])}", fontsize=8.3, va="center")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([row["label"] for row in rows])
    ax.set_xlim(0.0, 1.58)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_xticklabels(["min", "mid", "max"])
    ax.set_xlabel("position within canonical five-point range")
    ax.grid(axis="x", alpha=0.22, linewidth=0.6)
    ax.legend(fontsize=7.5, loc="lower right", frameon=False)
    ax.text(
        0.02,
        0.04,
        "Trusted observables are the pre-commit timing pair plus source-aligned trap burden. Values shown at right are balanced -> stale.",
        transform=ax.transAxes,
        fontsize=7.7,
        bbox={"facecolor": "white", "alpha": 0.90, "edgecolor": "0.82"},
    )


def draw_panel_f(ax: plt.Axes, conditioning_df: pd.DataFrame, refined_summary_df: pd.DataFrame) -> None:
    ax.set_axis_off()
    cond = conditioning_df[conditioning_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    cond = cond.set_index("canonical_label")
    refined = refined_summary_df[refined_summary_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    refined = refined.set_index("canonical_label")

    sections = [
        (
            "Audit-compatible capture-conditioned set",
            0.66,
            [
                ("capture_given_approach", "capture_given_approach"),
                ("return_to_wall_after_capture_rate", "return_to_wall_after_capture_rate"),
                ("crossing_given_capture", "crossing_given_capture"),
            ],
            cond,
        ),
        (
            "Refined gate-local set",
            0.30,
            [
                ("residence_given_approach", "residence_given_approach"),
                ("commit_given_residence", "commit_given_residence"),
                ("return_to_wall_after_commit_rate", "return_to_wall_after_commit_rate"),
                ("crossing_given_commit", "crossing_given_commit"),
            ],
            refined,
        ),
    ]

    for title, y0, rows, frame in sections:
        box_height = 0.26 if len(rows) <= 3 else 0.32
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.02, y0),
                0.96,
                box_height,
                boxstyle="round,pad=0.02",
                facecolor="#f7f7f7",
                edgecolor="0.82",
            )
        )
        ax.text(0.04, y0 + box_height - 0.03, title, fontsize=9.2, fontweight="bold", va="top")
        ax.text(0.62, y0 + box_height - 0.03, "ridge", fontsize=8, fontweight="bold", color="#31a354", va="top", ha="right")
        ax.text(0.82, y0 + box_height - 0.03, "stale", fontsize=8, fontweight="bold", color="#de2d26", va="top", ha="right")
        ax.text(0.95, y0 + box_height - 0.03, "delta", fontsize=8, fontweight="bold", color="0.35", va="top", ha="right")
        for index, (column, display) in enumerate(rows):
            y = y0 + box_height - 0.08 - index * 0.055
            ridge_value = float(frame.loc["OP_BALANCED_RIDGE_MID", column])
            stale_value = float(frame.loc["OP_STALE_CONTROL_OFF_RIDGE", column])
            ax.text(0.04, y, display, fontsize=8, va="center")
            ax.text(0.62, y, format_value(ridge_value), fontsize=8, va="center", ha="right")
            ax.text(0.82, y, format_value(stale_value), fontsize=8, va="center", ha="right")
            ax.text(0.95, y, format_value(stale_value - ridge_value), fontsize=8, va="center", ha="right")

    balanced_captures = int(cond.loc["OP_BALANCED_RIDGE_MID", "n_capture_events"])
    stale_captures = int(cond.loc["OP_STALE_CONTROL_OFF_RIDGE", "n_capture_events"])
    ax.text(
        0.02,
        0.06,
        f"Capture-conditioned rows use compatible proxy sets (`n_capture_events`: ridge {balanced_captures}, stale {stale_captures}), but crossing remains sparse in both the old and refined graphs. Keep these as secondary diagnostic quantities rather than leading mechanism variables.",
        fontsize=7.7,
        va="bottom",
    )


def build_figure(inputs: dict[str, Any]) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(16.5, 10.2))
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.08, top=0.88, wspace=0.34, hspace=0.40)
    axes = axes.flatten()

    draw_panel_a(axes[0], inputs["event_summary"])
    draw_panel_b(axes[1], inputs["trap"])
    draw_panel_c(axes[2], inputs["compare"])
    draw_panel_d(axes[3], inputs["threshold"])
    draw_panel_e(axes[4], inputs["refined"])
    draw_panel_f(axes[5], inputs["conditioning"], inputs["refined"])

    for ax, panel_letter in zip(axes, ["A", "B", "C", "D", "E", "F"]):
        annotate_panel(ax, panel_letter)
        ax.set_title(PANEL_TITLES[panel_letter], fontsize=12)

    fig.suptitle("Extended Data Figure 3. Mechanism Extraction, Audit Checks, and Threshold Sensitivity", fontsize=17, fontweight="bold")
    fig.text(
        0.5,
        0.93,
        "Audit-level robustness package for the pre-commit mechanism: thresholding, trap alignment, refined gate states, matched-pair audits, and cautionary proxy-conditioned observables. Post-commit crossing remains sparse and secondary.",
        ha="center",
        fontsize=10,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_manifest(inputs: dict[str, Any]) -> None:
    search_share = inputs["event_summary"]["state_fractions"]["bulk_motion"] + inputs["event_summary"]["state_fractions"]["wall_sliding"]
    crossing_share = inputs["event_summary"]["transition_shares"][("gate_commit", "gate_crossing")]
    lines = [
        "# Extended Data Figure 3 Panel Manifest",
        "",
        "## Scope",
        "",
        "This note documents the panel logic for Extended Data Figure 3, which validates the robustness of the mechanism package while keeping audit detail out of the main figures.",
        "",
        "Primary data sources:",
        "",
        f"- [mechanism_event_classification_note.md](file://{PROJECT_ROOT / 'docs' / 'mechanism_event_classification_note.md'})",
        f"- [mechanism_dataset_audit.md](file://{PROJECT_ROOT / 'docs' / 'mechanism_dataset_audit.md'})",
        f"- [mechanism_metric_alignment_note.md](file://{PROJECT_ROOT / 'docs' / 'mechanism_metric_alignment_note.md'})",
        f"- [gate_state_refinement_note.md](file://{PROJECT_ROOT / 'docs' / 'gate_state_refinement_note.md'})",
        f"- [mechanism_refined_run_report.md](file://{PROJECT_ROOT / 'docs' / 'mechanism_refined_run_report.md'})",
        f"- [threshold_sensitivity_summary.csv](file://{THRESHOLD_SENSITIVITY_PATH})",
        f"- [trap_metric_alignment.csv](file://{TRAP_ALIGNMENT_PATH})",
        f"- [conditioning_alignment.csv](file://{CONDITIONING_ALIGNMENT_PATH})",
        f"- [old_vs_refined_summary.csv](file://{OLD_REFINED_PATH})",
        f"- [refined_summary_by_point.csv](file://{REFINED_SUMMARY_PATH})",
        f"- [event_level.parquet](file://{EVENT_PATH})",
        f"- [ED Figure 3 PNG](file://{PNG_PATH})",
        f"- [ED Figure 3 SVG](file://{SVG_PATH})",
        "",
        "## Figure-Level Message",
        "",
        "- this figure exists to validate robustness of the mechanism package rather than to carry the main-text principle claim",
        "- the strongest audited observables remain pre-commit timing plus source-aligned trap burden",
        "- proxy-conditioned gate-local observables are shown explicitly, but kept separate from the trustworthy pre-commit layer",
        "- post-commit crossing remains sparse and is not promoted to the leading mechanism variable",
        "",
        "## Panel Logic",
        "",
        "### Panel A",
        "",
        "- title: `Event-classification thresholds and refined state graph`",
        "- purpose: summarize the refined threshold rules and the coarse event-graph occupancy / exit structure",
        f"- quantitative note: `bulk` plus `wall` occupy `{search_share * 100:.1f}%` of event rows, while `commit -> crossing` is only `{crossing_share * 100:.4f}%` of commit exits",
        "",
        "### Panel B",
        "",
        "- title: `Trap metric alignment: source-compatible and raw event durations`",
        "- purpose: show that source-compatible trap burden is recovered by aligned event durations and episode-conditioned trajectory totals, while raw event duration undercounts the trap episode",
        "- quantitative note: only the success tip and stale-control point carry nonzero trap episodes in the current canonical set",
        "",
        "### Panel C",
        "",
        "- title: `Old and refined gate-state definitions on the matched pair`",
        "- purpose: compare the original proxy capture state with the refined residence / commit split on the balanced ridge versus stale-control pair",
        "- quantitative note: the refined graph raises timing observables slightly but drives post-commit return fractions far below the old proxy capture return values",
        "",
        "### Panel D",
        "",
        "- title: `Threshold sensitivity of classifier-near event shares`",
        "- purpose: report how much of each classified event family sits close to the operative thresholds",
        "- quantitative note: wall-sliding near-threshold shares stay near `0.05`, gate-capture depth shares near `0.54`, and trap-duration shares appear only where confirmed traps exist",
        "",
        "### Panel E",
        "",
        "- title: `Trusted ridge-versus-stale observables in the refined audit`",
        "- purpose: isolate the robust matched-pair discriminators already promoted into the refined mechanism reading",
        "- quantitative note: the trusted layer is `first_gate_commit_delay`, `wall_dwell_before_first_commit`, and source-aligned `trap_burden_mean`",
        "",
        "### Panel F",
        "",
        "- title: `Proxy-conditioned gate-local observables and compatibility`",
        "- purpose: keep the compatible but weaker gate-local proxy observables visible without promoting them into the leading mechanism argument",
        "- quantitative note: crossing probabilities remain on the order of `1e-4` or smaller and therefore stay secondary",
        "",
        "## Trusted Versus Proxy-Conditioned Observables",
        "",
        "- trustworthy now: `first_gate_commit_delay`, `wall_dwell_before_first_commit`, and source-compatible `trap_burden_mean`",
        "- weaker or proxy-conditioned: `capture_given_approach`, `residence_given_approach`, `commit_given_residence`, `crossing_given_capture`, `crossing_given_commit`, and the return-to-wall fractions tied to those proxy states",
        "",
        "## Why this stays pre-commit",
        "",
        "- the figure keeps the decisive mechanism on the pre-commit side by separating trusted timing observables from sparse post-commit crossing quantities",
        "- post-commit crossing is shown mainly to justify why it is not the headline mechanism variable",
        "",
        "## Bottom Line",
        "",
        "Extended Data Figure 3 is the robustness layer behind the pre-commit mechanism package. It shows that the event classification, trap bookkeeping, refined gate-state split, and matched-pair audits are coherent enough to support the pre-commit reading while keeping proxy-conditioned and post-commit quantities explicitly secondary.",
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
    parser = argparse.ArgumentParser(description="Build Extended Data Figure 3: mechanism extraction, audit checks, and threshold sensitivity.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
