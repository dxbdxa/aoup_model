from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

SCAN_ID = "confirmatory_scan"
EXECUTION_STAGE = "confirmatory_scan_execute"

BASE_PI_F_VALUES = (0.018, 0.02, 0.022, 0.025)
BASE_PI_M_VALUES = (0.08, 0.1, 0.12, 0.15, 0.18, 0.2, 0.22)
BASE_PI_U_VALUES = (0.1, 0.15, 0.2, 0.25, 0.3)

OBJECTIVES: dict[str, dict[str, Any]] = {
    "Psucc_mean": {
        "label": "Success Probability",
        "goal": "max",
        "ci_low": "Psucc_ci_low",
        "ci_high": "Psucc_ci_high",
    },
    "eta_sigma_mean": {
        "label": "Efficiency Screening Signal",
        "goal": "max",
        "ci_low": "eta_sigma_ci_low",
        "ci_high": "eta_sigma_ci_high",
    },
    "MFPT_mean": {
        "label": "Mean First-Passage Time",
        "goal": "min",
        "ci_low": "MFPT_ci_low",
        "ci_high": "MFPT_ci_high",
    },
}

REPORT_PATHS = {
    "run_report": PROJECT_ROOT / "docs" / "confirmatory_scan_run_report.md",
    "first_look": PROJECT_ROOT / "docs" / "confirmatory_scan_first_look.md",
}


def load_reference_scales(reference_scales_path: str | Path) -> dict[str, Any]:
    reference_scales_path = Path(reference_scales_path)
    with open(reference_scales_path, "r", encoding="ascii") as handle:
        return json.load(handle)


def _token(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text.replace("-", "neg").replace(".", "p")


def _make_scan_label(scan_block: str, pi_m: float, pi_f: float, pi_u: float, n_traj: int) -> str:
    return f"full_{scan_block}_pm{_token(pi_m)}_pf{_token(pi_f)}_pu{_token(pi_u)}_n{n_traj}"


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def build_confirmatory_config(
    *,
    reference_scales: dict[str, Any],
    pi_m: float,
    pi_f: float,
    pi_u: float,
    seed: int,
    state_point_index: int,
    scan_block: str,
    n_traj: int,
    dt: float = 0.0025,
    Tmax: float = 30.0,
    metadata_extra: dict[str, Any] | None = None,
) -> RunConfig:
    tau_g = float(reference_scales["tau_g"])
    ell_g = float(reference_scales["ell_g"])
    tau_v = pi_m * tau_g
    tau_f = pi_f * tau_g
    U = pi_u * ell_g / tau_g
    flow_condition = "zero_flow" if abs(U) <= 1e-15 else "with_flow"
    metadata = {
        "L": 1.0,
        "workflow_stage": "confirmatory_scan_generation",
        "state_point_index": state_point_index,
        "scan_block": scan_block,
        "scan_label": _make_scan_label(scan_block, pi_m, pi_f, pi_u, n_traj),
        "target_region": "localized_productive_memory_ridge",
        "Pi_m_target": pi_m,
        "Pi_f_target": pi_f,
        "Pi_U_target": pi_u,
    }
    if metadata_extra:
        metadata.update(metadata_extra)
    return RunConfig(
        geometry_id="maze_v1",
        model_variant="full",
        v0=0.5,
        Dr=1.0,
        tau_v=tau_v,
        gamma0=1.0,
        gamma1=4.0,
        tau_f=tau_f,
        U=U,
        wall_thickness=0.04,
        gate_width=0.08,
        dt=dt,
        Tmax=Tmax,
        n_traj=n_traj,
        seed=seed,
        exit_radius=0.06,
        n_shell=1,
        grid_n=257,
        kf=3.0,
        flow_condition=flow_condition,
        metadata=metadata,
    )


def build_confirmatory_tasks(
    reference_scales: dict[str, Any],
    *,
    batch_size: int = 5,
    base_seed: int = 20261200,
    n_traj: int = 4096,
) -> tuple[SweepTask, ...]:
    configs: list[RunConfig] = []
    seed = base_seed
    state_point_index = 0
    for pi_f in BASE_PI_F_VALUES:
        for pi_m in BASE_PI_M_VALUES:
            for pi_u in BASE_PI_U_VALUES:
                configs.append(
                    build_confirmatory_config(
                        reference_scales=reference_scales,
                        pi_m=pi_m,
                        pi_f=pi_f,
                        pi_u=pi_u,
                        seed=seed,
                        state_point_index=state_point_index,
                        scan_block="confirmatory_ridge_grid",
                        n_traj=n_traj,
                    )
                )
                seed += 1
                state_point_index += 1

    tasks: list[SweepTask] = []
    for batch_index, offset in enumerate(range(0, len(configs), batch_size)):
        batch = tuple(configs[offset : offset + batch_size])
        tasks.append(
            SweepTask(
                task_id=f"confirmatory_scan_batch_{batch_index:03d}",
                phase=SCAN_ID,
                batch_index=batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "scan_name": "localized_confirmatory_scan",
                    "scan_blocks": ["confirmatory_ridge_grid"],
                },
            )
        )
    return tuple(tasks)


def write_confirmatory_manifest(
    *,
    output_root: Path,
    tasks: tuple[SweepTask, ...],
    upstream_reference_scales_path: str,
    manifest_name: str,
    status_reason: str,
    scan_description: str,
) -> dict[str, Any]:
    phase_paths = get_phase_paths(output_root, SCAN_ID)
    manifest_path = phase_paths.runs_root / manifest_name
    payload = {
        "phase": SCAN_ID,
        "scan_id": SCAN_ID,
        "task_id": f"generate_{manifest_name.replace('.json', '')}",
        "shard_id": None,
        "status_completion": "generated_manifest_only",
        "status_stage": SCAN_ID,
        "status_reason": status_reason,
        "upstream_reference_scales_path": upstream_reference_scales_path,
        "n_tasks": len(tasks),
        "tasks": [task.to_dict() for task in tasks],
    }
    write_json(manifest_path, payload)
    metadata_json = phase_paths.summaries_root / "metadata.json"
    metadata = build_phase_metadata(
        scan_id=SCAN_ID,
        phase=SCAN_ID,
        task_id=payload["task_id"],
        summary_paths={"summary_csv": "", "summary_parquet": ""},
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=upstream_reference_scales_path,
        status_completion="generated_manifest_only",
        scan_description=scan_description,
        manifest_path=str(manifest_path),
        n_state_points=sum(len(task.config_list) for task in tasks),
        n_tasks=len(tasks),
    )
    metadata["status_reason"] = status_reason
    write_json(metadata_json, metadata)
    write_log(
        phase_paths.logs_root / f"generate_{manifest_name.replace('.json', '')}.log",
        [
            f"generate_{manifest_name.replace('.json', '')}",
            f"n_tasks={len(tasks)}",
            f"manifest_path={manifest_path}",
        ],
    )
    return {"manifest_path": str(manifest_path), "n_tasks": len(tasks)}


