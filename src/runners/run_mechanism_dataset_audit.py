from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.runners.run_mechanism_dataset import add_event_alignment_columns, load_canonical_points, load_reference_scales

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_POINTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "canonical_operating_points.csv"
TRAJECTORY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset" / "trajectory_level.parquet"
EVENT_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset" / "event_level.parquet"
GATE_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset" / "gate_conditioned.parquet"
AUDIT_DOC_PATH = PROJECT_ROOT / "docs" / "mechanism_dataset_audit.md"
ALIGNMENT_NOTE_PATH = PROJECT_ROOT / "docs" / "mechanism_metric_alignment_note.md"
AUDIT_FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_audit"


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return math.nan
    return float(values.mean())


def ensure_aligned_event_columns() -> tuple[pd.DataFrame, list[str], float]:
    points = load_canonical_points()
    reference_scales = load_reference_scales()
    del reference_scales
    config = points[0].config
    trap_min_duration = 0.50 * (1.0 / config.Dr)
    event_df = pd.read_parquet(EVENT_PATH)
    changelog: list[str] = []
    required = {"t_start_aligned", "duration_aligned", "trap_confirmation_backshift"}
    if not required.issubset(event_df.columns):
        event_df = add_event_alignment_columns(
            event_df,
            dt=config.dt,
            trap_min_duration=trap_min_duration,
        )
        event_df.to_parquet(EVENT_PATH, index=False)
        changelog.append(
            "Updated `event_level.parquet` to add `t_start_aligned`, `duration_aligned`, "
            "and `trap_confirmation_backshift` for source-compatible trap aggregation."
        )
    return event_df, changelog, trap_min_duration


