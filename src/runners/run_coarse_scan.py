from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from src.configs.schema import RunConfig, SweepTask
from src.utils.workflow_schema import build_phase_metadata, get_phase_paths, write_json, write_log, write_summary_tables


def _variant_parameters(model_variant: str, base_gamma0: float) -> tuple[float, float]:
    if model_variant == "full":
        return 4.0 * base_gamma0, 3.0
    if model_variant == "no_memory":
        return 0.0, 3.0
    if model_variant == "no_feedback":
        return 4.0 * base_gamma0, 0.0
    if model_variant == "no_flow":
        return 4.0 * base_gamma0, 3.0
    raise ValueError(f"Unsupported coarse scan variant: {model_variant}")


def _lhs_linear(low: float, high: float, n: int, rng: np.random.Generator) -> np.ndarray:
    bins = (np.arange(n, dtype=float) + rng.random(n)) / n
    rng.shuffle(bins)
    return low + (high - low) * bins


def _lhs_log10(low: float, high: float, n: int, rng: np.random.Generator) -> np.ndarray:
    log_values = _lhs_linear(math.log10(low), math.log10(high), n, rng)
    return np.power(10.0, log_values)


def build_coarse_scan_configs(
    *,
    num_points: int = 24,
    model_variants: tuple[str, ...] = ("full",),
    base_seed: int = 20260411,
    geometry_id: str = "maze_v1",
    n_traj: int = 256,
    Tmax: float = 20.0,
    grid_n: int = 257,
    n_shell: int = 1,
) -> tuple[RunConfig, ...]:
    rng = np.random.default_rng(base_seed)
    Dr_values = _lhs_log10(0.2, 2.0, num_points, rng)
    tau_v_values = _lhs_log10(1e-2, 1e2, num_points, rng)
    tau_f_values = _lhs_log10(1e-2, 1e2, num_points, rng)
    U_values = _lhs_linear(-0.75, 0.75, num_points, rng)

    configs: list[RunConfig] = []
    config_index = 0
    for model_variant in model_variants:
        for point_index in range(num_points):
            gamma1, kf = _variant_parameters(model_variant, base_gamma0=1.0)
            U = float(U_values[point_index])
            flow_condition = "with_flow"
            normalized_variant = model_variant
            legacy_model_variant = None
            if model_variant == "no_flow":
                U = 0.0
                flow_condition = "explicit_no_flow_control"
                normalized_variant = "full"
                legacy_model_variant = "no_flow"
            elif abs(U) <= 1e-15:
                flow_condition = "zero_flow"
            configs.append(
                RunConfig(
                    geometry_id=geometry_id,
                    model_variant=normalized_variant,
                    v0=0.5,
                    Dr=float(Dr_values[point_index]),
                    tau_v=float(tau_v_values[point_index]),
                    gamma0=1.0,
                    gamma1=gamma1,
                    tau_f=float(tau_f_values[point_index]),
                    U=U,
                    wall_thickness=0.04,
                    gate_width=0.08,
                    dt=0.0025,
                    Tmax=Tmax,
                    n_traj=n_traj,
                    seed=base_seed + config_index,
                    exit_radius=0.06,
                    n_shell=n_shell,
                    grid_n=grid_n,
                    kf=kf,
                    flow_condition=flow_condition,
                    metadata={
                        "L": 1.0,
                        "workflow_stage": "coarse_scan_generation",
                        "state_point_index": point_index,
                    },
                    legacy_model_variant=legacy_model_variant,
                )
            )
            config_index += 1
    return tuple(configs)


def generate_coarse_scan_tasks(
    *,
    num_points: int = 24,
    batch_size: int = 8,
    model_variants: tuple[str, ...] = ("full",),
    base_seed: int = 20260411,
) -> tuple[SweepTask, ...]:
    configs = build_coarse_scan_configs(
        num_points=num_points,
        model_variants=model_variants,
        base_seed=base_seed,
    )
    tasks: list[SweepTask] = []
    for batch_index, offset in enumerate(range(0, len(configs), batch_size)):
        batch = configs[offset : offset + batch_size]
        tasks.append(
            SweepTask(
                task_id=f"coarse_scan_batch_{batch_index:03d}",
                phase="coarse_scan",
                batch_index=batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "model_variants": list(model_variants),
                    "base_seed": base_seed,
                },
            )
        )
    return tuple(tasks)


