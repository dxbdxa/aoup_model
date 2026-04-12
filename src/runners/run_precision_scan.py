from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

SCAN_ID = "precision_scan"
EXECUTION_STAGE = "precision_scan_execute"


def load_reference_scales(reference_scales_path: str | Path) -> dict[str, Any]:
    reference_scales_path = Path(reference_scales_path)
    with open(reference_scales_path, "r", encoding="ascii") as handle:
        return json.load(handle)


def _token(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text.replace("-", "neg").replace(".", "p")


def _make_scan_label(scan_block: str, pi_m: float, pi_f: float, pi_u: float, n_traj: int) -> str:
    return f"full_{scan_block}_pm{_token(pi_m)}_pf{_token(pi_f)}_pu{_token(pi_u)}_n{n_traj}"


def build_precision_config(
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
        "workflow_stage": "precision_scan_generation",
        "state_point_index": state_point_index,
        "scan_block": scan_block,
        "scan_label": _make_scan_label(scan_block, pi_m, pi_f, pi_u, n_traj),
        "target_region": "precision_ridge_envelope",
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


def build_precision_tasks(
    reference_scales: dict[str, Any],
    *,
    batch_size: int = 8,
    base_seed: int = 20261000,
    n_traj: int = 2048,
) -> tuple[SweepTask, ...]:
    pi_f_values = (0.02, 0.025, 0.03)
    pi_m_values = (0.05, 0.08, 0.1, 0.12, 0.15, 0.18, 0.2, 0.25)
    pi_u_values = (0.1, 0.15, 0.2, 0.25, 0.3)
    configs: list[RunConfig] = []
    seed = base_seed
    state_point_index = 0
    for pi_f in pi_f_values:
        for pi_m in pi_m_values:
            for pi_u in pi_u_values:
                configs.append(
                    build_precision_config(
                        reference_scales=reference_scales,
                        pi_m=pi_m,
                        pi_f=pi_f,
                        pi_u=pi_u,
                        seed=seed,
                        state_point_index=state_point_index,
                        scan_block="precision_ridge_grid",
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
                task_id=f"precision_scan_batch_{batch_index:03d}",
                phase=SCAN_ID,
                batch_index=batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "scan_name": "targeted_precision_scan",
                    "scan_blocks": ["precision_ridge_grid"],
                },
            )
        )
    return tuple(tasks)


def write_precision_manifest(
    project_root: str | Path,
    *,
    tasks: tuple[SweepTask, ...],
    output_root: str | Path | None = None,
    upstream_reference_scales_path: str | None = None,
    manifest_name: str = "task_manifest.json",
    status_reason: str = "precision_scan_generation_only",
    scan_description: str = "Precision-scan task generation only; no execution is performed at this stage.",
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
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

    rows: list[dict[str, Any]] = []
    for task in tasks:
        for config in task.config_list:
            tau_p = (1.0 / config.Dr) if config.Dr != 0.0 else None
            gamma1_over_gamma0 = config.gamma1_over_gamma0
            if gamma1_over_gamma0 is None:
                gamma1_over_gamma0 = (config.gamma1 / config.gamma0) if config.gamma0 != 0.0 else None
            rows.append(
                {
                    "scan_id": SCAN_ID,
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
                    "status_stage": SCAN_ID,
                    "status_reason": status_reason,
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
                    "reference_tau_g": None,
                    "reference_l_g": None,
                    "reference_tau_p": None,
                    "Pi_m": None,
                    "Pi_f": None,
                    "Pi_U": None,
                    "metadata_json": json.dumps(config.metadata, sort_keys=True),
                }
            )
    existing_summary_path = phase_paths.summaries_root / "summary.csv"
    if existing_summary_path.exists():
        existing_df = pd.read_csv(existing_summary_path)
        summary_df = pd.concat([existing_df, pd.DataFrame(rows)], ignore_index=True)
    else:
        summary_df = pd.DataFrame(rows)
    summary_paths = write_summary_tables(phase_paths, summary_df) if not summary_df.empty else {"summary_csv": "", "summary_parquet": ""}
    metadata_json = phase_paths.summaries_root / "metadata.json"
    metadata = build_phase_metadata(
        scan_id=SCAN_ID,
        phase=SCAN_ID,
        task_id=payload["task_id"],
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=upstream_reference_scales_path,
        status_completion="generated_manifest_only",
        scan_description=scan_description,
        manifest_path=str(manifest_path),
        n_state_points=int(len(summary_df)),
        n_tasks=len(tasks),
    )
    metadata["status_reason"] = status_reason
    metadata["model_variants"] = ["full"]
    metadata["flow_conditions"] = sorted({config.flow_condition for task in tasks for config in task.config_list})
    write_json(metadata_json, metadata)
    write_log(
        phase_paths.logs_root / f"generate_{manifest_name.replace('.json', '')}.log",
        [
            f"generate_{manifest_name.replace('.json', '')}",
            f"n_tasks={len(tasks)}",
            f"manifest_path={manifest_path}",
        ],
    )
    return {
        "manifest_path": str(manifest_path),
        "n_tasks": len(tasks),
        "tasks": tasks,
        "summary_csv": summary_paths["summary_csv"],
        "summary_parquet": summary_paths["summary_parquet"],
        "metadata_json": str(metadata_json),
    }


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
    status_reason = None if status_completion == "completed" else "precision_scan_partial_execution"
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
    return result


def _execute_tasks(
    *,
    project_root: Path,
    phase_paths: Any,
    tasks: tuple[SweepTask, ...],
    reference_scales_path: str,
    reference_scales: dict[str, Any],
    manifest_path: str,
    retry_limit: int,
    completed_shards: list[str],
    failed_shards: list[dict[str, Any]],
    attempt_log: list[dict[str, Any]],
) -> None:
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
                    scan_description="Targeted precision scan along the refined productive ridge.",
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
                    phase_paths.logs_root / f"precision_scan_execute_{shard_id}.log",
                    [
                        "precision_scan_execute",
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


def _build_resample_tasks(
    summary_df: pd.DataFrame,
    reference_scales: dict[str, Any],
    *,
    n_candidates: int = 10,
    batch_size: int = 5,
    base_seed: int = 20262000,
    n_traj: int = 4096,
) -> tuple[SweepTask, ...]:
    base_df = _metadata_columns(summary_df)
    base_df = base_df[
        (base_df["status_completion"] == "completed")
        & (base_df["scan_block"] == "precision_ridge_grid")
        & (base_df["n_traj"] == 2048)
    ].copy()
    base_df["rank_psucc"] = base_df["Psucc_mean"].rank(ascending=False, method="min")
    base_df["rank_mfpt"] = base_df["MFPT_mean"].rank(ascending=True, method="min")
    base_df["rank_eta_sigma"] = base_df["eta_sigma_mean"].rank(ascending=False, method="min")
    base_df["rank_trap_time"] = base_df["trap_time_mean"].rank(ascending=True, method="min")
    base_df["precision_rank_sum"] = (
        base_df["rank_psucc"] + base_df["rank_mfpt"] + base_df["rank_eta_sigma"] + base_df["rank_trap_time"]
    )
    selected = base_df.sort_values(["precision_rank_sum", "rank_eta_sigma", "rank_psucc"]).head(n_candidates)
    tasks: list[SweepTask] = []
    configs: list[RunConfig] = []
    seed = base_seed
    for state_point_index, row in enumerate(selected.itertuples(index=False), start=len(base_df)):
        metadata_extra = {
            "resampled_from_state_point_id": row.state_point_id,
            "resampled_from_scan_label": row.scan_label,
            "base_n_traj": int(row.n_traj),
        }
        configs.append(
            build_precision_config(
                reference_scales=reference_scales,
                pi_m=float(row.Pi_m),
                pi_f=float(row.Pi_f),
                pi_u=float(row.Pi_U),
                seed=seed,
                state_point_index=state_point_index,
                scan_block="top_candidate_resample",
                n_traj=n_traj,
                metadata_extra=metadata_extra,
            )
        )
        seed += 1
    for batch_index, offset in enumerate(range(0, len(configs), batch_size)):
        batch = tuple(configs[offset : offset + batch_size])
        tasks.append(
            SweepTask(
                task_id=f"precision_resample_batch_{batch_index:03d}",
                phase=SCAN_ID,
                batch_index=100 + batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "scan_name": "precision_scan_resample",
                    "scan_blocks": ["top_candidate_resample"],
                },
            )
        )
    return tuple(tasks)


def generate_precision_outputs(summary_df: pd.DataFrame, figure_root: Path) -> dict[str, str]:
    figure_root.mkdir(parents=True, exist_ok=True)
    plot_df = _metadata_columns(summary_df)
    base_df = plot_df[
        (plot_df["status_completion"] == "completed")
        & (plot_df["scan_block"] == "precision_ridge_grid")
        & (plot_df["n_traj"] == 2048)
    ].copy()
    outputs: dict[str, str] = {}
    if base_df.empty:
        return outputs

    metrics = {
        "Psucc_mean": ("Success Probability", False),
        "MFPT_mean": ("Mean First-Passage Time", True),
        "eta_sigma_mean": ("Efficiency Screening Signal", False),
        "trap_time_mean": ("Mean Trap Residence", True),
    }
    pi_f_values = sorted(set(base_df["Pi_f"].dropna().astype(float).tolist()))
    for metric, (title, lower_is_better) in metrics.items():
        metric_df = base_df[base_df[metric].notna()].copy()
        fig, axes = plt.subplots(1, len(pi_f_values), figsize=(5 * len(pi_f_values), 4.5), squeeze=False)
        axes_flat = axes.flatten()
        image = None
        for axis, pi_f in zip(axes_flat, pi_f_values):
            subset = metric_df[metric_df["Pi_f"] == pi_f]
            pivot = subset.pivot(index="Pi_U", columns="Pi_m", values=metric).sort_index(ascending=False)
            image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis")
            axis.set_title(f"{title} at Pi_f={pi_f:g}")
            axis.set_xticks(range(len(pivot.columns)))
            axis.set_xticklabels([f"{value:g}" for value in pivot.columns], rotation=45)
            axis.set_yticks(range(len(pivot.index)))
            axis.set_yticklabels([f"{value:g}" for value in pivot.index])
            axis.set_xlabel("Pi_m")
            axis.set_ylabel("Pi_U")
        if image is not None:
            fig.colorbar(image, ax=axes_flat.tolist(), shrink=0.85, label=metric)
        fig.suptitle(f"Precision Scan: {title}")
        fig.tight_layout()
        figure_path = figure_root / f"{metric}.png"
        fig.savefig(figure_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        outputs[metric] = str(figure_path)

    top_psucc = base_df.sort_values(["Psucc_mean", "eta_sigma_mean"], ascending=[False, False]).head(10).copy()
    top_psucc["objective"] = "Psucc_mean"
    top_eta = base_df.sort_values(["eta_sigma_mean", "Psucc_mean"], ascending=[False, False]).head(10).copy()
    top_eta["objective"] = "eta_sigma_mean"
    top_mfpt = base_df.sort_values(["MFPT_mean", "Psucc_mean"], ascending=[True, False]).head(10).copy()
    top_mfpt["objective"] = "MFPT_mean"
    candidate_table = pd.concat([top_psucc, top_eta, top_mfpt], ignore_index=True)
    candidate_table_path = figure_root / "top_points_by_objective.csv"
    candidate_table[
        [
            "objective",
            "scan_label",
            "Pi_m",
            "Pi_f",
            "Pi_U",
            "n_traj",
            "Psucc_mean",
            "MFPT_mean",
            "eta_sigma_mean",
            "trap_time_mean",
            "result_json",
        ]
    ].to_csv(candidate_table_path, index=False)
    outputs["top_points_by_objective_csv"] = str(candidate_table_path)

    resample_df = plot_df[
        (plot_df["status_completion"] == "completed")
        & (plot_df["scan_block"] == "top_candidate_resample")
        & (plot_df["n_traj"] == 4096)
    ].copy()
    if not resample_df.empty:
        base_compare = base_df[
            [
                "state_point_id",
                "scan_label",
                "Pi_m",
                "Pi_f",
                "Pi_U",
                "n_traj",
                "Psucc_mean",
                "MFPT_mean",
                "eta_sigma_mean",
                "trap_time_mean",
            ]
        ].rename(columns=lambda value: f"base_{value}" if value not in {"Pi_m", "Pi_f", "Pi_U"} else value)
        resample_compare = resample_df[
            [
                "resampled_from_state_point_id",
                "scan_label",
                "n_traj",
                "Psucc_mean",
                "MFPT_mean",
                "eta_sigma_mean",
                "trap_time_mean",
            ]
        ].rename(
            columns={
                "resampled_from_state_point_id": "state_point_id",
                "scan_label": "resample_scan_label",
                "n_traj": "resample_n_traj",
                "Psucc_mean": "resample_Psucc_mean",
                "MFPT_mean": "resample_MFPT_mean",
                "eta_sigma_mean": "resample_eta_sigma_mean",
                "trap_time_mean": "resample_trap_time_mean",
            }
        )
        resample_comparison = base_compare.merge(resample_compare, on="state_point_id", how="inner")
        resample_path = figure_root / "resample_comparison.csv"
        resample_comparison.to_csv(resample_path, index=False)
        outputs["resample_comparison_csv"] = str(resample_path)
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


def run_precision_scan(
    project_root: str | Path,
    *,
    reference_scales_path: str | Path,
    output_root: str | Path | None = None,
    batch_size: int = 8,
    retry_limit: int = 1,
    resample_top_n: int = 10,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
    reference_scales_path = str(Path(reference_scales_path))
    reference_scales = load_reference_scales(reference_scales_path)
    phase_paths = get_phase_paths(output_root, SCAN_ID)

    base_tasks = build_precision_tasks(reference_scales, batch_size=batch_size)
    manifest_result = write_precision_manifest(
        project_root,
        tasks=base_tasks,
        output_root=output_root,
        upstream_reference_scales_path=reference_scales_path,
        manifest_name="task_manifest.json",
    )

    completed_shards: list[str] = []
    failed_shards: list[dict[str, Any]] = []
    attempt_log: list[dict[str, Any]] = []

    _execute_tasks(
        project_root=project_root,
        phase_paths=phase_paths,
        tasks=base_tasks,
        reference_scales_path=reference_scales_path,
        reference_scales=reference_scales,
        manifest_path=manifest_result["manifest_path"],
        retry_limit=retry_limit,
        completed_shards=completed_shards,
        failed_shards=failed_shards,
        attempt_log=attempt_log,
    )

    summary_df = pd.read_csv(phase_paths.summaries_root / "summary.csv")
    resample_tasks = _build_resample_tasks(summary_df, reference_scales, n_candidates=resample_top_n)
    resample_manifest_result = write_precision_manifest(
        project_root,
        tasks=resample_tasks,
        output_root=output_root,
        upstream_reference_scales_path=reference_scales_path,
        manifest_name="top_candidate_resample_manifest.json",
        status_reason="precision_scan_resample_generation_only",
        scan_description="Top-candidate resample generation for the precision scan.",
    )

    _execute_tasks(
        project_root=project_root,
        phase_paths=phase_paths,
        tasks=resample_tasks,
        reference_scales_path=reference_scales_path,
        reference_scales=reference_scales,
        manifest_path=resample_manifest_result["manifest_path"],
        retry_limit=retry_limit,
        completed_shards=completed_shards,
        failed_shards=failed_shards,
        attempt_log=attempt_log,
    )

    summary_df = pd.read_csv(phase_paths.summaries_root / "summary.csv")
    figure_root = output_root / "figures" / "precision_scan"
    precision_outputs = generate_precision_outputs(summary_df, figure_root)
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
        task_id="precision_scan_complete",
        summary_paths=summary_paths,
        metadata_json_path=str(metadata_json),
        upstream_reference_scales_path=reference_scales_path,
        status_completion=progress["status_completion"],
        scan_description="Targeted precision scan along the refined productive ridge.",
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
    metadata["resample_manifest_path"] = resample_manifest_result["manifest_path"]
    write_json(metadata_json, metadata)

    shard_report = {
        "scan_id": SCAN_ID,
        "manifest_path": manifest_result["manifest_path"],
        "resample_manifest_path": resample_manifest_result["manifest_path"],
        "summary_csv": str(phase_paths.summaries_root / "summary.csv"),
        "summary_parquet": str(phase_paths.summaries_root / "summary.parquet"),
        "completed_shards": completed_shards,
        "failed_shards": failed_shards,
        "attempt_log": attempt_log,
        "retry_policy": {
            "retry_limit": retry_limit,
            "rule": "Retry each failed shard once immediately; if it still fails, record it and stop without global search expansion.",
        },
        "missing_outputs": missing_outputs,
        "precision_outputs": precision_outputs,
        "resample_top_n": resample_top_n,
    }
    shard_report_path = phase_paths.summaries_root / "shard_execution_report.json"
    write_json(shard_report_path, shard_report)
    return {
        "manifest": manifest_result,
        "resample_manifest": resample_manifest_result,
        "summary_df": summary_df,
        "precision_outputs": precision_outputs,
        "shard_report": shard_report,
        "shard_report_path": str(shard_report_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a targeted precision scan along the refined productive ridge.")
    parser.add_argument(
        "--reference-scales-path",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json",
        help="Reference scales JSON used to dimensionalize the precision design.",
    )
    parser.add_argument("--output-root", type=Path, help="Override output root; defaults to project outputs.")
    parser.add_argument("--batch-size", type=int, default=8, help="Number of state points per base shard.")
    parser.add_argument("--retry-limit", type=int, default=1, help="Immediate retries allowed per failed shard.")
    parser.add_argument("--resample-top-n", type=int, default=10, help="Top candidates to resample at 4096 trajectories.")
    args = parser.parse_args(argv)

    result = run_precision_scan(
        PROJECT_ROOT,
        reference_scales_path=args.reference_scales_path,
        output_root=args.output_root,
        batch_size=args.batch_size,
        retry_limit=args.retry_limit,
        resample_top_n=args.resample_top_n,
    )
    print(json.dumps(result["shard_report"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
