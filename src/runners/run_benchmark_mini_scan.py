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


def load_reference_scales(reference_scales_path: str | Path | None) -> dict[str, Any] | None:
    if reference_scales_path is None:
        return None
    reference_scales_path = Path(reference_scales_path)
    if not reference_scales_path.exists():
        return None
    with open(reference_scales_path, "r", encoding="ascii") as handle:
        return json.load(handle)


def augment_row_with_reference_scales(row: dict[str, Any], reference_scales: dict[str, Any] | None) -> dict[str, Any]:
    if reference_scales is None:
        row["reference_tau_g"] = None
        row["reference_l_g"] = None
        row["reference_tau_p"] = None
        row["tau_v_over_tau_g"] = None
        row["tau_f_over_tau_g"] = None
        row["U_tau_g_over_l_g"] = None
        row["Pi_m"] = None
        row["Pi_f"] = None
        row["Pi_U"] = None
        return row

    tau_g = reference_scales.get("tau_g")
    l_g = reference_scales.get("ell_g")
    tau_p = reference_scales.get("tau_p")
    row["reference_tau_g"] = tau_g
    row["reference_l_g"] = l_g
    row["reference_tau_p"] = tau_p
    row["tau_v_over_tau_g"] = (row["tau_v"] / tau_g) if tau_g else None
    row["tau_f_over_tau_g"] = (row["tau_f"] / tau_g) if tau_g else None
    row["U_tau_g_over_l_g"] = (row["U"] * tau_g / l_g) if l_g else None
    row["Pi_m"] = row["tau_v_over_tau_g"]
    row["Pi_f"] = row["tau_f_over_tau_g"]
    row["Pi_U"] = row["U_tau_g_over_l_g"]
    return row


def _variant_parameters(model_variant: str) -> tuple[float, float]:
    if model_variant == "full":
        return 4.0, 3.0
    if model_variant == "no_memory":
        return 0.0, 3.0
    if model_variant == "no_feedback":
        return 4.0, 0.0
    raise ValueError(f"Unsupported benchmark mini-scan variant: {model_variant}")


def build_benchmark_mini_scan_configs(
    *,
    geometry_id: str = "maze_v1",
    variants: tuple[str, ...] = ("full", "no_memory", "no_feedback"),
    Dr_values: tuple[float, ...] = (2.0, 1.0, 0.5),
    tau_v_values: tuple[float, ...] = (0.25, 0.5, 1.0),
    tau_f_values: tuple[float, ...] = (0.125, 0.25, 0.5),
    U_values: tuple[float, ...] = (0.0, 0.125, 0.25),
    base_seed: int = 20260411,
    n_traj: int = 64,
    Tmax: float = 20.0,
    grid_n: int = 257,
    n_shell: int = 1,
) -> tuple[RunConfig, ...]:
    if not (len(Dr_values) == len(tau_v_values) == len(tau_f_values) == len(U_values)):
        raise ValueError("Mini-scan control tuples must have matching lengths.")

    configs: list[RunConfig] = []
    point_index = 0
    for variant in variants:
        gamma1, kf = _variant_parameters(variant)
        for Dr, tau_v, tau_f, U in zip(Dr_values, tau_v_values, tau_f_values, U_values):
            configs.append(
                RunConfig(
                    geometry_id=geometry_id,
                    model_variant=variant,
                    v0=0.5,
                    Dr=Dr,
                    tau_v=tau_v,
                    gamma0=1.0,
                    gamma1=gamma1,
                    tau_f=tau_f,
                    U=U,
                    wall_thickness=0.04,
                    gate_width=0.08,
                    dt=0.0025,
                    Tmax=Tmax,
                    n_traj=n_traj,
                    seed=base_seed + point_index,
                    exit_radius=0.06,
                    n_shell=n_shell,
                    grid_n=grid_n,
                    kf=kf,
                    flow_condition="zero_flow" if abs(U) <= 1e-15 else "with_flow",
                    metadata={
                        "L": 1.0,
                        "workflow_stage": "benchmark_mini_scan",
                        "state_point_index": point_index,
                    },
                )
            )
            point_index += 1
    return tuple(configs)


