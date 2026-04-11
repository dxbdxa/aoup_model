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
from src.configs.schema import RunConfig, SweepTask
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

EXECUTION_STAGE = "coarse_scan_execute"
EXECUTION_REASON = "executed_from_manifest"


def load_coarse_scan_manifest(manifest_path: str | Path) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    with open(manifest_path, "r", encoding="ascii") as handle:
        payload = json.load(handle)
    if payload.get("scan_id") != "coarse_scan":
        raise ValueError(f"Unsupported manifest scan_id: {payload.get('scan_id')!r}")
    return payload


def manifest_tasks_from_payload(payload: dict[str, Any]) -> tuple[SweepTask, ...]:
    tasks: list[SweepTask] = []
    for task_payload in payload.get("tasks", []):
        configs = tuple(RunConfig.from_dict(item) for item in task_payload.get("config_list", []))
        tasks.append(
            SweepTask(
                task_id=str(task_payload["task_id"]),
                phase=str(task_payload["phase"]),
                batch_index=int(task_payload["batch_index"]),
                config_list=configs,
                metadata=dict(task_payload.get("metadata", {})),
            )
        )
    return tuple(tasks)


def infer_output_root_from_manifest(manifest_path: str | Path) -> Path:
    manifest_path = Path(manifest_path)
    if manifest_path.name != "task_manifest.json":
        raise ValueError(f"Manifest path must end in task_manifest.json: {manifest_path}")
    return manifest_path.parents[2]


def load_reference_scales(reference_scales_path: str | Path | None) -> dict[str, Any] | None:
    if reference_scales_path in (None, ""):
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


def _task_matches(
    task: SweepTask,
    *,
    task_id: str | None,
    batch_index: int | None,
    shard_id: str | None,
) -> bool:
    if task_id is not None and task.task_id != task_id:
        return False
    if batch_index is not None and task.batch_index != batch_index:
        return False
    if shard_id is not None and f"batch_{task.batch_index:03d}" != shard_id:
        return False
    return True


def select_manifest_tasks(
    tasks: tuple[SweepTask, ...],
    *,
    task_id: str | None = None,
    batch_index: int | None = None,
    shard_id: str | None = None,
) -> tuple[SweepTask, ...]:
    if task_id is None and batch_index is None and shard_id is None:
        return tasks
    selected = tuple(
        task for task in tasks if _task_matches(task, task_id=task_id, batch_index=batch_index, shard_id=shard_id)
    )
    if not selected:
        raise ValueError("No coarse-scan tasks matched the requested selector.")
    return selected


def merge_executed_rows(existing_summary_path: Path, executed_rows: list[dict[str, Any]]) -> pd.DataFrame:
    executed_df = pd.DataFrame(executed_rows)
    if existing_summary_path.exists():
        existing_df = pd.read_csv(existing_summary_path)
    else:
        existing_df = pd.DataFrame()

    if existing_df.empty:
        return executed_df
    if "state_point_id" not in existing_df.columns:
        raise ValueError(f"Existing coarse-scan summary is missing state_point_id: {existing_summary_path}")
    if "state_point_id" not in executed_df.columns:
        raise ValueError("Executed coarse-scan rows are missing state_point_id.")
    ordered_state_point_ids = existing_df["state_point_id"].astype(str).tolist()
    merged_by_state_point = {
        str(row["state_point_id"]): row for row in existing_df.to_dict(orient="records") if row.get("state_point_id") is not None
    }
    for row in executed_rows:
        state_point_id = str(row["state_point_id"])
        merged_by_state_point[state_point_id] = row
        if state_point_id not in ordered_state_point_ids:
            ordered_state_point_ids.append(state_point_id)
    return pd.DataFrame([merged_by_state_point[state_point_id] for state_point_id in ordered_state_point_ids])