def write_coarse_scan_manifest(
    project_root: str | Path,
    *,
    tasks: tuple[SweepTask, ...] | None = None,
    output_root: str | Path | None = None,
    upstream_reference_scales_path: str | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
    phase_paths = get_phase_paths(output_root, "coarse_scan")
    scan_id = "coarse_scan"
    task_list = tasks or generate_coarse_scan_tasks()
    manifest_path = phase_paths.runs_root / "task_manifest.json"
    payload = {
        "phase": scan_id,
        "scan_id": scan_id,
        "task_id": "generate_coarse_scan_tasks",
        "shard_id": None,
        "status_completion": "generated_manifest_only",
        "status_stage": scan_id,
        "status_reason": "coarse_scan_generation_only",
        "upstream_reference_scales_path": upstream_reference_scales_path,
        "n_tasks": len(task_list),
        "tasks": [task.to_dict() for task in task_list],
    }
    write_json(manifest_path, payload)

    rows: list[dict[str, Any]] = []
    for task in task_list:
        for config in task.config_list:
            tau_p = (1.0 / config.Dr) if config.Dr != 0.0 else None
            gamma1_over_gamma0 = config.gamma1_over_gamma0
            if gamma1_over_gamma0 is None:
                gamma1_over_gamma0 = (config.gamma1 / config.gamma0) if config.gamma0 != 0.0 else None
            rows.append(
                {
                    "scan_id": scan_id,
                    "task_id": task.task_id,
                    "shard_id": f"batch_{task.batch_index:03d}",
                    "phase": task.phase,
                    "batch_index": task.batch_index,
                    "state_point_id": config.config_hash,
                    "config_hash": config.config_hash,
                    "geometry_id": config.geometry_id,
                    "model_variant": config.model_variant,
                    "flow_condition": config.flow_condition,
                    "legacy_model_variant": config.legacy_model_variant,
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
                    "n_traj": config.n_traj,
                    "n_success": None,
                    "Psucc_mean": None,
                    "Psucc_ci_low": None,
                    "Psucc_ci_high": None,
                    "MFPT_mean": None,
                    "MFPT_median": None,
                    "FPT_q10": None,
                    "FPT_q90": None,
                    "trap_time_mean": None,
                    "trap_count_mean": None,
                    "wall_fraction_mean": None,
                    "Sigma_drag_mean": None,
                    "J_proxy": None,
                    "eta_sigma_mean": None,
                    "eta_sigma_ci_low": None,
                    "eta_sigma_ci_high": None,
                    "revisit_mean": None,
                    "alignment_mean": None,
                    "alignment_lag_peak": None,
                    "status_converged": None,
                    "status_rare_event_used": False,
                    "status_completion": "generated_manifest_only",
                    "status_stage": scan_id,
                    "status_reason": "coarse_scan_generation_only",
                    "runtime_seconds": None,
                    "code_version": None,
                    "result_json": None,
                    "normalized_result_path": None,
                    "normalized_result_kind": "not_applicable_generation_only",
                    "raw_summary_path": None,
                    "raw_summary_kind": "not_applicable_generation_only",
                    "raw_summary_status": "not_applicable",
                    "phase_summary_path": str(phase_paths.summaries_root / "summary.csv"),
                    "phase_summary_kind": "phase_summary_table",
                    "metadata_sidecar_path": str(phase_paths.summaries_root / "metadata.json"),
                    "metadata_sidecar_kind": "metadata_json_sidecar",
                    "task_manifest_path": str(manifest_path),
                    "task_manifest_kind": "task_manifest_json",
                    "upstream_reference_scales_path": upstream_reference_scales_path,
                    "metadata_json": json.dumps(config.metadata, sort_keys=True),
                }
            )
    if rows:
        import pandas as pd

        summary_paths = write_summary_tables(phase_paths, pd.DataFrame(rows))
    else:
        summary_paths = {"summary_csv": "", "summary_parquet": ""}
    metadata_json = phase_paths.summaries_root / "metadata.json"
    metadata = build_phase_metadata(
        scan_id=scan_id,
        phase=scan_id,
        task_id="generate_coarse_scan_tasks",
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=upstream_reference_scales_path,
        status_completion="generated_manifest_only",
        scan_description="Coarse-scan task generation only; no execution is performed at this stage.",
        manifest_path=str(manifest_path),
        n_state_points=len(rows),
        n_tasks=len(task_list),
    )
    metadata["status_reason"] = "coarse_scan_generation_only"
    metadata["model_variants"] = sorted({config.model_variant for task in task_list for config in task.config_list})
    metadata["flow_conditions"] = sorted({config.flow_condition for task in task_list for config in task.config_list})
    write_json(metadata_json, metadata)
    write_log(
        phase_paths.logs_root / "generate_coarse_scan_tasks.log",
        [
            "generate_coarse_scan_tasks",
            f"n_tasks={len(task_list)}",
            f"manifest_path={manifest_path}",
        ],
    )
    return {
        "manifest_path": str(manifest_path),
        "n_tasks": len(task_list),
        "tasks": task_list,
        "summary_csv": summary_paths["summary_csv"],
        "summary_parquet": summary_paths["summary_parquet"],
        "metadata_json": str(metadata_json),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate coarse scan tasks compatible with the legacy adapter.")
    parser.add_argument("--output-root", type=Path, help="Override manifest output directory.")
    parser.add_argument("--num-points", type=int, default=24, help="State points per model variant.")
    parser.add_argument("--batch-size", type=int, default=8, help="Configs per coarse scan task.")
    args = parser.parse_args(argv)

    tasks = generate_coarse_scan_tasks(num_points=args.num_points, batch_size=args.batch_size)
    result = write_coarse_scan_manifest(PROJECT_ROOT, tasks=tasks, output_root=args.output_root)
    print(json.dumps({"manifest_path": result["manifest_path"], "n_tasks": result["n_tasks"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
