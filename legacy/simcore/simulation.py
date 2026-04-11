from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.ndimage import distance_transform_edt
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

from .models import DynamicsConfig, GeometryConfig, RuntimePaths, SimulationTask, SweepPoint, TaskRunResult, dataclass_dict


@dataclass(frozen=True)
class MazeGeometry:
    config: GeometryConfig
    x: np.ndarray
    y: np.ndarray
    X: np.ndarray
    Y: np.ndarray
    h: float
    wall: np.ndarray
    free: np.ndarray
    exit_mask: np.ndarray
    inlet_mask: np.ndarray
    signed_distance: np.ndarray
    grad_s_x: np.ndarray
    grad_s_y: np.ndarray

    def save(self, output_dir: Path) -> None:
        np.save(output_dir / "maze_mask.npy", self.wall)
        np.save(output_dir / "signed_distance.npy", self.signed_distance)
        np.save(output_dir / "exit_mask.npy", self.exit_mask)
        np.save(output_dir / "inlet_mask.npy", self.inlet_mask)


@dataclass(frozen=True)
class NavigationField:
    psi: np.ndarray
    grad_psi_x: np.ndarray
    grad_psi_y: np.ndarray

    def save(self, output_dir: Path) -> None:
        np.save(output_dir / "psi.npy", self.psi)
        np.save(output_dir / "grad_psi_x.npy", self.grad_psi_x)
        np.save(output_dir / "grad_psi_y.npy", self.grad_psi_y)


class MazeBuilder:
    def build(self, config: GeometryConfig) -> MazeGeometry:
        n = config.grid_n
        x = np.linspace(-config.L / 2.0, config.L / 2.0, n)
        y = np.linspace(-config.L / 2.0, config.L / 2.0, n)
        X, Y = np.meshgrid(x, y, indexing="xy")
        h = x[1] - x[0]

        wall = np.zeros((n, n), dtype=bool)
        outer = (
            (X <= -config.L / 2.0 + config.w)
            | (X >= config.L / 2.0 - config.w)
            | (Y <= -config.L / 2.0 + config.w)
            | (Y >= config.L / 2.0 - config.w)
        )
        inlet_open = (X <= -config.L / 2.0 + config.w) & (np.abs(Y) <= config.g / 2.0)
        wall |= outer & ~inlet_open

        delta_a = (config.L / 2.0 - config.r_exit - config.w) / (config.n_shell + 1)
        doorway_cycle = ("left", "top", "right", "bottom")
        for shell_id in range(1, config.n_shell + 1):
            a = config.L / 2.0 - shell_id * delta_a
            ring = (np.maximum(np.abs(X), np.abs(Y)) <= a + config.w / 2.0) & (
                np.maximum(np.abs(X), np.abs(Y)) >= a - config.w / 2.0
            )
            side = doorway_cycle[(shell_id - 1) % len(doorway_cycle)]
            if side == "left":
                doorway = (np.abs(X + a) <= config.w / 2.0) & (np.abs(Y) <= config.g / 2.0)
            elif side == "right":
                doorway = (np.abs(X - a) <= config.w / 2.0) & (np.abs(Y) <= config.g / 2.0)
            elif side == "top":
                doorway = (np.abs(Y - a) <= config.w / 2.0) & (np.abs(X) <= config.g / 2.0)
            else:
                doorway = (np.abs(Y + a) <= config.w / 2.0) & (np.abs(X) <= config.g / 2.0)
            wall |= ring & ~doorway

        exit_mask = (np.abs(X) <= config.r_exit) & (np.abs(Y) <= config.r_exit)
        inlet_mask = (X <= -config.L / 2.0 + config.w) & (np.abs(Y) <= config.g / 2.0)
        wall[exit_mask] = False
        free = ~wall
        free[inlet_mask] = True

        free_dist = distance_transform_edt(free) * h
        wall_dist = distance_transform_edt(~free) * h
        signed_distance = free_dist - wall_dist
        grad_s_y, grad_s_x = np.gradient(signed_distance, h, edge_order=2)
        return MazeGeometry(
            config=config,
            x=x,
            y=y,
            X=X,
            Y=Y,
            h=h,
            wall=wall,
            free=free,
            exit_mask=exit_mask,
            inlet_mask=inlet_mask,
            signed_distance=signed_distance,
            grad_s_x=grad_s_x,
            grad_s_y=grad_s_y,
        )


