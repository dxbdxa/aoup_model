from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.legacy_simcore_adapter import LegacySimcoreAdapter
from src.configs.schema import RunConfig
from src.utils.workflow_schema import (
    build_phase_metadata,
    build_state_point_record,
    get_phase_paths,
    get_run_dir,
    write_json,
    write_log,
    write_result_bundle,
    write_summary_tables,
)


def build_reference_run_config(
    *,
    geometry_id: str = "maze_v1",
    v0: float = 0.5,
    Dr: float = 1.0,
    dt: float = 0.0025,
    Tmax: float = 20.0,
    n_traj: int = 64,
    seed: int = 20260411,
    wall_thickness: float = 0.04,
    gate_width: float = 0.08,
    exit_radius: float = 0.06,
    n_shell: int = 1,
    grid_n: int = 257,
    metadata: dict[str, Any] | None = None,
) -> RunConfig:
    merged_metadata = {"L": 1.0, "workflow_stage": "reference_scale_extraction"}
    if metadata:
        merged_metadata.update(metadata)
    return RunConfig(
        geometry_id=geometry_id,
        model_variant="no_memory",
        v0=v0,
        Dr=Dr,
        tau_v=0.25,
        gamma0=1.0,
        gamma1=0.0,
        tau_f=0.0,
        U=0.0,
        wall_thickness=wall_thickness,
        gate_width=gate_width,
        dt=dt,
        Tmax=Tmax,
        n_traj=n_traj,
        seed=seed,
        exit_radius=exit_radius,
        n_shell=n_shell,
        grid_n=grid_n,
        kf=0.0,
        bootstrap_resamples=256,
        flow_condition="zero_flow",
        metadata=merged_metadata,
    )


def _write_table_with_optional_parquet(df: pd.DataFrame, csv_path: Path, parquet_path: Path) -> dict[str, str]:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    paths = {"csv": str(csv_path)}
    try:
        df.to_parquet(parquet_path, index=False)
        paths["parquet"] = str(parquet_path)
    except Exception:
        paths["parquet"] = ""
    return paths