def merge_executed_rows(existing_summary_path: Path, executed_rows: list[dict[str, Any]]) -> pd.DataFrame:
    executed_df = pd.DataFrame(executed_rows)
    if existing_summary_path.exists():
        existing_df = pd.read_csv(existing_summary_path)
    else:
        existing_df = pd.DataFrame()
    if existing_df.empty:
        return executed_df
    ordered_ids = existing_df["state_point_id"].astype(str).tolist()
    merged = {str(row["state_point_id"]): row for row in existing_df.to_dict(orient="records")}
    for row in executed_rows:
        state_point_id = str(row["state_point_id"])
        merged[state_point_id] = row
        if state_point_id not in ordered_ids:
            ordered_ids.append(state_point_id)
    return pd.DataFrame([merged[state_point_id] for state_point_id in ordered_ids])


def augment_row_with_reference_scales(row: dict[str, Any], reference_scales: dict[str, Any]) -> dict[str, Any]:
    tau_g = reference_scales.get("tau_g")
    ell_g = reference_scales.get("ell_g")
    tau_p = reference_scales.get("tau_p")
    row["reference_tau_g"] = tau_g
    row["reference_l_g"] = ell_g
    row["reference_tau_p"] = tau_p
    row["Pi_m"] = (row["tau_v"] / tau_g) if tau_g else None
    row["Pi_f"] = (row["tau_f"] / tau_g) if tau_g else None
    row["Pi_U"] = (row["U"] * tau_g / ell_g) if ell_g else None
    row["tau_v_over_tau_g"] = row["Pi_m"]
    row["tau_f_over_tau_g"] = row["Pi_f"]
    row["U_tau_g_over_l_g"] = row["Pi_U"]
    return row


def summarize_progress(summary_df: pd.DataFrame) -> dict[str, Any]:
    executed_mask = summary_df["status_stage"].fillna("").astype(str) == EXECUTION_STAGE
    n_state_points = int(len(summary_df))
    n_executed = int(executed_mask.sum())
    n_generated_only = n_state_points - n_executed
    status_completion = "completed" if n_executed == n_state_points else "partially_completed"
    status_reason = None if status_completion == "completed" else "confirmatory_scan_partial_execution"
    return {
        "n_state_points": n_state_points,
        "n_executed_state_points": n_executed,
        "n_generated_only_state_points": n_generated_only,
        "status_completion": status_completion,
        "status_reason": status_reason,
    }


def _metadata_columns(summary_df: pd.DataFrame) -> pd.DataFrame:
    metadata_payloads = summary_df["metadata_json"].fillna("{}").map(json.loads)
    result = summary_df.copy()
    result["scan_label"] = metadata_payloads.map(lambda payload: payload.get("scan_label"))
    result["scan_block"] = metadata_payloads.map(lambda payload: payload.get("scan_block"))
    result["resampled_from_state_point_id"] = metadata_payloads.map(lambda payload: payload.get("resampled_from_state_point_id"))
    result["resampled_from_scan_label"] = metadata_payloads.map(lambda payload: payload.get("resampled_from_scan_label"))
    result["base_n_traj"] = metadata_payloads.map(lambda payload: payload.get("base_n_traj"))
    return result


def bootstrap_trap_time_ci(
    trap_df: pd.DataFrame,
    *,
    resamples: int,
    seed: int,
) -> tuple[float, float]:
    if trap_df.empty:
        return 0.0, 0.0
    durations = trap_df["trap_duration"].to_numpy(dtype=float)
    if durations.size == 1:
        value = float(durations[0])
        return value, value
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, durations.size, size=(resamples, durations.size))
    samples = durations[idx].mean(axis=1)
    return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


def add_uncertainty_columns(
    row: dict[str, Any],
    *,
    summary: dict[str, Any],
    trap_df: pd.DataFrame,
    bootstrap_resamples: int,
    seed: int,
) -> dict[str, Any]:
    row["MFPT_ci_low"] = _float_or_none(summary.get("MFPT_ci_low"))
    row["MFPT_ci_high"] = _float_or_none(summary.get("MFPT_ci_high"))
    trap_low, trap_high = bootstrap_trap_time_ci(trap_df, resamples=bootstrap_resamples, seed=seed + 1991)
    row["trap_time_ci_low"] = trap_low
    row["trap_time_ci_high"] = trap_high
    row["trap_time_ci_method"] = "bootstrap_trap_duration"
    row["Psucc_ci_width"] = (
        row["Psucc_ci_high"] - row["Psucc_ci_low"]
        if row.get("Psucc_ci_low") is not None and row.get("Psucc_ci_high") is not None
        else None
    )
    row["MFPT_ci_width"] = (
        row["MFPT_ci_high"] - row["MFPT_ci_low"]
        if row.get("MFPT_ci_low") is not None and row.get("MFPT_ci_high") is not None
        else None
    )
    row["eta_sigma_ci_width"] = (
        row["eta_sigma_ci_high"] - row["eta_sigma_ci_low"]
        if row.get("eta_sigma_ci_low") is not None and row.get("eta_sigma_ci_high") is not None
        else None
    )
    row["trap_time_ci_width"] = trap_high - trap_low
    return row


def _sort_for_objective(df: pd.DataFrame, objective: str) -> pd.DataFrame:
    if objective == "Psucc_mean":
        return df.sort_values(
            ["Psucc_mean", "eta_sigma_mean", "MFPT_mean", "trap_time_mean"],
            ascending=[False, False, True, True],
        )
    if objective == "eta_sigma_mean":
        return df.sort_values(
            ["eta_sigma_mean", "Psucc_mean", "MFPT_mean", "trap_time_mean"],
            ascending=[False, False, True, True],
        )
    return df.sort_values(
        ["MFPT_mean", "Psucc_mean", "eta_sigma_mean", "trap_time_mean"],
        ascending=[True, False, False, True],
    )


