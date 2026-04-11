from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GeometryConfig:
    L: float = 1.0
    w: float = 0.04
    g: float = 0.08
    r_exit: float = 0.06
    n_shell: int = 6
    grid_n: int = 1024

    def with_overrides(self, **overrides: Any) -> "GeometryConfig":
        clean = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **clean)


@dataclass(frozen=True)
class DynamicsConfig:
    gamma0: float = 1.0
    gamma1_over_gamma0: float = 4.0
    Dr: float = 1.0
    v0: float = 0.5
    kf: float = 3.0
    kBT: float = 0.01
    dt: float = 0.0025
    Tmax: float = 40.0
    sigma_floor: float = 1e-12
    sigma_m: float = 0.0
    delta_t_s: float = 0.0025
    eps_psi: float = 1e-12
    bootstrap_resamples: int = 1000
    n_traj: int = 1000
    seed: int = 20260411

    @property
    def tau_p(self) -> float:
        return 1.0 / self.Dr

    def with_overrides(self, **overrides: Any) -> "DynamicsConfig":
        clean = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **clean)


@dataclass(frozen=True)
class SweepPoint:
    sweep_id: str
    figure_group: str
    control_label: str
    tau_v: float
    tau_f: float
    U: float
    gamma1_over_gamma0: float
    kf: float


@dataclass(frozen=True)
class SimulationTask:
    task_id: str
    description: str
    mode: str
    run_id: str
    geometry: GeometryConfig
    dynamics: DynamicsConfig
    points: tuple[SweepPoint, ...]
    detectability_analysis: bool = False
    notes: str = ""

    def with_updates(
        self,
        *,
        geometry: GeometryConfig | None = None,
        dynamics: DynamicsConfig | None = None,
        points: tuple[SweepPoint, ...] | None = None,
        run_id: str | None = None,
    ) -> "SimulationTask":
        return replace(
            self,
            geometry=geometry or self.geometry,
            dynamics=dynamics or self.dynamics,
            points=points or self.points,
            run_id=run_id or self.run_id,
        )


@dataclass(frozen=True)
class TaskOverride:
    run_id: str | None = None
    point_limit: int | None = None
    n_traj: int | None = None
    Tmax: float | None = None
    n_shell: int | None = None
    grid_n: int | None = None
    seed: int | None = None
    bootstrap_resamples: int | None = None
    overwrite: bool = False

    def apply(self, task: SimulationTask) -> SimulationTask:
        geometry = task.geometry.with_overrides(n_shell=self.n_shell, grid_n=self.grid_n)
        dynamics = task.dynamics.with_overrides(
            n_traj=self.n_traj,
            Tmax=self.Tmax,
            seed=self.seed,
            bootstrap_resamples=self.bootstrap_resamples,
        )
        points = task.points[: self.point_limit] if self.point_limit else task.points
        return task.with_updates(
            geometry=geometry,
            dynamics=dynamics,
            points=tuple(points),
            run_id=self.run_id,
        )


@dataclass(frozen=True)
class RuntimePaths:
    project_root: Path
    run_root: Path
    figure_root: Path
    table_root: Path

    @classmethod
    def default(cls, project_root: Path) -> "RuntimePaths":
        return cls(
            project_root=project_root,
            run_root=project_root / "Experiment" / "runs",
            figure_root=project_root / "Experiment" / "analysis" / "figures",
            table_root=project_root / "Experiment" / "analysis" / "tables",
        )

    def ensure(self) -> None:
        self.run_root.mkdir(parents=True, exist_ok=True)
        self.figure_root.mkdir(parents=True, exist_ok=True)
        self.table_root.mkdir(parents=True, exist_ok=True)

    def as_manifest_dict(self) -> dict[str, str]:
        return {
            "run_root": str(self.run_root),
            "figure_root": str(self.figure_root),
            "table_root": str(self.table_root),
        }


@dataclass(frozen=True)
class TaskRunResult:
    task: SimulationTask
    summary_df: Any
    trajectory_df: Any
    trap_df: Any
    detectability: dict[str, Any] | None
    manifest: dict[str, Any]
    artifact_paths: dict[str, str]


def dataclass_dict(instance: Any) -> dict[str, Any]:
    return asdict(instance)