def summarize_execution_progress(summary_df: pd.DataFrame) -> dict[str, Any]:
    if summary_df.empty:
        return {
            "n_state_points": 0,
            "n_executed_state_points": 0,
            "n_generated_only_state_points": 0,
            "status_completion": "partially_completed",
            "status_reason": "coarse_scan_no_rows",
        }

    status_stage = summary_df.get("status_stage")
    if status_stage is None:
        executed_mask = pd.Series(False, index=summary_df.index)
    else:
        executed_mask = status_stage.fillna("").astype(str) == EXECUTION_STAGE
    n_state_points = int(len(summary_df))
    n_executed = int(executed_mask.sum())
    n_generated_only = n_state_points - n_executed
    status_completion = "completed" if n_executed == n_state_points else "partially_completed"
    status_reason = None if status_completion == "completed" else "coarse_scan_partial_execution"
    return {
        "n_state_points": n_state_points,
        "n_executed_state_points": n_executed,
        "n_generated_only_state_points": n_generated_only,
        "status_completion": status_completion,
        "status_reason": status_reason,
    }


def run_coarse_scan_execute(
    project_root: str | Path,
    *,
    manifest_path: str | Path,
    output_root: str | Path | None = None,
    task_id: str | None = None,
    batch_index: int | None = None,
    shard_id: str | None = None,
    max_configs: int | None = None,
    upstream_reference_scales_path: str | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    manifest_path = Path(manifest_path)
    output_root = Path(output_root) if output_root is not None else infer_output_root_from_manifest(manifest_path)
    phase_paths = get_phase_paths(output_root, "coarse_scan")

    payload = load_coarse_scan_manifest(manifest_path)
    all_tasks = manifest_tasks_from_payload(payload)
    selected_tasks = select_manifest_tasks(all_tasks, task_id=task_id, batch_index=batch_index, shard_id=shard_id)

    selected_pairs: list[tuple[SweepTask, RunConfig]] = [
        (task, config) for task in selected_tasks for config in task.config_list
    ]
    if max_configs is not None:
        selected_pairs = selected_pairs[:max_configs]
    if not selected_pairs:
        raise ValueError("The selected coarse-scan execution set contains no state points.")

    upstream_path = upstream_reference_scales_path or payload.get("upstream_reference_scales_path")
    reference_scales = load_reference_scales(upstream_path)
    adapter = LegacySimcoreAdapter(project_root)

    executed_rows: list[dict[str, Any]] = []
    for task, config in selected_pairs:
        shard_label = f"batch_{task.batch_index:03d}"
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
            scan_id="coarse_scan",
            task_id=task.task_id,
            shard_id=shard_label,
            upstream_reference_scales_path=upstream_path,
            status_completion="completed",
            status_stage=EXECUTION_STAGE,
            status_reason=EXECUTION_REASON,
        )
        row = build_state_point_record(
            "coarse_scan",
            config,
            result,
            task_id=task.task_id,
            shard_id=shard_label,
            upstream_reference_scales_path=upstream_path,
            status_completion="completed",
            status_stage=EXECUTION_STAGE,
            traj_df=traj_df,
            result_json_path=run_paths["result_json"],
            raw_summary_kind="adapter_raw_summary_csv",
            raw_summary_status="available",
            phase_summary_path=str(phase_paths.summaries_root / "summary.csv"),
            metadata_sidecar_path=str(phase_paths.summaries_root / "metadata.json"),
            task_manifest_path=str(manifest_path),
        )
        row["status_reason"] = EXECUTION_REASON
        row["task_manifest_kind"] = "task_manifest_json"
        row["phase"] = task.phase
        row["batch_index"] = task.batch_index
        row = augment_row_with_reference_scales(row, reference_scales)
        row["result_json"] = run_paths["result_json"]
        executed_rows.append(row)

    summary_df = merge_executed_rows(phase_paths.summaries_root / "summary.csv", executed_rows)
    summary_paths = write_summary_tables(phase_paths, summary_df)
    progress = summarize_execution_progress(summary_df)
    metadata_json = phase_paths.summaries_root / "metadata.json"
    selected_task_ids = sorted({task.task_id for task, _ in selected_pairs})
    selected_shards = sorted({f"batch_{task.batch_index:03d}" for task, _ in selected_pairs})
    metadata = build_phase_metadata(
        scan_id="coarse_scan",
        phase="coarse_scan",
        task_id=selected_task_ids[0] if len(selected_task_ids) == 1 else "coarse_scan_execute",
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=upstream_path,
        status_completion=progress["status_completion"],
        scan_description="Executed coarse-scan state points from an existing manifest through the legacy adapter.",
        shard_id=selected_shards[0] if len(selected_shards) == 1 else None,
        manifest_path=str(manifest_path),
        n_state_points=progress["n_state_points"],
        n_tasks=len(all_tasks),
    )
    metadata["status_stage"] = EXECUTION_STAGE
    metadata["status_reason"] = progress["status_reason"]
    metadata["selected_task_ids"] = selected_task_ids
    metadata["selected_shards"] = selected_shards
    metadata["n_selected_tasks"] = len(selected_task_ids)
    metadata["n_executed_state_points"] = progress["n_executed_state_points"]
    metadata["n_generated_only_state_points"] = progress["n_generated_only_state_points"]
    metadata["model_variants"] = sorted(summary_df["model_variant"].dropna().astype(str).unique().tolist())
    metadata["flow_conditions"] = sorted(summary_df["flow_condition"].dropna().astype(str).unique().tolist())
    metadata["geometry_ids"] = sorted(summary_df["geometry_id"].dropna().astype(str).unique().tolist())
    metadata["reference_tau_g"] = reference_scales.get("tau_g") if reference_scales else None
    metadata["reference_l_g"] = reference_scales.get("ell_g") if reference_scales else None
    metadata["reference_tau_p"] = reference_scales.get("tau_p") if reference_scales else None
    write_json(metadata_json, metadata)

    log_suffix = selected_shards[0] if len(selected_shards) == 1 else "selected"
    write_log(
        phase_paths.logs_root / f"coarse_scan_execute_{log_suffix}.log",
        [
            "coarse_scan_execute",
            f"manifest_path={manifest_path}",
            f"selected_task_ids={','.join(selected_task_ids)}",
            f"selected_shards={','.join(selected_shards)}",
            f"n_executed_state_points={progress['n_executed_state_points']}",
            f"summary_csv={summary_paths['summary_csv']}",
        ],
    )
    metadata["metadata_json"] = str(metadata_json)
    return {
        "manifest_path": str(manifest_path),
        "selected_task_ids": selected_task_ids,
        "selected_shards": selected_shards,
        "executed_rows": executed_rows,
        "summary_df": summary_df,
        "metadata": metadata,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute one batch or shard from a coarse-scan task manifest.")
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "runs" / "coarse_scan" / "task_manifest.json",
        help="Path to an existing coarse-scan task manifest.",
    )
    parser.add_argument("--output-root", type=Path, help="Override output directory; defaults to the manifest root.")
    parser.add_argument("--task-id", help="Execute only the matching coarse-scan task_id.")
    parser.add_argument("--batch-index", type=int, help="Execute only the matching coarse-scan batch index.")
    parser.add_argument("--shard-id", help="Execute only the matching shard label, e.g. batch_000.")
    parser.add_argument("--max-configs", type=int, help="Limit execution to the first N selected state points.")
    parser.add_argument(
        "--upstream-reference-scales-path",
        help="Override the upstream reference scales path recorded in outputs.",
    )
    args = parser.parse_args(argv)

    result = run_coarse_scan_execute(
        PROJECT_ROOT,
        manifest_path=args.manifest_path,
        output_root=args.output_root,
        task_id=args.task_id,
        batch_index=args.batch_index,
        shard_id=args.shard_id,
        max_configs=args.max_configs,
        upstream_reference_scales_path=args.upstream_reference_scales_path,
    )
    print(json.dumps(result["metadata"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