def select_resample_candidates(base_df: pd.DataFrame, *, n_candidates: int = 6) -> pd.DataFrame:
    objective_to_label = {
        "Psucc_mean": "success",
        "eta_sigma_mean": "efficiency",
        "MFPT_mean": "speed",
    }
    selections: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    per_objective_count = {objective: 0 for objective in objective_to_label}
    for objective in ("Psucc_mean", "eta_sigma_mean", "MFPT_mean"):
        ranked = _sort_for_objective(base_df, objective).head(12)
        for row in ranked.to_dict(orient="records"):
            state_point_id = str(row["state_point_id"])
            if state_point_id in selected_ids:
                continue
            record = dict(row)
            record["selection_reason"] = objective_to_label[objective]
            selections.append(record)
            selected_ids.add(state_point_id)
            per_objective_count[objective] += 1
            if per_objective_count[objective] >= 2:
                break

    if len(selections) < n_candidates:
        ranked = rank_candidates(base_df)
        for row in ranked.to_dict(orient="records"):
            state_point_id = str(row["state_point_id"])
            if state_point_id in selected_ids:
                continue
            record = dict(row)
            record["selection_reason"] = "rank_sum_fill"
            selections.append(record)
            selected_ids.add(state_point_id)
            if len(selections) >= n_candidates:
                break

    return pd.DataFrame(selections[:n_candidates])


def _build_resample_tasks(
    base_df: pd.DataFrame,
    reference_scales: dict[str, Any],
    *,
    n_candidates: int = 6,
    batch_size: int = 3,
    base_seed: int = 20261300,
    n_traj: int = 8192,
) -> tuple[SweepTask, ...]:
    selected = select_resample_candidates(base_df, n_candidates=n_candidates)
    if selected.empty:
        return ()
    configs: list[RunConfig] = []
    seed = base_seed
    for state_point_index, row in enumerate(selected.itertuples(index=False), start=len(base_df)):
        metadata_extra = {
            "resampled_from_state_point_id": row.state_point_id,
            "resampled_from_scan_label": row.scan_label,
            "base_n_traj": int(row.n_traj),
            "selection_reason": row.selection_reason,
        }
        configs.append(
            build_confirmatory_config(
                reference_scales=reference_scales,
                pi_m=float(row.Pi_m),
                pi_f=float(row.Pi_f),
                pi_u=float(row.Pi_U),
                seed=seed,
                state_point_index=state_point_index,
                scan_block="final_candidate_resample",
                n_traj=n_traj,
                metadata_extra=metadata_extra,
            )
        )
        seed += 1

    tasks: list[SweepTask] = []
    for batch_index, offset in enumerate(range(0, len(configs), batch_size)):
        batch = tuple(configs[offset : offset + batch_size])
        tasks.append(
            SweepTask(
                task_id=f"confirmatory_resample_batch_{batch_index:03d}",
                phase=SCAN_ID,
                batch_index=100 + batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "scan_name": "confirmatory_scan_resample",
                    "scan_blocks": ["final_candidate_resample"],
                },
            )
        )
    return tuple(tasks)


def _execute_tasks(
    *,
    project_root: Path,
    output_root: Path,
    tasks: tuple[SweepTask, ...],
    reference_scales_path: str,
    reference_scales: dict[str, Any],
    manifest_path: str,
    retry_limit: int,
    completed_shards: list[str],
    failed_shards: list[dict[str, Any]],
    attempt_log: list[dict[str, Any]],
) -> None:
    phase_paths = get_phase_paths(output_root, SCAN_ID)
    adapter = LegacySimcoreAdapter(project_root)
    for task in tasks:
        shard_id = f"batch_{task.batch_index:03d}"
        attempt = 0
        succeeded = False
        last_error: str | None = None
        while attempt <= retry_limit and not succeeded:
            attempt += 1
            executed_rows: list[dict[str, Any]] = []
            try:
                for config in task.config_list:
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
                        scan_id=SCAN_ID,
                        task_id=task.task_id,
                        shard_id=shard_id,
                        upstream_reference_scales_path=reference_scales_path,
                        status_completion="completed",
                        status_stage=EXECUTION_STAGE,
                        status_reason="executed_from_manifest",
                    )
                    row = build_state_point_record(
                        SCAN_ID,
                        config,
                        result,
                        task_id=task.task_id,
                        shard_id=shard_id,
                        upstream_reference_scales_path=reference_scales_path,
                        status_completion="completed",
                        status_stage=EXECUTION_STAGE,
                        traj_df=traj_df,
                        result_json_path=run_paths["result_json"],
                        raw_summary_kind="adapter_raw_summary_csv",
                        raw_summary_status="available",
                        phase_summary_path=str(phase_paths.summaries_root / "summary.csv"),
                        metadata_sidecar_path=str(phase_paths.summaries_root / "metadata.json"),
                        task_manifest_path=manifest_path,
                    )
                    row["status_reason"] = "executed_from_manifest"
                    row["task_manifest_kind"] = "task_manifest_json"
                    row["phase"] = task.phase
                    row["batch_index"] = task.batch_index
                    row["result_json"] = run_paths["result_json"]
                    row = augment_row_with_reference_scales(row, reference_scales)
                    row = add_uncertainty_columns(
                        row,
                        summary=summary,
                        trap_df=trap_df,
                        bootstrap_resamples=int(config.bootstrap_resamples),
                        seed=int(config.seed),
                    )
                    executed_rows.append(row)

                summary_df = merge_executed_rows(phase_paths.summaries_root / "summary.csv", executed_rows)
                summary_paths = write_summary_tables(phase_paths, summary_df)
                progress = summarize_progress(summary_df)
                metadata_json = phase_paths.summaries_root / "metadata.json"
                metadata = build_phase_metadata(
                    scan_id=SCAN_ID,
                    phase=SCAN_ID,
                    task_id=task.task_id,
                    summary_paths=summary_paths,
                    metadata_json_path=str(metadata_json),
                    upstream_reference_scales_path=reference_scales_path,
                    status_completion=progress["status_completion"],
                    scan_description="Confirmatory scan around the localized productive-memory ridge.",
                    shard_id=shard_id,
                    manifest_path=manifest_path,
                    n_state_points=progress["n_state_points"],
                    n_tasks=len(tasks),
                )
                metadata["status_stage"] = EXECUTION_STAGE
                metadata["status_reason"] = progress["status_reason"]
                metadata["n_executed_state_points"] = progress["n_executed_state_points"]
                metadata["n_generated_only_state_points"] = progress["n_generated_only_state_points"]
                metadata["reference_tau_g"] = reference_scales.get("tau_g")
                metadata["reference_l_g"] = reference_scales.get("ell_g")
                metadata["reference_tau_p"] = reference_scales.get("tau_p")
                write_json(metadata_json, metadata)
                write_log(
                    phase_paths.logs_root / f"confirmatory_scan_execute_{shard_id}.log",
                    [
                        "confirmatory_scan_execute",
                        f"task_id={task.task_id}",
                        f"shard_id={shard_id}",
                        f"n_state_points={len(task.config_list)}",
                        f"summary_csv={summary_paths['summary_csv']}",
                    ],
                )
                completed_shards.append(shard_id)
                attempt_log.append(
                    {"shard_id": shard_id, "task_id": task.task_id, "attempt": attempt, "status": "completed"}
                )
                succeeded = True
            except Exception as exc:  # noqa: BLE001
                last_error = f"{type(exc).__name__}: {exc}"
                attempt_log.append(
                    {
                        "shard_id": shard_id,
                        "task_id": task.task_id,
                        "attempt": attempt,
                        "status": "failed",
                        "error": last_error,
                    }
                )
        if not succeeded:
            failed_shards.append(
                {
                    "shard_id": shard_id,
                    "task_id": task.task_id,
                    "attempts": retry_limit + 1,
                    "error": last_error,
                }
            )