class NavigationSolver:
    def solve(self, maze: MazeGeometry) -> NavigationField:
        free = maze.free
        inlet = maze.inlet_mask & free
        exit_mask = maze.exit_mask & free
        unknown = free & ~(inlet | exit_mask)

        unknown_indices = -np.ones_like(free, dtype=int)
        unknown_coords = np.argwhere(unknown)
        for idx, (row, col) in enumerate(unknown_coords):
            unknown_indices[row, col] = idx

        rows: list[int] = []
        cols: list[int] = []
        data: list[float] = []
        rhs = np.zeros(len(unknown_coords), dtype=float)
        bc_values = np.zeros_like(free, dtype=float)
        bc_values[inlet] = 1.0
        bc_values[exit_mask] = 0.0

        for row_id, (j, i) in enumerate(unknown_coords):
            diag = 0.0
            for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                jj = j + dj
                ii = i + di
                if jj < 0 or jj >= free.shape[0] or ii < 0 or ii >= free.shape[1]:
                    continue
                if not free[jj, ii]:
                    continue
                diag += 1.0
                neighbor_id = unknown_indices[jj, ii]
                if neighbor_id >= 0:
                    rows.append(row_id)
                    cols.append(neighbor_id)
                    data.append(-1.0)
                else:
                    rhs[row_id] += bc_values[jj, ii]
            rows.append(row_id)
            cols.append(row_id)
            data.append(diag if diag > 0 else 1.0)

        matrix = csr_matrix((data, (rows, cols)), shape=(len(unknown_coords), len(unknown_coords)))
        solution = spsolve(matrix, rhs)
        psi = np.zeros_like(bc_values)
        psi[inlet] = 1.0
        psi[exit_mask] = 0.0
        psi[unknown] = solution
        psi = self._fill_walls_from_nearest_free(psi, free)
        grad_psi_y, grad_psi_x = np.gradient(psi, maze.h, edge_order=2)
        grad_psi_x = self._fill_walls_from_nearest_free(grad_psi_x, free)
        grad_psi_y = self._fill_walls_from_nearest_free(grad_psi_y, free)
        return NavigationField(psi=psi, grad_psi_x=grad_psi_x, grad_psi_y=grad_psi_y)

    @staticmethod
    def _fill_walls_from_nearest_free(field: np.ndarray, free: np.ndarray) -> np.ndarray:
        _, indices = distance_transform_edt(~free, return_indices=True)
        return field[indices[0], indices[1]]


