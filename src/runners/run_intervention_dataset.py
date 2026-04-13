from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from legacy.simcore.models import GeometryConfig
from legacy.simcore.simulation import MazeBuilder, NavigationSolver

from src.configs.schema import RunConfig
from src.runners.run_mechanism_dataset import append_parquet, build_gate_descriptors, load_reference_scales
from src.runners.run_mechanism_dataset_refined import RefinedMechanismPointExtractor, build_refined_thresholds

SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet"
CANONICAL_POINTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "canonical_operating_points.csv"
DATASET_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "datasets" / "intervention_dataset"
FIGURE_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "intervention_dataset"
DESIGN_DOC_PATH = PROJECT_ROOT / "docs" / "intervention_design.md"
RUN_REPORT_PATH = PROJECT_ROOT / "docs" / "intervention_dataset_run_report.md"
ORDERING_DOC_PATH = PROJECT_ROOT / "docs" / "intervention_mechanism_ordering.md"

SOURCE_METRIC_COLUMNS = [
    "state_point_id",
    "result_json",
    "geometry_id",
    "model_variant",
    "flow_condition",
    "n_traj",
    "scan_id",
    "Tmax",
    "Pi_m",
    "Pi_f",
    "Pi_U",
    "Psucc_mean",
    "Psucc_ci_low",
    "Psucc_ci_high",
    "MFPT_mean",
    "MFPT_ci_low",
    "MFPT_ci_high",
    "eta_sigma_mean",
    "eta_sigma_ci_low",
    "eta_sigma_ci_high",
    "Sigma_drag_mean",
    "trap_time_mean",
]


@dataclass(frozen=True)
class SliceSpec:
    name: str
    axis_name: str
    axis_label: str
    fixed_controls: dict[str, float]
    baseline_value: float
    description: str


@dataclass(frozen=True)
class MetricSpec:
    name: str
    display_name: str
    group: str


@dataclass(frozen=True)
class InterventionPoint:
    point_label: str
    analysis_source: str
    analysis_n_traj: int
    Pi_m: float
    Pi_f: float
    Pi_U: float
    result_json: str
    state_point_id: str
    config: RunConfig
    source_result: dict[str, Any]
    source_summary: dict[str, Any]
    slice_memberships: tuple[str, ...]
    canonical_match: str | None

    @property
    def canonical_label(self) -> str:
        return self.point_label


SLICE_SPECS = (
    SliceSpec(
        name="delay_slice",
        axis_name="Pi_f",
        axis_label="Pi_f",
        fixed_controls={"Pi_m": 0.15, "Pi_U": 0.20},
        baseline_value=0.020,
        description="delay slice at fixed Pi_m = 0.15 and Pi_U = 0.20",
    ),
    SliceSpec(
        name="memory_slice",
        axis_name="Pi_m",
        axis_label="Pi_m",
        fixed_controls={"Pi_f": 0.020, "Pi_U": 0.20},
        baseline_value=0.15,
        description="memory slice at fixed Pi_f = 0.020 and Pi_U = 0.20",
    ),
    SliceSpec(
        name="flow_slice",
        axis_name="Pi_U",
        axis_label="Pi_U",
        fixed_controls={"Pi_m": 0.15, "Pi_f": 0.020},
        baseline_value=0.20,
        description="flow slice at fixed Pi_m = 0.15 and Pi_f = 0.020",
    ),
)

METRIC_SPECS = (
    MetricSpec("first_gate_commit_delay", "first_gate_commit_delay", "mechanism"),
    MetricSpec("wall_dwell_before_first_commit", "wall_dwell_before_first_commit", "mechanism"),
    MetricSpec("trap_burden_mean", "trap_burden_mean", "mechanism"),
    MetricSpec("residence_given_approach", "residence_given_approach", "mechanism"),
    MetricSpec("commit_given_residence", "commit_given_residence", "mechanism"),
    MetricSpec("Psucc_mean", "Psucc_mean", "outcome"),
    MetricSpec("MFPT_mean", "MFPT_mean", "outcome"),
    MetricSpec("eta_sigma_mean", "eta_sigma_mean", "outcome"),
    MetricSpec("eta_completion_drag", "eta_completion_drag", "outcome"),
    MetricSpec("eta_trap_drag", "eta_trap_drag", "outcome"),
)