def extract_reference_scales(
    project_root: str | Path,
    *,
    config: RunConfig | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
    phase_paths = get_phase_paths(output_root, "reference_scales")

    adapter = LegacySimcoreAdapter(project_root)
    run_config = config or build_reference_run_config()
    scan_id = "reference_scales"
    task_id = "reference_scale_extraction"
    summary, traj_df, trap_df = adapter.run_point(run_config)
    raw_summary_csv = get_run_dir(phase_paths, run_config) / "raw_summary.csv"
    result = adapter.summary_to_result(
        run_config,
        summary,
        traj_df=traj_df,
        trap_df=trap_df,
        artifact_paths={"summary_csv": str(raw_summary_csv)},
    )
    run_paths = write_result_bundle(
        phase_paths,
        run_config,
        result,
        raw_summary=summary,
        scan_id=scan_id,
        task_id=task_id,
        shard_id=None,
        upstream_reference_scales_path=None,
        status_completion="completed",
        status_stage=scan_id,
        status_reason=None,
    )

    tau_g = result.mfpt_mean if result.mfpt_mean is not None else run_config.Tmax
    ell_g = run_config.v0 * tau_g
    tau_p = 1.0 / run_config.Dr
    transition_df = traj_df.copy()
    transition_df["success"] = transition_df["success_flag"].astype(bool)
    transition_df["fpt"] = transition_df["t_exit_or_nan"]
    transition_df["wall_fraction"] = transition_df["boundary_contact_fraction_i"]
    transition_df["drag_dissipation"] = transition_df["Sigma_drag_i"]
    transition_df["scan_id"] = scan_id
    transition_df["task_id"] = task_id
    transition_df["shard_id"] = None
    transition_df["state_point_id"] = run_config.config_hash
    transition_df["config_hash"] = run_config.config_hash
    transition_df["seed"] = run_config.seed
    transition_df["geometry_id"] = run_config.geometry_id
    transition_df["model_variant"] = run_config.model_variant
    transition_df["termination_reason"] = transition_df["success"].map(lambda success: "exit" if success else "tmax")
    trap_counts = trap_df.groupby("traj_id").size() if not trap_df.empty else pd.Series(dtype=int)
    transition_df["trap_count"] = transition_df["traj_id"].map(trap_counts).fillna(0).astype(int)
    trap_totals = trap_df.groupby("traj_id")["trap_duration"].sum() if not trap_df.empty else pd.Series(dtype=float)
    transition_df["trap_time_total"] = transition_df["traj_id"].map(trap_totals).fillna(0.0)
    transition_df["path_length"] = None
    transition_df["revisit_count"] = None
    transition_df["mean_progress_along_nav"] = None
    transition_df["mean_speed"] = None
    transition_df["mean_rel_speed_to_flow"] = None
    transition_df["alignment_cos_mean"] = None
    transition_df["alignment_cos_std"] = None
    transition_df["gate_cross_count"] = None
    transition_df["last_gate_index"] = None
    transition_df["upstream_reference_scales_path"] = None
    transition_df["status_completion"] = "completed"
    transition_df["status_stage"] = scan_id
    transition_df["status_reason"] = None

    table_paths = _write_table_with_optional_parquet(
        transition_df,
        phase_paths.summaries_root / "baseline_transition_stats.csv",
        phase_paths.summaries_root / "baseline_transition_stats.parquet",
    )
    summary_df = pd.DataFrame(
        [
            build_state_point_record(
                scan_id,
                run_config,
                result,
                task_id=task_id,
                shard_id=None,
                upstream_reference_scales_path=None,
                status_completion="completed",
                status_stage=scan_id,
                traj_df=traj_df,
                result_json_path=run_paths["result_json"],
                raw_summary_kind="adapter_raw_summary_csv",
                raw_summary_status="available",
                phase_summary_path=str(phase_paths.summaries_root / "summary.csv"),
                metadata_sidecar_path=str(phase_paths.summaries_root / "metadata.json"),
                task_manifest_path=None,
            )
        ]
    )
    summary_paths = write_summary_tables(phase_paths, summary_df)
    reference_scales_json = phase_paths.summaries_root / "reference_scales.json"
    metadata_json = phase_paths.summaries_root / "metadata.json"
    scales = {
        "scan_id": "reference_scale_baseline",
        "task_id": task_id,
        "state_point_id": run_config.config_hash,
        "geometry_id": run_config.geometry_id,
        "model_variant": run_config.model_variant,
        "ell_g": ell_g,
        "tau_g": tau_g,
        "tau_p": tau_p,
        "v0": run_config.v0,
        "Dr": run_config.Dr,
        "n_traj": result.n_traj,
        "n_success": result.n_success,
        "p_succ": result.p_succ,
        "config_hash": run_config.config_hash,
        "reference_config": run_config.to_dict(),
        "result_json": run_paths["result_json"],
        "raw_summary_path": run_paths["raw_summary_csv"],
        "metadata_json": str(metadata_json),
        "transition_stats": table_paths,
        "summary_tables": summary_paths,
        "status_completion": "completed",
        "status_stage": scan_id,
        "status_reason": None,
        "upstream_reference_scales_path": None,
    }
    legacy_reference_dir = output_root / "reference"
    legacy_reference_dir.mkdir(parents=True, exist_ok=True)
    _write_table_with_optional_parquet(
        transition_df,
        legacy_reference_dir / "baseline_transition_stats.csv",
        legacy_reference_dir / "baseline_transition_stats.parquet",
    )
    write_log(
        phase_paths.logs_root / "reference_scale_extraction.log",
        [
            "reference_scale_extraction",
            f"geometry_id={run_config.geometry_id}",
            f"config_hash={run_config.config_hash}",
            f"result_json={run_paths['result_json']}",
        ],
    )
    scales["compatibility_shims"] = {
        "legacy_reference_scales_json": str(legacy_reference_dir / "reference_scales.json"),
        "legacy_transition_stats_csv": str(legacy_reference_dir / "baseline_transition_stats.csv"),
        "legacy_transition_stats_parquet": str(legacy_reference_dir / "baseline_transition_stats.parquet"),
    }
    scales["reference_scales_json"] = str(reference_scales_json)
    metadata = build_phase_metadata(
        scan_id=scan_id,
        phase=scan_id,
        task_id=task_id,
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=None,
        status_completion="completed",
        scan_description="Baseline reference-scale extraction through the legacy adapter.",
        n_state_points=1,
        compatibility_shims=scales["compatibility_shims"],
    )
    write_json(metadata_json, metadata)
    write_json(reference_scales_json, scales)
    write_json(legacy_reference_dir / "reference_scales.json", scales)
    return scales


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract reference scales using the legacy simcore adapter.")
    parser.add_argument("--output-root", type=Path, help="Override output directory for reference scales.")
    parser.add_argument("--n-traj", type=int, default=64, help="Trajectories for the baseline reference run.")
    parser.add_argument("--tmax", type=float, default=20.0, help="Maximum simulation time.")
    args = parser.parse_args(argv)

    config = build_reference_run_config(n_traj=args.n_traj, Tmax=args.tmax)
    result = extract_reference_scales(PROJECT_ROOT, config=config, output_root=args.output_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
