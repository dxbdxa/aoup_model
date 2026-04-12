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
import pyarrow.parquet as pq

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from legacy.simcore.models import DynamicsConfig, GeometryConfig, SweepPoint
from legacy.simcore.simulation import MazeBuilder, NavigationSolver, PointSimulator

from src.runners.run_mechanism_dataset import (
    CANONICAL_POINTS_PATH,
    add_event_alignment_columns,
    append_parquet,
    build_gate_descriptors,
    load_canonical_points,
    load_reference_scales,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined"
FIGURE_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined"
REFINEMENT_NOTE_PATH = PROJECT_ROOT / "docs" / "gate_state_refinement_note.md"
RUN_REPORT_PATH = PROJECT_ROOT / "docs" / "mechanism_refined_run_report.md"
OLD_TRAJECTORY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset" / "trajectory_level.parquet"
OLD_GATE_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset" / "gate_conditioned.parquet"

EVENT_CODE_TO_NAME = {
    0: "bulk_motion",
    1: "wall_sliding",
    2: "gate_approach",
    3: "gate_residence_precommit",
    4: "gate_commit",
    5: "gate_crossing",
    6: "trap_episode",
    7: "trap_escape",
    -1: "start",
    -2: "terminated",
}
NAME_TO_EVENT_CODE = {name: code for code, name in EVENT_CODE_TO_NAME.items()}
GATE_EVENT_NAMES = ("gate_approach", "gate_residence_precommit", "gate_commit", "gate_crossing")


@dataclass(frozen=True)
class RefinedThresholds:
    wall_contact_distance: float
    wall_sliding_alignment_min: float
    gate_lane_half_width: float
    gate_commit_lane_half_width: float
    gate_approach_depth: float
    gate_residence_depth: float
    gate_commit_outer_depth: float
    gate_commit_inner_depth: float
    gate_progress_min: float
    gate_commit_progress_min: float
    gate_commit_alignment_min: float
    gate_crossing_margin: float
    trap_progress_window: float
    trap_progress_max: float
    trap_min_duration: float


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _angle_wrap(values: np.ndarray) -> np.ndarray:
    return (values + np.pi) % (2.0 * np.pi) - np.pi


def _safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return math.nan
    return float(values.mean())


def _circular_mean_from_components(cos_sum: float, sin_sum: float) -> float:
    if abs(cos_sum) < 1e-15 and abs(sin_sum) < 1e-15:
        return math.nan
    return float(math.atan2(sin_sum, cos_sum))


def build_refined_thresholds(config: Any, reference_scales: dict[str, Any]) -> RefinedThresholds:
    tau_p = float(reference_scales["tau_p"])
    wall = float(config.wall_thickness)
    gate = float(config.gate_width)
    return RefinedThresholds(
        wall_contact_distance=wall,
        wall_sliding_alignment_min=0.70,
        gate_lane_half_width=0.50 * gate + 0.50 * wall,
        gate_commit_lane_half_width=0.30 * gate + 0.25 * wall,
        gate_approach_depth=max(0.75 * gate, 1.50 * wall),
        gate_residence_depth=max(0.35 * gate, 0.75 * wall),
        gate_commit_outer_depth=max(0.18 * gate, 0.45 * wall),
        gate_commit_inner_depth=max(0.50 * wall, 0.12 * gate),
        gate_progress_min=0.05 * float(config.v0),
        gate_commit_progress_min=0.15 * float(config.v0),
        gate_commit_alignment_min=0.60,
        gate_crossing_margin=0.25 * wall,
        trap_progress_window=0.25 * tau_p,
        trap_progress_max=0.0,
        trap_min_duration=0.50 * tau_p,
    )


class RefinedMechanismPointExtractor(PointSimulator):
    def __init__(
        self,
        *,
        maze: Any,
        navigation: Any,
        thresholds: RefinedThresholds,
        gates: tuple[Any, ...],
    ) -> None:
        super().__init__(maze, navigation)
        self.thresholds = thresholds
        self.gates = gates

    def _build_sweep_point(self, config: Any) -> SweepPoint:
        gamma1_over_gamma0 = config.gamma1_over_gamma0
        if gamma1_over_gamma0 is None:
            gamma1_over_gamma0 = (config.gamma1 / config.gamma0) if config.gamma0 else 0.0
        return SweepPoint(
            sweep_id=f"{config.geometry_id}_{config.model_variant}_{config.config_hash[:8]}",
            figure_group="mechanism_dataset_refined",
            control_label="coupled_baseline",
            tau_v=config.tau_v,
            tau_f=config.tau_f,
            U=config.U,
            gamma1_over_gamma0=gamma1_over_gamma0,
            kf=config.kf,
        )

    def _build_dynamics(self, config: Any) -> DynamicsConfig:
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
        point: Any,
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
        event_signed_wall_tangent_sum = np.zeros(n_traj, dtype=float)
        event_signed_wall_tangent_count = np.zeros(n_traj, dtype=np.int64)
        event_signed_gate_tangent_sum = np.zeros(n_traj, dtype=float)
        event_signed_gate_tangent_count = np.zeros(n_traj, dtype=np.int64)
        event_gate_approach_angle_sin = np.zeros(n_traj, dtype=float)
        event_gate_approach_angle_cos = np.zeros(n_traj, dtype=float)
        event_gate_approach_angle_count = np.zeros(n_traj, dtype=np.int64)
        event_recirculation_sum = np.zeros(n_traj, dtype=float)
        event_recirculation_count = np.zeros(n_traj, dtype=np.int64)
        event_global_circulation_sum = np.zeros(n_traj, dtype=float)
        event_global_circulation_count = np.zeros(n_traj, dtype=np.int64)
        event_wall_dist_sum = np.zeros(n_traj, dtype=float)
        event_wall_dist_count = np.zeros(n_traj, dtype=np.int64)
        event_gate_dist_sum = np.zeros(n_traj, dtype=float)
        event_gate_dist_count = np.zeros(n_traj, dtype=np.int64)
        event_speed_sum = np.zeros(n_traj, dtype=float)
        event_speed_count = np.zeros(n_traj, dtype=np.int64)
        event_x_start = np.zeros(n_traj, dtype=float)
        event_y_start = np.zeros(n_traj, dtype=float)

        traj_progress_total = np.zeros(n_traj, dtype=float)
        traj_lag_nav_sin = np.zeros(n_traj, dtype=float)
        traj_lag_nav_cos = np.zeros(n_traj, dtype=float)
        traj_lag_steer_sin = np.zeros(n_traj, dtype=float)
        traj_lag_steer_cos = np.zeros(n_traj, dtype=float)
        traj_alignment_gate_sum = np.zeros(n_traj, dtype=float)
        traj_alignment_gate_count = np.zeros(n_traj, dtype=np.int64)
        traj_alignment_wall_sum = np.zeros(n_traj, dtype=float)
        traj_alignment_wall_count = np.zeros(n_traj, dtype=np.int64)
        traj_signed_wall_tangent_sum = np.zeros(n_traj, dtype=float)
        traj_signed_wall_tangent_count = np.zeros(n_traj, dtype=np.int64)
        traj_gate_angle_sin = np.zeros(n_traj, dtype=float)
        traj_gate_angle_cos = np.zeros(n_traj, dtype=float)
        traj_gate_angle_count = np.zeros(n_traj, dtype=np.int64)
        traj_recirculation_sum = np.zeros(n_traj, dtype=float)
        traj_recirculation_count = np.zeros(n_traj, dtype=np.int64)
        traj_wall_circulation_sum = np.zeros(n_traj, dtype=float)
        traj_wall_circulation_count = np.zeros(n_traj, dtype=np.int64)

        wall_time_before_first_residence = np.zeros(n_traj, dtype=float)
        wall_time_before_first_commit = np.zeros(n_traj, dtype=float)
        first_residence_time = np.full(n_traj, np.nan, dtype=float)
        first_commit_time = np.full(n_traj, np.nan, dtype=float)

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
            event_signed_wall_tangent_sum[indices] = 0.0
            event_signed_wall_tangent_count[indices] = 0
            event_signed_gate_tangent_sum[indices] = 0.0
            event_signed_gate_tangent_count[indices] = 0
            event_gate_approach_angle_sin[indices] = 0.0
            event_gate_approach_angle_cos[indices] = 0.0
            event_gate_approach_angle_count[indices] = 0
            event_recirculation_sum[indices] = 0.0
            event_recirculation_count[indices] = 0
            event_global_circulation_sum[indices] = 0.0
            event_global_circulation_count[indices] = 0
            event_wall_dist_sum[indices] = 0.0
            event_wall_dist_count[indices] = 0
            event_gate_dist_sum[indices] = 0.0
            event_gate_dist_count[indices] = 0
            event_speed_sum[indices] = 0.0
            event_speed_count[indices] = 0

        def finalize_events(
            indices: np.ndarray,
            exited_to_code: int,
            *,
            t_end: float,
            x_end_now: np.ndarray,
            y_end_now: np.ndarray,
        ) -> None:
            for local_pos, traj_idx in enumerate(indices.tolist()):
                code = int(current_event_code[traj_idx])
                if code == -999 or event_duration[traj_idx] <= 0.0:
                    continue
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
                        "gate_id": int(current_event_gate_id[traj_idx]),
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
                        "signed_wall_tangent_mean": (
                            float(event_signed_wall_tangent_sum[traj_idx] / event_signed_wall_tangent_count[traj_idx])
                            if event_signed_wall_tangent_count[traj_idx] > 0
                            else math.nan
                        ),
                        "signed_gate_tangent_mean": (
                            float(event_signed_gate_tangent_sum[traj_idx] / event_signed_gate_tangent_count[traj_idx])
                            if event_signed_gate_tangent_count[traj_idx] > 0
                            else math.nan
                        ),
                        "signed_gate_approach_angle_mean": _circular_mean_from_components(
                            float(event_gate_approach_angle_cos[traj_idx]),
                            float(event_gate_approach_angle_sin[traj_idx]),
                        )
                        if event_gate_approach_angle_count[traj_idx] > 0
                        else math.nan,
                        "local_recirculation_polarity_mean": (
                            float(event_recirculation_sum[traj_idx] / event_recirculation_count[traj_idx])
                            if event_recirculation_count[traj_idx] > 0
                            else math.nan
                        ),
                        "wall_circulation_signed_mean": (
                            float(event_global_circulation_sum[traj_idx] / event_global_circulation_count[traj_idx])
                            if event_global_circulation_count[traj_idx] > 0
                            else math.nan
                        ),
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
            wall_alignment_signed = motion_x * wall_tx + motion_y * wall_ty
            wall_alignment = np.abs(wall_alignment_signed)

            radius = np.hypot(r[alive_idx, 0], r[alive_idx, 1])
            global_circulation = np.divide(
                r[alive_idx, 0] * motion_y - r[alive_idx, 1] * motion_x,
                np.maximum(radius, 1e-12),
            )

            active_gate_id = np.full(alive_idx.size, -1, dtype=int)
            active_gate_normal = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_tangent = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_distance = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_alignment = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_progress = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_tangent_motion = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_lane = np.zeros(alive_idx.size, dtype=bool)
            active_commit_lane = np.zeros(alive_idx.size, dtype=bool)
            active_gate_approach_angle = np.full(alive_idx.size, np.nan, dtype=float)
            active_gate_recirculation = np.full(alive_idx.size, np.nan, dtype=float)
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
                tangent_motion = motion_x * gate.tangent_x + motion_y * gate.tangent_y
                normal_motion = motion_x * gate.normal_x + motion_y * gate.normal_y
                approach_angle = np.arctan2(tangent_motion, np.maximum(np.abs(normal_motion), 1e-12))
                local_radius = np.hypot(rel_x, rel_y)
                recirculation = np.divide(rel_x * motion_y - rel_y * motion_x, np.maximum(local_radius, 1e-12))
                active_gate_id = np.where(better, gate.gate_id, active_gate_id)
                active_gate_normal = np.where(better, normal_coord, active_gate_normal)
                active_gate_tangent = np.where(better, tangent_coord, active_gate_tangent)
                active_gate_distance = np.where(better, gate_distance, active_gate_distance)
                active_gate_alignment = np.where(better, normal_motion, active_gate_alignment)
                active_gate_progress = np.where(
                    better,
                    v[alive_idx, 0] * gate.normal_x + v[alive_idx, 1] * gate.normal_y,
                    active_gate_progress,
                )
                active_gate_tangent_motion = np.where(better, tangent_motion, active_gate_tangent_motion)
                active_gate_approach_angle = np.where(better, approach_angle, active_gate_approach_angle)
                active_gate_recirculation = np.where(better, recirculation, active_gate_recirculation)
                active_gate_lane = np.where(
                    better,
                    np.abs(tangent_coord) <= self.thresholds.gate_lane_half_width,
                    active_gate_lane,
                )
                active_commit_lane = np.where(
                    better,
                    np.abs(tangent_coord) <= self.thresholds.gate_commit_lane_half_width,
                    active_commit_lane,
                )

            crossing_now = (
                (prev_gate_id[alive_idx] == active_gate_id)
                & prev_gate_in_lane[alive_idx]
                & active_commit_lane
                & np.isfinite(prev_gate_normal[alive_idx])
                & (prev_gate_normal[alive_idx] < -self.thresholds.gate_crossing_margin)
                & (active_gate_normal >= self.thresholds.gate_crossing_margin)
            )
            approach_now = (
                active_gate_lane
                & (active_gate_normal >= -self.thresholds.gate_approach_depth)
                & (active_gate_normal < -self.thresholds.gate_residence_depth)
                & (active_gate_progress >= self.thresholds.gate_progress_min)
            )
            residence_now = (
                active_gate_lane
                & (np.abs(active_gate_normal) <= self.thresholds.gate_residence_depth)
                & ~crossing_now
            )
            commit_now = (
                active_commit_lane
                & (active_gate_normal >= -self.thresholds.gate_commit_outer_depth)
                & (active_gate_normal <= self.thresholds.gate_commit_inner_depth)
                & (active_gate_progress >= self.thresholds.gate_commit_progress_min)
                & (active_gate_alignment >= self.thresholds.gate_commit_alignment_min)
                & ~crossing_now
            )
            residence_now = residence_now & ~commit_now
            wall_sliding_now = boundary_contact & (wall_alignment >= self.thresholds.wall_sliding_alignment_min)

            previous_trap_duration = trap_candidate_duration[alive_idx].copy()
            new_trap_start = trapped_now & (previous_trap_duration <= 0.0)
            if np.any(new_trap_start):
                trap_candidate_gate_id[alive_idx[new_trap_start]] = np.where(active_gate_id[new_trap_start] >= 0, active_gate_id[new_trap_start], -1)
            trap_candidate_duration[alive_idx] = np.where(trapped_now, previous_trap_duration + dt, 0.0)
            just_escaped = (~trapped_now) & (previous_trap_duration >= self.thresholds.trap_min_duration)
            confirmed_trap_now = trapped_now & (trap_candidate_duration[alive_idx] >= self.thresholds.trap_min_duration)

            proposed_code = np.full(alive_idx.size, NAME_TO_EVENT_CODE["bulk_motion"], dtype=int)
            proposed_gate_id = np.full(alive_idx.size, -1, dtype=int)
            proposed_code = np.where(wall_sliding_now, NAME_TO_EVENT_CODE["wall_sliding"], proposed_code)
            proposed_code = np.where(approach_now, NAME_TO_EVENT_CODE["gate_approach"], proposed_code)
            proposed_code = np.where(residence_now, NAME_TO_EVENT_CODE["gate_residence_precommit"], proposed_code)
            proposed_code = np.where(commit_now, NAME_TO_EVENT_CODE["gate_commit"], proposed_code)
            proposed_code = np.where(crossing_now, NAME_TO_EVENT_CODE["gate_crossing"], proposed_code)
            proposed_code = np.where(confirmed_trap_now, NAME_TO_EVENT_CODE["trap_episode"], proposed_code)
            proposed_code = np.where(just_escaped, NAME_TO_EVENT_CODE["trap_escape"], proposed_code)

            proposed_gate_id = np.where(np.isin(proposed_code, [NAME_TO_EVENT_CODE[name] for name in GATE_EVENT_NAMES]), active_gate_id, proposed_gate_id)
            proposed_gate_id = np.where(proposed_code == NAME_TO_EVENT_CODE["trap_episode"], trap_candidate_gate_id[alive_idx], proposed_gate_id)
            proposed_gate_id = np.where(proposed_code == NAME_TO_EVENT_CODE["trap_escape"], trap_candidate_gate_id[alive_idx], proposed_gate_id)

            unchanged = (current_event_code[alive_idx] == proposed_code) & (current_event_gate_id[alive_idx] == proposed_gate_id)
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
                current_event_entered_from[changed_indices] = np.where(
                    current_event_code[changed_indices] == -999,
                    NAME_TO_EVENT_CODE["start"],
                    current_event_code[changed_indices],
                )
                current_event_code[changed_indices] = proposed_code[~unchanged]
                current_event_gate_id[changed_indices] = proposed_gate_id[~unchanged]
                next_event_index[changed_indices] += 1

                residence_started = (
                    current_event_code[changed_indices] == NAME_TO_EVENT_CODE["gate_residence_precommit"]
                ) & ~np.isfinite(first_residence_time[changed_indices])
                if np.any(residence_started):
                    first_residence_time[changed_indices[residence_started]] = step * dt

                commit_started = (
                    current_event_code[changed_indices] == NAME_TO_EVENT_CODE["gate_commit"]
                ) & ~np.isfinite(first_commit_time[changed_indices])
                if np.any(commit_started):
                    first_commit_time[changed_indices[commit_started]] = step * dt

            gate_valid = np.isin(current_event_code[alive_idx], [NAME_TO_EVENT_CODE[name] for name in GATE_EVENT_NAMES])
            gate_approach_valid = np.isin(
                current_event_code[alive_idx],
                [
                    NAME_TO_EVENT_CODE["gate_approach"],
                    NAME_TO_EVENT_CODE["gate_residence_precommit"],
                    NAME_TO_EVENT_CODE["gate_commit"],
                    NAME_TO_EVENT_CODE["gate_crossing"],
                ],
            )
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
            event_signed_wall_tangent_sum[alive_idx[wall_valid]] += wall_alignment_signed[wall_valid]
            event_signed_wall_tangent_count[alive_idx[wall_valid]] += 1
            event_signed_gate_tangent_sum[alive_idx[gate_valid]] += active_gate_tangent_motion[gate_valid]
            event_signed_gate_tangent_count[alive_idx[gate_valid]] += 1
            event_gate_approach_angle_sin[alive_idx[gate_approach_valid]] += np.sin(active_gate_approach_angle[gate_approach_valid])
            event_gate_approach_angle_cos[alive_idx[gate_approach_valid]] += np.cos(active_gate_approach_angle[gate_approach_valid])
            event_gate_approach_angle_count[alive_idx[gate_approach_valid]] += 1
            event_recirculation_sum[alive_idx[gate_valid]] += active_gate_recirculation[gate_valid]
            event_recirculation_count[alive_idx[gate_valid]] += 1
            event_global_circulation_sum[alive_idx[wall_valid]] += global_circulation[wall_valid]
            event_global_circulation_count[alive_idx[wall_valid]] += 1

            traj_progress_total[alive_idx] += progress_speed * dt
            traj_lag_nav_sin[alive_idx] += np.sin(lag_nav)
            traj_lag_nav_cos[alive_idx] += np.cos(lag_nav)
            traj_lag_steer_sin[alive_idx] += np.sin(lag_steer)
            traj_lag_steer_cos[alive_idx] += np.cos(lag_steer)
            traj_alignment_gate_sum[alive_idx[gate_valid]] += active_gate_alignment[gate_valid]
            traj_alignment_gate_count[alive_idx[gate_valid]] += 1
            traj_alignment_wall_sum[alive_idx[wall_valid]] += wall_alignment[wall_valid]
            traj_alignment_wall_count[alive_idx[wall_valid]] += 1
            traj_signed_wall_tangent_sum[alive_idx[wall_valid]] += wall_alignment_signed[wall_valid]
            traj_signed_wall_tangent_count[alive_idx[wall_valid]] += 1
            traj_gate_angle_sin[alive_idx[gate_approach_valid]] += np.sin(active_gate_approach_angle[gate_approach_valid])
            traj_gate_angle_cos[alive_idx[gate_approach_valid]] += np.cos(active_gate_approach_angle[gate_approach_valid])
            traj_gate_angle_count[alive_idx[gate_approach_valid]] += 1
            traj_recirculation_sum[alive_idx[gate_valid]] += active_gate_recirculation[gate_valid]
            traj_recirculation_count[alive_idx[gate_valid]] += 1
            traj_wall_circulation_sum[alive_idx[wall_valid]] += global_circulation[wall_valid]
            traj_wall_circulation_count[alive_idx[wall_valid]] += 1

            wall_time_before_first_residence[alive_idx[wall_valid & ~np.isfinite(first_residence_time[alive_idx])]] += dt
            wall_time_before_first_commit[alive_idx[wall_valid & ~np.isfinite(first_commit_time[alive_idx])]] += dt

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
            prev_gate_in_lane[alive_idx] = active_commit_lane

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
            event_counts = event_df.groupby(["traj_id", "event_type"]).size().unstack(fill_value=0)
            duration_by_type = event_df.groupby(["traj_id", "event_type"])["duration"].sum().unstack(fill_value=0.0)
            crossing_events = event_df[event_df["event_type"] == "gate_crossing"]
            for traj_id, group in crossing_events.groupby("traj_id"):
                gate_visit_sequence[int(traj_id)] = [f"gate_{int(g)}" for g in group["gate_id"].tolist()]
        else:
            event_counts = pd.DataFrame(index=pd.Index([], name="traj_id"))
            duration_by_type = pd.DataFrame(index=pd.Index([], name="traj_id"))

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
                    "boundary_contact_fraction_i": float(boundary_steps[traj_id] / max(live_steps[traj_id], 1)),
                    "n_gate_approach_events": int(event_counts.get("gate_approach", pd.Series(dtype=int)).get(traj_id, 0)),
                    "n_gate_residence_precommit_events": int(event_counts.get("gate_residence_precommit", pd.Series(dtype=int)).get(traj_id, 0)),
                    "n_gate_commit_events": int(event_counts.get("gate_commit", pd.Series(dtype=int)).get(traj_id, 0)),
                    "n_gate_crossing_events": int(event_counts.get("gate_crossing", pd.Series(dtype=int)).get(traj_id, 0)),
                    "n_trap_events": int(n_trap_exact[traj_id]),
                    "trap_time_total": float(trap_time_total_exact[traj_id]),
                    "bulk_time_total": float(duration_by_type.get("bulk_motion", pd.Series(dtype=float)).get(traj_id, 0.0)),
                    "wall_sliding_time_total": float(duration_by_type.get("wall_sliding", pd.Series(dtype=float)).get(traj_id, 0.0)),
                    "gate_residence_precommit_time_total": float(duration_by_type.get("gate_residence_precommit", pd.Series(dtype=float)).get(traj_id, 0.0)),
                    "gate_commit_time_total": float(duration_by_type.get("gate_commit", pd.Series(dtype=float)).get(traj_id, 0.0)),
                    "progress_along_navigation_total": float(traj_progress_total[traj_id]),
                    "progress_along_navigation_rate": float(traj_progress_total[traj_id] / max(t_stop[traj_id], 1e-12)),
                    "phase_lag_navigation_mean": _circular_mean_from_components(float(traj_lag_nav_cos[traj_id]), float(traj_lag_nav_sin[traj_id])),
                    "phase_lag_steering_mean": _circular_mean_from_components(float(traj_lag_steer_cos[traj_id]), float(traj_lag_steer_sin[traj_id])),
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
                    "signed_wall_tangent_mean": (
                        float(traj_signed_wall_tangent_sum[traj_id] / traj_signed_wall_tangent_count[traj_id])
                        if traj_signed_wall_tangent_count[traj_id] > 0
                        else math.nan
                    ),
                    "signed_gate_approach_angle_mean": _circular_mean_from_components(
                        float(traj_gate_angle_cos[traj_id]),
                        float(traj_gate_angle_sin[traj_id]),
                    )
                    if traj_gate_angle_count[traj_id] > 0
                    else math.nan,
                    "local_recirculation_polarity_mean": (
                        float(traj_recirculation_sum[traj_id] / traj_recirculation_count[traj_id])
                        if traj_recirculation_count[traj_id] > 0
                        else math.nan
                    ),
                    "wall_circulation_signed_mean": (
                        float(traj_wall_circulation_sum[traj_id] / traj_wall_circulation_count[traj_id])
                        if traj_wall_circulation_count[traj_id] > 0
                        else math.nan
                    ),
                    "Sigma_drag_i": float(sigma_drag_i[traj_id] / Tmax),
                    "live_steps": int(live_steps[traj_id]),
                    "boundary_steps": int(boundary_steps[traj_id]),
                    "largest_trap_duration": float(largest_trap_duration[traj_id]),
                    "gate_visit_sequence": json.dumps(gate_visit_sequence[traj_id]),
                    "first_gate_residence_delay": float(first_residence_time[traj_id]) if np.isfinite(first_residence_time[traj_id]) else math.nan,
                    "first_gate_commit_delay": float(first_commit_time[traj_id]) if np.isfinite(first_commit_time[traj_id]) else math.nan,
                    "wall_dwell_before_first_residence": (
                        float(wall_time_before_first_residence[traj_id]) if np.isfinite(first_residence_time[traj_id]) else math.nan
                    ),
                    "wall_dwell_before_first_commit": (
                        float(wall_time_before_first_commit[traj_id]) if np.isfinite(first_commit_time[traj_id]) else math.nan
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
            precommit_events = gate_events[gate_events["event_type"] == "gate_residence_precommit"] if not gate_events.empty else pd.DataFrame()
            commit_events = gate_events[gate_events["event_type"] == "gate_commit"] if not gate_events.empty else pd.DataFrame()
            crossing_events = gate_events[gate_events["event_type"] == "gate_crossing"] if not gate_events.empty else pd.DataFrame()
            gate_local = gate_events[gate_events["event_type"].isin(GATE_EVENT_NAMES)] if not gate_events.empty else pd.DataFrame()

            n_approach = len(approach_events)
            n_precommit = len(precommit_events)
            n_commit = len(commit_events)
            n_crossing = len(crossing_events)
            approach_to_residence = (
                float((approach_events["exited_to_event_type"] == "gate_residence_precommit").mean())
                if n_approach > 0
                else math.nan
            )
            residence_to_commit = (
                float((precommit_events["exited_to_event_type"] == "gate_commit").mean())
                if n_precommit > 0
                else math.nan
            )
            commit_to_crossing = (
                float((commit_events["exited_to_event_type"] == "gate_crossing").mean())
                if n_commit > 0
                else math.nan
            )
            row = dict(shared_payload)
            row.update(
                {
                    "gate_id": gate.gate_id,
                    "n_gate_approach": int(n_approach),
                    "n_gate_residence_precommit": int(n_precommit),
                    "n_gate_commit": int(n_commit),
                    "n_gate_crossing": int(n_crossing),
                    "residence_given_approach": approach_to_residence,
                    "commit_given_residence": residence_to_commit,
                    "crossing_given_commit": commit_to_crossing,
                    "mean_approach_duration": _safe_mean(approach_events["duration"]) if n_approach else math.nan,
                    "mean_precommit_duration": _safe_mean(precommit_events["duration"]) if n_precommit else math.nan,
                    "mean_commit_duration": _safe_mean(commit_events["duration"]) if n_commit else math.nan,
                    "mean_crossing_duration": _safe_mean(crossing_events["duration"]) if n_crossing else math.nan,
                    "alignment_at_gate_mean": _safe_mean(gate_local["alignment_gate_mean"]) if not gate_local.empty else math.nan,
                    "steering_lag_at_commit_mean": _safe_mean(commit_events["phase_lag_steering_mean"]) if n_commit else math.nan,
                    "signed_gate_approach_angle_mean": _safe_mean(approach_events["signed_gate_approach_angle_mean"]) if n_approach else math.nan,
                    "local_recirculation_polarity_mean": _safe_mean(gate_local["local_recirculation_polarity_mean"]) if not gate_local.empty else math.nan,
                    "return_to_wall_after_precommit_rate": (
                        float(precommit_events["exited_to_event_type"].isin(["wall_sliding", "trap_episode", "trap_escape"]).mean())
                        if n_precommit > 0
                        else math.nan
                    ),
                    "return_to_wall_after_commit_rate": (
                        float(commit_events["exited_to_event_type"].isin(["wall_sliding", "trap_episode", "trap_escape"]).mean())
                        if n_commit > 0
                        else math.nan
                    ),
                    "return_to_bulk_after_commit_rate": (
                        float(commit_events["exited_to_event_type"].isin(["bulk_motion", "gate_approach", "gate_residence_precommit"]).mean())
                        if n_commit > 0
                        else math.nan
                    ),
                    "gate_x": gate.center_x,
                    "gate_y": gate.center_y,
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
            "source_wall_fraction_mean": float(source_result["wall_fraction_mean"]),
            "replayed_wall_fraction_mean": float(trajectory_df["boundary_contact_fraction_i"].mean()),
            "delta_wall_fraction_mean": float(trajectory_df["boundary_contact_fraction_i"].mean() - float(source_result["wall_fraction_mean"])),
            "source_trap_time_mean": float(source_result["trap_time_mean"] or 0.0),
            "replayed_episode_conditioned_trap_mean": (
                float(trajectory_df["trap_time_total"].sum() / trajectory_df["n_trap_events"].sum())
                if trajectory_df["n_trap_events"].sum() > 0
                else 0.0
            ),
        }
        return trajectory_df, event_df, gate_df, validation


def summarize_refined_by_point(trajectory_df: pd.DataFrame, gate_df: pd.DataFrame) -> pd.DataFrame:
    traj_summary = (
        trajectory_df.groupby("canonical_label")
        .agg(
            state_point_id=("state_point_id", "first"),
            Pi_m=("Pi_m", "first"),
            Pi_f=("Pi_f", "first"),
            Pi_U=("Pi_U", "first"),
            n_traj=("traj_id", "count"),
            success_probability=("success_flag", "mean"),
            first_gate_residence_delay=("first_gate_residence_delay", "mean"),
            first_gate_commit_delay=("first_gate_commit_delay", "mean"),
            wall_dwell_before_first_residence=("wall_dwell_before_first_residence", "mean"),
            wall_dwell_before_first_commit=("wall_dwell_before_first_commit", "mean"),
            trap_burden_mean=("trap_time_total", "mean"),
            trap_event_count_mean=("n_trap_events", "mean"),
            phase_lag_steering_mean=("phase_lag_steering_mean", "mean"),
            signed_wall_tangent_mean=("signed_wall_tangent_mean", "mean"),
            signed_gate_approach_angle_mean=("signed_gate_approach_angle_mean", "mean"),
            local_recirculation_polarity_mean=("local_recirculation_polarity_mean", "mean"),
            wall_circulation_signed_mean=("wall_circulation_signed_mean", "mean"),
        )
        .reset_index()
    )
    gate_summary = (
        gate_df.groupby("canonical_label")
        .agg(
            residence_given_approach=("residence_given_approach", "mean"),
            commit_given_residence=("commit_given_residence", "mean"),
            crossing_given_commit=("crossing_given_commit", "mean"),
            return_to_wall_after_precommit_rate=("return_to_wall_after_precommit_rate", "mean"),
            return_to_wall_after_commit_rate=("return_to_wall_after_commit_rate", "mean"),
            steering_lag_at_commit_mean=("steering_lag_at_commit_mean", "mean"),
            local_recirculation_at_gate_mean=("local_recirculation_polarity_mean", "mean"),
        )
        .reset_index()
    )
    return traj_summary.merge(gate_summary, on="canonical_label", how="left").sort_values(["Pi_f", "Pi_m", "Pi_U"]).reset_index(drop=True)


def compare_old_vs_refined(refined_summary_df: pd.DataFrame) -> pd.DataFrame:
    old_traj = pd.read_parquet(OLD_TRAJECTORY_PATH)
    old_gate = pd.read_parquet(OLD_GATE_PATH)
    old_summary = (
        old_traj.groupby("canonical_label")
        .agg(
            old_gate_capture_delay=("gate_capture_delay", "mean"),
            old_wall_dwell_before_capture=("wall_dwell_before_first_capture", "mean"),
            old_trap_burden_mean=("trap_time_total", "mean"),
            old_phase_lag_steering_mean=("phase_lag_steering_mean", "mean"),
        )
        .reset_index()
    ).merge(
        old_gate.groupby("canonical_label")
        .agg(
            old_gate_capture_probability=("capture_given_approach", "mean"),
            old_return_to_wall_after_capture_rate=("return_to_wall_after_capture_rate", "mean"),
        )
        .reset_index(),
        on="canonical_label",
        how="left",
    )
    compare = old_summary.merge(refined_summary_df, on="canonical_label", how="inner")
    compare["delay_separation_metric"] = compare["first_gate_commit_delay"] - compare["old_gate_capture_delay"]
    return compare


def make_refined_figures(refined_summary_df: pd.DataFrame, compare_df: pd.DataFrame) -> dict[str, str]:
    FIGURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_csv = FIGURE_OUTPUT_DIR / "refined_summary_by_point.csv"
    compare_csv = FIGURE_OUTPUT_DIR / "old_vs_refined_summary.csv"
    refined_summary_df.to_csv(summary_csv, index=False)
    compare_df.to_csv(compare_csv, index=False)

    overview_path = FIGURE_OUTPUT_DIR / "refined_gate_state_summary.png"
    stale_path = FIGURE_OUTPUT_DIR / "balanced_vs_stale_refined.png"
    compare_path = FIGURE_OUTPUT_DIR / "old_vs_refined_balanced_stale.png"

    ordered = refined_summary_df.copy()
    ordered["label_short"] = ordered["canonical_label"].str.replace("OP_", "", regex=False)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    panels = [
        ("commit_given_residence", "Commit Given Residence"),
        ("crossing_given_commit", "Crossing Given Commit"),
        ("first_gate_commit_delay", "First Commit Delay"),
        ("return_to_wall_after_commit_rate", "Return To Wall After Commit"),
    ]
    for ax, (column, title) in zip(axes.ravel(), panels):
        ax.bar(ordered["label_short"], ordered[column], color="#6baed6")
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(overview_path, dpi=200)
    plt.close(fig)

    stale = ordered[ordered["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    stale_panels = [
        ("first_gate_commit_delay", "First Commit Delay"),
        ("wall_dwell_before_first_commit", "Wall Dwell Before Commit"),
        ("return_to_wall_after_commit_rate", "Return To Wall After Commit"),
        ("trap_burden_mean", "Trap Burden"),
        ("steering_lag_at_commit_mean", "Steering Lag At Commit"),
        ("local_recirculation_at_gate_mean", "Gate Recirculation Polarity"),
    ]
    for ax, (column, title) in zip(axes.ravel(), stale_panels):
        ax.bar(stale["label_short"], stale[column], color=["#74c476", "#fb6a4a"])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(stale_path, dpi=200)
    plt.close(fig)

    compare = compare_df[compare_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    metrics = [
        ("old_gate_capture_delay", "first_gate_commit_delay", "Delay"),
        ("old_wall_dwell_before_capture", "wall_dwell_before_first_commit", "Wall Dwell"),
        ("old_gate_capture_probability", "commit_given_residence", "Commit/Residence"),
        ("old_return_to_wall_after_capture_rate", "return_to_wall_after_commit_rate", "Return To Wall"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, (old_col, new_col, title) in zip(axes.ravel(), metrics):
        x = np.arange(len(compare))
        ax.bar(x - 0.18, compare[old_col], width=0.36, label="old", color="#9ecae1")
        ax.bar(x + 0.18, compare[new_col], width=0.36, label="refined", color="#3182bd")
        ax.set_xticks(x)
        ax.set_xticklabels(compare["canonical_label"].str.replace("OP_", "", regex=False), rotation=20)
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(compare_path, dpi=200)
    plt.close(fig)

    return {
        "summary_csv": str(summary_csv),
        "compare_csv": str(compare_csv),
        "overview_figure": str(overview_path),
        "stale_figure": str(stale_path),
        "compare_figure": str(compare_path),
    }


def write_refinement_note(
    *,
    thresholds: RefinedThresholds,
    refined_summary_df: pd.DataFrame,
    figure_paths: dict[str, str],
) -> None:
    balanced = refined_summary_df[refined_summary_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = refined_summary_df[refined_summary_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    max_crossing_given_commit = float(refined_summary_df["crossing_given_commit"].max())
    content = f"""# Gate State Refinement Note

## Scope

This note defines the refined gate-local wrapper-side state graph used before any coarse-grained gate theory fit.

- canonical manifest: {_path_link(CANONICAL_POINTS_PATH)}
- refined dataset directory: {_path_link(DATASET_OUTPUT_DIR)}
- refined figure directory: {_path_link(FIGURE_OUTPUT_DIR)}

The legacy physics kernel remains unchanged.

## Why The Original Gate States Were Refined

The audit showed that the first `gate_capture` proxy was too broad: it mixed mouth residence, partial commitment, and non-transiting near-gate dwell. As a result, `crossing_given_capture` was too small to use directly as a first rate-model transition probability.

## Refined Gate-Local Taxonomy

### `gate_approach`

- outer-side, gate-lane motion with positive inward progress
- intended to represent guided arrival toward the doorway mouth

### `gate_residence_precommit`

- near-mouth residence inside the broader gate band
- may include dithering, tangential recirculation, or failed alignment before commitment

### `gate_commit`

- narrower gate lane
- near-mouth or slightly inner-side position
- stronger inward alignment and stronger inward progress
- intended to represent a cleaner crossing-preparation state

### `gate_crossing`

- actual through-door sign-change transit in the narrow gate lane

## Thresholds

| Quantity | Value |
|---|---:|
| wall_sliding_alignment_min | {thresholds.wall_sliding_alignment_min:.2f} |
| gate_lane_half_width | {thresholds.gate_lane_half_width:.4f} |
| gate_commit_lane_half_width | {thresholds.gate_commit_lane_half_width:.4f} |
| gate_approach_depth | {thresholds.gate_approach_depth:.4f} |
| gate_residence_depth | {thresholds.gate_residence_depth:.4f} |
| gate_commit_outer_depth | {thresholds.gate_commit_outer_depth:.4f} |
| gate_commit_inner_depth | {thresholds.gate_commit_inner_depth:.4f} |
| gate_progress_min | {thresholds.gate_progress_min:.4f} |
| gate_commit_progress_min | {thresholds.gate_commit_progress_min:.4f} |
| gate_commit_alignment_min | {thresholds.gate_commit_alignment_min:.2f} |
| gate_crossing_margin | {thresholds.gate_crossing_margin:.4f} |

## Added Directional Observables

- `signed_wall_tangent_mean`: signed local wall-tangent motion rather than unsigned tangentiality only
- `wall_circulation_signed_mean`: signed circulation around the maze center during wall-local motion
- `signed_gate_approach_angle_mean`: signed gate-local approach angle using tangent-versus-normal motion decomposition
- `local_recirculation_polarity_mean`: signed orbital polarity around the gate center during gate-local states

## Old Versus Refined Definitions

| Old state | Refined interpretation |
|---|---|
| `gate_capture` | split into `gate_residence_precommit` and `gate_commit` |
| `gate_crossing` | preserved, but now attached to a narrower commit lane |
| unsigned wall tangentiality only | supplemented with signed wall circulation and tangent direction |
| unsigned gate-forward alignment only | supplemented with signed gate approach angle and local recirculation polarity |

## Did the refined gate-state definition make stale-control more mechanistically distinguishable?

Only modestly. The refined state graph improves interpretability and makes the matched comparison better targeted, but it does not yet produce a strong stale-control separation in the gate-local transition statistics.

- first gate commit delay: `{balanced["first_gate_commit_delay"]:.4f}` on-ridge vs `{stale["first_gate_commit_delay"]:.4f}` off-ridge
- wall dwell before first commit: `{balanced["wall_dwell_before_first_commit"]:.4f}` on-ridge vs `{stale["wall_dwell_before_first_commit"]:.4f}` off-ridge
- return to wall after commit: `{balanced["return_to_wall_after_commit_rate"]:.4f}` on-ridge vs `{stale["return_to_wall_after_commit_rate"]:.4f}` off-ridge
- steering lag at commit: `{balanced["steering_lag_at_commit_mean"]:.4f}` on-ridge vs `{stale["steering_lag_at_commit_mean"]:.4f}` off-ridge

The delay and wall-dwell differences remain in the expected direction, but the commit conversion and post-commit return metrics remain too similar to support a strong mechanistic separation on gate-local statistics alone.

## Is the refined state graph now clean enough for a first rate model?

Not yet. The refined graph is cleaner than the original because it separates gate-mouth residence from stronger forward commitment. The first candidate state graph is:

- bulk
- wall_sliding
- gate_approach
- gate_residence_precommit
- gate_commit
- gate_crossing
- trap_episode

However, the present refined replay still yields `crossing_given_commit` values only on the order of `{max_crossing_given_commit:.5f}` and `commit_given_residence` remains nearly unchanged across the matched ridge/stale pair. The refined graph should therefore be treated as a cleaner diagnostic layer, not yet as a final first rate-model state graph.

Supporting diagnostics:

- {_path_link(figure_paths["overview_figure"])}
- {_path_link(figure_paths["stale_figure"])}
- {_path_link(figure_paths["compare_figure"])}
"""
    REFINEMENT_NOTE_PATH.write_text(content, encoding="ascii")


def write_refined_run_report(
    *,
    points: list[Any],
    refined_summary_df: pd.DataFrame,
    compare_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    figure_paths: dict[str, str],
) -> None:
    balanced = refined_summary_df[refined_summary_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = refined_summary_df[refined_summary_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    max_crossing_given_commit = float(refined_summary_df["crossing_given_commit"].max())
    compare_slice = compare_df[
        compare_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])
    ][
        [
            "canonical_label",
            "old_gate_capture_delay",
            "first_gate_commit_delay",
            "old_wall_dwell_before_capture",
            "wall_dwell_before_first_commit",
            "old_gate_capture_probability",
            "commit_given_residence",
            "old_return_to_wall_after_capture_rate",
            "return_to_wall_after_commit_rate",
        ]
    ]
    lines = [
        "# Mechanism Refined Run Report",
        "",
        "## Scope",
        "",
        "This report summarizes the refined gate-local mechanism replay on the frozen canonical operating points.",
        "",
        f"- canonical manifest: {_path_link(CANONICAL_POINTS_PATH)}",
        f"- refinement note: {_path_link(REFINEMENT_NOTE_PATH)}",
        f"- refined trajectory parquet: {_path_link(DATASET_OUTPUT_DIR / 'trajectory_level.parquet')}",
        f"- refined event parquet: {_path_link(DATASET_OUTPUT_DIR / 'event_level.parquet')}",
        f"- refined gate-conditioned parquet: {_path_link(DATASET_OUTPUT_DIR / 'gate_conditioned.parquet')}",
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
            "## Refined Summary",
            "",
            refined_summary_df.to_markdown(index=False),
            "",
            "## Replay Validation",
            "",
            validation_df.to_markdown(index=False),
            "",
            "## Old Versus Refined Gate Definition",
            "",
            compare_slice.to_markdown(index=False),
            "",
            "## Did the refined gate-state definition make stale-control more mechanistically distinguishable?",
            "",
            f"- First commit delay increases from {balanced['first_gate_commit_delay']:.4f} on the balanced ridge point to {stale['first_gate_commit_delay']:.4f} on the stale-control point.",
            f"- Wall dwell before first commit increases from {balanced['wall_dwell_before_first_commit']:.4f} to {stale['wall_dwell_before_first_commit']:.4f}.",
            f"- Post-commit return-to-wall changes from {balanced['return_to_wall_after_commit_rate']:.4f} to {stale['return_to_wall_after_commit_rate']:.4f}.",
            f"- Trap burden changes from {balanced['trap_burden_mean']:.6f} to {stale['trap_burden_mean']:.6f}.",
            f"- Steering lag at commit changes from {balanced['steering_lag_at_commit_mean']:.4f} to {stale['steering_lag_at_commit_mean']:.4f}.",
            "",
            "This refined matched comparison is more interpretable than the original proxy capture state because the compared quantities are tied to a narrower commitment definition rather than broad gate-mouth residence.",
            "",
            "## Is the refined state graph now clean enough for a first rate model?",
            "",
            f"- `commit_given_residence` at the balanced ridge point is {balanced['commit_given_residence']:.4f}; at the stale-control point it is {stale['commit_given_residence']:.4f}.",
            f"- `crossing_given_commit` at the balanced ridge point is {balanced['crossing_given_commit']:.4f}; at the stale-control point it is {stale['crossing_given_commit']:.4f}.",
            "- If `crossing_given_commit` is now materially larger and less degenerate than the old `crossing_given_capture`, the refined graph is suitable for a first reduced rate model.",
            "- If post-commit return remains dominant and crossing remains extremely sparse, the graph is improved but still should be treated as a pre-rate-model diagnostic layer.",
            "",
            "## Diagnostic Outputs",
            "",
            f"- {_path_link(figure_paths['overview_figure'])}",
            f"- {_path_link(figure_paths['stale_figure'])}",
            f"- {_path_link(figure_paths['compare_figure'])}",
            f"- {_path_link(figure_paths['summary_csv'])}",
            f"- {_path_link(figure_paths['compare_csv'])}",
        ]
    )
    RUN_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_refined_dataset() -> dict[str, str]:
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

    for point in points:
        shared_payload = {
            "schema_version": "mechanism_dataset_refined_v1",
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
        trajectory_df, event_df, gate_df, validation = extractor.extract_point(point=point, shared_payload=shared_payload)
        trajectory_writer = append_parquet(trajectory_writer, trajectory_df, trajectory_path)
        event_writer = append_parquet(event_writer, event_df, event_path)
        gate_writer = append_parquet(gate_writer, gate_df, gate_path)
        trajectory_frames.append(trajectory_df)
        gate_frames.append(gate_df)
        validation_rows.append(validation)

    for writer in (trajectory_writer, event_writer, gate_writer):
        if writer is not None:
            writer.close()

    trajectory_df = pd.concat(trajectory_frames, ignore_index=True)
    gate_df = pd.concat(gate_frames, ignore_index=True)
    validation_df = pd.DataFrame(validation_rows)
    refined_summary_df = summarize_refined_by_point(trajectory_df, gate_df)
    compare_df = compare_old_vs_refined(refined_summary_df)
    figure_paths = make_refined_figures(refined_summary_df, compare_df)
    validation_csv = FIGURE_OUTPUT_DIR / "refined_replay_validation.csv"
    validation_df.to_csv(validation_csv, index=False)
    figure_paths["validation_csv"] = str(validation_csv)

    write_refinement_note(
        thresholds=thresholds,
        refined_summary_df=refined_summary_df,
        figure_paths=figure_paths,
    )
    write_refined_run_report(
        points=points,
        refined_summary_df=refined_summary_df,
        compare_df=compare_df,
        validation_df=validation_df,
        figure_paths=figure_paths,
    )
    return {
        "trajectory_level": str(trajectory_path),
        "event_level": str(event_path),
        "gate_conditioned": str(gate_path),
        "refinement_note": str(REFINEMENT_NOTE_PATH),
        "run_report": str(RUN_REPORT_PATH),
        "figure_dir": str(FIGURE_OUTPUT_DIR),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the refined gate-state mechanism dataset from frozen canonical operating points.")
    parser.parse_args(argv)
    result = build_refined_dataset()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
