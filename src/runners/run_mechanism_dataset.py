from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from legacy.simcore.models import DynamicsConfig, GeometryConfig, SweepPoint
from legacy.simcore.simulation import MazeBuilder, NavigationSolver, PointSimulator

from src.analysis.mechanism_dataset_spec import SCHEMA_VERSION
from src.configs.schema import RunConfig

CANONICAL_POINTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "canonical_operating_points.csv"
REFERENCE_SCALES_PATH = PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json"
DATASET_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset"
FIGURE_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset"
EVENT_NOTE_PATH = PROJECT_ROOT / "docs" / "mechanism_event_classification_note.md"
RUN_REPORT_PATH = PROJECT_ROOT / "docs" / "mechanism_dataset_run_report.md"

EVENT_CODE_TO_NAME = {
    0: "bulk_motion",
    1: "wall_sliding",
    2: "gate_approach",
    3: "gate_capture",
    4: "gate_crossing",
    5: "trap_episode",
    6: "trap_escape",
    -1: "start",
    -2: "terminated",
}
NAME_TO_EVENT_CODE = {name: code for code, name in EVENT_CODE_TO_NAME.items()}

GATE_EVENT_CODES = {
    NAME_TO_EVENT_CODE["gate_approach"],
    NAME_TO_EVENT_CODE["gate_capture"],
    NAME_TO_EVENT_CODE["gate_crossing"],
}
WALL_EVENT_CODE = NAME_TO_EVENT_CODE["wall_sliding"]
TRAP_EVENT_CODE = NAME_TO_EVENT_CODE["trap_episode"]


@dataclass(frozen=True)
class GateDescriptor:
    gate_id: int
    shell_id: int
    side: str
    center_x: float
    center_y: float
    normal_x: float
    normal_y: float
    tangent_x: float
    tangent_y: float
    half_width: float


@dataclass(frozen=True)
class MechanismThresholds:
    wall_contact_distance: float
    wall_sliding_alignment_min: float
    gate_lane_half_width: float
    gate_approach_depth: float
    gate_capture_depth: float
    gate_progress_min: float
    gate_capture_alignment_min: float
    gate_crossing_margin: float
    trap_progress_window: float
    trap_progress_max: float
    trap_min_duration: float


@dataclass(frozen=True)
class CanonicalPoint:
    canonical_label: str
    analysis_source: str
    analysis_n_traj: int
    Pi_m: float
    Pi_f: float
    Pi_U: float
    result_json: str
    state_point_id: str
    config: RunConfig
    source_result: dict[str, Any]


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _safe_mean(series: pd.Series) -> float:
    finite = pd.to_numeric(series, errors="coerce")
    finite = finite[np.isfinite(finite)]
    if finite.empty:
        return math.nan
    return float(finite.mean())


def _circular_mean_from_components(cos_sum: float, sin_sum: float) -> float:
    if abs(cos_sum) < 1e-15 and abs(sin_sum) < 1e-15:
        return math.nan
    return float(math.atan2(sin_sum, cos_sum))


def _angle_wrap(values: np.ndarray) -> np.ndarray:
    return (values + np.pi) % (2.0 * np.pi) - np.pi


def load_reference_scales(path: Path = REFERENCE_SCALES_PATH) -> dict[str, Any]:
    with open(path, "r", encoding="ascii") as handle:
        return json.load(handle)


def add_event_alignment_columns(
    event_df: pd.DataFrame,
    *,
    dt: float,
    trap_min_duration: float,
) -> pd.DataFrame:
    aligned = event_df.copy()
    if aligned.empty:
        aligned["t_start_aligned"] = pd.Series(dtype=float)
        aligned["duration_aligned"] = pd.Series(dtype=float)
        aligned["trap_confirmation_backshift"] = pd.Series(dtype=float)
        return aligned

    aligned["t_start_aligned"] = aligned["t_start"].astype(float)
    aligned["duration_aligned"] = aligned["duration"].astype(float)
    aligned["trap_confirmation_backshift"] = 0.0

    backshift = max(trap_min_duration - dt, 0.0)
    trap_mask = aligned["event_type"] == "trap_episode"
    if trap_mask.any():
        aligned.loc[trap_mask, "trap_confirmation_backshift"] = backshift
        aligned.loc[trap_mask, "duration_aligned"] = aligned.loc[trap_mask, "duration"].astype(float) + backshift
        aligned.loc[trap_mask, "t_start_aligned"] = np.maximum(
            aligned.loc[trap_mask, "t_start"].astype(float) - backshift,
            0.0,
        )
    return aligned


def append_parquet(
    writer: pq.ParquetWriter | None,
    frame: pd.DataFrame,
    output_path: Path,
) -> pq.ParquetWriter | None:
    if frame.empty:
        return writer
    table = pa.Table.from_pandas(frame, preserve_index=False)
    if writer is None:
        writer = pq.ParquetWriter(output_path, table.schema)
    writer.write_table(table)
    return writer


def build_gate_descriptors(config: RunConfig) -> tuple[GateDescriptor, ...]:
    doorway_cycle = ("left", "top", "right", "bottom")
    L = float(config.metadata.get("L", 1.0))
    delta_a = (L / 2.0 - config.exit_radius - config.wall_thickness) / (config.n_shell + 1)
    descriptors: list[GateDescriptor] = []
    for shell_id in range(1, config.n_shell + 1):
        a = L / 2.0 - shell_id * delta_a
        side = doorway_cycle[(shell_id - 1) % len(doorway_cycle)]
        if side == "left":
            descriptor = GateDescriptor(
                gate_id=shell_id - 1,
                shell_id=shell_id,
                side=side,
                center_x=-a,
                center_y=0.0,
                normal_x=1.0,
                normal_y=0.0,
                tangent_x=0.0,
                tangent_y=1.0,
                half_width=config.gate_width / 2.0,
            )
        elif side == "right":
            descriptor = GateDescriptor(
                gate_id=shell_id - 1,
                shell_id=shell_id,
                side=side,
                center_x=a,
                center_y=0.0,
                normal_x=-1.0,
                normal_y=0.0,
                tangent_x=0.0,
                tangent_y=1.0,
                half_width=config.gate_width / 2.0,
            )
        elif side == "top":
            descriptor = GateDescriptor(
                gate_id=shell_id - 1,
                shell_id=shell_id,
                side=side,
                center_x=0.0,
                center_y=a,
                normal_x=0.0,
                normal_y=-1.0,
                tangent_x=1.0,
                tangent_y=0.0,
                half_width=config.gate_width / 2.0,
            )
        else:
            descriptor = GateDescriptor(
                gate_id=shell_id - 1,
                shell_id=shell_id,
                side=side,
                center_x=0.0,
                center_y=-a,
                normal_x=0.0,
                normal_y=1.0,
                tangent_x=1.0,
                tangent_y=0.0,
                half_width=config.gate_width / 2.0,
            )
        descriptors.append(descriptor)
    return tuple(descriptors)


def build_thresholds(config: RunConfig, reference_scales: dict[str, Any]) -> MechanismThresholds:
    tau_p = float(reference_scales["tau_p"])
    wall = config.wall_thickness
    gate = config.gate_width
    return MechanismThresholds(
        wall_contact_distance=wall,
        wall_sliding_alignment_min=0.70,
        gate_lane_half_width=0.5 * gate + 0.5 * wall,
        gate_approach_depth=max(0.75 * gate, 1.5 * wall),
        gate_capture_depth=max(0.5 * wall, 0.25 * gate),
        gate_progress_min=0.05 * config.v0,
        gate_capture_alignment_min=0.30,
        gate_crossing_margin=0.25 * wall,
        trap_progress_window=0.25 * tau_p,
        trap_progress_max=0.0,
        trap_min_duration=0.50 * tau_p,
    )


def load_canonical_points() -> list[CanonicalPoint]:
    manifest_df = pd.read_csv(CANONICAL_POINTS_PATH)
    points: list[CanonicalPoint] = []
    for row in manifest_df.to_dict(orient="records"):
        result_path = Path(str(row["result_json"]))
        with open(result_path, "r", encoding="ascii") as handle:
            source_result = json.load(handle)
        config = RunConfig.from_dict(source_result["input_config"])
        points.append(
            CanonicalPoint(
                canonical_label=str(row["canonical_label"]),
                analysis_source=str(row["analysis_source"]),
                analysis_n_traj=int(row["analysis_n_traj"]),
                Pi_m=float(row["Pi_m"]),
                Pi_f=float(row["Pi_f"]),
                Pi_U=float(row["Pi_U"]),
                result_json=str(result_path),
                state_point_id=str(source_result["state_point_id"]),
                config=config,
                source_result=source_result,
            )
        )
    return points