def build_trap_alignment_summary(
    canonical_df: pd.DataFrame,
    trajectory_df: pd.DataFrame,
    event_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for _, row in canonical_df.iterrows():
        label = str(row["canonical_label"])
        tg = trajectory_df[trajectory_df["canonical_label"] == label]
        eg = event_df[event_df["canonical_label"] == label]
        traps = eg[eg["event_type"] == "trap_episode"]
        rows.append(
            {
                "canonical_label": label,
                "source_trap_time_mean": float(row["trap_time_mean"]),
                "trajectory_mean_trap_time_total": float(tg["trap_time_total"].mean()),
                "trajectory_episode_mean_from_totals": (
                    float(tg["trap_time_total"].sum() / tg["n_trap_events"].sum())
                    if tg["n_trap_events"].sum() > 0
                    else 0.0
                ),
                "event_duration_raw_mean": _safe_mean(traps["duration"]) if not traps.empty else 0.0,
                "event_duration_aligned_mean": _safe_mean(traps["duration_aligned"]) if not traps.empty else 0.0,
                "n_trap_events": int(tg["n_trap_events"].sum()),
            }
        )
    return pd.DataFrame(rows)


def build_conditioning_summary(event_df: pd.DataFrame, gate_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for label, gg in gate_df.groupby("canonical_label"):
        captures = event_df[(event_df["canonical_label"] == label) & (event_df["event_type"] == "gate_capture")]
        exit_share = captures["exited_to_event_type"].value_counts(normalize=True) if not captures.empty else pd.Series(dtype=float)
        rows.append(
            {
                "canonical_label": str(label),
                "capture_given_approach": float(gg["capture_given_approach"].mean()),
                "crossing_given_capture": float(gg["crossing_given_capture"].mean()),
                "return_to_wall_after_capture_rate": float(gg["return_to_wall_after_capture_rate"].mean()),
                "capture_exit_to_bulk_motion": float(exit_share.get("bulk_motion", 0.0)),
                "capture_exit_to_gate_approach": float(exit_share.get("gate_approach", 0.0)),
                "capture_exit_to_wall_sliding": float(exit_share.get("wall_sliding", 0.0)),
                "capture_exit_to_gate_crossing": float(exit_share.get("gate_crossing", 0.0)),
                "n_capture_events": int(len(captures)),
            }
        )
    return pd.DataFrame(rows).sort_values("canonical_label").reset_index(drop=True)


def build_observable_summary(
    trajectory_df: pd.DataFrame,
    gate_df: pd.DataFrame,
) -> pd.DataFrame:
    traj_summary = (
        trajectory_df.groupby("canonical_label")
        .agg(
            success_probability=("success_flag", "mean"),
            phase_lag_navigation_mean=("phase_lag_navigation_mean", "mean"),
            phase_lag_steering_mean=("phase_lag_steering_mean", "mean"),
            alignment_at_gate_mean=("alignment_gate_mean", "mean"),
            alignment_on_wall_mean=("alignment_wall_mean", "mean"),
            gate_capture_delay=("gate_capture_delay", "mean"),
            wall_dwell_before_capture=("wall_dwell_before_first_capture", "mean"),
            trap_episode_count_mean=("n_trap_events", "mean"),
            trap_total_per_trajectory=("trap_time_total", "mean"),
        )
        .reset_index()
    )
    gate_summary = (
        gate_df.groupby("canonical_label")
        .agg(
            capture_given_approach=("capture_given_approach", "mean"),
            crossing_given_capture=("crossing_given_capture", "mean"),
            return_to_wall_after_capture_rate=("return_to_wall_after_capture_rate", "mean"),
        )
        .reset_index()
    )
    return traj_summary.merge(gate_summary, on="canonical_label", how="left").sort_values("canonical_label").reset_index(drop=True)


def make_figures(
    trap_alignment_df: pd.DataFrame,
    conditioning_df: pd.DataFrame,
    observable_df: pd.DataFrame,
) -> dict[str, str]:
    AUDIT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    trap_path = AUDIT_FIGURE_DIR / "trap_metric_alignment.png"
    capture_path = AUDIT_FIGURE_DIR / "capture_exit_partition.png"
    stale_path = AUDIT_FIGURE_DIR / "ridge_vs_stale_audit.png"

    ordered = trap_alignment_df.copy()
    ordered["label_short"] = ordered["canonical_label"].str.replace("OP_", "", regex=False)
    x = np.arange(len(ordered))
    width = 0.22

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - 1.5 * width, ordered["source_trap_time_mean"], width, label="source trap_time_mean")
    ax.bar(x - 0.5 * width, ordered["trajectory_mean_trap_time_total"], width, label="trajectory mean trap_time_total")
    ax.bar(x + 0.5 * width, ordered["event_duration_raw_mean"], width, label="event raw duration mean")
    ax.bar(x + 1.5 * width, ordered["event_duration_aligned_mean"], width, label="event aligned duration mean")
    ax.set_xticks(x)
    ax.set_xticklabels(ordered["label_short"], rotation=35)
    ax.set_ylabel("time")
    ax.set_title("Trap Metric Alignment")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(trap_path, dpi=200)
    plt.close(fig)

    cond = conditioning_df.copy()
    cond["label_short"] = cond["canonical_label"].str.replace("OP_", "", regex=False)
    fig, ax = plt.subplots(figsize=(11, 5))
    bottoms = np.zeros(len(cond))
    parts = [
        ("capture_exit_to_bulk_motion", "bulk_motion", "#9ecae1"),
        ("capture_exit_to_gate_approach", "gate_approach", "#6baed6"),
        ("capture_exit_to_wall_sliding", "wall_sliding", "#3182bd"),
        ("capture_exit_to_gate_crossing", "gate_crossing", "#08519c"),
    ]
    for column, label, color in parts:
        values = cond[column].to_numpy()
        ax.bar(cond["label_short"], values, bottom=bottoms, label=label, color=color)
        bottoms += values
    ax.set_ylim(0.0, 1.0)
    ax.set_title("Exit Partition After Gate Capture")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(capture_path, dpi=200)
    plt.close(fig)

    compare = observable_df[observable_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    compare["label_short"] = compare["canonical_label"].str.replace("OP_", "", regex=False)
    metrics = [
        "gate_capture_delay",
        "wall_dwell_before_capture",
        "trap_total_per_trajectory",
        "capture_given_approach",
        "return_to_wall_after_capture_rate",
        "phase_lag_steering_mean",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    for ax, column in zip(axes.ravel(), metrics):
        ax.bar(compare["label_short"], compare[column], color=["#74c476", "#fb6a4a"])
        ax.set_title(column)
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(stale_path, dpi=200)
    plt.close(fig)

    trap_csv = AUDIT_FIGURE_DIR / "trap_metric_alignment.csv"
    conditioning_csv = AUDIT_FIGURE_DIR / "conditioning_alignment.csv"
    observable_csv = AUDIT_FIGURE_DIR / "observable_summary.csv"
    trap_alignment_df.to_csv(trap_csv, index=False)
    conditioning_df.to_csv(conditioning_csv, index=False)
    observable_df.to_csv(observable_csv, index=False)

    return {
        "trap_figure": str(trap_path),
        "capture_figure": str(capture_path),
        "stale_figure": str(stale_path),
        "trap_csv": str(trap_csv),
        "conditioning_csv": str(conditioning_csv),
        "observable_csv": str(observable_csv),
    }


def write_alignment_note(
    *,
    trap_min_duration: float,
    dt: float,
    changelog: list[str],
) -> None:
    backshift = max(trap_min_duration - dt, 0.0)
    lines = [
        "# Mechanism Metric Alignment Note",
        "",
        "## Metric Definitions",
        "",
        "- `phase_lag_navigation_mean`: circular mean of `motion_angle - navigation_angle`, wrapped to `(-pi, pi]`; positive values mean the velocity direction is rotated counterclockwise relative to the local navigation field.",
        "- `phase_lag_steering_mean`: circular mean of `motion_angle - steering_angle`, where `steering_angle` is the delayed controller target `theta_star` when the delayed navigation gradient is resolved, and falls back to the local navigation angle otherwise.",
        "- `alignment_at_gate_mean`: mean of `u . n_gate` on gate-local rows; the doorway normal points inward through the shell doorway, so positive values indicate doorway-forward motion and values near `1` indicate strong forward alignment.",
        "- `alignment_on_wall_mean`: mean of `|u . t_wall|` on wall-sliding rows; it is an unsigned tangentiality measure, so it quantifies how strongly the motion follows the wall but does not preserve clockwise/counterclockwise direction.",
        "",
        "## Trap Alignment",
        "",
        "- Legacy/source `trap_time_mean` is a mean over confirmed trap episodes, not a mean over all trajectories.",
        "- `trajectory_level.parquet` already stores source-compatible total trap burden via `trap_time_total` and `n_trap_events`; use `sum(trap_time_total) / sum(n_trap_events)` when comparing to the canonical source trap metric.",
        "- `event_level.parquet` originally stored trap-row `duration` only from the confirmation step onward. The updated parquet now adds onset-aligned fields:",
        f"  - `trap_confirmation_backshift = {backshift:.4f}`",
        "  - `t_start_aligned`",
        "  - `duration_aligned`",
        "- Use `duration_aligned` for any event-level trap aggregation intended to match legacy/source trap durations.",
        "",
        "## Conditioning Compatibility",
        "",
        "- `gate_capture_probability` is computed as `capture_given_approach` on the current gate-local proxy state definitions.",
        "- `return_to_wall_after_capture_rate` is computed on the set of `gate_capture` rows only.",
        "- These conditioning sets are internally compatible with one another, but they are not yet equivalent to a clean doorway Markov chain because `gate_capture` behaves like a gate-mouth residence proxy while `gate_crossing` is a much stricter sign-change event.",
        "- For immediate interpretive use, treat `gate_capture_probability` and `return_to_wall_after_capture_rate` as proxy-conditioned observables rather than final gate-transition probabilities.",
        "",
        "## Changelog",
        "",
    ]
    if changelog:
        lines.extend(f"- {item}" for item in changelog)
    else:
        lines.append("- No parquet rewrite was needed during this audit.")
    ALIGNMENT_NOTE_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_audit_report(
    *,
    trap_alignment_df: pd.DataFrame,
    conditioning_df: pd.DataFrame,
    observable_df: pd.DataFrame,
    figure_paths: dict[str, str],
    changelog: list[str],
) -> None:
    balanced = observable_df[observable_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = observable_df[observable_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    trap_issue = trap_alignment_df[
        [
            "canonical_label",
            "source_trap_time_mean",
            "trajectory_mean_trap_time_total",
            "trajectory_episode_mean_from_totals",
            "event_duration_raw_mean",
            "event_duration_aligned_mean",
            "n_trap_events",
        ]
    ]
    lines = [
        "# Mechanism Dataset Audit",
        "",
        "## Scope",
        "",
        "This audit checks the built mechanism dataset against the canonical source semantics before any strong mechanism interpretation.",
        "",
        f"- canonical manifest: {_path_link(CANONICAL_POINTS_PATH)}",
        f"- trajectory dataset: {_path_link(TRAJECTORY_PATH)}",
        f"- event dataset: {_path_link(EVENT_PATH)}",
        f"- gate-conditioned dataset: {_path_link(GATE_PATH)}",
        f"- metric alignment note: {_path_link(ALIGNMENT_NOTE_PATH)}",
        "",
        "## Main Findings",
        "",
        "- The source/replay trap mismatch is primarily a definition mismatch plus confirmed-trap bookkeeping, not a physics replay failure.",
        "- Source `trap_time_mean` is an episode-conditioned mean. Comparing it to trajectory-mean `trap_time_total` artificially suppresses the replayed value by a factor of approximately the trap-event rarity.",
        "- The original event-table trap rows undercounted trap duration because `duration` started at confirmation rather than onset. This audit adds onset-aligned trap fields to `event_level.parquet`.",
        "- `phase_lag_navigation_mean`, `phase_lag_steering_mean`, and `alignment_at_gate_mean` use signed conventions; `alignment_on_wall_mean` is unsigned by construction.",
        "- `gate_capture_probability` and `return_to_wall_after_capture_rate` are internally compatible on their present proxy-conditioned sets, but they are not yet clean gate-transition probabilities because `gate_crossing` is extremely sparse relative to `gate_capture`.",
        "",
        "## Trap Metric Audit",
        "",
        trap_issue.to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        "- `trajectory_episode_mean_from_totals` matches the canonical source trap metric, which shows that the trajectory-level trap totals are already source-compatible.",
        "- `event_duration_raw_mean` is the bookkeeping mismatch: it captures only the post-confirmation tail of a trap episode.",
        "- `event_duration_aligned_mean` restores the source-compatible duration by adding the deterministic confirmation backshift.",
        "",
        "## Sign And Meaning Audit",
        "",
        "- `phase_lag_navigation_mean`: signed circular lag in radians relative to the navigation field; positive is counterclockwise relative to the navigation direction.",
        "- `phase_lag_steering_mean`: signed circular lag in radians relative to the delayed steering target; same sign convention.",
        "- `alignment_at_gate_mean`: signed cosine-like gate-forward alignment; positive means inward through-door motion.",
        "- `alignment_on_wall_mean`: unsigned wall tangentiality in `[0, 1]`; it cannot distinguish opposite circulation senses.",
        "",
        "## Conditioning Audit",
        "",
        conditioning_df.to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        "- `capture_given_approach` and `return_to_wall_after_capture_rate` are computed on compatible current gate-proxy states.",
        "- The large bulk-motion and wall-sliding exit fractions, together with the tiny `crossing_given_capture`, show that current `gate_capture` is best treated as gate-mouth residence rather than a committed shell-transition state.",
        "",
        "## Which current observables are trustworthy enough for gate theory, and which need caution?",
        "",
        "- Trustworthy now: success probability, source-compatible trap burden from `trap_time_total` and `n_trap_events`, wall-contact fraction from the replay, first-capture delay as a gate-proxy timing observable, and wall dwell before first capture as a pre-capture residence observable.",
        "- Use with caution: `phase_lag_navigation_mean` and `phase_lag_steering_mean` are well-defined but currently weak ridge-vs-stale discriminators because their point-level means stay close to zero.",
        "- Use with caution: `alignment_at_gate_mean` is interpretable, but only on the current gate-local proxy conditioning set.",
        "- Use with caution: `alignment_on_wall_mean` is robust as tangentiality magnitude, but not as a directional wall-circulation observable because the sign is discarded.",
        "- Not yet trustworthy as final gate-theory rates: `gate_capture_probability`, `crossing_given_capture`, and `return_to_wall_after_capture_rate` because the present `gate_capture`/`gate_crossing` pair does not yet form a clean transition chain.",
        "",
        "## Can the stale-control point already be distinguished mechanistically with confidence?",
        "",
        f"- Not with high confidence from the current gate-local proxy metrics alone. `capture_given_approach` is {balanced['capture_given_approach']:.4f} for the balanced ridge point and {stale['capture_given_approach']:.4f} for the stale-control point, while `return_to_wall_after_capture_rate` is {balanced['return_to_wall_after_capture_rate']:.4f} vs {stale['return_to_wall_after_capture_rate']:.4f}; these are too close for a strong mechanistic separation.",
        f"- The stale-control point does show a somewhat larger first-capture delay ({stale['gate_capture_delay']:.4f} vs {balanced['gate_capture_delay']:.4f}) and wall dwell before capture ({stale['wall_dwell_before_capture']:.4f} vs {balanced['wall_dwell_before_capture']:.4f}), but the differences are moderate rather than decisive.",
        f"- Trap burden is suggestive but sparse: the balanced ridge point has mean trap burden {balanced['trap_total_per_trajectory']:.6f}, while the stale-control point has {stale['trap_total_per_trajectory']:.6f}. This supports cautionary qualitative separation, not yet a strong quantitative mechanism claim.",
        "",
        "## Changelog",
        "",
    ]
    if changelog:
        lines.extend(f"- {item}" for item in changelog)
    else:
        lines.append("- No parquet files required modification during this audit.")
    lines.extend(
        [
            "",
            "## Audit Outputs",
            "",
            f"- {_path_link(figure_paths['trap_figure'])}",
            f"- {_path_link(figure_paths['capture_figure'])}",
            f"- {_path_link(figure_paths['stale_figure'])}",
            f"- {_path_link(figure_paths['trap_csv'])}",
            f"- {_path_link(figure_paths['conditioning_csv'])}",
            f"- {_path_link(figure_paths['observable_csv'])}",
        ]
    )
    AUDIT_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def run_audit() -> dict[str, str]:
    canonical_df = pd.read_csv(CANONICAL_POINTS_PATH)
    trajectory_df = pd.read_parquet(TRAJECTORY_PATH)
    gate_df = pd.read_parquet(GATE_PATH)
    event_df, changelog, trap_min_duration = ensure_aligned_event_columns()

    trap_alignment_df = build_trap_alignment_summary(canonical_df, trajectory_df, event_df)
    conditioning_df = build_conditioning_summary(event_df, gate_df)
    observable_df = build_observable_summary(trajectory_df, gate_df)
    figure_paths = make_figures(trap_alignment_df, conditioning_df, observable_df)

    dt = load_canonical_points()[0].config.dt
    write_alignment_note(
        trap_min_duration=trap_min_duration,
        dt=dt,
        changelog=changelog,
    )
    write_audit_report(
        trap_alignment_df=trap_alignment_df,
        conditioning_df=conditioning_df,
        observable_df=observable_df,
        figure_paths=figure_paths,
        changelog=changelog,
    )
    return {
        "audit_doc": str(AUDIT_DOC_PATH),
        "alignment_note": str(ALIGNMENT_NOTE_PATH),
        "audit_figure_dir": str(AUDIT_FIGURE_DIR),
        "event_parquet": str(EVENT_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit and align the mechanism dataset for interpretive use.")
    parser.parse_args(argv)
    result = run_audit()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