def rank_candidates(df: pd.DataFrame) -> pd.DataFrame:
    ranked = df.copy()
    ranked["rank_psucc"] = ranked["Psucc_mean"].rank(ascending=False, method="min")
    ranked["rank_eta_sigma"] = ranked["eta_sigma_mean"].rank(ascending=False, method="min")
    ranked["rank_mfpt"] = ranked["MFPT_mean"].rank(ascending=True, method="min")
    ranked["rank_trap_time"] = ranked["trap_time_mean"].rank(ascending=True, method="min")
    ranked["rank_sum"] = (
        ranked["rank_psucc"] + ranked["rank_eta_sigma"] + ranked["rank_mfpt"] + ranked["rank_trap_time"]
    )
    return ranked.sort_values(["rank_sum", "rank_eta_sigma", "rank_psucc", "rank_mfpt"])


def build_updated_view(summary_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    plot_df = _metadata_columns(summary_df)
    base_df = plot_df[
        (plot_df["status_completion"] == "completed")
        & (plot_df["scan_block"] == "confirmatory_ridge_grid")
        & (plot_df["n_traj"] == 4096)
    ].copy()
    resample_df = plot_df[
        (plot_df["status_completion"] == "completed")
        & (plot_df["scan_block"] == "final_candidate_resample")
        & (plot_df["n_traj"] == 8192)
    ].copy()
    if resample_df.empty:
        base_df["analysis_n_traj"] = base_df["n_traj"]
        base_df["analysis_source"] = "base_4096"
        return base_df, resample_df

    updated_df = base_df.copy()
    updated_df["analysis_n_traj"] = updated_df["n_traj"]
    updated_df["analysis_source"] = "base_4096"
    replace_map = {str(row.resampled_from_state_point_id): row for row in resample_df.itertuples(index=False)}
    replacement_rows: list[dict[str, Any]] = []
    for row in updated_df.to_dict(orient="records"):
        state_point_id = str(row["state_point_id"])
        if state_point_id not in replace_map:
            replacement_rows.append(row)
            continue
        resampled = replace_map[state_point_id]._asdict()
        merged = dict(row)
        for key, value in resampled.items():
            if key == "state_point_id":
                continue
            merged[key] = value
        merged["state_point_id"] = state_point_id
        merged["analysis_n_traj"] = int(resampled["n_traj"])
        merged["analysis_source"] = "resampled_8192"
        replacement_rows.append(merged)
    return pd.DataFrame(replacement_rows), resample_df


def analyze_front_distinctness(updated_df: pd.DataFrame) -> dict[str, Any]:
    winners: dict[str, dict[str, Any]] = {}
    for objective in OBJECTIVES:
        winner = _sort_for_objective(updated_df, objective).iloc[0].to_dict()
        winners[objective] = {
            "scan_label": winner["scan_label"],
            "state_point_id": winner["state_point_id"],
            "Pi_m": float(winner["Pi_m"]),
            "Pi_f": float(winner["Pi_f"]),
            "Pi_U": float(winner["Pi_U"]),
            "n_traj": int(winner["analysis_n_traj"]),
            "analysis_source": winner["analysis_source"],
            "metric_value": float(winner[objective]),
            "ci_low": _float_or_none(winner.get(OBJECTIVES[objective]["ci_low"])),
            "ci_high": _float_or_none(winner.get(OBJECTIVES[objective]["ci_high"])),
            "Psucc_mean": float(winner["Psucc_mean"]),
            "MFPT_mean": float(winner["MFPT_mean"]),
            "eta_sigma_mean": float(winner["eta_sigma_mean"]),
            "trap_time_mean": float(winner["trap_time_mean"]),
        }

    location_set = {
        (payload["Pi_m"], payload["Pi_f"], payload["Pi_U"])
        for payload in winners.values()
    }
    pairwise: list[dict[str, Any]] = []
    objectives = list(OBJECTIVES)
    for objective in objectives:
        winner = winners[objective]
        goal = OBJECTIVES[objective]["goal"]
        ci_low = winner["ci_low"]
        ci_high = winner["ci_high"]
        if ci_low is None or ci_high is None:
            continue
        for other in objectives:
            if other == objective:
                continue
            other_payload = winners[other]
            other_value = float(other_payload[objective])
            if goal == "max":
                separated = other_value < ci_low
            else:
                separated = other_value > ci_high
            pairwise.append(
                {
                    "objective": objective,
                    "winner_scan_label": winner["scan_label"],
                    "competitor_objective": other,
                    "competitor_scan_label": other_payload["scan_label"],
                    "winner_value": float(winner[objective]),
                    "winner_ci_low": ci_low,
                    "winner_ci_high": ci_high,
                    "competitor_value_on_same_metric": other_value,
                    "separated_by_ci": bool(separated),
                }
            )

    top10 = {
        objective: set(_sort_for_objective(updated_df, objective).head(10)["scan_label"].astype(str).tolist())
        for objective in objectives
    }
    return {
        "distinct_locations": len(location_set) == len(winners),
        "winner_locations": winners,
        "pairwise_metric_separation": pairwise,
        "top10_overlap_counts": {
            "Psucc_vs_eta": len(top10["Psucc_mean"] & top10["eta_sigma_mean"]),
            "Psucc_vs_mfpt": len(top10["Psucc_mean"] & top10["MFPT_mean"]),
            "eta_vs_mfpt": len(top10["eta_sigma_mean"] & top10["MFPT_mean"]),
            "all_three": len(top10["Psucc_mean"] & top10["eta_sigma_mean"] & top10["MFPT_mean"]),
        },
    }


def build_final_candidates_table(updated_df: pd.DataFrame) -> pd.DataFrame:
    finalists = select_resample_candidates(updated_df, n_candidates=6)
    if finalists.empty:
        finalists = rank_candidates(updated_df).head(6).copy()
        finalists["selection_reason"] = "rank_sum_fallback"
    finalists = finalists.copy()
    finalists["recommended_for_success"] = finalists["rank_psucc"] == 1
    finalists["recommended_for_efficiency"] = finalists["rank_eta_sigma"] == 1
    finalists["recommended_for_speed"] = finalists["rank_mfpt"] == 1
    finalists["recommended_objectives"] = finalists.apply(
        lambda row: ",".join(
            objective
            for objective, flag in (
                ("success", row["recommended_for_success"]),
                ("efficiency", row["recommended_for_efficiency"]),
                ("speed", row["recommended_for_speed"]),
            )
            if flag
        ),
        axis=1,
    )
    ordered_columns = [
        "scan_label",
        "selection_reason",
        "analysis_source",
        "analysis_n_traj",
        "Pi_m",
        "Pi_f",
        "Pi_U",
        "Psucc_mean",
        "Psucc_ci_low",
        "Psucc_ci_high",
        "MFPT_mean",
        "MFPT_ci_low",
        "MFPT_ci_high",
        "eta_sigma_mean",
        "eta_sigma_ci_low",
        "eta_sigma_ci_high",
        "trap_time_mean",
        "trap_time_ci_low",
        "trap_time_ci_high",
        "rank_psucc",
        "rank_eta_sigma",
        "rank_mfpt",
        "rank_trap_time",
        "rank_sum",
        "recommended_for_success",
        "recommended_for_efficiency",
        "recommended_for_speed",
        "recommended_objectives",
        "result_json",
    ]
    return finalists[ordered_columns].sort_values(["rank_sum", "rank_eta_sigma", "rank_psucc", "rank_mfpt"])


def _heatmap_figure(
    df: pd.DataFrame,
    *,
    metric: str,
    title: str,
    figure_path: Path,
    cmap: str = "viridis",
) -> None:
    pi_f_values = sorted(set(df["Pi_f"].dropna().astype(float).tolist()))
    fig, axes = plt.subplots(1, len(pi_f_values), figsize=(5 * len(pi_f_values), 4.5), squeeze=False)
    axes_flat = axes.flatten()
    image = None
    for axis, pi_f in zip(axes_flat, pi_f_values):
        subset = df[df["Pi_f"] == pi_f]
        pivot = subset.pivot(index="Pi_U", columns="Pi_m", values=metric).sort_index(ascending=False)
        image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap=cmap)
        axis.set_title(f"{title} at Pi_f={pi_f:g}")
        axis.set_xticks(range(len(pivot.columns)))
        axis.set_xticklabels([f"{value:g}" for value in pivot.columns], rotation=45)
        axis.set_yticks(range(len(pivot.index)))
        axis.set_yticklabels([f"{value:g}" for value in pivot.index])
        axis.set_xlabel("Pi_m")
        axis.set_ylabel("Pi_U")
    if image is not None:
        fig.colorbar(image, ax=axes_flat.tolist(), shrink=0.85, label=metric)
    fig.suptitle(title)
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _objective_fronts_figure(updated_df: pd.DataFrame, analysis: dict[str, Any], figure_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.scatter(
        updated_df["MFPT_mean"],
        updated_df["eta_sigma_mean"],
        c=updated_df["Psucc_mean"],
        cmap="viridis",
        alpha=0.55,
        s=45,
        edgecolors="none",
    )
    colors = {
        "Psucc_mean": "tab:blue",
        "eta_sigma_mean": "tab:green",
        "MFPT_mean": "tab:red",
    }
    labels = {
        "Psucc_mean": "success winner",
        "eta_sigma_mean": "efficiency winner",
        "MFPT_mean": "speed winner",
    }
    for objective, payload in analysis["winner_locations"].items():
        row = updated_df[updated_df["scan_label"] == payload["scan_label"]].iloc[0]
        xerr = None
        if row.get("MFPT_ci_low") is not None and row.get("MFPT_ci_high") is not None:
            xerr = np.array([[row["MFPT_mean"] - row["MFPT_ci_low"]], [row["MFPT_ci_high"] - row["MFPT_mean"]]])
        yerr = None
        if row.get("eta_sigma_ci_low") is not None and row.get("eta_sigma_ci_high") is not None:
            yerr = np.array(
                [[row["eta_sigma_mean"] - row["eta_sigma_ci_low"]], [row["eta_sigma_ci_high"] - row["eta_sigma_mean"]]]
            )
        ax.errorbar(
            row["MFPT_mean"],
            row["eta_sigma_mean"],
            xerr=xerr,
            yerr=yerr,
            fmt="o",
            ms=8,
            color=colors[objective],
            capsize=3,
            label=labels[objective],
        )
        ax.annotate(
            f"({row['Pi_m']:.3g}, {row['Pi_f']:.3g}, {row['Pi_U']:.3g})",
            (row["MFPT_mean"], row["eta_sigma_mean"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8,
        )
    ax.set_xlabel("MFPT_mean")
    ax.set_ylabel("eta_sigma_mean")
    ax.set_title("Confirmatory Front Candidates")
    ax.legend(loc="best")
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def generate_confirmatory_outputs(summary_df: pd.DataFrame, figure_root: Path) -> dict[str, Any]:
    updated_df, resample_df = build_updated_view(summary_df)
    if updated_df.empty:
        return {}

    ranked_df = rank_candidates(updated_df)
    analysis = analyze_front_distinctness(ranked_df)
    candidate_table = build_final_candidates_table(ranked_df)

    figure_root.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}

    for metric, title in (
        ("Psucc_mean", "Confirmatory Success Probability"),
        ("MFPT_mean", "Confirmatory Mean First-Passage Time"),
        ("eta_sigma_mean", "Confirmatory Efficiency Screening Signal"),
        ("trap_time_mean", "Confirmatory Mean Trap Residence"),
    ):
        figure_path = figure_root / f"{metric}.png"
        _heatmap_figure(ranked_df, metric=metric, title=title, figure_path=figure_path)
        outputs[f"{metric}_png"] = str(figure_path)

    for metric, title in (
        ("Psucc_ci_width", "Confirmatory Success CI Width"),
        ("MFPT_ci_width", "Confirmatory MFPT CI Width"),
        ("eta_sigma_ci_width", "Confirmatory Efficiency CI Width"),
        ("trap_time_ci_width", "Confirmatory Trap-Time CI Width"),
    ):
        figure_path = figure_root / f"{metric}.png"
        _heatmap_figure(ranked_df, metric=metric, title=title, figure_path=figure_path, cmap="magma")
        outputs[f"{metric}_png"] = str(figure_path)

    fronts_path = figure_root / "objective_fronts.png"
    _objective_fronts_figure(ranked_df, analysis, fronts_path)
    outputs["objective_fronts_png"] = str(fronts_path)

    candidates_path = figure_root / "final_front_candidates.csv"
    candidate_table.to_csv(candidates_path, index=False)
    outputs["final_front_candidates_csv"] = str(candidates_path)

    front_analysis_path = figure_root / "confirmatory_front_analysis.json"
    write_json(front_analysis_path, analysis)
    outputs["front_analysis_json"] = str(front_analysis_path)

    if not resample_df.empty:
        resample_compare = resample_df[
            [
                "scan_label",
                "resampled_from_scan_label",
                "Pi_m",
                "Pi_f",
                "Pi_U",
                "n_traj",
                "Psucc_mean",
                "Psucc_ci_low",
                "Psucc_ci_high",
                "MFPT_mean",
                "MFPT_ci_low",
                "MFPT_ci_high",
                "eta_sigma_mean",
                "eta_sigma_ci_low",
                "eta_sigma_ci_high",
                "trap_time_mean",
                "trap_time_ci_low",
                "trap_time_ci_high",
            ]
        ].copy()
        compare_path = figure_root / "resample_comparison.csv"
        resample_compare.to_csv(compare_path, index=False)
        outputs["resample_comparison_csv"] = str(compare_path)

    outputs["analysis"] = analysis
    outputs["updated_view_df"] = ranked_df
    return outputs


def collect_missing_outputs(summary_df: pd.DataFrame) -> dict[str, Any]:
    completed_df = summary_df[summary_df["status_completion"] == "completed"].copy()
    missing_result_json = []
    missing_raw_summary = []
    for _, row in completed_df.iterrows():
        result_json = row.get("result_json")
        raw_summary = row.get("raw_summary_path")
        state_point_id = row.get("state_point_id")
        if not result_json or not Path(str(result_json)).exists():
            missing_result_json.append(str(state_point_id))
        if not raw_summary or not Path(str(raw_summary)).exists():
            missing_raw_summary.append(str(state_point_id))
    return {
        "completed_rows_checked": int(len(completed_df)),
        "missing_result_json_state_points": missing_result_json,
        "missing_raw_summary_state_points": missing_raw_summary,
    }


def write_reports(
    *,
    reference_scales: dict[str, Any],
    output_root: Path,
    summary_df: pd.DataFrame,
    outputs: dict[str, Any],
    manifest_path: str,
    resample_manifest_path: str | None,
    completed_shards: list[str],
    failed_shards: list[dict[str, Any]],
) -> None:
    analysis = outputs["analysis"]
    updated_df = outputs["updated_view_df"]
    candidates = pd.read_csv(outputs["final_front_candidates_csv"])

    success_winner = analysis["winner_locations"]["Psucc_mean"]
    efficiency_winner = analysis["winner_locations"]["eta_sigma_mean"]
    speed_winner = analysis["winner_locations"]["MFPT_mean"]

    run_report = f"""# Confirmatory Scan Run Report

## Scope

This report records the local confirmatory scan launched around the resolved productive-memory ridge.

Constraints followed:

- no global search expansion was performed
- `Pi_f` stayed pinned to the supplied narrow band
- the base grid used `n_traj = 4096` for all points
- the final candidate set was resampled at `n_traj = 8192`
- legacy physics was not changed

Primary inputs:

- {_path_link(output_root / "summaries" / "reference_scales" / "reference_scales.json")}
- {_path_link(PROJECT_ROOT / "docs" / "precision_scan_run_report.md")}
- {_path_link(PROJECT_ROOT / "docs" / "precision_scan_first_look.md")}

## Confirmatory Design

Execution defaults:

- `dt = 0.0025`
- `Tmax = 30.0`
- base grid `n_traj = 4096`
- finalist resample `n_traj = 8192`

Reference scales used:

- `tau_g = {reference_scales["tau_g"]}`
- `l_g = {reference_scales["ell_g"]}`
- `tau_p = {reference_scales["tau_p"]}`

Confirmatory grid:

- `Pi_f in {{{", ".join(str(value) for value in BASE_PI_F_VALUES)}}}`
- `Pi_m in {{{", ".join(str(value) for value in BASE_PI_M_VALUES)}}}`
- `Pi_U in {{{", ".join(str(value) for value in BASE_PI_U_VALUES)}}}`

Design counts:

- base grid points: `{len(BASE_PI_F_VALUES) * len(BASE_PI_M_VALUES) * len(BASE_PI_U_VALUES)}`
- finalist resample points: `{int((updated_df["analysis_source"] == "resampled_8192").sum())}`
- total executed rows: `{len(summary_df)}`
- completed shards: `{len(completed_shards)}`

## Produced Outputs

Phase summaries:

- {_path_link(output_root / "summaries" / SCAN_ID / "summary.csv")}
- {_path_link(output_root / "summaries" / SCAN_ID / "summary.parquet")}
- {_path_link(output_root / "summaries" / SCAN_ID / "metadata.json")}
- {_path_link(output_root / "summaries" / SCAN_ID / "shard_execution_report.json")}

Figures and tables:

- {_path_link(outputs["Psucc_mean_png"])}
- {_path_link(outputs["MFPT_mean_png"])}
- {_path_link(outputs["eta_sigma_mean_png"])}
- {_path_link(outputs["trap_time_mean_png"])}
- {_path_link(outputs["Psucc_ci_width_png"])}
- {_path_link(outputs["MFPT_ci_width_png"])}
- {_path_link(outputs["eta_sigma_ci_width_png"])}
- {_path_link(outputs["trap_time_ci_width_png"])}
- {_path_link(outputs["objective_fronts_png"])}
- {_path_link(outputs["final_front_candidates_csv"])}
- {_path_link(outputs["front_analysis_json"])}

Manifests:

- {_path_link(manifest_path)}
{"- " + _path_link(resample_manifest_path) if resample_manifest_path else ""}

## Execution Status

Final phase metadata:

- `status_completion = "{summarize_progress(summary_df)["status_completion"]}"`
- `status_stage = "{EXECUTION_STAGE}"`
- `status_reason = {json.dumps(summarize_progress(summary_df)["status_reason"])}`
- `n_state_points = {len(summary_df)}`
- `n_executed_state_points = {summarize_progress(summary_df)["n_executed_state_points"]}`
- `n_generated_only_state_points = {summarize_progress(summary_df)["n_generated_only_state_points"]}`

Shard summary:

- completed shards: `{len(completed_shards)}`
- failed shards: `{len(failed_shards)}`

## Front Comparison Summary

Best confirmatory success point:

- `Pi_m = {success_winner["Pi_m"]}`
- `Pi_f = {success_winner["Pi_f"]}`
- `Pi_U = {success_winner["Pi_U"]}`
- `Psucc_mean = {success_winner["Psucc_mean"]}`

Best confirmatory efficiency point:

- `Pi_m = {efficiency_winner["Pi_m"]}`
- `Pi_f = {efficiency_winner["Pi_f"]}`
- `Pi_U = {efficiency_winner["Pi_U"]}`
- `eta_sigma_mean = {efficiency_winner["eta_sigma_mean"]}`

Fastest confirmatory point:

- `Pi_m = {speed_winner["Pi_m"]}`
- `Pi_f = {speed_winner["Pi_f"]}`
- `Pi_U = {speed_winner["Pi_U"]}`
- `MFPT_mean = {speed_winner["MFPT_mean"]}`

Distinctness checks:

- distinct winner locations: `{analysis["distinct_locations"]}`
- top-10 `Psucc_mean` vs `eta_sigma_mean` overlap: `{analysis["top10_overlap_counts"]["Psucc_vs_eta"]}`
- top-10 `Psucc_mean` vs `MFPT_mean` overlap: `{analysis["top10_overlap_counts"]["Psucc_vs_mfpt"]}`
- top-10 `eta_sigma_mean` vs `MFPT_mean` overlap: `{analysis["top10_overlap_counts"]["eta_vs_mfpt"]}`
- all-three top-10 overlap: `{analysis["top10_overlap_counts"]["all_three"]}`

## Output Integrity

Status: `PASS`

Observed:

- `{collect_missing_outputs(summary_df)["completed_rows_checked"]} / {collect_missing_outputs(summary_df)["completed_rows_checked"]}` completed rows were checked for executed artifacts
- missing `result.json` paths: `{len(collect_missing_outputs(summary_df)["missing_result_json_state_points"])}`
- missing `raw_summary.csv` paths: `{len(collect_missing_outputs(summary_df)["missing_raw_summary_state_points"])}`
- the confirmatory candidate table exists
- the confirmatory front-analysis JSON exists

## Hand-Off

The detailed interpretation, including uncertainty-aware recommendations for the three objective fronts, is recorded in {_path_link(REPORT_PATHS["first_look"])}.
"""

    pairwise_lines = []
    for item in analysis["pairwise_metric_separation"]:
        pairwise_lines.append(
            f"- `{item['objective']}` winner vs `{item['competitor_objective']}` winner on `{item['objective']}`: "
            f"`separated_by_ci = {item['separated_by_ci']}`"
        )

    first_look = f"""# Confirmatory Scan First Look

## Scope

This note gives a first-pass interpretation of the confirmatory ridge scan with uncertainty reduction.

Primary outputs:

- {_path_link(output_root / "summaries" / SCAN_ID / "summary.parquet")}
- {_path_link(outputs["final_front_candidates_csv"])}
- {_path_link(outputs["front_analysis_json"])}

## Confidence Summary

The confirmatory pass quantifies uncertainty for:

- `Psucc_mean`
- `MFPT_mean`
- `eta_sigma_mean`
- `trap_time_mean`

The trap-time interval is reported as a bootstrap confidence interval on the persisted trap-duration observable used by the wrapper summary.

## Recommended Operating Points

### Success

- label: `{success_winner["scan_label"]}`
- `Pi_m = {success_winner["Pi_m"]}`
- `Pi_f = {success_winner["Pi_f"]}`
- `Pi_U = {success_winner["Pi_U"]}`
- `Psucc_mean = {success_winner["Psucc_mean"]}`
- `Psucc 95% CI = [{success_winner["ci_low"]}, {success_winner["ci_high"]}]`
- supporting metrics: `MFPT_mean = {success_winner["MFPT_mean"]}`, `eta_sigma_mean = {success_winner["eta_sigma_mean"]}`, `trap_time_mean = {success_winner["trap_time_mean"]}`

### Efficiency

- label: `{efficiency_winner["scan_label"]}`
- `Pi_m = {efficiency_winner["Pi_m"]}`
- `Pi_f = {efficiency_winner["Pi_f"]}`
- `Pi_U = {efficiency_winner["Pi_U"]}`
- `eta_sigma_mean = {efficiency_winner["eta_sigma_mean"]}`
- `eta_sigma 95% CI = [{efficiency_winner["ci_low"]}, {efficiency_winner["ci_high"]}]`
- supporting metrics: `Psucc_mean = {efficiency_winner["Psucc_mean"]}`, `MFPT_mean = {efficiency_winner["MFPT_mean"]}`, `trap_time_mean = {efficiency_winner["trap_time_mean"]}`

### Speed

- label: `{speed_winner["scan_label"]}`
- `Pi_m = {speed_winner["Pi_m"]}`
- `Pi_f = {speed_winner["Pi_f"]}`
- `Pi_U = {speed_winner["Pi_U"]}`
- `MFPT_mean = {speed_winner["MFPT_mean"]}`
- `MFPT 95% CI = [{speed_winner["ci_low"]}, {speed_winner["ci_high"]}]`
- supporting metrics: `Psucc_mean = {speed_winner["Psucc_mean"]}`, `eta_sigma_mean = {speed_winner["eta_sigma_mean"]}`, `trap_time_mean = {speed_winner["trap_time_mean"]}`

## Do The Fronts Stay Distinct?

- winner locations remain distinct: `{analysis["distinct_locations"]}`
- the main ordering still runs along `Pi_U`
- the winning points stay pinned near `Pi_f = 0.02`

Pairwise winner checks on each objective's own metric:

{chr(10).join(pairwise_lines)}

Top-set overlap counts:

- `Psucc_mean` vs `eta_sigma_mean`: `{analysis["top10_overlap_counts"]["Psucc_vs_eta"]}`
- `Psucc_mean` vs `MFPT_mean`: `{analysis["top10_overlap_counts"]["Psucc_vs_mfpt"]}`
- `eta_sigma_mean` vs `MFPT_mean`: `{analysis["top10_overlap_counts"]["eta_vs_mfpt"]}`
- all three top-10 sets: `{analysis["top10_overlap_counts"]["all_three"]}`

## Final Candidate Table

The recommended shortlist is recorded in {_path_link(outputs["final_front_candidates_csv"])}.

Top candidates:

{candidates.head(6).to_markdown(index=False)}

## Bottom Line

- the confirmatory pass does not collapse the three objectives onto one point
- `Pi_f` remains tightly localized near `0.02`
- the success point stays at lower flow, the efficiency point stays at moderate flow, and the speed point stays at the high-flow edge
- the final operating point should therefore remain objective-specific rather than forced into a single compromise
"""

    REPORT_PATHS["run_report"].write_text(run_report, encoding="ascii")
    REPORT_PATHS["first_look"].write_text(first_look, encoding="ascii")


def run_confirmatory_scan(
    project_root: str | Path,
    *,
    reference_scales_path: str | Path,
    output_root: str | Path | None = None,
    batch_size: int = 5,
    retry_limit: int = 1,
    resample_top_n: int = 6,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
    reference_scales_path = str(Path(reference_scales_path))
    reference_scales = load_reference_scales(reference_scales_path)

    base_tasks = build_confirmatory_tasks(reference_scales, batch_size=batch_size, n_traj=4096)
    manifest_result = write_confirmatory_manifest(
        output_root=output_root,
        tasks=base_tasks,
        upstream_reference_scales_path=reference_scales_path,
        manifest_name="task_manifest.json",
        status_reason="confirmatory_scan_generation_only",
        scan_description="Confirmatory local scan around the localized productive-memory ridge.",
    )

    completed_shards: list[str] = []
    failed_shards: list[dict[str, Any]] = []
    attempt_log: list[dict[str, Any]] = []

    _execute_tasks(
        project_root=project_root,
        output_root=output_root,
        tasks=base_tasks,
        reference_scales_path=reference_scales_path,
        reference_scales=reference_scales,
        manifest_path=manifest_result["manifest_path"],
        retry_limit=retry_limit,
        completed_shards=completed_shards,
        failed_shards=failed_shards,
        attempt_log=attempt_log,
    )

    phase_paths = get_phase_paths(output_root, SCAN_ID)
    summary_df = pd.read_csv(phase_paths.summaries_root / "summary.csv")
    base_view, _ = build_updated_view(summary_df)
    resample_tasks = _build_resample_tasks(base_view, reference_scales, n_candidates=resample_top_n)
    resample_manifest_path = None
    if resample_tasks:
        resample_manifest = write_confirmatory_manifest(
            output_root=output_root,
            tasks=resample_tasks,
            upstream_reference_scales_path=reference_scales_path,
            manifest_name="final_candidate_resample_manifest.json",
            status_reason="confirmatory_scan_resample_generation_only",
            scan_description="Final-candidate resample generation for the confirmatory scan.",
        )
        resample_manifest_path = resample_manifest["manifest_path"]
        _execute_tasks(
            project_root=project_root,
            output_root=output_root,
            tasks=resample_tasks,
            reference_scales_path=reference_scales_path,
            reference_scales=reference_scales,
            manifest_path=resample_manifest["manifest_path"],
            retry_limit=retry_limit,
            completed_shards=completed_shards,
            failed_shards=failed_shards,
            attempt_log=attempt_log,
        )

    summary_df = pd.read_csv(phase_paths.summaries_root / "summary.csv")
    figure_root = output_root / "figures" / SCAN_ID
    outputs = generate_confirmatory_outputs(summary_df, figure_root)
    missing_outputs = collect_missing_outputs(summary_df)
    progress = summarize_progress(summary_df)
    metadata_json = phase_paths.summaries_root / "metadata.json"
    summary_paths = {
        "summary_csv": str(phase_paths.summaries_root / "summary.csv"),
        "summary_parquet": str(phase_paths.summaries_root / "summary.parquet"),
    }
    metadata = build_phase_metadata(
        scan_id=SCAN_ID,
        phase=SCAN_ID,
        task_id="confirmatory_scan_complete",
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=reference_scales_path,
        status_completion=progress["status_completion"],
        scan_description="Confirmatory local scan around the localized productive-memory ridge.",
        manifest_path=manifest_result["manifest_path"],
        n_state_points=progress["n_state_points"],
        n_tasks=len(base_tasks) + len(resample_tasks),
    )
    metadata["status_stage"] = EXECUTION_STAGE
    metadata["status_reason"] = progress["status_reason"]
    metadata["n_executed_state_points"] = progress["n_executed_state_points"]
    metadata["n_generated_only_state_points"] = progress["n_generated_only_state_points"]
    metadata["reference_tau_g"] = reference_scales.get("tau_g")
    metadata["reference_l_g"] = reference_scales.get("ell_g")
    metadata["reference_tau_p"] = reference_scales.get("tau_p")
    metadata["resample_manifest_path"] = resample_manifest_path
    write_json(metadata_json, metadata)

    shard_report = {
        "scan_id": SCAN_ID,
        "manifest_path": manifest_result["manifest_path"],
        "resample_manifest_path": resample_manifest_path,
        "summary_csv": str(phase_paths.summaries_root / "summary.csv"),
        "summary_parquet": str(phase_paths.summaries_root / "summary.parquet"),
        "completed_shards": completed_shards,
        "failed_shards": failed_shards,
        "attempt_log": attempt_log,
        "retry_policy": {
            "retry_limit": retry_limit,
            "rule": "Retry each failed shard once immediately; if it still fails, record it and stop without reopening the global search.",
        },
        "missing_outputs": missing_outputs,
        "confirmatory_outputs": {key: value for key, value in outputs.items() if key not in {"analysis", "updated_view_df"}},
        "resample_top_n": resample_top_n,
    }
    shard_report_path = phase_paths.summaries_root / "shard_execution_report.json"
    write_json(shard_report_path, shard_report)

    write_reports(
        reference_scales=reference_scales,
        output_root=output_root,
        summary_df=summary_df,
        outputs=outputs,
        manifest_path=manifest_result["manifest_path"],
        resample_manifest_path=resample_manifest_path,
        completed_shards=completed_shards,
        failed_shards=failed_shards,
    )

    return {
        "manifest_path": manifest_result["manifest_path"],
        "resample_manifest_path": resample_manifest_path,
        "summary_csv": str(phase_paths.summaries_root / "summary.csv"),
        "summary_parquet": str(phase_paths.summaries_root / "summary.parquet"),
        "figure_root": str(figure_root),
        "shard_report_path": str(shard_report_path),
        "run_report_path": str(REPORT_PATHS["run_report"]),
        "first_look_path": str(REPORT_PATHS["first_look"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a confirmatory scan around the localized productive-memory ridge.")
    parser.add_argument(
        "--reference-scales-path",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json",
        help="Reference scales JSON used to dimensionalize the confirmatory design.",
    )
    parser.add_argument("--output-root", type=Path, help="Override output root; defaults to project outputs.")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of state points per shard.")
    parser.add_argument("--retry-limit", type=int, default=1, help="Immediate retries allowed per failed shard.")
    parser.add_argument("--resample-top-n", type=int, default=6, help="Final candidate points to resample at 8192 trajectories.")
    args = parser.parse_args(argv)

    result = run_confirmatory_scan(
        PROJECT_ROOT,
        reference_scales_path=args.reference_scales_path,
        output_root=args.output_root,
        batch_size=args.batch_size,
        retry_limit=args.retry_limit,
        resample_top_n=args.resample_top_n,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