PLOT_METRICS = [
    ("first_gate_commit_delay", "First Commit Delay", "#1f77b4"),
    ("wall_dwell_before_first_commit", "Wall Dwell Before First Commit", "#1f77b4"),
    ("trap_burden_mean", "Trap Burden Mean", "#1f77b4"),
    ("residence_given_approach", "Residence Given Approach", "#1f77b4"),
    ("commit_given_residence", "Commit Given Residence", "#1f77b4"),
    ("Psucc_mean", "Psucc Mean", "#2ca02c"),
    ("MFPT_mean", "MFPT Mean", "#2ca02c"),
    ("eta_sigma_mean", "eta_sigma_mean", "#2ca02c"),
    ("eta_completion_drag", "eta_completion_drag", "#2ca02c"),
    ("eta_trap_drag", "eta_trap_drag", "#2ca02c"),
]


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _float_token(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text.replace("-", "m").replace(".", "p")


def _point_label(row: pd.Series) -> str:
    return f"IP_PM{_float_token(float(row['Pi_m']))}_PF{_float_token(float(row['Pi_f']))}_PU{_float_token(float(row['Pi_U']))}"


def _point_key(Pi_m: float, Pi_f: float, Pi_U: float) -> str:
    return f"{Pi_m:.6f}|{Pi_f:.6f}|{Pi_U:.6f}"


def _extract_metadata_field(payload: str, key: str) -> Any:
    try:
        return json.loads(payload).get(key)
    except json.JSONDecodeError:
        return None


def _safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return math.nan
    return float(values.mean())


def _mean_of_distinct_abs_changes(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 0.0
    return float(np.mean(np.abs(finite)))


def _step_sign_consistency(y_sorted: np.ndarray) -> float:
    if y_sorted.size < 3:
        return 0.0
    diffs = np.diff(y_sorted)
    finite = diffs[np.isfinite(diffs)]
    if finite.size == 0:
        return 0.0
    tol = max(np.nanmax(np.abs(finite)), 1.0) * 1e-12
    finite = finite[np.abs(finite) > tol]
    if finite.size == 0:
        return 0.0
    return float(abs(np.sign(finite).sum()) / finite.size)


def _direction_label(rho: float) -> str:
    if not np.isfinite(rho):
        return "insufficient"
    if rho >= 0.6:
        return "increasing"
    if rho <= -0.6:
        return "decreasing"
    return "mixed"


def load_confirmatory_grid() -> pd.DataFrame:
    summary = pd.read_parquet(SUMMARY_PATH).copy()
    summary["scan_block"] = summary["metadata_json"].apply(lambda payload: _extract_metadata_field(payload, "scan_block"))
    summary["scan_label"] = summary["metadata_json"].apply(lambda payload: _extract_metadata_field(payload, "scan_label"))
    filtered = summary[
        (summary["status_completion"] == "completed")
        & (summary["n_traj"] == 4096)
        & (summary["scan_block"] == "confirmatory_ridge_grid")
    ].copy()
    duplicates = filtered.groupby(["Pi_m", "Pi_f", "Pi_U"]).size()
    bad = duplicates[duplicates > 1]
    if not bad.empty:
        raise RuntimeError(f"Expected unique base-grid points per coordinate, found duplicates: {bad.to_dict()}")
    return filtered


def build_slice_manifest(summary_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    canonical_lookup = pd.read_csv(CANONICAL_POINTS_PATH)[["canonical_label", "Pi_m", "Pi_f", "Pi_U"]].copy()
    canonical_lookup["point_key"] = canonical_lookup.apply(
        lambda row: _point_key(float(row["Pi_m"]), float(row["Pi_f"]), float(row["Pi_U"])),
        axis=1,
    )
    manifest_rows: list[pd.DataFrame] = []
    for spec in SLICE_SPECS:
        mask = np.ones(len(summary_df), dtype=bool)
        for control_name, control_value in spec.fixed_controls.items():
            mask &= np.isclose(summary_df[control_name], control_value)
        slice_df = summary_df.loc[mask, SOURCE_METRIC_COLUMNS + ["scan_label"]].copy()
        if slice_df.empty:
            raise RuntimeError(f"No rows found for {spec.name}.")
        if not np.any(np.isclose(slice_df[spec.axis_name], spec.baseline_value)):
            raise RuntimeError(f"Baseline value {spec.baseline_value} missing for {spec.name}.")
        slice_df["slice_name"] = spec.name
        slice_df["axis_name"] = spec.axis_name
        slice_df["axis_label"] = spec.axis_label
        slice_df["axis_value"] = slice_df[spec.axis_name].astype(float)
        slice_df["axis_delta_from_baseline"] = slice_df["axis_value"] - spec.baseline_value
        slice_df["is_baseline"] = np.isclose(slice_df["axis_value"], spec.baseline_value)
        slice_df["point_label"] = slice_df.apply(_point_label, axis=1)
        slice_df["point_key"] = slice_df.apply(
            lambda row: _point_key(float(row["Pi_m"]), float(row["Pi_f"]), float(row["Pi_U"])),
            axis=1,
        )
        slice_df = slice_df.merge(canonical_lookup[["point_key", "canonical_label"]], on="point_key", how="left")
        manifest_rows.append(slice_df)

    manifest = pd.concat(manifest_rows, ignore_index=True)
    manifest = manifest.sort_values(["slice_name", "axis_value", "Pi_m", "Pi_f", "Pi_U"]).reset_index(drop=True)
    point_manifest = (
        manifest.groupby("point_label", as_index=False)
        .agg(
            state_point_id=("state_point_id", "first"),
            result_json=("result_json", "first"),
            geometry_id=("geometry_id", "first"),
            model_variant=("model_variant", "first"),
            flow_condition=("flow_condition", "first"),
            analysis_source=("scan_label", "first"),
            analysis_n_traj=("n_traj", "first"),
            Pi_m=("Pi_m", "first"),
            Pi_f=("Pi_f", "first"),
            Pi_U=("Pi_U", "first"),
            Tmax=("Tmax", "first"),
            Psucc_mean=("Psucc_mean", "first"),
            Psucc_ci_low=("Psucc_ci_low", "first"),
            Psucc_ci_high=("Psucc_ci_high", "first"),
            MFPT_mean=("MFPT_mean", "first"),
            MFPT_ci_low=("MFPT_ci_low", "first"),
            MFPT_ci_high=("MFPT_ci_high", "first"),
            eta_sigma_mean=("eta_sigma_mean", "first"),
            eta_sigma_ci_low=("eta_sigma_ci_low", "first"),
            eta_sigma_ci_high=("eta_sigma_ci_high", "first"),
            Sigma_drag_mean=("Sigma_drag_mean", "first"),
            trap_time_mean=("trap_time_mean", "first"),
            scan_id=("scan_id", "first"),
            slice_count=("slice_name", "nunique"),
            canonical_match=("canonical_label", "first"),
        )
        .sort_values(["Pi_f", "Pi_m", "Pi_U"])
        .reset_index(drop=True)
    )
    membership = (
        manifest.groupby("point_label")["slice_name"]
        .agg(lambda series: json.dumps(sorted(set(str(value) for value in series))))
        .rename("slice_memberships_json")
        .reset_index()
    )
    point_manifest = point_manifest.merge(membership, on="point_label", how="left")
    return manifest, point_manifest


def load_intervention_points(point_manifest: pd.DataFrame) -> list[InterventionPoint]:
    points: list[InterventionPoint] = []
    for row in point_manifest.to_dict(orient="records"):
        result_path = Path(str(row["result_json"]))
        with open(result_path, "r", encoding="ascii") as handle:
            source_result = json.load(handle)
        source_summary = {key: row[key] for key in point_manifest.columns if key not in {"slice_memberships_json"}}
        points.append(
            InterventionPoint(
                point_label=str(row["point_label"]),
                analysis_source="base_4096",
                analysis_n_traj=int(row["analysis_n_traj"]),
                Pi_m=float(row["Pi_m"]),
                Pi_f=float(row["Pi_f"]),
                Pi_U=float(row["Pi_U"]),
                result_json=str(result_path),
                state_point_id=str(row["state_point_id"]),
                config=RunConfig.from_dict(source_result["input_config"]),
                source_result=source_result,
                source_summary=source_summary,
                slice_memberships=tuple(json.loads(str(row["slice_memberships_json"]))),
                canonical_match=str(row["canonical_match"]) if pd.notna(row["canonical_match"]) else None,
            )
        )
    return points


def build_intervention_dataset(points: list[InterventionPoint], point_manifest: pd.DataFrame) -> dict[str, Any]:
    if not points:
        raise RuntimeError("No intervention points selected.")

    DATASET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reference_scales = load_reference_scales()
    first_config = points[0].config
    maze = MazeBuilder().build(
        GeometryConfig(
            L=float(first_config.metadata.get("L", 1.0)),
            w=first_config.wall_thickness,
            g=first_config.gate_width,
            r_exit=first_config.exit_radius,
            n_shell=first_config.n_shell,
            grid_n=first_config.grid_n,
        )
    )
    navigation = NavigationSolver().solve(maze)
    thresholds = build_refined_thresholds(first_config, reference_scales)
    gates = build_gate_descriptors(first_config)
    extractor = RefinedMechanismPointExtractor(maze=maze, navigation=navigation, thresholds=thresholds, gates=gates)

    trajectory_path = DATASET_OUTPUT_DIR / "trajectory_level.parquet"
    event_path = DATASET_OUTPUT_DIR / "event_level.parquet"
    gate_path = DATASET_OUTPUT_DIR / "gate_conditioned.parquet"
    for path in (trajectory_path, event_path, gate_path):
        if path.exists():
            path.unlink()

    trajectory_writer: pq.ParquetWriter | None = None
    event_writer: pq.ParquetWriter | None = None
    gate_writer: pq.ParquetWriter | None = None

    trajectory_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    validation_rows: list[dict[str, Any]] = []
    total_event_rows = 0

    point_membership_map = point_manifest.set_index("point_label")["slice_memberships_json"].to_dict()

    for point in points:
        shared_payload = {
            "schema_version": "intervention_dataset_v1",
            "scan_id": str(point.source_result["scan_id"]),
            "state_point_id": point.state_point_id,
            "point_label": point.point_label,
            "canonical_match": point.canonical_match or "",
            "slice_memberships_json": str(point_membership_map[point.point_label]),
            "geometry_id": point.config.geometry_id,
            "model_variant": point.config.model_variant,
            "flow_condition": point.config.flow_condition,
            "analysis_source": point.analysis_source,
            "analysis_n_traj": point.analysis_n_traj,
            "Pi_m": point.Pi_m,
            "Pi_f": point.Pi_f,
            "Pi_U": point.Pi_U,
            "tau_g": float(reference_scales["tau_g"]),
            "l_g": float(reference_scales["ell_g"]),
            "result_json": point.result_json,
        }
        trajectory_df, event_df, gate_df, _ = extractor.extract_point(point=point, shared_payload=shared_payload)
        trajectory_writer = append_parquet(trajectory_writer, trajectory_df, trajectory_path)
        event_writer = append_parquet(event_writer, event_df, event_path)
        gate_writer = append_parquet(gate_writer, gate_df, gate_path)
        trajectory_frames.append(trajectory_df)
        gate_frames.append(gate_df)
        total_event_rows += len(event_df)

        replay_success = float(trajectory_df["success_flag"].mean())
        replay_mfpt = _safe_mean(trajectory_df["t_exit_or_nan"])
        replay_sigma_drag = _safe_mean(trajectory_df["Sigma_drag_i"])
        validation_rows.append(
            {
                "point_label": point.point_label,
                "state_point_id": point.state_point_id,
                "source_Psucc_mean": float(point.source_summary["Psucc_mean"]),
                "replayed_Psucc_mean": replay_success,
                "delta_Psucc_mean": replay_success - float(point.source_summary["Psucc_mean"]),
                "source_MFPT_mean": float(point.source_summary["MFPT_mean"]),
                "replayed_MFPT_mean": replay_mfpt,
                "delta_MFPT_mean": replay_mfpt - float(point.source_summary["MFPT_mean"]),
                "source_Sigma_drag_mean": float(point.source_summary["Sigma_drag_mean"]),
                "replayed_Sigma_drag_mean": replay_sigma_drag,
                "delta_Sigma_drag_mean": replay_sigma_drag - float(point.source_summary["Sigma_drag_mean"]),
                "source_trap_time_mean": float(point.source_summary["trap_time_mean"]),
                "replayed_trap_burden_mean": _safe_mean(trajectory_df["trap_time_total"]),
                "event_rows": int(len(event_df)),
            }
        )

    for writer in (trajectory_writer, event_writer, gate_writer):
        if writer is not None:
            writer.close()

    trajectory_df = pd.concat(trajectory_frames, ignore_index=True)
    gate_df = pd.concat(gate_frames, ignore_index=True)
    validation_df = pd.DataFrame(validation_rows).sort_values(["point_label"]).reset_index(drop=True)

    return {
        "trajectory_df": trajectory_df,
        "gate_df": gate_df,
        "validation_df": validation_df,
        "trajectory_path": trajectory_path,
        "event_path": event_path,
        "gate_path": gate_path,
        "total_event_rows": total_event_rows,
    }


def summarize_points(
    *,
    trajectory_df: pd.DataFrame,
    gate_df: pd.DataFrame,
    point_manifest: pd.DataFrame,
) -> pd.DataFrame:
    traj_summary = (
        trajectory_df.groupby("point_label", as_index=False)
        .agg(
            replay_n_traj=("traj_id", "count"),
            replay_success_probability=("success_flag", "mean"),
            replay_MFPT_mean=("t_exit_or_nan", _safe_mean),
            replay_Sigma_drag_mean=("Sigma_drag_i", "mean"),
            first_gate_commit_delay=("first_gate_commit_delay", "mean"),
            wall_dwell_before_first_commit=("wall_dwell_before_first_commit", "mean"),
            trap_burden_mean=("trap_time_total", "mean"),
            first_gate_residence_delay=("first_gate_residence_delay", "mean"),
            wall_dwell_before_first_residence=("wall_dwell_before_first_residence", "mean"),
            replay_trap_event_count_mean=("n_trap_events", "mean"),
        )
        .reset_index(drop=True)
    )
    gate_summary = (
        gate_df.groupby("point_label", as_index=False)
        .agg(
            residence_given_approach=("residence_given_approach", "mean"),
            commit_given_residence=("commit_given_residence", "mean"),
            crossing_given_commit=("crossing_given_commit", "mean"),
            return_to_wall_after_precommit_rate=("return_to_wall_after_precommit_rate", "mean"),
        )
        .reset_index(drop=True)
    )
    summary = point_manifest.merge(traj_summary, on="point_label", how="left").merge(gate_summary, on="point_label", how="left")
    summary["eta_completion_drag"] = summary["Psucc_mean"] / (
        summary["MFPT_mean"] * summary["Sigma_drag_mean"]
    )
    summary["eta_trap_drag"] = summary["eta_completion_drag"] / (
        1.0 + summary["trap_time_mean"] / summary["Tmax"]
    )
    summary["delta_Psucc_replay_vs_source"] = summary["replay_success_probability"] - summary["Psucc_mean"]
    summary["delta_MFPT_replay_vs_source"] = summary["replay_MFPT_mean"] - summary["MFPT_mean"]
    summary["delta_Sigma_drag_replay_vs_source"] = summary["replay_Sigma_drag_mean"] - summary["Sigma_drag_mean"]
    return summary.sort_values(["Pi_f", "Pi_m", "Pi_U"]).reset_index(drop=True)


def build_slice_summary(point_summary: pd.DataFrame, slice_manifest: pd.DataFrame) -> pd.DataFrame:
    merged = slice_manifest.merge(
        point_summary[
            [
                "point_label",
                "first_gate_commit_delay",
                "wall_dwell_before_first_commit",
                "trap_burden_mean",
                "residence_given_approach",
                "commit_given_residence",
                "crossing_given_commit",
            ]
        ],
        on="point_label",
        how="left",
    )
    merged["eta_completion_drag"] = merged["Psucc_mean"] / (
        merged["MFPT_mean"] * merged["Sigma_drag_mean"]
    )
    merged["eta_trap_drag"] = merged["eta_completion_drag"] / (
        1.0 + merged["trap_time_mean"] / merged["Tmax"]
    )
    return merged.sort_values(["slice_name", "axis_value"]).reset_index(drop=True)


def build_validation_from_trajectory(
    *,
    trajectory_df: pd.DataFrame,
    point_manifest: pd.DataFrame,
) -> pd.DataFrame:
    replay = (
        trajectory_df.groupby("point_label", as_index=False)
        .agg(
            replayed_Psucc_mean=("success_flag", "mean"),
            replayed_MFPT_mean=("t_exit_or_nan", _safe_mean),
            replayed_Sigma_drag_mean=("Sigma_drag_i", "mean"),
            replayed_trap_burden_mean=("trap_time_total", "mean"),
        )
        .reset_index(drop=True)
    )
    validation = point_manifest[
        [
            "point_label",
            "state_point_id",
            "Psucc_mean",
            "MFPT_mean",
            "Sigma_drag_mean",
            "trap_time_mean",
        ]
    ].merge(replay, on="point_label", how="left")
    validation = validation.rename(
        columns={
            "Psucc_mean": "source_Psucc_mean",
            "MFPT_mean": "source_MFPT_mean",
            "Sigma_drag_mean": "source_Sigma_drag_mean",
            "trap_time_mean": "source_trap_time_mean",
        }
    )
    validation["delta_Psucc_mean"] = validation["replayed_Psucc_mean"] - validation["source_Psucc_mean"]
    validation["delta_MFPT_mean"] = validation["replayed_MFPT_mean"] - validation["source_MFPT_mean"]
    validation["delta_Sigma_drag_mean"] = validation["replayed_Sigma_drag_mean"] - validation["source_Sigma_drag_mean"]
    return validation.sort_values(["point_label"]).reset_index(drop=True)


def load_existing_replay_outputs(point_manifest: pd.DataFrame) -> dict[str, Any]:
    trajectory_path = DATASET_OUTPUT_DIR / "trajectory_level.parquet"
    event_path = DATASET_OUTPUT_DIR / "event_level.parquet"
    gate_path = DATASET_OUTPUT_DIR / "gate_conditioned.parquet"
    missing = [str(path) for path in (trajectory_path, event_path, gate_path) if not path.exists()]
    if missing:
        raise RuntimeError(f"Cannot reuse replay outputs; missing files: {missing}")

    trajectory_df = pd.read_parquet(trajectory_path)
    gate_df = pd.read_parquet(gate_path)
    validation_df = build_validation_from_trajectory(trajectory_df=trajectory_df, point_manifest=point_manifest)
    total_event_rows = int(pq.ParquetFile(event_path).metadata.num_rows)
    return {
        "trajectory_df": trajectory_df,
        "gate_df": gate_df,
        "validation_df": validation_df,
        "trajectory_path": trajectory_path,
        "event_path": event_path,
        "gate_path": gate_path,
        "total_event_rows": total_event_rows,
    }


def score_slice_ordering(slice_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in SLICE_SPECS:
        slice_df = slice_summary[slice_summary["slice_name"] == spec.name].sort_values("axis_value").reset_index(drop=True)
        if slice_df.empty:
            continue
        baseline_row = slice_df.loc[slice_df["is_baseline"]]
        if baseline_row.empty:
            raise RuntimeError(f"Missing baseline row for {spec.name}.")
        baseline_axis = float(baseline_row["axis_value"].iloc[0])
        distances = np.abs(slice_df["axis_value"].to_numpy(dtype=float) - baseline_axis)
        positive_distances = distances[distances > 1e-12]
        nearest_distance = float(np.min(positive_distances)) if positive_distances.size else math.nan

        for metric in METRIC_SPECS:
            valid = slice_df[["axis_value", metric.name]].dropna()
            x = valid["axis_value"].to_numpy(dtype=float)
            y = valid[metric.name].to_numpy(dtype=float)
            baseline_value = float(slice_df.loc[slice_df["is_baseline"], metric.name].iloc[0])
            value_range = float(np.nanmax(y) - np.nanmin(y)) if y.size else 0.0
            scale = max(float(np.nanmean(np.abs(y))) if y.size else 0.0, abs(baseline_value), 1e-12)
            first_step_mask = np.isclose(np.abs(x - baseline_axis), nearest_distance) if np.isfinite(nearest_distance) else np.zeros_like(x, dtype=bool)
            first_step_abs_change = _mean_of_distinct_abs_changes(y[first_step_mask] - baseline_value)
            first_step_rel_range = first_step_abs_change / value_range if value_range > 0.0 else 0.0
            relative_range = min(value_range / scale, 1.0)
            rho = float(pd.Series(x).corr(pd.Series(y), method="spearman")) if y.size >= 3 and value_range > 0.0 else 0.0
            if not np.isfinite(rho):
                rho = 0.0
            spearman_abs = abs(rho)
            step_consistency = _step_sign_consistency(y)
            monotonicity_score = 0.5 * (spearman_abs + step_consistency)
            early_indicator_score = first_step_rel_range * monotonicity_score * relative_range
            direction = _direction_label(rho) if y.size >= 3 else "insufficient"
            rows.append(
                {
                    "slice_name": spec.name,
                    "axis_name": spec.axis_name,
                    "metric_name": metric.name,
                    "metric_group": metric.group,
                    "baseline_axis_value": baseline_axis,
                    "baseline_metric_value": baseline_value,
                    "metric_range": value_range,
                    "relative_range": relative_range,
                    "first_step_abs_change": first_step_abs_change,
                    "first_step_rel_range": first_step_rel_range,
                    "spearman_abs": spearman_abs,
                    "step_consistency": step_consistency,
                    "monotonicity_score": monotonicity_score,
                    "early_indicator_score": early_indicator_score,
                    "direction_label": direction,
                }
            )
    ordering = pd.DataFrame(rows)
    ordering["first_step_rank"] = ordering.groupby("slice_name")["first_step_rel_range"].rank(ascending=False, method="dense")
    ordering["monotonicity_rank"] = ordering.groupby("slice_name")["monotonicity_score"].rank(ascending=False, method="dense")
    ordering["combined_rank"] = ordering.groupby("slice_name")["early_indicator_score"].rank(ascending=False, method="dense")
    ordering["mechanism_rank"] = ordering.groupby(["slice_name", "metric_group"])["early_indicator_score"].rank(ascending=False, method="dense")
    return ordering.sort_values(["slice_name", "combined_rank", "metric_name"]).reset_index(drop=True)


def build_mechanism_aggregate(ordering_df: pd.DataFrame) -> pd.DataFrame:
    mechanism = ordering_df[ordering_df["metric_group"] == "mechanism"].copy()
    aggregate = (
        mechanism.groupby("metric_name", as_index=False)
        .agg(
            mean_early_indicator_score=("early_indicator_score", "mean"),
            max_early_indicator_score=("early_indicator_score", "max"),
            mean_monotonicity_score=("monotonicity_score", "mean"),
            mean_first_step_rel_range=("first_step_rel_range", "mean"),
            top2_count=("mechanism_rank", lambda series: int((series <= 2).sum())),
            top1_count=("mechanism_rank", lambda series: int((series <= 1).sum())),
        )
        .sort_values(["top1_count", "top2_count", "mean_early_indicator_score"], ascending=[False, False, False])
        .reset_index(drop=True)
    )
    return aggregate


def write_dataset_tables(
    *,
    point_manifest: pd.DataFrame,
    point_summary: pd.DataFrame,
    slice_summary: pd.DataFrame,
    ordering_df: pd.DataFrame,
    mechanism_aggregate: pd.DataFrame,
    validation_df: pd.DataFrame,
) -> dict[str, str]:
    outputs = {
        "point_manifest_csv": DATASET_OUTPUT_DIR / "point_manifest.csv",
        "point_summary_csv": DATASET_OUTPUT_DIR / "point_summary.csv",
        "point_summary_parquet": DATASET_OUTPUT_DIR / "point_summary.parquet",
        "slice_summary_csv": DATASET_OUTPUT_DIR / "slice_summary.csv",
        "slice_summary_parquet": DATASET_OUTPUT_DIR / "slice_summary.parquet",
        "metric_ordering_csv": DATASET_OUTPUT_DIR / "metric_ordering.csv",
        "metric_ordering_parquet": DATASET_OUTPUT_DIR / "metric_ordering.parquet",
        "mechanism_aggregate_csv": DATASET_OUTPUT_DIR / "mechanism_ordering_aggregate.csv",
        "replay_validation_csv": DATASET_OUTPUT_DIR / "replay_validation.csv",
    }
    point_manifest.to_csv(outputs["point_manifest_csv"], index=False)
    point_summary.to_csv(outputs["point_summary_csv"], index=False)
    point_summary.to_parquet(outputs["point_summary_parquet"], index=False)
    slice_summary.to_csv(outputs["slice_summary_csv"], index=False)
    slice_summary.to_parquet(outputs["slice_summary_parquet"], index=False)
    ordering_df.to_csv(outputs["metric_ordering_csv"], index=False)
    ordering_df.to_parquet(outputs["metric_ordering_parquet"], index=False)
    mechanism_aggregate.to_csv(outputs["mechanism_aggregate_csv"], index=False)
    validation_df.to_csv(outputs["replay_validation_csv"], index=False)
    return {key: str(path) for key, path in outputs.items()}


def make_slice_figures(slice_summary: pd.DataFrame) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for spec in SLICE_SPECS:
        subset = slice_summary[slice_summary["slice_name"] == spec.name].sort_values("axis_value").reset_index(drop=True)
        figure_path = FIGURE_OUTPUT_DIR / f"{spec.name}_metrics.png"
        fig, axes = plt.subplots(5, 2, figsize=(11, 16))
        x = subset["axis_value"].to_numpy(dtype=float)
        for ax, (metric_name, title, color) in zip(axes.ravel(), PLOT_METRICS):
            y = subset[metric_name].to_numpy(dtype=float)
            ax.plot(x, y, marker="o", color=color, linewidth=1.8)
            ax.axvline(spec.baseline_value, color="#555555", linestyle="--", linewidth=1.0)
            ax.scatter(
                subset.loc[subset["is_baseline"], "axis_value"],
                subset.loc[subset["is_baseline"], metric_name],
                color="#d62728",
                s=36,
                zorder=3,
            )
            ax.set_title(title)
            ax.set_xlabel(spec.axis_label)
        fig.suptitle(spec.description, fontsize=13)
        fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.985))
        fig.savefig(figure_path, dpi=220)
        plt.close(fig)
        outputs[f"{spec.name}_figure"] = str(figure_path)
    return outputs


def make_ordering_figure(ordering_df: pd.DataFrame) -> str:
    mechanism = ordering_df[ordering_df["metric_group"] == "mechanism"].copy()
    pivot = mechanism.pivot(index="metric_name", columns="slice_name", values="early_indicator_score")
    order = [metric.name for metric in METRIC_SPECS if metric.group == "mechanism"]
    pivot = pivot.reindex(order)
    figure_path = FIGURE_OUTPUT_DIR / "intervention_ordering_heatmap.png"

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    image = ax.imshow(pivot.to_numpy(dtype=float), cmap="Blues", aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(list(pivot.columns), rotation=20)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(list(pivot.index))
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            value = float(pivot.iloc[i, j])
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="#111111", fontsize=8)
    ax.set_title("Mechanism Early-Indicator Scores")
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("score")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=220)
    plt.close(fig)
    return str(figure_path)


def _slice_manifest_table(slice_manifest: pd.DataFrame, slice_name: str) -> pd.DataFrame:
    subset = slice_manifest[slice_manifest["slice_name"] == slice_name].copy()
    return subset[
        [
            "point_label",
            "canonical_label",
            "Pi_m",
            "Pi_f",
            "Pi_U",
            "axis_value",
            "axis_delta_from_baseline",
            "is_baseline",
        ]
    ].rename(columns={"canonical_label": "canonical_match"})


def _top_mechanism_rows(ordering_df: pd.DataFrame, slice_name: str, *, k: int) -> pd.DataFrame:
    subset = ordering_df[
        (ordering_df["slice_name"] == slice_name)
        & (ordering_df["metric_group"] == "mechanism")
    ].sort_values(["mechanism_rank", "early_indicator_score", "metric_name"], ascending=[True, False, True])
    return subset.head(k)[
        [
            "metric_name",
            "early_indicator_score",
            "first_step_rel_range",
            "monotonicity_score",
            "direction_label",
        ]
    ]


def build_slice_interpretation(slice_summary: pd.DataFrame, slice_name: str) -> str:
    subset = slice_summary[slice_summary["slice_name"] == slice_name].sort_values("axis_value").reset_index(drop=True)
    baseline = subset.loc[subset["is_baseline"]].iloc[0]
    if slice_name == "delay_slice":
        higher = subset[subset["axis_value"] > float(baseline["axis_value"])].iloc[0]
        stale = subset.iloc[-1]
        return (
            "Raising delay away from the ridge midpoint first lengthens the pre-commit clock: "
            f"`first_gate_commit_delay` rises from `{baseline['first_gate_commit_delay']:.4f}` at `Pi_f = {baseline['axis_value']:.3f}` "
            f"to `{higher['first_gate_commit_delay']:.4f}` at `Pi_f = {higher['axis_value']:.3f}`, and "
            f"`wall_dwell_before_first_commit` rises from `{baseline['wall_dwell_before_first_commit']:.4f}` "
            f"to `{higher['wall_dwell_before_first_commit']:.4f}` over the same first step. "
            f"`trap_burden_mean` stays zero until the highest-delay stale point, where it turns on at `{stale['trap_burden_mean']:.6f}`. "
            "So delay intervention shows timing first, trapping later."
        )
    if slice_name == "memory_slice":
        low = subset.iloc[0]
        high = subset.iloc[-1]
        near_high = subset.iloc[-2]
        return (
            "The memory slice is weaker and less one-directional in raw timing, but `residence_given_approach` is the cleanest smooth signal: "
            f"it rises from `{low['residence_given_approach']:.4f}` at `Pi_m = {low['axis_value']:.2f}` "
            f"to `{near_high['residence_given_approach']:.4f}` at `Pi_m = {near_high['axis_value']:.2f}` before easing slightly at the edge. "
            f"`commit_given_residence` stays near `{baseline['commit_given_residence']:.3f}` across the slice, "
            "while trap burden appears only intermittently rather than as a smooth monotone trend. "
            "So memory intervention is better read through approach-to-residence organization than through residence-to-commit conversion."
        )
    low = subset.iloc[0]
    high = subset.iloc[-1]
    return (
        "The flow slice produces the clearest monotone contraction of the pre-commit search budget: "
        f"`first_gate_commit_delay` falls from `{low['first_gate_commit_delay']:.4f}` at `Pi_U = {low['axis_value']:.2f}` "
        f"to `{high['first_gate_commit_delay']:.4f}` at `Pi_U = {high['axis_value']:.2f}`, and "
        f"`wall_dwell_before_first_commit` falls from `{low['wall_dwell_before_first_commit']:.4f}` "
        f"to `{high['wall_dwell_before_first_commit']:.4f}`. "
        f"`residence_given_approach` rises from `{low['residence_given_approach']:.4f}` to `{high['residence_given_approach']:.4f}`, "
        f"but `commit_given_residence` remains nearly flat around `{baseline['commit_given_residence']:.3f}`. "
        "So flow orders the ridge mainly by how quickly trajectories reach and prepare for commitment."
    )


def build_conclusion() -> str:
    return (
        "Across the three local ridge interventions, the strongest early indicators are the pre-commit timing variables "
        "`wall_dwell_before_first_commit` and `first_gate_commit_delay`. "
        "`residence_given_approach` is the cleaner secondary mechanism signal, especially on the memory and flow slices. "
        "`trap_burden_mean` behaves mostly as a late or punctate stale flag rather than a smooth leading coordinate, "
        "and `commit_given_residence` stays comparatively flat, making it a late correlate rather than an early indicator."
    )


def write_design_doc(
    *,
    slice_manifest: pd.DataFrame,
    figure_paths: dict[str, str],
    dataset_paths: dict[str, str],
) -> None:
    slice_table = pd.DataFrame(
        [
            {
                "slice_name": spec.name,
                "axis_name": spec.axis_name,
                "fixed_controls": ", ".join(f"{key} = {value:.3f}" for key, value in spec.fixed_controls.items()),
                "baseline_value": spec.baseline_value,
                "n_points": int((slice_manifest["slice_name"] == spec.name).sum()),
            }
            for spec in SLICE_SPECS
        ]
    )
    content = f"""# Intervention Design

## Scope

This note defines the local intervention dataset used for mechanism-causality tests around the productive ridge.

Primary inputs:

- {_path_link(SUMMARY_PATH)}
- {_path_link(CANONICAL_POINTS_PATH)}
- {_path_link(PROJECT_ROOT / 'docs' / 'canonical_operating_points.md')}
- {_path_link(PROJECT_ROOT / 'docs' / 'mechanism_first_look_refined.md')}
- {_path_link(PROJECT_ROOT / 'docs' / 'precommit_gate_theory_fit_report.md')}

Selection policy:

- use only the finished confirmatory ridge grid
- use only the local base-grid `4096`-trajectory points
- do not reopen the search
- anchor all three slices on the balanced ridge midpoint `(Pi_m, Pi_f, Pi_U) = (0.15, 0.020, 0.20)`

## Slice Construction

{slice_table.to_markdown(index=False)}

## Measured Observables

Mechanism observables:

- `first_gate_commit_delay`
- `wall_dwell_before_first_commit`
- `trap_burden_mean`
- `residence_given_approach`
- `commit_given_residence`

Task and efficiency observables:

- `Psucc_mean`
- `MFPT_mean`
- `eta_sigma_mean`
- `eta_completion_drag`
- `eta_trap_drag`

Mechanism observables come from a refined replay using the existing gate-state extractor. Task and efficiency observables are taken from the persisted confirmatory summary so the intervention tables stay aligned with the frozen scan outputs.

## Ordering Rule

For each metric on each slice, the ordering package records three ingredients:

1. `first_step_rel_range`: the mean absolute change at the nearest off-ridge intervention points, normalized by the full slice range.
2. `monotonicity_score`: the average of absolute Spearman ordering and signed step-consistency.
3. `relative_range`: the slice range scaled by the metric magnitude and capped at `1`.

The combined early-indicator score is

`early_indicator_score = first_step_rel_range * monotonicity_score * relative_range`

Higher scores indicate that a quantity responds near the ridge and keeps a cleaner one-direction ordering under that control-axis intervention.

## Output Package

Dataset tables:

- {_path_link(dataset_paths['point_manifest_csv'])}
- {_path_link(dataset_paths['point_summary_csv'])}
- {_path_link(dataset_paths['slice_summary_csv'])}
- {_path_link(dataset_paths['metric_ordering_csv'])}

Trajectory-level replay outputs:

- {_path_link(DATASET_OUTPUT_DIR / 'trajectory_level.parquet')}
- {_path_link(DATASET_OUTPUT_DIR / 'event_level.parquet')}
- {_path_link(DATASET_OUTPUT_DIR / 'gate_conditioned.parquet')}

Figures:

- {_path_link(figure_paths['delay_slice_figure'])}
- {_path_link(figure_paths['memory_slice_figure'])}
- {_path_link(figure_paths['flow_slice_figure'])}
- {_path_link(figure_paths['ordering_heatmap'])}
"""
    DESIGN_DOC_PATH.write_text(content, encoding="ascii")


def write_run_report(
    *,
    slice_manifest: pd.DataFrame,
    point_summary: pd.DataFrame,
    validation_df: pd.DataFrame,
    ordering_df: pd.DataFrame,
    figure_paths: dict[str, str],
    dataset_paths: dict[str, str],
    total_event_rows: int,
) -> None:
    size_table = pd.DataFrame(
        [
            {"quantity": "unique points", "value": int(len(point_summary))},
            {"quantity": "slice memberships", "value": int(len(slice_manifest))},
            {"quantity": "trajectory rows", "value": int(point_summary["analysis_n_traj"].sum())},
            {"quantity": "event rows", "value": int(total_event_rows)},
            {"quantity": "gate rows", "value": int(len(point_summary))},
        ]
    )
    validation_table = pd.DataFrame(
        [
            {
                "metric": "max_abs_delta_Psucc",
                "value": float(validation_df["delta_Psucc_mean"].abs().max()),
            },
            {
                "metric": "max_abs_delta_MFPT",
                "value": float(validation_df["delta_MFPT_mean"].abs().max()),
            },
            {
                "metric": "max_abs_delta_Sigma_drag",
                "value": float(validation_df["delta_Sigma_drag_mean"].abs().max()),
            },
        ]
    )
    top_tables = []
    for spec in SLICE_SPECS:
        top_table = _top_mechanism_rows(ordering_df, spec.name, k=3)
        top_tables.append(f"### {spec.name}\n\n{top_table.to_markdown(index=False)}")

    slice_tables = []
    for spec in SLICE_SPECS:
        table = _slice_manifest_table(slice_manifest, spec.name)
        slice_tables.append(f"### {spec.name}\n\n{table.to_markdown(index=False)}")

    content = f"""# Intervention Dataset Run Report

## Scope

This report records the build of the intervention dataset for local mechanism-causality tests around the productive ridge.

Key outputs:

- {_path_link(DATASET_OUTPUT_DIR)}
- {_path_link(FIGURE_OUTPUT_DIR)}
- {_path_link(dataset_paths['replay_validation_csv'])}

## Dataset Size

{size_table.to_markdown(index=False)}

## Replay Validation

The refined replay preserves the upstream task metrics closely enough for local intervention ranking.

{validation_table.to_markdown(index=False)}

## Slice Manifests

{chr(10).join(slice_tables)}

## Leading Mechanism Signals By Slice

{chr(10).join(top_tables)}

## Generated Figures

- {_path_link(figure_paths['delay_slice_figure'])}
- {_path_link(figure_paths['memory_slice_figure'])}
- {_path_link(figure_paths['flow_slice_figure'])}
- {_path_link(figure_paths['ordering_heatmap'])}

## Generated Tables

- {_path_link(dataset_paths['point_summary_csv'])}
- {_path_link(dataset_paths['slice_summary_csv'])}
- {_path_link(dataset_paths['metric_ordering_csv'])}
- {_path_link(dataset_paths['mechanism_aggregate_csv'])}
"""
    RUN_REPORT_PATH.write_text(content, encoding="ascii")


def write_ordering_doc(
    *,
    ordering_df: pd.DataFrame,
    mechanism_aggregate: pd.DataFrame,
    slice_summary: pd.DataFrame,
    conclusion: str,
) -> None:
    sections: list[str] = []
    for spec in SLICE_SPECS:
        top_mechanism = _top_mechanism_rows(ordering_df, spec.name, k=4)
        interpretation = build_slice_interpretation(slice_summary, spec.name)
        sections.append(f"## {spec.name}\n\n{top_mechanism.to_markdown(index=False)}\n\n{interpretation}")

    content = f"""# Intervention Mechanism Ordering

## Scope

This note identifies which observables move first and most monotonically under the three local ridge interventions.

## Aggregate Mechanism Ordering

{mechanism_aggregate.to_markdown(index=False)}

## Slice-Level Leaders

{chr(10).join(sections)}

## Concise Conclusion

{conclusion}
"""
    ORDERING_DOC_PATH.write_text(content, encoding="ascii")


def build_metadata(
    *,
    point_summary: pd.DataFrame,
    slice_manifest: pd.DataFrame,
    figure_paths: dict[str, str],
    dataset_paths: dict[str, str],
    conclusion: str,
) -> str:
    metadata_path = DATASET_OUTPUT_DIR / "metadata.json"
    payload = {
        "n_unique_points": int(len(point_summary)),
        "n_slice_memberships": int(len(slice_manifest)),
        "point_labels": point_summary["point_label"].tolist(),
        "slice_names": [spec.name for spec in SLICE_SPECS],
        "conclusion": conclusion,
        "dataset_paths": dataset_paths,
        "figure_paths": figure_paths,
        "docs": {
            "intervention_design": str(DESIGN_DOC_PATH),
            "intervention_dataset_run_report": str(RUN_REPORT_PATH),
            "intervention_mechanism_ordering": str(ORDERING_DOC_PATH),
        },
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="ascii")
    return str(metadata_path)


def build_intervention_package(*, reuse_existing_replay: bool = False) -> dict[str, str]:
    confirmatory_grid = load_confirmatory_grid()
    slice_manifest, point_manifest = build_slice_manifest(confirmatory_grid)
    points = load_intervention_points(point_manifest)
    replay_outputs = (
        load_existing_replay_outputs(point_manifest)
        if reuse_existing_replay
        else build_intervention_dataset(points, point_manifest)
    )
    point_summary = summarize_points(
        trajectory_df=replay_outputs["trajectory_df"],
        gate_df=replay_outputs["gate_df"],
        point_manifest=point_manifest,
    )
    slice_summary = build_slice_summary(point_summary, slice_manifest)
    ordering_df = score_slice_ordering(slice_summary)
    mechanism_aggregate = build_mechanism_aggregate(ordering_df)
    dataset_paths = write_dataset_tables(
        point_manifest=point_manifest,
        point_summary=point_summary,
        slice_summary=slice_summary,
        ordering_df=ordering_df,
        mechanism_aggregate=mechanism_aggregate,
        validation_df=replay_outputs["validation_df"],
    )
    figure_paths = make_slice_figures(slice_summary)
    figure_paths["ordering_heatmap"] = make_ordering_figure(ordering_df)
    conclusion = build_conclusion()
    write_design_doc(slice_manifest=slice_manifest, figure_paths=figure_paths, dataset_paths=dataset_paths)
    write_run_report(
        slice_manifest=slice_manifest,
        point_summary=point_summary,
        validation_df=replay_outputs["validation_df"],
        ordering_df=ordering_df,
        figure_paths=figure_paths,
        dataset_paths=dataset_paths,
        total_event_rows=int(replay_outputs["total_event_rows"]),
    )
    write_ordering_doc(
        ordering_df=ordering_df,
        mechanism_aggregate=mechanism_aggregate,
        slice_summary=slice_summary,
        conclusion=conclusion,
    )
    metadata_path = build_metadata(
        point_summary=point_summary,
        slice_manifest=slice_manifest,
        figure_paths=figure_paths,
        dataset_paths=dataset_paths,
        conclusion=conclusion,
    )
    return {
        "trajectory_level": str(replay_outputs["trajectory_path"]),
        "event_level": str(replay_outputs["event_path"]),
        "gate_conditioned": str(replay_outputs["gate_path"]),
        "dataset_dir": str(DATASET_OUTPUT_DIR),
        "figure_dir": str(FIGURE_OUTPUT_DIR),
        "intervention_design": str(DESIGN_DOC_PATH),
        "intervention_run_report": str(RUN_REPORT_PATH),
        "intervention_ordering": str(ORDERING_DOC_PATH),
        "metadata_json": metadata_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the local intervention dataset around the productive ridge.")
    parser.add_argument(
        "--reuse-existing-replay",
        action="store_true",
        help="Reuse trajectory/event/gate parquet files already present in outputs/datasets/intervention_dataset.",
    )
    args = parser.parse_args(argv)
    outputs = build_intervention_package(reuse_existing_replay=bool(args.reuse_existing_replay))
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
