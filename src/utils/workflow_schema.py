from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import platform
from pathlib import Path
import sys
from typing import Any

import pandas as pd

from src.configs.schema import RunConfig, RunResult, normalize_model_variant_payload


@dataclass(frozen=True)
class WorkflowPhasePaths:
    phase: str
    runs_root: Path
    summaries_root: Path
    logs_root: Path


def get_phase_paths(outputs_root: str | Path, phase: str) -> WorkflowPhasePaths:
    outputs_root = Path(outputs_root)
    paths = WorkflowPhasePaths(
        phase=phase,
        runs_root=outputs_root / "runs" / phase,
        summaries_root=outputs_root / "summaries" / phase,
        logs_root=outputs_root / "logs" / phase,
    )
    paths.runs_root.mkdir(parents=True, exist_ok=True)
    paths.summaries_root.mkdir(parents=True, exist_ok=True)
    paths.logs_root.mkdir(parents=True, exist_ok=True)
    return paths


def get_run_dir(phase_paths: WorkflowPhasePaths, config: RunConfig) -> Path:
    run_dir = phase_paths.runs_root / config.geometry_id / config.config_hash
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(_json_safe(payload), handle, indent=2, allow_nan=False)


def write_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="ascii") as handle:
        handle.write("\n".join(lines) + "\n")


def write_summary_tables(phase_paths: WorkflowPhasePaths, df: pd.DataFrame) -> dict[str, str]:
    csv_path = phase_paths.summaries_root / "summary.csv"
    parquet_path = phase_paths.summaries_root / "summary.parquet"
    df.to_csv(csv_path, index=False)
    paths = {"summary_csv": str(csv_path), "summary_parquet": ""}
    try:
        df.to_parquet(parquet_path, index=False)
        paths["summary_parquet"] = str(parquet_path)
    except Exception:
        pass
    return paths


def write_result_bundle(
    phase_paths: WorkflowPhasePaths,
    config: RunConfig,
    result: RunResult,
    *,
    raw_summary: dict[str, Any],
    scan_id: str,
    task_id: str,
    shard_id: str | None,
    upstream_reference_scales_path: str | None,
    status_completion: str,
    status_stage: str,
    status_reason: str | None,
) -> dict[str, str]:
    """Write the per-config artifacts for an executed phase.

    Artifact semantics:
    - `raw_summary.csv` is the adapter-written raw summary snapshot for one config only.
    - `result.json` is the normalized workflow-facing result for that same config.
    """
    run_dir = get_run_dir(phase_paths, config)
    raw_summary_path = run_dir / "raw_summary.csv"
    pd.DataFrame([raw_summary]).to_csv(raw_summary_path, index=False)

    result_payload = result.to_dict()
    result_payload["input_config"] = config.to_dict()
    result_payload["raw_summary_path"] = str(raw_summary_path)
    result_payload["raw_summary_kind"] = "adapter_raw_summary_csv"
    result_payload["raw_summary_status"] = "available"
    result_payload["normalized_result_path"] = str(run_dir / "result.json")
    result_payload["normalized_result_kind"] = "normalized_result_json"
    result_payload["scan_id"] = scan_id
    result_payload["task_id"] = task_id
    result_payload["shard_id"] = shard_id
    result_payload["state_point_id"] = config.config_hash
    result_payload["seed"] = config.seed
    result_payload["upstream_reference_scales_path"] = upstream_reference_scales_path
    result_payload["status_completion"] = status_completion
    result_payload["status_stage"] = status_stage
    result_payload["status_reason"] = status_reason
    result_json_path = run_dir / "result.json"
    write_json(result_json_path, result_payload)

    return {
        "run_dir": str(run_dir),
        "raw_summary_csv": str(raw_summary_path),
        "result_json": str(result_json_path),
    }


