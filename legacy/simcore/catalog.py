from __future__ import annotations

import csv
from pathlib import Path

from .models import DynamicsConfig, GeometryConfig, SimulationTask, SweepPoint


RUN_DATE = "2026-04-11"


class TaskCatalog:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._tasks: dict[str, SimulationTask] = {}
        self._register_builtin_tasks()
        self._register_startup_matrix_tasks()

    def list_tasks(self) -> list[SimulationTask]:
        return [self._tasks[key] for key in sorted(self._tasks)]

    def get(self, task_id: str) -> SimulationTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            available = ", ".join(sorted(self._tasks))
            raise KeyError(f"Unknown task '{task_id}'. Available tasks: {available}") from exc

    def _register(self, task: SimulationTask) -> None:
        self._tasks[task.task_id] = task

    def _register_builtin_tasks(self) -> None:
        geometry = GeometryConfig(n_shell=1, grid_n=257)
        dynamics = DynamicsConfig(n_traj=64, Tmax=20.0)
        points: list[SweepPoint] = []
        for tau_v in (0.25, 0.5, 1.0, 2.0):
            for tau_f in (0.125, 0.25, 0.5, 1.0):
                points.append(
                    SweepPoint(
                        sweep_id=f"P1_U025_DETECT_tau_v_{tau_v:g}_tau_f_{tau_f:g}",
                        figure_group="fig1_detectability_map",
                        control_label="coupled_baseline",
                        tau_v=tau_v,
                        tau_f=tau_f,
                        U=0.25,
                        gamma1_over_gamma0=4.0,
                        kf=3.0,
                    )
                )
        for control_label, gamma_ratio, kf in (
            ("coupled_mid_memory", 4.0, 3.0),
            ("no_memory", 0.0, 3.0),
            ("no_feedback", 4.0, 0.0),
        ):
            for U in (0.0, 0.125, 0.25, 0.375, 0.5):
                points.append(
                    SweepPoint(
                        sweep_id=f"P2_{control_label}_U_{U:g}",
                        figure_group="fig2_flow_competition",
                        control_label=control_label,
                        tau_v=0.5,
                        tau_f=0.5,
                        U=U,
                        gamma1_over_gamma0=gamma_ratio,
                        kf=kf,
                    )
                )
        self._register(
            SimulationTask(
                task_id="simplified_detectability",
                description="One-shell G1 detectability pre-pilot used to validate ridge and ranking-reversal signal.",
                mode="simplified_detectability_prepilot",
                run_id=f"simplified_startup_pilot_{RUN_DATE}",
                geometry=geometry,
                dynamics=dynamics,
                points=tuple(points),
                detectability_analysis=True,
                notes="Legacy-compatible task that reproduces the simplified startup pilot.",
            )
        )

    def _register_startup_matrix_tasks(self) -> None:
        csv_path = self.project_root / "Experiment" / "designs" / "startup_parameter_sweep_matrix_2026-04-11.csv"
        with open(csv_path, newline="", encoding="ascii") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                task = self._task_from_matrix_row(row)
                self._register(task)

    def _task_from_matrix_row(self, row: dict[str, str]) -> SimulationTask:
        block_id = row["block_id"]
        task_id = block_id.lower()
        geometry = GeometryConfig(
            L=1.0,
            w=0.04,
            g=0.08,
            r_exit=0.06,
            n_shell=6,
            grid_n=int(row["grid_n"]),
        )
        dynamics = DynamicsConfig(
            gamma0=1.0,
            gamma1_over_gamma0=float(row["gamma1_over_gamma0"]),
            Dr=float(row["Dr"]),
            v0=float(row["v0"]),
            kf=float(row["kf"]),
            kBT=0.01,
            dt=0.0025,
            Tmax=40.0,
            sigma_m=0.0,
            delta_t_s=0.0025,
            bootstrap_resamples=1000,
            n_traj=int(row["n_traj_per_point"]),
            seed=20260411,
        )
        tau_v_values = self._parse_values(row["tau_v_values"])
        tau_f_values = self._parse_values(row["tau_f_values"])
        U_values = self._parse_values(row["U_values"])
        points = self._build_points(
            block_id=block_id,
            figure_target=row["figure_target"],
            control_label=row["control_label"],
            tau_v_values=tau_v_values,
            tau_f_values=tau_f_values,
            U_values=U_values,
            gamma1_over_gamma0=float(row["gamma1_over_gamma0"]),
            kf=float(row["kf"]),
        )
        return SimulationTask(
            task_id=task_id,
            description=f"{row['figure_target']} / {row['purpose']} / {row['notes']}",
            mode="startup_matrix_block",
            run_id=f"{task_id}_{RUN_DATE}",
            geometry=geometry,
            dynamics=dynamics,
            points=tuple(points),
            detectability_analysis=False,
            notes=row["notes"],
        )

    @staticmethod
    def _parse_values(raw: str) -> tuple[float, ...]:
        return tuple(float(token) for token in raw.split("|"))

    @staticmethod
    def _build_points(
        *,
        block_id: str,
        figure_target: str,
        control_label: str,
        tau_v_values: tuple[float, ...],
        tau_f_values: tuple[float, ...],
        U_values: tuple[float, ...],
        gamma1_over_gamma0: float,
        kf: float,
    ) -> list[SweepPoint]:
        figure_group = "fig1_timescale_map" if figure_target == "Figure1" else "fig2_flow_competition"
        points: list[SweepPoint] = []
        for tau_v in tau_v_values:
            for tau_f in tau_f_values:
                for U in U_values:
                    sweep_id = f"{block_id}_tau_v_{tau_v:g}_tau_f_{tau_f:g}_U_{U:g}"
                    points.append(
                        SweepPoint(
                            sweep_id=sweep_id,
                            figure_group=figure_group,
                            control_label=control_label,
                            tau_v=tau_v,
                            tau_f=tau_f,
                            U=U,
                            gamma1_over_gamma0=gamma1_over_gamma0,
                            kf=kf,
                        )
                    )
        return points