class StatisticsEstimator:
    @staticmethod
    def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
        if n == 0:
            return math.nan, math.nan
        phat = successes / n
        denom = 1.0 + z * z / n
        centre = (phat + z * z / (2.0 * n)) / denom
        half = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n) / denom
        return max(0.0, centre - half), min(1.0, centre + half)

    @staticmethod
    def bootstrap_point_metrics(
        *,
        success: np.ndarray,
        t_exit: np.ndarray,
        sigma_drag_i: np.ndarray,
        Tmax: float,
        sigma_floor: float,
        resamples: int,
        rng: np.random.Generator,
    ) -> dict[str, float]:
        def percentile_or_nan(sample: np.ndarray, q: float) -> float:
            finite = sample[np.isfinite(sample)]
            if finite.size == 0:
                return math.nan
            return float(np.percentile(finite, q))

        n = len(success)
        idx = rng.integers(0, n, size=(resamples, n))
        mfpt_samples = np.empty(resamples, dtype=float)
        j_samples = np.empty(resamples, dtype=float)
        sigma_samples = np.empty(resamples, dtype=float)
        eta_samples = np.empty(resamples, dtype=float)
        for sample_id in range(resamples):
            pick = idx[sample_id]
            success_b = success[pick]
            t_exit_b = t_exit[pick]
            sigma_b = sigma_drag_i[pick]
            p_b = float(success_b.mean())
            finite_exit = t_exit_b[np.isfinite(t_exit_b)]
            mfpt_samples[sample_id] = np.nan if finite_exit.size == 0 else float(finite_exit.mean())
            j_b = p_b / Tmax
            j_samples[sample_id] = j_b
            sigma_rate_b = float(np.mean(sigma_b))
            sigma_samples[sample_id] = sigma_rate_b
            eta_samples[sample_id] = j_b / max(sigma_rate_b, sigma_floor)
        return {
            "MFPT_ci_low": percentile_or_nan(mfpt_samples, 2.5),
            "MFPT_ci_high": percentile_or_nan(mfpt_samples, 97.5),
            "J_proxy_ci_low": float(np.nanpercentile(j_samples, 2.5)),
            "J_proxy_ci_high": float(np.nanpercentile(j_samples, 97.5)),
            "sigma_drag_ci_low": float(np.nanpercentile(sigma_samples, 2.5)),
            "sigma_drag_ci_high": float(np.nanpercentile(sigma_samples, 97.5)),
            "eta_sigma_ci_low": float(np.nanpercentile(eta_samples, 2.5)),
            "eta_sigma_ci_high": float(np.nanpercentile(eta_samples, 97.5)),
        }


class DetectabilityAnalyzer:
    def summarize(self, summary_df: pd.DataFrame) -> dict[str, Any]:
        fig1 = summary_df[summary_df["figure_group"].isin(["fig1_detectability_map", "fig1_timescale_map"])].copy()
        fig2 = summary_df[summary_df["figure_group"] == "fig2_flow_competition"].copy()
        if fig1.empty or fig2.empty:
            return {
                "ridge_detected": False,
                "ranking_reversal_detected": False,
                "reason": "insufficient figure groups for detectability analysis",
            }

        interior_mask = fig1["tau_v"].isin([0.5, 1.0]) & fig1["tau_f"].isin([0.25, 0.5])
        fig1_sorted = fig1.sort_values("eta_sigma", ascending=False)
        best_fig1 = fig1_sorted.iloc[0]
        edge_eta = fig1.loc[~interior_mask, "eta_sigma"]
        ridge_detected = bool(interior_mask.loc[best_fig1.name]) and bool(best_fig1["eta_sigma"] > edge_eta.median())

        coupled = fig2[fig2["control_label"].str.contains("coupled")].sort_values("U")
        coupled_valid = coupled[np.isfinite(coupled["MFPT_success_only"])]
        ranking_reversal = False
        mfpt_best_u = math.nan
        eta_best_u = math.nan
        if not coupled_valid.empty:
            mfpt_best_u = float(coupled_valid.loc[coupled_valid["MFPT_success_only"].idxmin(), "U"])
            eta_best_u = float(coupled_valid.loc[coupled_valid["eta_sigma"].idxmax(), "U"])
            ranking_reversal = not math.isclose(mfpt_best_u, eta_best_u)
        return {
            "ridge_detected": ridge_detected,
            "ridge_best_point": {
                "tau_v": float(best_fig1["tau_v"]),
                "tau_f": float(best_fig1["tau_f"]),
                "Xi": float(best_fig1["Xi"]),
                "eta_sigma": float(best_fig1["eta_sigma"]),
                "MFPT_success_only": float(best_fig1["MFPT_success_only"]) if np.isfinite(best_fig1["MFPT_success_only"]) else math.nan,
            },
            "ranking_reversal_detected": ranking_reversal,
            "ranking_reversal_details": {
                "coupled_branch_mfpt_best_U": mfpt_best_u,
                "coupled_branch_eta_sigma_best_U": eta_best_u,
            },
        }


