from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
import hashlib
import json
import math
from typing import Any

BRANCH_VARIANTS = {"full", "no_memory", "no_feedback"}
LEGACY_BRANCH_VARIANTS = BRANCH_VARIANTS | {"no_flow"}
FLOW_CONDITIONS = {"with_flow", "zero_flow", "explicit_no_flow_control"}


def infer_flow_condition(U: float, *, legacy_model_variant: str | None = None, flow_condition: str | None = None) -> str:
    if flow_condition is not None:
        return flow_condition
    if legacy_model_variant == "no_flow":
        return "explicit_no_flow_control"
    if abs(U) <= 1e-15:
        return "zero_flow"
    return "with_flow"


def normalize_model_variant_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    legacy_model_variant = _normalize_optional_string(normalized.get("legacy_model_variant"))
    model_variant = _normalize_optional_string(normalized.get("model_variant"))
    flow_condition = _normalize_optional_string(normalized.get("flow_condition"))

    if model_variant == "no_flow":
        normalized["legacy_model_variant"] = "no_flow"
        normalized["model_variant"] = "full"
        normalized["flow_condition"] = infer_flow_condition(
            float(normalized.get("U", 0.0)),
            legacy_model_variant="no_flow",
            flow_condition=flow_condition,
        )
    else:
        normalized["legacy_model_variant"] = legacy_model_variant
        normalized["flow_condition"] = infer_flow_condition(
            float(normalized.get("U", 0.0)),
            legacy_model_variant=legacy_model_variant,
            flow_condition=flow_condition,
        )
    return normalized


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _filter_dataclass_kwargs(cls: type, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {item.name for item in fields(cls)}
    return {key: value for key, value in payload.items() if key in allowed}


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return str(value)


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
    flow_condition: str = "with_flow"
    metadata: dict[str, Any] = field(default_factory=dict)
    legacy_model_variant: str | None = None

    def _payload_without_hash(self) -> dict[str, Any]:
        return asdict(self)

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_hash()
        payload["config_hash"] = self.config_hash
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunConfig":
        payload = dict(payload)
        payload.pop("config_hash", None)
        normalized = normalize_model_variant_payload(payload)
        return cls(**_filter_dataclass_kwargs(cls, normalized))

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(_stable_json(self._payload_without_hash()).encode("ascii")).hexdigest()


@dataclass(frozen=True)
class RunResult:
    """Normalized per-config result.

    Provenance note:
    - `raw_summary_path` refers only to the adapter-written one-row CSV snapshot of the
      legacy summary dictionary for this exact config.
    - It does not refer to phase-level summary tables or task manifests.
    - When a workflow phase is generation-only and therefore has no per-config raw summary,
      downstream persisted rows must make that case explicit via provenance status fields
      rather than overloading this field silently.
    """

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
    flow_condition: str = "with_flow"
    ci: dict[str, Any] = field(default_factory=dict)
    raw_summary_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    legacy_model_variant: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunResult":
        normalized = normalize_model_variant_payload(dict(payload))
        return cls(**_filter_dataclass_kwargs(cls, normalized))


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