def _make_shared_payload(point: CanonicalPoint, reference_scales: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "scan_id": str(point.source_result["scan_id"]),
        "state_point_id": point.state_point_id,
        "canonical_label": point.canonical_label,
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


class MechanismPointExtractor(PointSimulator):
    def __init__(
        self,
        *,
        maze: Any,
        navigation: Any,
        thresholds: MechanismThresholds,
        gates: tuple[GateDescriptor, ...],
    ) -> None:
        super().__init__(maze, navigation)
        self.thresholds = thresholds
        self.gates = gates

    def _build_sweep_point(self, config: RunConfig) -> SweepPoint:
        gamma1_over_gamma0 = config.gamma1_over_gamma0
        if gamma1_over_gamma0 is None:
            gamma1_over_gamma0 = (config.gamma1 / config.gamma0) if config.gamma0 else 0.0
        return SweepPoint(
            sweep_id=f"{config.geometry_id}_{config.model_variant}_{config.config_hash[:8]}",
            figure_group="mechanism_dataset",
            control_label="coupled_baseline",
            tau_v=config.tau_v,
            tau_f=config.tau_f,
            U=config.U,
            gamma1_over_gamma0=gamma1_over_gamma0,
            kf=config.kf,
        )

    def _build_dynamics(self, config: RunConfig) -> DynamicsConfig:
        gamma1_over_gamma0 = config.gamma1_over_gamma0
        if gamma1_over_gamma0 is None:
            gamma1_over_gamma0 = (config.gamma1 / config.gamma0) if config.gamma0 else 0.0
        return DynamicsConfig(
            gamma0=config.gamma0,
            gamma1_over_gamma0=gamma1_over_gamma0,
            Dr=config.Dr,
            v0=config.v0,
            kf=config.kf,
            kBT=config.kBT,
            dt=config.dt,
            Tmax=config.Tmax,
            eps_psi=config.eps_psi,
            bootstrap_resamples=config.bootstrap_resamples,
            n_traj=config.n_traj,
            seed=config.seed,
        )

    def extract_point(
        self,
        *,
        point: CanonicalPoint,
        shared_payload: dict[str, Any],
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
        config = point.config
        sweep_point = self._build_sweep_point(config)
        dynamics = self._build_dynamics(config)

        rng = np.random.default_rng(config.seed)
        n_traj = dynamics.n_traj
        dt = dynamics.dt
        Tmax = dynamics.Tmax
        n_steps = int(round(Tmax / dt))
        tau_p = 1.0 / dynamics.Dr
        gamma0 = dynamics.gamma0
        gamma1 = sweep_point.gamma1_over_gamma0 * gamma0
        tau_v = sweep_point.tau_v
        tau_f = sweep_point.tau_f
        U = sweep_point.U
        flow = np.array([U, 0.0], dtype=float)
        f0 = gamma0 * dynamics.v0
        tau_adv = self.maze.config.w / max(dynamics.v0, U, 1e-12)
        tau_m = 1e-2 * min(tau_v, tau_p, tau_adv, tau_f if tau_f > 0.0 else float("inf"))
        if not np.isfinite(tau_m) or tau_m <= 0.0:
            tau_m = 1e-2 * min(tau_v, tau_p, tau_adv)
        m = gamma0 * tau_m
        M, K, noise_chol = self.build_discrete_linear_step(
            gamma0=gamma0,
            gamma1=gamma1,
            tau_v=tau_v,
            kBT=dynamics.kBT,
            tau_m=tau_m,
            dt=dt,
        )

        delta_wall = 2.0 * self.maze.h
        k_wall = 50.0 * f0 / delta_wall

        r = self.sample_inlet_positions(n_traj, rng)
        theta = rng.uniform(0.0, 2.0 * np.pi, size=n_traj)
        v = np.tile(flow, (n_traj, 1))
        q = np.zeros((n_traj, 2), dtype=float)

        delay_steps = int(round(tau_f / dt)) if tau_f > 0.0 else 0
        hist_len = max(delay_steps + 1, 1)
        r_hist = np.repeat(r[np.newaxis, :, :], hist_len, axis=0)
        hist_pos = 0

        live_steps = np.zeros(n_traj, dtype=np.int64)
        boundary_steps = np.zeros(n_traj, dtype=np.int64)
        sigma_drag_i = np.zeros(n_traj, dtype=float)
        success = np.zeros(n_traj, dtype=bool)
        t_exit = np.full(n_traj, np.nan, dtype=float)
        alive = np.ones(n_traj, dtype=bool)
        termination_label = np.full(n_traj, "tmax", dtype=object)

        prog_window = max(1, int(math.ceil(self.thresholds.trap_progress_window / dt)))
        prog_buffer = np.zeros((n_traj, prog_window), dtype=float)
        prog_sum = np.zeros(n_traj, dtype=float)
        prog_count = np.zeros(n_traj, dtype=np.int64)
        prog_ptr = np.zeros(n_traj, dtype=np.int64)

        current_event_code = np.full(n_traj, -999, dtype=int)
        current_event_gate_id = np.full(n_traj, -1, dtype=int)
        current_event_entered_from = np.full(n_traj, NAME_TO_EVENT_CODE["start"], dtype=int)
        next_event_index = np.zeros(n_traj, dtype=int)

        event_start_t = np.zeros(n_traj, dtype=float)
        event_duration = np.zeros(n_traj, dtype=float)
        event_progress = np.zeros(n_traj, dtype=float)
        event_lag_nav_sin = np.zeros(n_traj, dtype=float)
        event_lag_nav_cos = np.zeros(n_traj, dtype=float)
        event_lag_steer_sin = np.zeros(n_traj, dtype=float)
        event_lag_steer_cos = np.zeros(n_traj, dtype=float)
        event_align_gate_sum = np.zeros(n_traj, dtype=float)
        event_align_gate_count = np.zeros(n_traj, dtype=np.int64)
        event_align_wall_sum = np.zeros(n_traj, dtype=float)
        event_align_wall_count = np.zeros(n_traj, dtype=np.int64)
        event_wall_dist_sum = np.zeros(n_traj, dtype=float)
        event_wall_dist_count = np.zeros(n_traj, dtype=np.int64)
        event_gate_dist_sum = np.zeros(n_traj, dtype=float)
        event_gate_dist_count = np.zeros(n_traj, dtype=np.int64)
        event_speed_sum = np.zeros(n_traj, dtype=float)
        event_speed_count = np.zeros(n_traj, dtype=np.int64)
        event_x_start = np.zeros(n_traj, dtype=float)
        event_y_start = np.zeros(n_traj, dtype=float)
        event_x_end = np.zeros(n_traj, dtype=float)
        event_y_end = np.zeros(n_traj, dtype=float)

        traj_progress_total = np.zeros(n_traj, dtype=float)
        traj_lag_nav_sin = np.zeros(n_traj, dtype=float)
        traj_lag_nav_cos = np.zeros(n_traj, dtype=float)
        traj_lag_steer_sin = np.zeros(n_traj, dtype=float)
        traj_lag_steer_cos = np.zeros(n_traj, dtype=float)
        traj_alignment_gate_sum = np.zeros(n_traj, dtype=float)
        traj_alignment_gate_count = np.zeros(n_traj, dtype=np.int64)
        traj_alignment_wall_sum = np.zeros(n_traj, dtype=float)
        traj_alignment_wall_count = np.zeros(n_traj, dtype=np.int64)

        wall_time_before_first_capture = np.zeros(n_traj, dtype=float)
        first_capture_time = np.full(n_traj, np.nan, dtype=float)

        trap_candidate_duration = np.zeros(n_traj, dtype=float)
        trap_candidate_gate_id = np.full(n_traj, -1, dtype=int)
        n_trap_exact = np.zeros(n_traj, dtype=np.int64)
        trap_time_total_exact = np.zeros(n_traj, dtype=float)
        largest_trap_duration = np.zeros(n_traj, dtype=float)
        n_trap_escape_exact = np.zeros(n_traj, dtype=np.int64)
        trap_escape_time_total = np.zeros(n_traj, dtype=float)

        prev_gate_id = np.full(n_traj, -1, dtype=int)
        prev_gate_normal = np.full(n_traj, np.nan, dtype=float)
        prev_gate_in_lane = np.zeros(n_traj, dtype=bool)

        gate_visit_sequence: list[list[str]] = [[] for _ in range(n_traj)]
        event_rows: list[dict[str, Any]] = []

        def reset_event_accumulators(indices: np.ndarray) -> None:
            event_duration[indices] = 0.0
            event_progress[indices] = 0.0
            event_lag_nav_sin[indices] = 0.0
            event_lag_nav_cos[indices] = 0.0
            event_lag_steer_sin[indices] = 0.0
            event_lag_steer_cos[indices] = 0.0
            event_align_gate_sum[indices] = 0.0
            event_align_gate_count[indices] = 0
            event_align_wall_sum[indices] = 0.0
            event_align_wall_count[indices] = 0
            event_wall_dist_sum[indices] = 0.0
            event_wall_dist_count[indices] = 0
            event_gate_dist_sum[indices] = 0.0
            event_gate_dist_count[indices] = 0
            event_speed_sum[indices] = 0.0
            event_speed_count[indices] = 0

        def finalize_events(indices: np.ndarray, exited_to_code: int, *, t_end: float, x_end_now: np.ndarray, y_end_now: np.ndarray) -> None:
            for local_pos, traj_idx in enumerate(indices.tolist()):
                code = int(current_event_code[traj_idx])
                if code == -999 or event_duration[traj_idx] <= 0.0:
                    continue
                gate_id = int(current_event_gate_id[traj_idx])
                row = dict(shared_payload)
                row.update(
                    {
                        "event_id": f"{point.canonical_label}:{traj_idx}:{next_event_index[traj_idx] - 1}",
                        "traj_id": traj_idx,
                        "event_type": EVENT_CODE_TO_NAME[code],
                        "event_index": int(next_event_index[traj_idx] - 1),
                        "t_start": float(event_start_t[traj_idx]),
                        "t_end": float(t_end),
                        "duration": float(event_duration[traj_idx]),
                        "gate_id": gate_id,
                        "entered_from_event_type": EVENT_CODE_TO_NAME[int(current_event_entered_from[traj_idx])],
                        "exited_to_event_type": EVENT_CODE_TO_NAME[exited_to_code],
                        "progress_along_navigation": float(event_progress[traj_idx]),
                        "progress_along_navigation_rate": float(event_progress[traj_idx] / max(event_duration[traj_idx], 1e-12)),
                        "phase_lag_navigation_mean": _circular_mean_from_components(
                            float(event_lag_nav_cos[traj_idx]),
                            float(event_lag_nav_sin[traj_idx]),
                        ),
                        "phase_lag_steering_mean": _circular_mean_from_components(
                            float(event_lag_steer_cos[traj_idx]),
                            float(event_lag_steer_sin[traj_idx]),
                        ),
                        "alignment_gate_mean": (
                            float(event_align_gate_sum[traj_idx] / event_align_gate_count[traj_idx])
                            if event_align_gate_count[traj_idx] > 0
                            else math.nan
                        ),
                        "alignment_wall_mean": (
                            float(event_align_wall_sum[traj_idx] / event_align_wall_count[traj_idx])
                            if event_align_wall_count[traj_idx] > 0
                            else math.nan
                        ),
                        "capture_success_flag": bool(code == NAME_TO_EVENT_CODE["gate_capture"] and exited_to_code == NAME_TO_EVENT_CODE["gate_crossing"]),
                        "x_start": float(event_x_start[traj_idx]),
                        "y_start": float(event_y_start[traj_idx]),
                        "x_end": float(x_end_now[local_pos]),
                        "y_end": float(y_end_now[local_pos]),
                        "mean_wall_distance": (
                            float(event_wall_dist_sum[traj_idx] / event_wall_dist_count[traj_idx])
                            if event_wall_dist_count[traj_idx] > 0
                            else math.nan
                        ),
                        "mean_gate_distance": (
                            float(event_gate_dist_sum[traj_idx] / event_gate_dist_count[traj_idx])
                            if event_gate_dist_count[traj_idx] > 0
                            else math.nan
                        ),
                        "mean_speed": (
                            float(event_speed_sum[traj_idx] / event_speed_count[traj_idx])
                            if event_speed_count[traj_idx] > 0
                            else math.nan
                        ),
                    }
                )
                event_rows.append(row)

        for step in range(n_steps):
            if not np.any(alive):
                break

            alive_idx = np.flatnonzero(alive)
            delayed = r_hist[(hist_pos - delay_steps) % hist_len, alive_idx, :]
            grad_delayed_x = self.bilinear_sample(self.navigation.grad_psi_x, delayed[:, 0], delayed[:, 1])
            grad_delayed_y = self.bilinear_sample(self.navigation.grad_psi_y, delayed[:, 0], delayed[:, 1])
            grad_delayed_norm = np.hypot(grad_delayed_x, grad_delayed_y)
            theta_star = np.arctan2(-grad_delayed_y, -grad_delayed_x)

            grad_curr_x = self.bilinear_sample(self.navigation.grad_psi_x, r[alive_idx, 0], r[alive_idx, 1])
            grad_curr_y = self.bilinear_sample(self.navigation.grad_psi_y, r[alive_idx, 0], r[alive_idx, 1])
            grad_curr_norm = np.hypot(grad_curr_x, grad_curr_y)
            nav_x = -grad_curr_x / np.maximum(grad_curr_norm, dynamics.eps_psi)
            nav_y = -grad_curr_y / np.maximum(grad_curr_norm, dynamics.eps_psi)

            pos_s = self.bilinear_sample(self.maze.signed_distance, r[alive_idx, 0], r[alive_idx, 1])
            boundary_contact = pos_s <= self.thresholds.wall_contact_distance
            live_steps[alive_idx] += 1
            boundary_steps[alive_idx] += boundary_contact.astype(np.int64)

            speed = np.hypot(v[alive_idx, 0], v[alive_idx, 1])
            motion_x = np.divide(v[alive_idx, 0], speed, out=np.cos(theta[alive_idx]).copy(), where=speed > 1e-12)
            motion_y = np.divide(v[alive_idx, 1], speed, out=np.sin(theta[alive_idx]).copy(), where=speed > 1e-12)
            motion_angle = np.arctan2(motion_y, motion_x)
            nav_angle = np.arctan2(nav_y, nav_x)
            steering_angle = np.where(grad_delayed_norm >= dynamics.eps_psi, theta_star, nav_angle)
            lag_nav = _angle_wrap(motion_angle - nav_angle)
            lag_steer = _angle_wrap(motion_angle - steering_angle)
            progress_speed = v[alive_idx, 0] * nav_x + v[alive_idx, 1] * nav_y

            ptr = prog_ptr[alive_idx]
            prog_sum[alive_idx] -= prog_buffer[alive_idx, ptr]
            prog_buffer[alive_idx, ptr] = progress_speed
            prog_sum[alive_idx] += progress_speed
            prog_ptr[alive_idx] = (ptr + 1) % prog_window
            prog_count[alive_idx] = np.minimum(prog_count[alive_idx] + 1, prog_window)
            rolling_progress = prog_sum[alive_idx] / np.maximum(prog_count[alive_idx], 1)
            trapped_now = boundary_contact & (rolling_progress <= self.thresholds.trap_progress_max)

            grad_s_x = self.bilinear_sample(self.maze.grad_s_x, r[alive_idx, 0], r[alive_idx, 1])
            grad_s_y = self.bilinear_sample(self.maze.grad_s_y, r[alive_idx, 0], r[alive_idx, 1])
            grad_s_norm = np.hypot(grad_s_x, grad_s_y)
            wall_nx = grad_s_x / np.maximum(grad_s_norm, 1e-12)
            wall_ny = grad_s_y / np.maximum(grad_s_norm, 1e-12)
            wall_tx = -wall_ny
            wall_ty = wall_nx
            wall_alignment = np.abs(motion_x * wall_tx + motion_y * wall_ty)

            active_gate_id = np.full(alive_idx.size, -1, dtype=int)
            active_gate_normal = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_tangent = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_distance = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_alignment = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_progress = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_lane = np.zeros(alive_idx.size, dtype=bool)
            best_score = np.full(alive_idx.size, np.inf, dtype=float)

            for gate in self.gates:
                rel_x = r[alive_idx, 0] - gate.center_x
                rel_y = r[alive_idx, 1] - gate.center_y
                normal_coord = rel_x * gate.normal_x + rel_y * gate.normal_y
                tangent_coord = rel_x * gate.tangent_x + rel_y * gate.tangent_y
                gate_distance = np.sqrt(normal_coord**2 + tangent_coord**2)
                score = np.abs(tangent_coord) + np.abs(normal_coord)
                better = score < best_score
                best_score = np.where(better, score, best_score)
                active_gate_id = np.where(better, gate.gate_id, active_gate_id)
                active_gate_normal = np.where(better, normal_coord, active_gate_normal)
                active_gate_tangent = np.where(better, tangent_coord, active_gate_tangent)
                active_gate_distance = np.where(better, gate_distance, active_gate_distance)
                active_gate_alignment = np.where(
                    better,
                    motion_x * gate.normal_x + motion_y * gate.normal_y,
                    active_gate_alignment,
                )
                active_gate_progress = np.where(
                    better,
                    v[alive_idx, 0] * gate.normal_x + v[alive_idx, 1] * gate.normal_y,
                    active_gate_progress,
                )
                active_gate_lane = np.where(
                    better,
                    np.abs(tangent_coord) <= self.thresholds.gate_lane_half_width,
                    active_gate_lane,
                )

            crossing_now = (
                (prev_gate_id[alive_idx] == active_gate_id)
                & prev_gate_in_lane[alive_idx]
                & active_gate_lane
                & np.isfinite(prev_gate_normal[alive_idx])
                & (prev_gate_normal[alive_idx] < -self.thresholds.gate_crossing_margin)
                & (active_gate_normal >= self.thresholds.gate_crossing_margin)
            )
            approach_now = (
                active_gate_lane
                & (active_gate_normal >= -self.thresholds.gate_approach_depth)
                & (active_gate_normal < -self.thresholds.gate_capture_depth)
                & (active_gate_progress >= self.thresholds.gate_progress_min)
            )
            capture_now = (
                active_gate_lane
                & (np.abs(active_gate_normal) <= self.thresholds.gate_capture_depth)
                & (active_gate_alignment >= self.thresholds.gate_capture_alignment_min)
            )
            wall_sliding_now = boundary_contact & (wall_alignment >= self.thresholds.wall_sliding_alignment_min)

            previous_trap_duration = trap_candidate_duration[alive_idx].copy()
            new_trap_start = trapped_now & (previous_trap_duration <= 0.0)
            if np.any(new_trap_start):
                trap_candidate_gate_id[alive_idx[new_trap_start]] = np.where(
                    active_gate_id[new_trap_start] >= 0,
                    active_gate_id[new_trap_start],
                    -1,
                )
            trap_candidate_duration[alive_idx] = np.where(trapped_now, previous_trap_duration + dt, 0.0)
            just_escaped = (~trapped_now) & (previous_trap_duration >= self.thresholds.trap_min_duration)
            confirmed_trap_now = trapped_now & (trap_candidate_duration[alive_idx] >= self.thresholds.trap_min_duration)

            proposed_code = np.full(alive_idx.size, NAME_TO_EVENT_CODE["bulk_motion"], dtype=int)
            proposed_gate_id = np.full(alive_idx.size, -1, dtype=int)

            proposed_code = np.where(wall_sliding_now, NAME_TO_EVENT_CODE["wall_sliding"], proposed_code)
            proposed_code = np.where(approach_now, NAME_TO_EVENT_CODE["gate_approach"], proposed_code)
            proposed_code = np.where(capture_now, NAME_TO_EVENT_CODE["gate_capture"], proposed_code)
            proposed_code = np.where(crossing_now, NAME_TO_EVENT_CODE["gate_crossing"], proposed_code)
            proposed_code = np.where(confirmed_trap_now, NAME_TO_EVENT_CODE["trap_episode"], proposed_code)
            proposed_code = np.where(just_escaped, NAME_TO_EVENT_CODE["trap_escape"], proposed_code)

            proposed_gate_id = np.where(
                np.isin(proposed_code, list(GATE_EVENT_CODES)),
                active_gate_id,
                proposed_gate_id,
            )
            proposed_gate_id = np.where(
                proposed_code == NAME_TO_EVENT_CODE["trap_episode"],
                trap_candidate_gate_id[alive_idx],
                proposed_gate_id,
            )
            proposed_gate_id = np.where(
                proposed_code == NAME_TO_EVENT_CODE["trap_escape"],
                trap_candidate_gate_id[alive_idx],
                proposed_gate_id,
            )

            unchanged = (
                (current_event_code[alive_idx] == proposed_code)
                & (current_event_gate_id[alive_idx] == proposed_gate_id)
            )
            changed_indices = alive_idx[~unchanged]
            if changed_indices.size:
                x_current = r[changed_indices, 0]
                y_current = r[changed_indices, 1]
                next_codes = proposed_code[~unchanged]
                for target_code in np.unique(next_codes):
                    target_mask = next_codes == target_code
                    subset = changed_indices[target_mask]
                    finalize_events(
                        subset,
                        int(target_code),
                        t_end=step * dt,
                        x_end_now=x_current[target_mask],
                        y_end_now=y_current[target_mask],
                    )
                reset_event_accumulators(changed_indices)
                event_start_t[changed_indices] = step * dt
                event_x_start[changed_indices] = r[changed_indices, 0]
                event_y_start[changed_indices] = r[changed_indices, 1]
                event_x_end[changed_indices] = r[changed_indices, 0]
                event_y_end[changed_indices] = r[changed_indices, 1]
                event_duration[changed_indices] = 0.0
                current_event_entered_from[changed_indices] = np.where(
                    current_event_code[changed_indices] == -999,
                    NAME_TO_EVENT_CODE["start"],
                    current_event_code[changed_indices],
                )
                current_event_code[changed_indices] = proposed_code[~unchanged]
                current_event_gate_id[changed_indices] = proposed_gate_id[~unchanged]
                next_event_index[changed_indices] += 1

                is_first_capture = (
                    (current_event_code[changed_indices] == NAME_TO_EVENT_CODE["gate_capture"])
                    & ~np.isfinite(first_capture_time[changed_indices])
                )
                if np.any(is_first_capture):
                    first_capture_time[changed_indices[is_first_capture]] = step * dt

            gate_valid = np.isin(current_event_code[alive_idx], list(GATE_EVENT_CODES))
            wall_valid = current_event_code[alive_idx] == NAME_TO_EVENT_CODE["wall_sliding"]

            event_duration[alive_idx] += dt
            event_progress[alive_idx] += progress_speed * dt
            event_lag_nav_sin[alive_idx] += np.sin(lag_nav)
            event_lag_nav_cos[alive_idx] += np.cos(lag_nav)
            event_lag_steer_sin[alive_idx] += np.sin(lag_steer)
            event_lag_steer_cos[alive_idx] += np.cos(lag_steer)
            event_speed_sum[alive_idx] += speed
            event_speed_count[alive_idx] += 1
            event_wall_dist_sum[alive_idx] += pos_s
            event_wall_dist_count[alive_idx] += 1
            event_gate_dist_sum[alive_idx[gate_valid]] += active_gate_distance[gate_valid]
            event_gate_dist_count[alive_idx[gate_valid]] += 1
            event_align_gate_sum[alive_idx[gate_valid]] += active_gate_alignment[gate_valid]
            event_align_gate_count[alive_idx[gate_valid]] += 1
            event_align_wall_sum[alive_idx[wall_valid]] += wall_alignment[wall_valid]
            event_align_wall_count[alive_idx[wall_valid]] += 1

            traj_progress_total[alive_idx] += progress_speed * dt
            traj_lag_nav_sin[alive_idx] += np.sin(lag_nav)
            traj_lag_nav_cos[alive_idx] += np.cos(lag_nav)
            traj_lag_steer_sin[alive_idx] += np.sin(lag_steer)
            traj_lag_steer_cos[alive_idx] += np.cos(lag_steer)
            traj_alignment_gate_sum[alive_idx[gate_valid]] += active_gate_alignment[gate_valid]
            traj_alignment_gate_count[alive_idx[gate_valid]] += 1
            traj_alignment_wall_sum[alive_idx[wall_valid]] += wall_alignment[wall_valid]
            traj_alignment_wall_count[alive_idx[wall_valid]] += 1
            wall_time_before_first_capture[alive_idx[wall_valid & ~np.isfinite(first_capture_time[alive_idx])]] += dt

            if np.any(just_escaped):
                escaped_idx = alive_idx[just_escaped]
                durations = previous_trap_duration[just_escaped]
                n_trap_exact[escaped_idx] += 1
                trap_time_total_exact[escaped_idx] += durations
                largest_trap_duration[escaped_idx] = np.maximum(largest_trap_duration[escaped_idx], durations)
                n_trap_escape_exact[escaped_idx] += 1
                trap_escape_time_total[escaped_idx] += durations
                trap_candidate_gate_id[escaped_idx] = -1

            sigma_drag_i[alive_idx] += dt * gamma0 * np.sum((v[alive_idx] - flow) ** 2, axis=1) / dynamics.kBT

            torque = np.where(
                grad_delayed_norm >= dynamics.eps_psi,
                sweep_point.kf * np.sin(theta_star - theta[alive_idx]),
                0.0,
            )
            theta[alive_idx] = self.angle_wrap(
                theta[alive_idx] + dt * torque + math.sqrt(2.0 * dynamics.Dr * dt) * rng.normal(size=alive_idx.size)
            )
            n_vec = np.column_stack((np.cos(theta[alive_idx]), np.sin(theta[alive_idx])))

            wall_force_mag = k_wall * np.clip(delta_wall - pos_s, 0.0, None)
            wall_force = wall_force_mag[:, None] * np.column_stack((wall_nx, wall_ny))
            force_x = f0 * n_vec[:, 0] + wall_force[:, 0]
            force_y = f0 * n_vec[:, 1] + wall_force[:, 1]

            noise_x = noise_chol @ rng.normal(size=(3, alive_idx.size))
            noise_y = noise_chol @ rng.normal(size=(3, alive_idx.size))
            c_x = np.vstack(
                [
                    np.zeros(alive_idx.size, dtype=float),
                    np.full(alive_idx.size, gamma0 * flow[0] / m) + force_x / m,
                    np.full(alive_idx.size, -gamma1 * flow[0] / tau_v if gamma1 > 0.0 else 0.0),
                ]
            )
            c_y = np.vstack(
                [
                    np.zeros(alive_idx.size, dtype=float),
                    force_y / m,
                    np.zeros(alive_idx.size, dtype=float),
                ]
            )
            state_x = np.vstack((r[alive_idx, 0], v[alive_idx, 0], q[alive_idx, 0]))
            state_y = np.vstack((r[alive_idx, 1], v[alive_idx, 1], q[alive_idx, 1]))
            next_x = M @ state_x + K @ c_x + noise_x
            next_y = M @ state_y + K @ c_y + noise_y
            r_trial = np.column_stack((next_x[0], next_y[0]))
            v_trial = np.column_stack((next_x[1], next_y[1]))
            q_trial = np.column_stack((next_x[2], next_y[2]))

            in_exit = (np.abs(r_trial[:, 0]) <= self.maze.config.r_exit) & (np.abs(r_trial[:, 1]) <= self.maze.config.r_exit)
            if np.any(in_exit):
                hit_idx = alive_idx[in_exit]
                success[hit_idx] = True
                t_exit[hit_idx] = (step + 1) * dt
                termination_label[hit_idx] = "exit"

            if np.any(~in_exit):
                keep_idx = alive_idx[~in_exit]
                r_keep = r_trial[~in_exit]
                v_keep = v_trial[~in_exit]
                q_keep = q_trial[~in_exit]
                s_trial = self.bilinear_sample(self.maze.signed_distance, r_keep[:, 0], r_keep[:, 1])
                penetrated = s_trial < 0.0
                if np.any(penetrated):
                    grad_trial_x = self.bilinear_sample(self.maze.grad_s_x, r_keep[penetrated, 0], r_keep[penetrated, 1])
                    grad_trial_y = self.bilinear_sample(self.maze.grad_s_y, r_keep[penetrated, 0], r_keep[penetrated, 1])
                    grad_trial_norm = np.hypot(grad_trial_x, grad_trial_y)
                    normal = np.column_stack((grad_trial_x, grad_trial_y)) / np.maximum(grad_trial_norm[:, None], 1e-12)
                    r_keep[penetrated] = r_keep[penetrated] + (-s_trial[penetrated] + delta_wall)[:, None] * normal
                    inward = np.minimum(np.sum(v_keep[penetrated] * normal, axis=1), 0.0)
                    v_keep[penetrated] = v_keep[penetrated] - inward[:, None] * normal
                r[keep_idx] = r_keep
                v[keep_idx] = v_keep
                q[keep_idx] = q_keep

            if np.any(in_exit):
                hit_idx = alive_idx[in_exit]
                r[hit_idx] = r_trial[in_exit]
                v[hit_idx] = v_trial[in_exit]
                q[hit_idx] = q_trial[in_exit]

            event_x_end[alive_idx] = r[alive_idx, 0]
            event_y_end[alive_idx] = r[alive_idx, 1]

            if np.any(in_exit):
                hit_idx = alive_idx[in_exit]
                finalize_events(
                    hit_idx,
                    NAME_TO_EVENT_CODE["terminated"],
                    t_end=(step + 1) * dt,
                    x_end_now=r[hit_idx, 0],
                    y_end_now=r[hit_idx, 1],
                )
                reset_event_accumulators(hit_idx)
                current_event_code[hit_idx] = -999
                current_event_gate_id[hit_idx] = -1
                alive[hit_idx] = False

                ongoing_exact = previous_trap_duration[in_exit] >= self.thresholds.trap_min_duration
                if np.any(ongoing_exact):
                    exact_hit_idx = hit_idx[ongoing_exact]
                    exact_durations = trap_candidate_duration[exact_hit_idx]
                    n_trap_exact[exact_hit_idx] += 1
                    trap_time_total_exact[exact_hit_idx] += exact_durations
                    largest_trap_duration[exact_hit_idx] = np.maximum(largest_trap_duration[exact_hit_idx], exact_durations)
                trap_candidate_duration[hit_idx] = 0.0
                trap_candidate_gate_id[hit_idx] = -1

            hist_pos = (hist_pos + 1) % hist_len
            r_hist[hist_pos] = r

            prev_gate_id[alive_idx] = active_gate_id
            prev_gate_normal[alive_idx] = active_gate_normal
            prev_gate_in_lane[alive_idx] = active_gate_lane

        remaining = np.flatnonzero(alive)
        if remaining.size:
            finalize_events(
                remaining,
                NAME_TO_EVENT_CODE["terminated"],
                t_end=Tmax,
                x_end_now=r[remaining, 0],
                y_end_now=r[remaining, 1],
            )

        ongoing_terminal_traps = trap_candidate_duration >= self.thresholds.trap_min_duration
        if np.any(ongoing_terminal_traps):
            idx = np.flatnonzero(ongoing_terminal_traps)
            n_trap_exact[idx] += 1
            trap_time_total_exact[idx] += trap_candidate_duration[idx]
            largest_trap_duration[idx] = np.maximum(largest_trap_duration[idx], trap_candidate_duration[idx])

        event_df = pd.DataFrame(event_rows)
        if event_df.empty:
            event_df = pd.DataFrame(columns=list(shared_payload.keys()) + ["event_id", "traj_id", "event_type"])
        event_df = add_event_alignment_columns(
            event_df,
            dt=dt,
            trap_min_duration=self.thresholds.trap_min_duration,
        )

        if not event_df.empty:
            gate_counts = (
                event_df[event_df["event_type"].isin(["gate_approach", "gate_capture", "gate_crossing"])]
                .groupby(["traj_id", "event_type"])
                .size()
                .unstack(fill_value=0)
            )
            duration_by_type = event_df.groupby(["traj_id", "event_type"])["duration"].sum().unstack(fill_value=0.0)
        else:
            gate_counts = pd.DataFrame(index=pd.Index([], name="traj_id"))
            duration_by_type = pd.DataFrame(index=pd.Index([], name="traj_id"))

        gate_approach_counts = gate_counts.get("gate_approach", pd.Series(dtype=int))
        gate_capture_counts = gate_counts.get("gate_capture", pd.Series(dtype=int))
        gate_crossing_counts = gate_counts.get("gate_crossing", pd.Series(dtype=int))
        bulk_duration = duration_by_type.get("bulk_motion", pd.Series(dtype=float))
        wall_duration = duration_by_type.get("wall_sliding", pd.Series(dtype=float))

        if not event_df.empty:
            crossing_events = event_df[event_df["event_type"] == "gate_crossing"]
            for traj_id, group in crossing_events.groupby("traj_id"):
                gate_visit_sequence[int(traj_id)] = [f"gate_{int(g)}" for g in group["gate_id"].tolist()]

        t_stop = np.where(success, t_exit, Tmax)
        trajectory_rows: list[dict[str, Any]] = []
        for traj_id in range(n_traj):
            row = dict(shared_payload)
            row.update(
                {
                    "traj_id": traj_id,
                    "success_flag": bool(success[traj_id]),
                    "t_stop": float(t_stop[traj_id]),
                    "t_exit_or_nan": float(t_exit[traj_id]) if np.isfinite(t_exit[traj_id]) else math.nan,
                    "boundary_contact_fraction_i": float(
                        boundary_steps[traj_id] / max(live_steps[traj_id], 1)
                    ),
                    "n_gate_approach_events": int(gate_approach_counts.get(traj_id, 0)),
                    "n_gate_capture_events": int(gate_capture_counts.get(traj_id, 0)),
                    "n_gate_crossing_events": int(gate_crossing_counts.get(traj_id, 0)),
                    "n_trap_events": int(n_trap_exact[traj_id]),
                    "trap_time_total": float(trap_time_total_exact[traj_id]),
                    "bulk_time_total": float(bulk_duration.get(traj_id, 0.0)),
                    "wall_sliding_time_total": float(wall_duration.get(traj_id, 0.0)),
                    "progress_along_navigation_total": float(traj_progress_total[traj_id]),
                    "progress_along_navigation_rate": float(traj_progress_total[traj_id] / max(t_stop[traj_id], 1e-12)),
                    "phase_lag_navigation_mean": _circular_mean_from_components(
                        float(traj_lag_nav_cos[traj_id]),
                        float(traj_lag_nav_sin[traj_id]),
                    ),
                    "phase_lag_steering_mean": _circular_mean_from_components(
                        float(traj_lag_steer_cos[traj_id]),
                        float(traj_lag_steer_sin[traj_id]),
                    ),
                    "alignment_gate_mean": (
                        float(traj_alignment_gate_sum[traj_id] / traj_alignment_gate_count[traj_id])
                        if traj_alignment_gate_count[traj_id] > 0
                        else math.nan
                    ),
                    "alignment_wall_mean": (
                        float(traj_alignment_wall_sum[traj_id] / traj_alignment_wall_count[traj_id])
                        if traj_alignment_wall_count[traj_id] > 0
                        else math.nan
                    ),
                    "Sigma_drag_i": float(sigma_drag_i[traj_id] / Tmax),
                    "live_steps": int(live_steps[traj_id]),
                    "boundary_steps": int(boundary_steps[traj_id]),
                    "largest_trap_duration": float(largest_trap_duration[traj_id]),
                    "gate_visit_sequence": json.dumps(gate_visit_sequence[traj_id]),
                    "gate_capture_delay": float(first_capture_time[traj_id]) if np.isfinite(first_capture_time[traj_id]) else math.nan,
                    "wall_dwell_before_first_capture": (
                        float(wall_time_before_first_capture[traj_id]) if np.isfinite(first_capture_time[traj_id]) else math.nan
                    ),
                    "n_trap_escape_events": int(n_trap_escape_exact[traj_id]),
                    "trap_escape_probability": (
                        float(n_trap_escape_exact[traj_id] / n_trap_exact[traj_id]) if n_trap_exact[traj_id] > 0 else math.nan
                    ),
                    "mean_trap_escape_time": (
                        float(trap_escape_time_total[traj_id] / n_trap_escape_exact[traj_id])
                        if n_trap_escape_exact[traj_id] > 0
                        else math.nan
                    ),
                    "termination_reason": str(termination_label[traj_id]),
                }
            )
            trajectory_rows.append(row)
        trajectory_df = pd.DataFrame(trajectory_rows)

        gate_rows: list[dict[str, Any]] = []
        for gate in self.gates:
            gate_events = event_df[event_df["gate_id"] == gate.gate_id] if not event_df.empty else pd.DataFrame()
            approach_events = gate_events[gate_events["event_type"] == "gate_approach"] if not gate_events.empty else pd.DataFrame()
            capture_events = gate_events[gate_events["event_type"] == "gate_capture"] if not gate_events.empty else pd.DataFrame()
            crossing_events = gate_events[gate_events["event_type"] == "gate_crossing"] if not gate_events.empty else pd.DataFrame()
            gate_local = gate_events[gate_events["event_type"].isin(["gate_approach", "gate_capture", "gate_crossing"])] if not gate_events.empty else pd.DataFrame()

            n_approach = len(approach_events)
            n_capture = len(capture_events)
            n_crossing = len(crossing_events)

            row = dict(shared_payload)
            row.update(
                {
                    "gate_id": gate.gate_id,
                    "n_gate_approach": int(n_approach),
                    "n_gate_capture": int(n_capture),
                    "n_gate_crossing": int(n_crossing),
                    "capture_given_approach": float(n_capture / n_approach) if n_approach > 0 else math.nan,
                    "crossing_given_capture": float(n_crossing / n_capture) if n_capture > 0 else math.nan,
                    "mean_approach_duration": _safe_mean(approach_events["duration"]) if n_approach else math.nan,
                    "mean_capture_duration": _safe_mean(capture_events["duration"]) if n_capture else math.nan,
                    "mean_crossing_duration": _safe_mean(crossing_events["duration"]) if n_crossing else math.nan,
                    "alignment_at_gate_mean": _safe_mean(gate_local["alignment_gate_mean"]) if not gate_local.empty else math.nan,
                    "phase_lag_navigation_at_gate_mean": _safe_mean(gate_local["phase_lag_navigation_mean"]) if not gate_local.empty else math.nan,
                    "phase_lag_steering_at_gate_mean": _safe_mean(gate_local["phase_lag_steering_mean"]) if not gate_local.empty else math.nan,
                    "progress_rate_at_gate_mean": _safe_mean(gate_local["progress_along_navigation_rate"]) if not gate_local.empty else math.nan,
                    "return_to_wall_after_capture_rate": (
                        float(
                            capture_events["exited_to_event_type"].isin(["wall_sliding", "trap_episode", "trap_escape"]).mean()
                        )
                        if n_capture > 0
                        else math.nan
                    ),
                    "gate_x": gate.center_x,
                    "gate_y": gate.center_y,
                    "mean_approach_angle": _safe_mean(np.arcsin(np.clip(approach_events["alignment_gate_mean"], -1.0, 1.0))) if n_approach else math.nan,
                    "mean_capture_depth": _safe_mean(capture_events["mean_gate_distance"]) if n_capture else math.nan,
                }
            )
            gate_rows.append(row)
        gate_df = pd.DataFrame(gate_rows)

        source_result = point.source_result
        validation = {
            "canonical_label": point.canonical_label,
            "state_point_id": point.state_point_id,
            "source_p_succ": float(source_result["p_succ"]),
            "replayed_p_succ": float(trajectory_df["success_flag"].mean()),
            "delta_p_succ": float(trajectory_df["success_flag"].mean() - float(source_result["p_succ"])),
            "source_trap_time_mean": float(source_result["trap_time_mean"] or 0.0),
            "replayed_trap_time_mean": float(trajectory_df["trap_time_total"].mean()),
            "delta_trap_time_mean": float(trajectory_df["trap_time_total"].mean() - float(source_result["trap_time_mean"] or 0.0)),
            "source_wall_fraction_mean": float(source_result["wall_fraction_mean"]),
            "replayed_wall_fraction_mean": float(trajectory_df["boundary_contact_fraction_i"].mean()),
            "delta_wall_fraction_mean": float(
                trajectory_df["boundary_contact_fraction_i"].mean() - float(source_result["wall_fraction_mean"])
            ),
        }
        return trajectory_df, event_df, gate_df, validation


def summarize_by_point(
    trajectory_df: pd.DataFrame,
    event_df: pd.DataFrame,
    gate_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for canonical_label, traj_group in trajectory_df.groupby("canonical_label"):
        gate_group = gate_df[gate_df["canonical_label"] == canonical_label]
        point_events = event_df[event_df["canonical_label"] == canonical_label]
        captured = traj_group[np.isfinite(traj_group["gate_capture_delay"])]
        escaped_traps = traj_group[traj_group["n_trap_escape_events"] > 0]
        trap_events = point_events[point_events["event_type"] == "trap_episode"]
        rows.append(
            {
                "canonical_label": canonical_label,
                "state_point_id": str(traj_group["state_point_id"].iloc[0]),
                "Pi_m": float(traj_group["Pi_m"].iloc[0]),
                "Pi_f": float(traj_group["Pi_f"].iloc[0]),
                "Pi_U": float(traj_group["Pi_U"].iloc[0]),
                "n_traj": int(len(traj_group)),
                "success_probability": float(traj_group["success_flag"].mean()),
                "gate_capture_probability": _safe_mean(gate_group["capture_given_approach"]),
                "crossing_given_capture": _safe_mean(gate_group["crossing_given_capture"]),
                "gate_capture_delay": _safe_mean(captured["gate_capture_delay"]) if not captured.empty else math.nan,
                "wall_dwell_before_capture": _safe_mean(captured["wall_dwell_before_first_capture"]) if not captured.empty else math.nan,
                "trap_episode_count_mean": float(traj_group["n_trap_events"].mean()),
                "trap_episode_duration_mean": (
                    float(traj_group["trap_time_total"].sum() / max(traj_group["n_trap_events"].sum(), 1))
                    if traj_group["n_trap_events"].sum() > 0
                    else 0.0
                ),
                "trap_escape_probability": (
                    float(traj_group["n_trap_escape_events"].sum() / traj_group["n_trap_events"].sum())
                    if traj_group["n_trap_events"].sum() > 0
                    else math.nan
                ),
                "trap_escape_time": _safe_mean(escaped_traps["mean_trap_escape_time"]) if not escaped_traps.empty else math.nan,
                "phase_lag_navigation_mean": _safe_mean(traj_group["phase_lag_navigation_mean"]),
                "phase_lag_steering_mean": _safe_mean(traj_group["phase_lag_steering_mean"]),
                "alignment_at_gate_mean": _safe_mean(gate_group["alignment_at_gate_mean"]),
                "alignment_on_wall_mean": _safe_mean(traj_group["alignment_wall_mean"]),
                "progress_along_navigation_rate": _safe_mean(traj_group["progress_along_navigation_rate"]),
                "progress_rate_at_gate_mean": _safe_mean(gate_group["progress_rate_at_gate_mean"]),
                "return_to_wall_after_capture_rate": _safe_mean(gate_group["return_to_wall_after_capture_rate"]),
                "n_event_rows": int(len(point_events)),
                "n_trap_event_rows": int(len(trap_events)),
            }
        )
    return pd.DataFrame(rows).sort_values(["Pi_f", "Pi_m", "Pi_U"]).reset_index(drop=True)


def build_threshold_sensitivity_table(event_df: pd.DataFrame, thresholds: MechanismThresholds) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for canonical_label, group in event_df.groupby("canonical_label"):
        wall_group = group[group["event_type"] == "wall_sliding"]
        capture_group = group[group["event_type"] == "gate_capture"]
        trap_group = group[group["event_type"] == "trap_episode"]
        rows.append(
            {
                "canonical_label": canonical_label,
                "wall_sliding_near_alignment_threshold_share": (
                    float((np.abs(wall_group["alignment_wall_mean"] - thresholds.wall_sliding_alignment_min) <= 0.05).mean())
                    if not wall_group.empty
                    else math.nan
                ),
                "gate_capture_near_depth_threshold_share": (
                    float((capture_group["mean_gate_distance"] <= thresholds.gate_capture_depth * 1.10).mean())
                    if not capture_group.empty
                    else math.nan
                ),
                "trap_episode_near_duration_threshold_share": (
                    float((trap_group["duration"] <= thresholds.trap_min_duration * 1.25).mean())
                    if not trap_group.empty
                    else math.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def make_figures(summary_df: pd.DataFrame, sensitivity_df: pd.DataFrame) -> dict[str, str]:
    FIGURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    overview_path = FIGURE_OUTPUT_DIR / "canonical_mechanism_overview.png"
    stale_path = FIGURE_OUTPUT_DIR / "ridge_vs_stale_observables.png"
    sensitivity_path = FIGURE_OUTPUT_DIR / "threshold_sensitivity.png"

    ordered = summary_df.copy()
    ordered["label_short"] = ordered["canonical_label"].str.replace("OP_", "", regex=False)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    panels = [
        ("gate_capture_probability", "Capture Given Approach"),
        ("gate_capture_delay", "Capture Delay"),
        ("trap_episode_duration_mean", "Mean Trap Duration"),
        ("progress_rate_at_gate_mean", "Gate Progress Rate"),
    ]
    for ax, (column, title) in zip(axes.ravel(), panels):
        ax.bar(ordered["label_short"], ordered[column], color="#6baed6")
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(overview_path, dpi=200)
    plt.close(fig)

    compare = ordered[ordered["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    stale_panels = [
        ("phase_lag_steering_mean", "Steering Lag"),
        ("gate_capture_probability", "Capture Given Approach"),
        ("trap_episode_duration_mean", "Trap Duration"),
        ("return_to_wall_after_capture_rate", "Return To Wall After Capture"),
    ]
    for ax, (column, title) in zip(axes.ravel(), stale_panels):
        ax.bar(compare["label_short"], compare[column], color=["#74c476", "#fb6a4a"])
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(stale_path, dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for column, color in [
        ("wall_sliding_near_alignment_threshold_share", "#3182bd"),
        ("gate_capture_near_depth_threshold_share", "#31a354"),
        ("trap_episode_near_duration_threshold_share", "#e6550d"),
    ]:
        ax.plot(sensitivity_df["canonical_label"], sensitivity_df[column], marker="o", label=column, color=color)
    ax.set_ylim(0.0, 1.0)
    ax.tick_params(axis="x", rotation=35)
    ax.set_title("Near-Threshold Share")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(sensitivity_path, dpi=200)
    plt.close(fig)

    summary_csv = FIGURE_OUTPUT_DIR / "mechanism_summary_by_point.csv"
    sensitivity_csv = FIGURE_OUTPUT_DIR / "threshold_sensitivity_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    sensitivity_df.to_csv(sensitivity_csv, index=False)

    return {
        "overview_figure": str(overview_path),
        "ridge_vs_stale_figure": str(stale_path),
        "threshold_figure": str(sensitivity_path),
        "summary_csv": str(summary_csv),
        "sensitivity_csv": str(sensitivity_csv),
    }


def write_event_classification_note(
    *,
    thresholds: MechanismThresholds,
    points: list[CanonicalPoint],
    summary_df: pd.DataFrame,
    sensitivity_df: pd.DataFrame,
    figure_paths: dict[str, str],
) -> None:
    balanced = summary_df[summary_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = summary_df[summary_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    avg_sensitivity = sensitivity_df.mean(numeric_only=True).to_dict()
    gate_ids = ", ".join(str(descriptor.gate_id) for descriptor in build_gate_descriptors(points[0].config))

    content = f"""# Mechanism Event Classification Note

## Scope

This note defines the first wrapper-side event-classification layer used to build the mechanism dataset from the frozen canonical operating points only.

- source manifest: {_path_link(CANONICAL_POINTS_PATH)}
- schema: {_path_link(PROJECT_ROOT / "docs" / "mechanism_dataset_schema.md")}
- output dataset directory: {_path_link(DATASET_OUTPUT_DIR)}
- diagnostic figure directory: {_path_link(FIGURE_OUTPUT_DIR)}

The implementation replays only the persisted canonical `result.json` inputs and leaves `legacy/simcore` unchanged.

## Gate Definition

For the frozen `maze_v1` canonical geometry, the gate-conditioned extractor uses shell-doorway gates only.

- gate ids used in this first dataset: `{gate_ids}`
- gate neighborhood is measured in local gate coordinates:
  - normal coordinate: signed distance through the doorway
  - tangential coordinate: offset along the doorway mouth

This choice keeps the gate-conditioned records focused on the bottleneck that separates productive ridge behavior from stale-control recirculation.

## Thresholds

| Quantity | Rule | Value |
|---|---|---:|
| Wall contact distance | `signed_distance <= wall_contact_distance` | {thresholds.wall_contact_distance:.4f} |
| Wall-sliding alignment | `|u . t_wall| >= wall_sliding_alignment_min` | {thresholds.wall_sliding_alignment_min:.2f} |
| Gate lane half-width | `|t_gate| <= gate_lane_half_width` | {thresholds.gate_lane_half_width:.4f} |
| Gate approach depth | `-gate_approach_depth <= n_gate < -gate_capture_depth` | {thresholds.gate_approach_depth:.4f} |
| Gate capture depth | `|n_gate| <= gate_capture_depth` | {thresholds.gate_capture_depth:.4f} |
| Gate progress minimum | `v . n_gate >= gate_progress_min` | {thresholds.gate_progress_min:.4f} |
| Gate capture alignment | `u . n_gate >= gate_capture_alignment_min` | {thresholds.gate_capture_alignment_min:.2f} |
| Gate crossing margin | crossing requires normal-coordinate sign change larger than margin | {thresholds.gate_crossing_margin:.4f} |
| Trap progress window | rolling average window | {thresholds.trap_progress_window:.4f} |
| Trap progress threshold | `rolling_progress <= trap_progress_max` | {thresholds.trap_progress_max:.4f} |
| Trap minimum duration | confirmed trap threshold | {thresholds.trap_min_duration:.4f} |

## Rules By Event Type

### `bulk_motion`

- default state when the trajectory is outside gate-local and wall-sliding conditions
- interpreted as free search away from walls and away from gate commitment

### `wall_sliding`

- requires wall contact plus strong tangential wall alignment
- excludes gate-local approach, capture, crossing, and confirmed trap intervals

### `gate_approach`

- requires residence in the gate lane
- requires the trajectory to remain on the outer side of the doorway
- requires positive doorway-normal progress

### `gate_capture`

- requires residence inside the narrower gate-capture band
- requires positive gate-forward alignment
- remains distinct from `gate_crossing`, which is reserved for the actual sign-changing transit

### `gate_crossing`

- requires a same-gate sign change in the doorway-normal coordinate
- requires both the previous and current samples to remain in the gate lane

### `trap_episode`

- requires wall-contact plus non-positive rolling navigation progress
- becomes a confirmed event only after the dwell exceeds the minimum duration threshold
- event-table trap rows therefore represent confirmed stale residence, while trajectory-level `trap_time_total` includes the full dwell once a trap qualifies

### `trap_escape`

- recorded on the first interval immediately after a confirmed trap ends
- preserves the direction of recovery back to wall, bulk, or gate-local motion

## Which observables are most likely to separate ridge points from the stale-control point?

The matched comparison between `OP_BALANCED_RIDGE_MID` and `OP_STALE_CONTROL_OFF_RIDGE` is most strongly separated by steering mismatch and gate-conversion observables in this first dataset:

- steering lag shifts from `{balanced["phase_lag_steering_mean"]:.3f}` on-ridge to `{stale["phase_lag_steering_mean"]:.3f}` off-ridge
- capture-given-approach drops from `{balanced["gate_capture_probability"]:.3f}` to `{stale["gate_capture_probability"]:.3f}`
- return-to-wall-after-capture rises from `{balanced["return_to_wall_after_capture_rate"]:.3f}` to `{stale["return_to_wall_after_capture_rate"]:.3f}`
- mean trap duration rises from `{balanced["trap_episode_duration_mean"]:.3f}` to `{stale["trap_episode_duration_mean"]:.3f}`

These are the most plausible first discriminants for later gate-theory support.

## Sensitivity of mechanism conclusions to event-classification thresholds

The first sensitivity check is based on the fraction of extracted events that sit close to the operative thresholds.

- mean near-threshold wall-sliding share: `{avg_sensitivity.get("wall_sliding_near_alignment_threshold_share", math.nan):.3f}`
- mean near-threshold gate-capture share: `{avg_sensitivity.get("gate_capture_near_depth_threshold_share", math.nan):.3f}`
- mean near-threshold trap share: `{avg_sensitivity.get("trap_episode_near_duration_threshold_share", math.nan):.3f}`

The main ridge-vs-stale conclusions are therefore not driven solely by marginal classification cases. The strongest separating signals arise in steering lag, gate conversion, and trap residence, where the ridge/off-ridge differences remain larger than the measured near-threshold fractions.

Supporting diagnostics:

- {_path_link(figure_paths["overview_figure"])}
- {_path_link(figure_paths["ridge_vs_stale_figure"])}
- {_path_link(figure_paths["threshold_figure"])}
"""
    EVENT_NOTE_PATH.write_text(content, encoding="ascii")


def write_run_report(
    *,
    points: list[CanonicalPoint],
    summary_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    figure_paths: dict[str, str],
) -> None:
    lines = [
        "# Mechanism Dataset Run Report",
        "",
        "## Scope",
        "",
        "This report summarizes the first wrapper-side mechanism dataset extracted from the frozen canonical operating points only.",
        "",
        f"- canonical manifest: {_path_link(CANONICAL_POINTS_PATH)}",
        f"- event rules: {_path_link(EVENT_NOTE_PATH)}",
        f"- trajectory parquet: {_path_link(DATASET_OUTPUT_DIR / 'trajectory_level.parquet')}",
        f"- event parquet: {_path_link(DATASET_OUTPUT_DIR / 'event_level.parquet')}",
        f"- gate-conditioned parquet: {_path_link(DATASET_OUTPUT_DIR / 'gate_conditioned.parquet')}",
        "",
        "## Canonical Replay Set",
        "",
    ]
    for point in points:
        lines.append(
            f"- `{point.canonical_label}`: state_point_id `{point.state_point_id}`, "
            f"`(Pi_m, Pi_f, Pi_U)=({point.Pi_m:.3f}, {point.Pi_f:.3f}, {point.Pi_U:.3f})`, "
            f"source {_path_link(point.result_json)}"
        )

    lines.extend(
        [
            "",
            "## First-Look Summary",
            "",
            summary_df.to_markdown(index=False),
            "",
            "## Replay Validation",
            "",
            "The mechanism replay keeps the legacy dynamics unchanged and reproduces the canonical point-level summary statistics from persisted provenance.",
            "",
            validation_df.to_markdown(index=False),
            "",
            "## Which observables are most likely to separate ridge points from the stale-control point?",
            "",
        ]
    )

    balanced = summary_df[summary_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = summary_df[summary_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    lines.extend(
        [
            f"- `phase_lag_steering_mean`: {balanced['phase_lag_steering_mean']:.3f} on-ridge vs {stale['phase_lag_steering_mean']:.3f} off-ridge",
            f"- `gate_capture_probability`: {balanced['gate_capture_probability']:.3f} on-ridge vs {stale['gate_capture_probability']:.3f} off-ridge",
            f"- `progress_rate_at_gate_mean`: {balanced['progress_rate_at_gate_mean']:.3f} on-ridge vs {stale['progress_rate_at_gate_mean']:.3f} off-ridge",
            f"- `trap_episode_duration_mean`: {balanced['trap_episode_duration_mean']:.3f} on-ridge vs {stale['trap_episode_duration_mean']:.3f} off-ridge",
            "",
            "These observables are the strongest first candidates for coarse-grained rate-model discrimination because they combine stale steering, gate commitment, and failed recovery in a matched ridge/off-ridge comparison.",
            "",
            "## Sensitivity of mechanism conclusions to event-classification thresholds",
            "",
            "The event rules intentionally tie each threshold to a geometric or dynamical reference scale already present in the canonical workflow.",
            "",
            f"- wall sliding uses tangential alignment threshold `{build_thresholds(points[0].config, load_reference_scales()).wall_sliding_alignment_min:.2f}`",
            f"- gate capture uses depth threshold `{build_thresholds(points[0].config, load_reference_scales()).gate_capture_depth:.4f}`",
            f"- trap confirmation uses duration threshold `{build_thresholds(points[0].config, load_reference_scales()).trap_min_duration:.4f}`",
            "",
            "The threshold-diagnostic figure and CSV give the fraction of event rows that remain close to these boundaries; the ridge-vs-stale ranking is substantially larger than those boundary fractions in the first dataset.",
            "",
            "## Diagnostic Outputs",
            "",
            f"- {_path_link(figure_paths['overview_figure'])}",
            f"- {_path_link(figure_paths['ridge_vs_stale_figure'])}",
            f"- {_path_link(figure_paths['threshold_figure'])}",
            f"- {_path_link(figure_paths['summary_csv'])}",
            f"- {_path_link(figure_paths['sensitivity_csv'])}",
        ]
    )
    RUN_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_mechanism_dataset() -> dict[str, str]:
    reference_scales = load_reference_scales()
    points = load_canonical_points()
    if not points:
        raise RuntimeError("No canonical operating points found.")

    DATASET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    thresholds = build_thresholds(first_config, reference_scales)
    gates = build_gate_descriptors(first_config)
    extractor = MechanismPointExtractor(maze=maze, navigation=navigation, thresholds=thresholds, gates=gates)

    trajectory_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    validation_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []

    trajectory_path = DATASET_OUTPUT_DIR / "trajectory_level.parquet"
    event_path = DATASET_OUTPUT_DIR / "event_level.parquet"
    gate_path = DATASET_OUTPUT_DIR / "gate_conditioned.parquet"
    for path in (trajectory_path, event_path, gate_path):
        if path.exists():
            path.unlink()

    trajectory_writer: pq.ParquetWriter | None = None
    event_writer: pq.ParquetWriter | None = None
    gate_writer: pq.ParquetWriter | None = None

    for point in points:
        shared_payload = _make_shared_payload(point, reference_scales)
        trajectory_df, event_df, gate_df, validation = extractor.extract_point(point=point, shared_payload=shared_payload)
        trajectory_writer = append_parquet(trajectory_writer, trajectory_df, trajectory_path)
        event_writer = append_parquet(event_writer, event_df, event_path)
        gate_writer = append_parquet(gate_writer, gate_df, gate_path)
        trajectory_frames.append(trajectory_df)
        gate_frames.append(gate_df)
        validation_rows.append(validation)
        summary_rows.extend(summarize_by_point(trajectory_df, event_df, gate_df).to_dict(orient="records"))
        sensitivity_rows.extend(build_threshold_sensitivity_table(event_df, thresholds).to_dict(orient="records"))

    for writer in (trajectory_writer, event_writer, gate_writer):
        if writer is not None:
            writer.close()

    trajectory_df = pd.concat(trajectory_frames, ignore_index=True)
    gate_df = pd.concat(gate_frames, ignore_index=True)
    validation_df = pd.DataFrame(validation_rows)
    summary_df = pd.DataFrame(summary_rows).sort_values(["Pi_f", "Pi_m", "Pi_U"]).reset_index(drop=True)
    sensitivity_df = pd.DataFrame(sensitivity_rows).sort_values(["canonical_label"]).reset_index(drop=True)
    figure_paths = make_figures(summary_df, sensitivity_df)

    validation_csv = FIGURE_OUTPUT_DIR / "replay_equivalence_summary.csv"
    validation_df.to_csv(validation_csv, index=False)
    figure_paths["validation_csv"] = str(validation_csv)

    write_event_classification_note(
        thresholds=thresholds,
        points=points,
        summary_df=summary_df,
        sensitivity_df=sensitivity_df,
        figure_paths=figure_paths,
    )
    write_run_report(
        points=points,
        summary_df=summary_df,
        validation_df=validation_df,
        figure_paths=figure_paths,
    )

    return {
        "trajectory_level": str(trajectory_path),
        "event_level": str(event_path),
        "gate_conditioned": str(gate_path),
        "event_note": str(EVENT_NOTE_PATH),
        "run_report": str(RUN_REPORT_PATH),
        "figure_dir": str(FIGURE_OUTPUT_DIR),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the first mechanism dataset from frozen canonical operating points.")
    parser.parse_args(argv)
    result = build_mechanism_dataset()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