class PointSimulator:
    def __init__(self, maze: MazeGeometry, navigation: NavigationField) -> None:
        self.maze = maze
        self.navigation = navigation
        self.stats = StatisticsEstimator()

    @staticmethod
    def angle_wrap(theta: np.ndarray) -> np.ndarray:
        return (theta + np.pi) % (2.0 * np.pi) - np.pi

    def bilinear_sample(self, field: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        dx = self.maze.x[1] - self.maze.x[0]
        dy = self.maze.y[1] - self.maze.y[0]
        fx = np.clip((x - self.maze.x[0]) / dx, 0.0, len(self.maze.x) - 1.000001)
        fy = np.clip((y - self.maze.y[0]) / dy, 0.0, len(self.maze.y) - 1.000001)
        i0 = np.floor(fx).astype(np.int64)
        j0 = np.floor(fy).astype(np.int64)
        i1 = np.clip(i0 + 1, 0, len(self.maze.x) - 1)
        j1 = np.clip(j0 + 1, 0, len(self.maze.y) - 1)
        tx = fx - i0
        ty = fy - j0
        f00 = field[j0, i0]
        f10 = field[j0, i1]
        f01 = field[j1, i0]
        f11 = field[j1, i1]
        return (1.0 - tx) * (1.0 - ty) * f00 + tx * (1.0 - ty) * f10 + (1.0 - tx) * ty * f01 + tx * ty * f11

    def sample_inlet_positions(self, n_traj: int, rng: np.random.Generator) -> np.ndarray:
        inlet_indices = np.argwhere(self.maze.inlet_mask & self.maze.free)
        picks = inlet_indices[rng.integers(0, len(inlet_indices), size=n_traj)]
        jitter = rng.uniform(-0.45 * self.maze.h, 0.45 * self.maze.h, size=(n_traj, 2))
        positions = np.column_stack((self.maze.x[picks[:, 1]], self.maze.y[picks[:, 0]])) + jitter
        positions[:, 0] = np.clip(positions[:, 0], self.maze.x[0] + self.maze.h, self.maze.x[-1] - self.maze.h)
        positions[:, 1] = np.clip(positions[:, 1], self.maze.y[0] + self.maze.h, self.maze.y[-1] - self.maze.h)
        return positions

    @staticmethod
    def build_discrete_linear_step(
        *,
        gamma0: float,
        gamma1: float,
        tau_v: float,
        kBT: float,
        tau_m: float,
        dt: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        m = gamma0 * tau_m
        sigma_v = math.sqrt(2.0 * gamma0 * kBT) / m
        sigma_q = math.sqrt(2.0 * max(gamma1, 0.0) * kBT) / tau_v if gamma1 > 0.0 else 0.0
        A = np.array(
            [
                [0.0, 1.0, 0.0],
                [0.0, -gamma0 / m, -1.0 / m],
                [0.0, gamma1 / tau_v, -1.0 / tau_v],
            ],
            dtype=float,
        )
        G = np.array([[0.0, 0.0], [sigma_v, 0.0], [0.0, sigma_q]], dtype=float)
        n = A.shape[0]
        aug = np.zeros((2 * n, 2 * n), dtype=float)
        aug[:n, :n] = A
        aug[:n, n:] = np.eye(n)
        exp_aug = expm(aug * dt)
        M = exp_aug[:n, :n]
        K = exp_aug[:n, n:]

        GGt = G @ G.T
        van_loan = np.zeros((2 * n, 2 * n), dtype=float)
        van_loan[:n, :n] = A
        van_loan[:n, n:] = GGt
        van_loan[n:, n:] = -A.T
        exp_vl = expm(van_loan * dt)
        C = exp_vl[:n, n:]
        Q = C @ M.T
        Q = 0.5 * (Q + Q.T)
        jitter = 1e-12 * np.eye(n)
        return M, K, np.linalg.cholesky(Q + jitter)

    def run(self, point: SweepPoint, dynamics: DynamicsConfig, point_seed: int) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame]:
        rng = np.random.default_rng(point_seed)
        n_traj = dynamics.n_traj
        dt = dynamics.dt
        Tmax = dynamics.Tmax
        n_steps = int(round(Tmax / dt))
        tau_p = dynamics.tau_p
        gamma0 = dynamics.gamma0
        gamma1 = point.gamma1_over_gamma0 * gamma0
        tau_v = point.tau_v
        tau_f = point.tau_f
        U = point.U
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

        prog_window = max(1, int(math.ceil(0.25 * tau_p / dt)))
        prog_buffer = np.zeros((n_traj, prog_window), dtype=float)
        prog_sum = np.zeros(n_traj, dtype=float)
        prog_count = np.zeros(n_traj, dtype=np.int64)
        prog_ptr = np.zeros(n_traj, dtype=np.int64)
        current_trap = np.zeros(n_traj, dtype=float)
        trap_records: list[dict[str, float]] = []

        for step in range(n_steps):
            if not np.any(alive):
                break
            alive_idx = np.flatnonzero(alive)
            delayed = r_hist[(hist_pos - delay_steps) % hist_len, alive_idx, :]
            grad_delayed_x = self.bilinear_sample(self.navigation.grad_psi_x, delayed[:, 0], delayed[:, 1])
            grad_delayed_y = self.bilinear_sample(self.navigation.grad_psi_y, delayed[:, 0], delayed[:, 1])
            grad_delayed_norm = np.hypot(grad_delayed_x, grad_delayed_y)
            theta_star = np.arctan2(-grad_delayed_y, -grad_delayed_x)
            torque = np.where(
                grad_delayed_norm >= dynamics.eps_psi,
                point.kf * np.sin(theta_star - theta[alive_idx]),
                0.0,
            )
            theta[alive_idx] = self.angle_wrap(
                theta[alive_idx] + dt * torque + math.sqrt(2.0 * dynamics.Dr * dt) * rng.normal(size=alive_idx.size)
            )
            n_vec = np.column_stack((np.cos(theta[alive_idx]), np.sin(theta[alive_idx])))

            grad_curr_x = self.bilinear_sample(self.navigation.grad_psi_x, r[alive_idx, 0], r[alive_idx, 1])
            grad_curr_y = self.bilinear_sample(self.navigation.grad_psi_y, r[alive_idx, 0], r[alive_idx, 1])
            grad_curr_norm = np.hypot(grad_curr_x, grad_curr_y)
            dir_x = -grad_curr_x / np.maximum(grad_curr_norm, dynamics.eps_psi)
            dir_y = -grad_curr_y / np.maximum(grad_curr_norm, dynamics.eps_psi)
            progress_speed = v[alive_idx, 0] * dir_x + v[alive_idx, 1] * dir_y

            pos_s = self.bilinear_sample(self.maze.signed_distance, r[alive_idx, 0], r[alive_idx, 1])
            boundary_contact = pos_s <= self.maze.config.w
            boundary_steps[alive_idx] += boundary_contact.astype(np.int64)
            live_steps[alive_idx] += 1

            for local_idx, traj_idx in enumerate(alive_idx):
                ptr = prog_ptr[traj_idx]
                prog_sum[traj_idx] -= prog_buffer[traj_idx, ptr]
                prog_buffer[traj_idx, ptr] = progress_speed[local_idx]
                prog_sum[traj_idx] += progress_speed[local_idx]
                prog_ptr[traj_idx] = (ptr + 1) % prog_window
                prog_count[traj_idx] = min(prog_count[traj_idx] + 1, prog_window)
                trapped = boundary_contact[local_idx] and (prog_sum[traj_idx] / prog_count[traj_idx]) <= 0.0
                if trapped:
                    current_trap[traj_idx] += dt
                else:
                    if current_trap[traj_idx] >= 0.5 * tau_p:
                        trap_records.append(
                            {"sweep_id": point.sweep_id, "traj_id": int(traj_idx), "trap_duration": float(current_trap[traj_idx])}
                        )
                    current_trap[traj_idx] = 0.0

            grad_s_now_x = self.bilinear_sample(self.maze.grad_s_x, r[alive_idx, 0], r[alive_idx, 1])
            grad_s_now_y = self.bilinear_sample(self.maze.grad_s_y, r[alive_idx, 0], r[alive_idx, 1])
            grad_s_norm = np.hypot(grad_s_now_x, grad_s_now_y)
            wall_normal = np.column_stack((grad_s_now_x, grad_s_now_y)) / np.maximum(grad_s_norm[:, None], 1e-12)
            wall_force_mag = k_wall * np.clip(delta_wall - pos_s, 0.0, None)
            wall_force = wall_force_mag[:, None] * wall_normal

            force_x = f0 * n_vec[:, 0] + wall_force[:, 0]
            force_y = f0 * n_vec[:, 1] + wall_force[:, 1]

            sigma_drag_i[alive_idx] += dt * gamma0 * np.sum((v[alive_idx] - flow) ** 2, axis=1) / dynamics.kBT

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
                alive[hit_idx] = False
                for traj_idx in hit_idx:
                    if current_trap[traj_idx] >= 0.5 * tau_p:
                        trap_records.append(
                            {"sweep_id": point.sweep_id, "traj_id": int(traj_idx), "trap_duration": float(current_trap[traj_idx])}
                        )
                    current_trap[traj_idx] = 0.0

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

            hist_pos = (hist_pos + 1) % hist_len
            r_hist[hist_pos] = r

        remaining = np.flatnonzero(alive)
        for traj_idx in remaining:
            if current_trap[traj_idx] >= 0.5 * tau_p:
                trap_records.append({"sweep_id": point.sweep_id, "traj_id": int(traj_idx), "trap_duration": float(current_trap[traj_idx])})

        trap_df = pd.DataFrame(trap_records, columns=["sweep_id", "traj_id", "trap_duration"])
        t_stop = np.where(success, t_exit, Tmax)
        traj_df = pd.DataFrame(
            {
                "sweep_id": point.sweep_id,
                "traj_id": np.arange(n_traj, dtype=int),
                "success_flag": success.astype(int),
                "t_stop": t_stop,
                "t_exit_or_nan": t_exit,
                "Sigma_drag_i": sigma_drag_i / Tmax,
                "live_steps": live_steps,
                "boundary_steps": boundary_steps,
                "boundary_contact_fraction_i": np.divide(
                    boundary_steps,
                    np.maximum(live_steps, 1),
                    out=np.zeros_like(boundary_steps, dtype=float),
                    where=live_steps > 0,
                ),
            }
        )

        n_success = int(success.sum())
        Psucc = float(n_success / n_traj)
        mfpt = float(np.mean(t_exit[success])) if n_success > 0 else math.nan
        J_proxy = Psucc / Tmax
        sigma_drag = float(np.mean(sigma_drag_i / Tmax))
        eta_sigma = J_proxy / max(sigma_drag, dynamics.sigma_floor)
        boundary_contact_fraction = float(boundary_steps.sum() / max(live_steps.sum(), 1))
        mean_trap = float(trap_df["trap_duration"].mean()) if not trap_df.empty else 0.0
        q90_trap = float(trap_df["trap_duration"].quantile(0.9)) if not trap_df.empty else 0.0
        p_ci_low, p_ci_high = self.stats.wilson_interval(n_success, n_traj)
        boot = self.stats.bootstrap_point_metrics(
            success=success.astype(float),
            t_exit=t_exit,
            sigma_drag_i=sigma_drag_i / Tmax,
            Tmax=Tmax,
            sigma_floor=dynamics.sigma_floor,
            resamples=dynamics.bootstrap_resamples,
            rng=np.random.default_rng(point_seed + 991),
        )

        tau_mem = 0.0 if gamma1 == 0.0 else (gamma1 / (gamma0 + gamma1)) * tau_v
        Xi = (tau_f + tau_mem) / tau_p
        De = 0.0 if U == 0.0 else tau_v * U / self.maze.config.L
        summary = {
            "sweep_id": point.sweep_id,
            "figure_group": point.figure_group,
            "control_label": point.control_label,
            "tau_v": tau_v,
            "tau_v_over_tau_p": tau_v / tau_p,
            "tau_f": tau_f,
            "tau_f_over_tau_p": tau_f / tau_p,
            "U": U,
            "U_over_v0": U / dynamics.v0,
            "gamma1_over_gamma0": point.gamma1_over_gamma0,
            "kf": point.kf,
            "v0": dynamics.v0,
            "Dr": dynamics.Dr,
            "Xi": Xi,
            "De": De,
            "n_traj": n_traj,
            "n_success": n_success,
            "Psucc": Psucc,
            "Psucc_ci_low": p_ci_low,
            "Psucc_ci_high": p_ci_high,
            "MFPT_success_only": mfpt,
            "J_proxy": J_proxy,
            "sigma_drag": sigma_drag,
            "eta_sigma": eta_sigma,
            "mean_trap_residence": mean_trap,
            "q90_trap_residence": q90_trap,
            "boundary_contact_fraction": boundary_contact_fraction,
            "dt": dt,
            "Tmax": Tmax,
            "tau_m": tau_m,
            "grid_n": self.maze.config.grid_n,
            "n_shell": self.maze.config.n_shell,
        }
        summary.update(boot)
        return summary, traj_df, trap_df


class ArtifactWriter:
    def __init__(self, paths: RuntimePaths) -> None:
        self.paths = paths

    def write(
        self,
        *,
        task: SimulationTask,
        maze: MazeGeometry,
        navigation: NavigationField,
        summary_df: pd.DataFrame,
        trajectory_df: pd.DataFrame,
        trap_df: pd.DataFrame,
        detectability: dict[str, Any] | None,
        overwrite: bool = False,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        self.paths.ensure()
        output_dir = self.paths.run_root / task.run_id
        if output_dir.exists():
            if not overwrite:
                raise FileExistsError(
                    f"Run directory already exists: {output_dir}. Use a new run id or pass overwrite=True."
                )
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        summary_path = output_dir / "pilot_point_summary.csv"
        trajectory_path = output_dir / "pilot_trajectory_summary.csv"
        trap_path = output_dir / "pilot_trap_episodes.csv"

        summary_df.to_csv(summary_path, index=False)
        trajectory_df.to_csv(trajectory_path, index=False)
        trap_df.to_csv(trap_path, index=False)
        maze.save(output_dir)
        navigation.save(output_dir)

        artifact_paths: dict[str, str] = {
            "summary_csv": self._display_path(summary_path),
            "trajectory_csv": self._display_path(trajectory_path),
            "trap_csv": self._display_path(trap_path),
        }

        for figure_group in sorted(summary_df["figure_group"].unique()):
            group_df = summary_df[summary_df["figure_group"] == figure_group]
            figure_path = self.paths.figure_root / f"{figure_group}_source_{task.run_id}.csv"
            group_df.to_csv(figure_path, index=False)
            artifact_paths[f"{figure_group}_csv"] = self._display_path(figure_path)

        fig2_df = summary_df[summary_df["figure_group"] == "fig2_flow_competition"]
        if not fig2_df.empty:
            table_path = self.paths.table_root / f"fig2_u_star_summary_{task.run_id}.csv"
            self._write_u_star_table(fig2_df, table_path)
            artifact_paths["fig2_u_star_table"] = self._display_path(table_path)

        manifest = {
            "run_id": task.run_id,
            "mode": task.mode,
            "task_id": task.task_id,
            "description": task.description,
            "geometry": dataclass_dict(task.geometry),
            "dynamics": dataclass_dict(task.dynamics),
            "n_points": len(task.points),
            "point_ids": [point.sweep_id for point in task.points],
            "paths": self.paths.as_manifest_dict(),
            "artifacts": artifact_paths,
            "notes": task.notes,
        }
        if detectability is not None:
            manifest["detectability"] = detectability
        with open(output_dir / "run_manifest.json", "w", encoding="ascii") as handle:
            json.dump(manifest, handle, indent=2)
        artifact_paths["manifest"] = self._display_path(output_dir / "run_manifest.json")
        return artifact_paths, manifest

    @staticmethod
    def _write_u_star_table(fig2_df: pd.DataFrame, output_path: Path) -> None:
        rows: list[dict[str, float]] = []
        for control_label, group in fig2_df.groupby("control_label"):
            sorted_group = group.sort_values("U")
            best = sorted_group.loc[sorted_group["eta_sigma"].idxmax()]
            rows.append(
                {
                    "control_label": control_label,
                    "tau_v": best["tau_v"],
                    "tau_f": best["tau_f"],
                    "gamma1_over_gamma0": best["gamma1_over_gamma0"],
                    "kf": best["kf"],
                    "U_star": best["U"],
                    "U_star_over_v0": best["U_over_v0"],
                    "eta_sigma_max": best["eta_sigma"],
                    "MFPT_at_U_star": best["MFPT_success_only"],
                    "Psucc_at_U_star": best["Psucc"],
                }
            )
        pd.DataFrame(rows).sort_values("control_label").to_csv(output_path, index=False)

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.paths.project_root))
        except ValueError:
            return str(path)