def build_phase_metadata(
    *,
    scan_id: str,
    phase: str,
    task_id: str,
    summary_paths: dict[str, str],
    metadata_json_path: str,
    upstream_reference_scales_path: str | None,
    status_completion: str,
    scan_description: str,
    shard_id: str | None = None,
    manifest_path: str | None = None,
    n_state_points: int | None = None,
    n_tasks: int | None = None,
    compatibility_shims: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build the phase-level metadata sidecar.

    This sidecar describes the phase summary tables and any phase-wide manifest,
    but it is not a replacement for per-config `result.json` files.
    """
    return {
        "scan_id": scan_id,
        "phase": phase,
        "task_id": task_id,
        "shard_id": shard_id,
        "summary_csv": summary_paths.get("summary_csv", ""),
        "summary_parquet": summary_paths.get("summary_parquet", ""),
        "metadata_json": metadata_json_path,
        "manifest_path": manifest_path,
        "upstream_reference_scales_path": upstream_reference_scales_path,
        "status_completion": status_completion,
        "status_stage": phase,
        "status_reason": None,
        "n_state_points": n_state_points,
        "n_tasks": n_tasks,
        "git_commit_hash": None,
        "environment_snapshot": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "geometry_checksum": None,
        "config_file_path": None,
        "random_seed_policy": "RunConfig.seed is persisted per state point; legacy trajectory RNG behavior is preserved unchanged.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scan_description": scan_description,
        "code_version": None,
        "compatibility_shims": compatibility_shims or {},
    }


def normalize_persisted_artifact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize old and new persisted payloads to the branch/flow-separated schema."""
    return normalize_model_variant_payload(dict(payload))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def build_state_point_record(
    scan_id: str,
    config: RunConfig,
    result: RunResult,
    *,
    task_id: str,
    shard_id: str | None = None,
    upstream_reference_scales_path: str | None = None,
    status_completion: str = "completed",
    status_stage: str | None = None,
    traj_df: pd.DataFrame | None = None,
    result_json_path: str | None = None,
    raw_summary_kind: str = "adapter_raw_summary_csv",
    raw_summary_status: str = "available",
    phase_summary_path: str | None = None,
    metadata_sidecar_path: str | None = None,
    task_manifest_path: str | None = None,
) -> dict[str, Any]:
    """Build a persisted state-point row with explicit artifact provenance.

    Provenance policy:
    - `raw_summary_path` refers only to the per-config adapter-written raw summary CSV.
    - `normalized_result_path` refers only to the per-config normalized `result.json`.
    - `phase_summary_path` refers to the phase-level summary table containing this row.
    - `metadata_sidecar_path` refers to the phase-level `metadata.json`.
    - `task_manifest_path` is only populated for manifest-producing phases such as coarse scan generation.
    """
    config_dict = config.to_dict()
    tau_p = (1.0 / config.Dr) if config.Dr != 0.0 else None
    gamma1_over_gamma0 = config.gamma1_over_gamma0
    if gamma1_over_gamma0 is None:
        gamma1_over_gamma0 = (config.gamma1 / config.gamma0) if config.gamma0 != 0.0 else None
    finite_fpt = pd.Series(dtype=float)
    if traj_df is not None and "t_exit_or_nan" in traj_df:
        finite_fpt = traj_df["t_exit_or_nan"].dropna()
    legacy_summary = result.metadata.get("legacy_summary", {})
    return {
        "scan_id": scan_id,
        "task_id": task_id,
        "shard_id": shard_id,
        "state_point_id": config.config_hash,
        "config_hash": config.config_hash,
        "geometry_id": result.geometry_id,
        "model_variant": result.model_variant,
        "flow_condition": result.flow_condition,
        "legacy_model_variant": result.legacy_model_variant,
        "seed": config.seed,
        "v0": config.v0,
        "Dr": config.Dr,
        "tau_v": config.tau_v,
        "gamma0": config.gamma0,
        "gamma1": config.gamma1,
        "tau_f": config.tau_f,
        "U": config.U,
        "wall_thickness": config.wall_thickness,
        "gate_width": config.gate_width,
        "dt": config.dt,
        "Tmax": config.Tmax,
        "exit_radius": config.exit_radius,
        "n_shell": config.n_shell,
        "grid_n": config.grid_n,
        "kf": config.kf,
        "kBT": config.kBT,
        "eps_psi": config.eps_psi,
        "gamma1_over_gamma0": gamma1_over_gamma0,
        "tau_p": tau_p,
        "tau_v_over_tau_p": (config.tau_v / tau_p) if tau_p else None,
        "tau_f_over_tau_p": (config.tau_f / tau_p) if tau_p else None,
        "U_over_v0": (config.U / config.v0) if config.v0 != 0.0 else None,
        "Xi": legacy_summary.get("Xi"),
        "De": legacy_summary.get("De"),
        "tau_m": legacy_summary.get("tau_m"),
        "n_traj": result.n_traj,
        "n_success": result.n_success,
        "Psucc_mean": result.p_succ,
        "Psucc_ci_low": result.ci.get("p_succ", {}).get("low"),
        "Psucc_ci_high": result.ci.get("p_succ", {}).get("high"),
        "MFPT_mean": result.mfpt_mean,
        "MFPT_median": result.mfpt_median,
        "FPT_q10": float(finite_fpt.quantile(0.1)) if not finite_fpt.empty else None,
        "FPT_q90": result.mfpt_q90,
        "trap_time_mean": result.trap_time_mean,
        "trap_count_mean": result.trap_count_mean,
        "wall_fraction_mean": result.wall_fraction_mean,
        "Sigma_drag_mean": result.sigma_drag_mean,
        "J_proxy": legacy_summary.get("J_proxy"),
        "eta_sigma_mean": result.eta_sigma,
        "eta_sigma_ci_low": result.ci.get("eta_sigma", {}).get("low"),
        "eta_sigma_ci_high": result.ci.get("eta_sigma", {}).get("high"),
        "revisit_mean": result.revisit_rate_mean,
        "alignment_mean": None,
        "alignment_lag_peak": None,
        "status_converged": None,
        "status_rare_event_used": False,
        "status_completion": status_completion,
        "status_stage": status_stage or scan_id,
        "status_reason": None,
        "runtime_seconds": None,
        "code_version": None,
        "result_json": result_json_path,
        "normalized_result_path": result_json_path,
        "normalized_result_kind": "normalized_result_json" if result_json_path else "not_applicable_generation_only",
        "raw_summary_path": result.raw_summary_path,
        "raw_summary_kind": raw_summary_kind,
        "raw_summary_status": raw_summary_status,
        "phase_summary_path": phase_summary_path,
        "phase_summary_kind": "phase_summary_table",
        "metadata_sidecar_path": metadata_sidecar_path,
        "metadata_sidecar_kind": "metadata_json_sidecar",
        "task_manifest_path": task_manifest_path,
        "task_manifest_kind": "task_manifest_json" if task_manifest_path else None,
        "upstream_reference_scales_path": upstream_reference_scales_path,
        "metadata_json": json.dumps(config_dict.get("metadata", {}), sort_keys=True),
    }
