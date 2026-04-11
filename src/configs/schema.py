from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class RunConfig:
    geometry_id: str
    model_variant: str
    v0: float
    Dr: float
    tau_v: float
    gamma0: float
    gamma1: float
    tau_f: float
    U: float
    wall_thickness: float
    gate_width: float
    dt: float
    Tmax: float
    n_traj: int
    seed: int
    exit_radius: float = 0.06
    n_shell: int = 6
    grid_n: int = 1024
    kf: float = 3.0
    gamma1_over_gamma0: float | None = None
    bootstrap_resamples: int = 1000
    kBT: float = 0.01
    eps_psi: float = 1e-12
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunConfig":
        return cls(**payload)

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(_stable_json(self.to_dict()).encode("ascii")).hexdigest()


@dataclass(frozen=True)
class RunResult:
    run_id: str
    config_hash: str
    geometry_id: str
    model_variant: str
    p_succ: float
    mfpt_mean: float | None
    mfpt_median: float | None
    mfpt_q90: float | None
    sigma_drag_mean: float | None
    eta_sigma: float | None
    trap_time_mean: float | None
    trap_count_mean: float | None
    wall_fraction_mean: float | None
    revisit_rate_mean: float | None
    n_traj: int
    n_success: int
    ci: dict[str, Any] = field(default_factory=dict)
    raw_summary_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SweepTask:
    task_id: str
    phase: str
    batch_index: int
    config_list: tuple[RunConfig, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "phase": self.phase,
            "batch_index": self.batch_index,
            "config_list": [config.to_dict() for config in self.config_list],
            "metadata": self.metadata,
        }