class SimulationTaskRunner:
    def __init__(self, paths: RuntimePaths) -> None:
        self.paths = paths
        self.maze_builder = MazeBuilder()
        self.navigation_solver = NavigationSolver()
        self.detectability = DetectabilityAnalyzer()
        self.writer = ArtifactWriter(paths)

    def run(self, task: SimulationTask, *, overwrite: bool = False) -> TaskRunResult:
        maze = self.maze_builder.build(task.geometry)
        navigation = self.navigation_solver.solve(maze)
        simulator = PointSimulator(maze, navigation)

        summary_rows: list[dict[str, float]] = []
        trajectory_frames: list[pd.DataFrame] = []
        trap_frames: list[pd.DataFrame] = []

        for point_index, point in enumerate(task.points):
            summary, trajectory_df, trap_df = simulator.run(point, task.dynamics, task.dynamics.seed + 1000 * point_index)
            summary_rows.append(summary)
            trajectory_frames.append(trajectory_df)
            trap_frames.append(trap_df)

        summary_df = pd.DataFrame(summary_rows).sort_values(["figure_group", "control_label", "tau_v", "tau_f", "U"])
        trajectory_df = pd.concat(trajectory_frames, ignore_index=True)
        nonempty_trap_frames = [frame for frame in trap_frames if not frame.empty]
        trap_df = (
            pd.concat(nonempty_trap_frames, ignore_index=True)
            if nonempty_trap_frames
            else pd.DataFrame(columns=["sweep_id", "traj_id", "trap_duration"])
        )
        detectability = self.detectability.summarize(summary_df) if task.detectability_analysis else None
        artifact_paths, manifest = self.writer.write(
            task=task,
            maze=maze,
            navigation=navigation,
            summary_df=summary_df,
            trajectory_df=trajectory_df,
            trap_df=trap_df,
            detectability=detectability,
            overwrite=overwrite,
        )
        return TaskRunResult(
            task=task,
            summary_df=summary_df,
            trajectory_df=trajectory_df,
            trap_df=trap_df,
            detectability=detectability,
            manifest=manifest,
            artifact_paths=artifact_paths,
        )