def run_benchmark_mini_scan(
    project_root: str | Path,
    *,
    configs: tuple[RunConfig, ...] | None = None,
    output_root: str | Path | None = None,
    max_configs: int | None = None,
    upstream_reference_scales_path: str | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
    phase_paths = get_phase_paths(output_root, "benchmark_mini_scan")
    scan_id = "benchmark_mini_scan"
    scan_configs = configs or build_benchmark_mini_scan_configs()
    if max_configs is not None:
        scan_configs = scan_configs[:max_configs]
    reference_scales = load_reference_scales(upstream_reference_scales_path)

    adapter = LegacySimcoreAdapter(project_root)
    rows: list[dict[str, Any]] = []
    for config in scan_configs:
        task_id = f"{scan_id}_{config.model_variant}"
        summary, traj_df, trap_df = adapter.run_point(config)
        raw_summary_csv = get_run_dir(phase_paths, config) / "raw_summary.csv"
        result = adapter.summary_to_result(
            config,
            summary,
            traj_df=traj_df,
            trap_df=trap_df,
            artifact_paths={"summary_csv": str(raw_summary_csv)},
        )
        run_paths = write_result_bundle(
            phase_paths,
            config,
            result,
            raw_summary=summary,
            scan_id=scan_id,
            task_id=task_id,
            shard_id=None,
            upstream_reference_scales_path=upstream_reference_scales_path,
            status_completion="completed",
            status_stage=scan_id,
            status_reason=None,
        )
        row = build_state_point_record(
            scan_id,
            config,
            result,
            task_id=task_id,
            shard_id=None,
            upstream_reference_scales_path=upstream_reference_scales_path,
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
        row = augment_row_with_reference_scales(row, reference_scales)
        for key in ("scan_block", "scan_label", "sensitivity_axis", "sensitivity_level"):
            row[key] = config.metadata.get(key)
        row["result_json"] = run_paths["result_json"]
        rows.append(row)

    summary_df = pd.DataFrame(rows)
    summary_paths = write_summary_tables(phase_paths, summary_df)
    metadata = {
        "scan_id": "benchmark_mini_scan",
        "n_configs": len(scan_configs),
        "summary_csv": summary_paths["summary_csv"],
        "summary_parquet": summary_paths["summary_parquet"],
        "model_variants": sorted({config.model_variant for config in scan_configs}),
        "flow_conditions": sorted({config.flow_condition for config in scan_configs}),
        "geometry_ids": sorted({config.geometry_id for config in scan_configs}),
        "upstream_reference_scales_path": upstream_reference_scales_path,
        "reference_tau_g": reference_scales.get("tau_g") if reference_scales else None,
        "reference_l_g": reference_scales.get("ell_g") if reference_scales else None,
        "reference_tau_p": reference_scales.get("tau_p") if reference_scales else None,
        "status_completion": "completed",
        "status_stage": scan_id,
        "status_reason": None,
    }
    metadata_json = phase_paths.summaries_root / "metadata.json"
    metadata = build_phase_metadata(
        scan_id=scan_id,
        phase=scan_id,
        task_id=scan_id,
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=upstream_reference_scales_path,
        status_completion="completed",
        scan_description="Benchmark mini-scan executed through the legacy adapter.",
        n_state_points=len(scan_configs),
    ) | metadata
    write_json(metadata_json, metadata)
    write_log(
        phase_paths.logs_root / "benchmark_mini_scan.log",
        [
            "benchmark_mini_scan",
            f"n_configs={len(scan_configs)}",
            f"summary_csv={summary_paths['summary_csv']}",
        ],
    )
    metadata["metadata_json"] = str(metadata_json)
    return {"summary_df": summary_df, "metadata": metadata}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a benchmark mini-scan through the legacy simcore adapter.")
    parser.add_argument("--output-root", type=Path, help="Override output directory.")
    parser.add_argument("--max-configs", type=int, help="Only run the first N mini-scan configurations.")
    parser.add_argument("--n-traj", type=int, default=64, help="Trajectories per mini-scan point.")
    args = parser.parse_args(argv)

    configs = build_benchmark_mini_scan_configs(n_traj=args.n_traj)
    result = run_benchmark_mini_scan(PROJECT_ROOT, configs=configs, output_root=args.output_root, max_configs=args.max_configs)
    print(json.dumps(result["metadata"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
