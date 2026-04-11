from __future__ import annotations

import argparse
import json
import math
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

from src.configs.schema import RunConfig, SweepTask
from src.runners.run_coarse_scan import write_coarse_scan_manifest
from src.runners.run_coarse_scan_execute import run_coarse_scan_execute
from src.utils.workflow_schema import write_json


def load_reference_scales(reference_scales_path: str | Path) -> dict[str, Any]:
    reference_scales_path = Path(reference_scales_path)
    with open(reference_scales_path, "r", encoding="ascii") as handle:
        return json.load(handle)


def _variant_parameters(model_variant: str) -> tuple[float, float]:
    if model_variant == "full":
        return 4.0, 3.0
    if model_variant == "no_memory":
        return 0.0, 3.0
    if model_variant == "no_feedback":
        return 4.0, 0.0
    raise ValueError(f"Unsupported production coarse variant: {model_variant}")


def _make_scan_label(model_variant: str, scan_block: str, pi_m: float, pi_f: float, pi_u: float) -> str:
    def _token(value: float) -> str:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return text.replace("-", "neg").replace(".", "p")

    return f"{model_variant}_{scan_block}_pm{_token(pi_m)}_pf{_token(pi_f)}_pu{_token(pi_u)}"


def _build_config(
    *,
    reference_scales: dict[str, Any],
    model_variant: str,
    pi_m: float,
    pi_f: float,
    pi_u: float,
    seed: int,
    state_point_index: int,
    scan_block: str,
    geometry_id: str = "maze_v1",
    dt: float = 0.0025,
    Tmax: float = 30.0,
    n_traj: int = 512,
    grid_n: int = 257,
    n_shell: int = 1,
) -> RunConfig:
    tau_g = float(reference_scales["tau_g"])
    ell_g = float(reference_scales["ell_g"])
    tau_v = pi_m * tau_g
    tau_f = pi_f * tau_g
    U = pi_u * ell_g / tau_g
    gamma1, kf = _variant_parameters(model_variant)
    flow_condition = "zero_flow" if abs(U) <= 1e-15 else "with_flow"
    return RunConfig(
        geometry_id=geometry_id,
        model_variant=model_variant,
        v0=0.5,
        Dr=1.0,
        tau_v=tau_v,
        gamma0=1.0,
        gamma1=gamma1,
        tau_f=tau_f,
        U=U,
        wall_thickness=0.04,
        gate_width=0.08,
        dt=dt,
        Tmax=Tmax,
        n_traj=n_traj,
        seed=seed,
        exit_radius=0.06,
        n_shell=n_shell,
        grid_n=grid_n,
        kf=kf,
        flow_condition=flow_condition,
        metadata={
            "L": 1.0,
            "workflow_stage": "coarse_scan_generation",
            "state_point_index": state_point_index,
            "scan_block": scan_block,
            "scan_label": _make_scan_label(model_variant, scan_block, pi_m, pi_f, pi_u),
            "target_region": "productive_memory_window" if scan_block != "outer_frame" else "outer_frame_check",
            "Pi_m_target": pi_m,
            "Pi_f_target": pi_f,
            "Pi_U_target": pi_u,
        },
    )


def build_production_coarse_tasks(
    reference_scales: dict[str, Any],
    *,
    batch_size: int = 6,
    base_seed: int = 20260800,
) -> tuple[SweepTask, ...]:
    inner_pi_m = (0.1, 0.3, 0.6, 1.0)
    inner_pi_f = (0.05, 0.1, 0.2, 0.3)
    inner_pi_u = (-0.1, 0.0, 0.25)
    outer_frame = (
        (3.0, 0.1, 0.0),
        (3.0, 0.3, 0.25),
        (3.0, 1.0, 0.0),
        (10.0, 0.1, 0.0),
        (10.0, 1.0, 0.25),
        (1.0, 1.0, -0.5),
        (1.0, 3.0, 0.0),
        (3.0, 3.0, 0.5),
    )
    sparse_controls = (
        ("no_memory", 1.0, 0.3, 0.0),
        ("no_memory", 1.0, 0.3, 0.25),
        ("no_feedback", 1.0, 0.3, 0.0),
        ("no_feedback", 1.0, 0.3, 0.25),
    )

    configs: list[RunConfig] = []
    state_point_index = 0
    seed = base_seed
    for pi_m in inner_pi_m:
        for pi_f in inner_pi_f:
            for pi_u in inner_pi_u:
                configs.append(
                    _build_config(
                        reference_scales=reference_scales,
                        model_variant="full",
                        pi_m=pi_m,
                        pi_f=pi_f,
                        pi_u=pi_u,
                        seed=seed,
                        state_point_index=state_point_index,
                        scan_block="dense_inner_box",
                    )
                )
                state_point_index += 1
                seed += 1
    for pi_m, pi_f, pi_u in outer_frame:
        configs.append(
            _build_config(
                reference_scales=reference_scales,
                model_variant="full",
                pi_m=pi_m,
                pi_f=pi_f,
                pi_u=pi_u,
                seed=seed,
                state_point_index=state_point_index,
                scan_block="outer_frame",
            )
        )
        state_point_index += 1
        seed += 1
    for model_variant, pi_m, pi_f, pi_u in sparse_controls:
        configs.append(
            _build_config(
                reference_scales=reference_scales,
                model_variant=model_variant,
                pi_m=pi_m,
                pi_f=pi_f,
                pi_u=pi_u,
                seed=seed,
                state_point_index=state_point_index,
                scan_block="validation_control",
            )
        )
        state_point_index += 1
        seed += 1

    tasks: list[SweepTask] = []
    for batch_index, offset in enumerate(range(0, len(configs), batch_size)):
        batch = tuple(configs[offset : offset + batch_size])
        tasks.append(
            SweepTask(
                task_id=f"coarse_scan_batch_{batch_index:03d}",
                phase="coarse_scan",
                batch_index=batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "scan_name": "production_coarse_scan",
                    "contains_model_variants": sorted({config.model_variant for config in batch}),
                    "scan_blocks": sorted({str(config.metadata.get('scan_block')) for config in batch}),
                },
            )
        )
    return tuple(tasks)


def _unique_sorted(values: pd.Series) -> list[float]:
    cleaned = values.dropna().astype(float).tolist()
    return sorted(set(cleaned))


def generate_quicklook_outputs(summary_df: pd.DataFrame, figure_root: Path) -> dict[str, str]:
    figure_root.mkdir(parents=True, exist_ok=True)
    full_df = summary_df[
        (summary_df["model_variant"] == "full")
        & (summary_df["status_completion"] == "completed")
        & summary_df["Pi_m"].notna()
        & summary_df["Pi_f"].notna()
        & summary_df["Pi_U"].notna()
    ].copy()
    metadata_payloads = full_df["metadata_json"].fillna("{}").map(json.loads)
    full_df["scan_label"] = metadata_payloads.map(lambda payload: payload.get("scan_label"))
    full_df["scan_block"] = metadata_payloads.map(lambda payload: payload.get("scan_block"))
    outputs: dict[str, str] = {}
    if full_df.empty:
        return outputs

    pi_u_values = _unique_sorted(full_df["Pi_U"])
    metrics = {
        "Psucc_mean": "Success Probability",
        "MFPT_mean": "Mean First-Passage Time",
        "eta_sigma_mean": "Efficiency Screening Signal",
        "trap_time_mean": "Mean Trap Residence",
    }
    for metric, title in metrics.items():
        metric_df = full_df[full_df[metric].notna()].copy()
        if metric_df.empty:
            continue
        ncols = min(3, max(1, len(pi_u_values)))
        nrows = math.ceil(len(pi_u_values) / ncols)
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)
        axes_flat = axes.flatten()
        scatter = None
        for axis, pi_u in zip(axes_flat, pi_u_values):
            subset = metric_df[metric_df["Pi_U"] == pi_u]
            if subset.empty:
                axis.set_visible(False)
                continue
            scatter = axis.scatter(
                subset["Pi_m"],
                subset["Pi_f"],
                c=subset[metric],
                cmap="viridis",
                s=100,
                edgecolors="black",
                linewidths=0.5,
            )
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.set_xlabel("Pi_m")
            axis.set_ylabel("Pi_f")
            axis.set_title(f"{title} at Pi_U={pi_u:g}")
            axis.grid(True, which="both", alpha=0.2)
        for axis in axes_flat[len(pi_u_values) :]:
            axis.set_visible(False)
        if scatter is not None:
            fig.colorbar(scatter, ax=axes_flat.tolist(), shrink=0.85, label=metric)
        fig.suptitle(f"Production Coarse Scan Quick-Look: {title}")
        fig.tight_layout()
        figure_path = figure_root / f"{metric}.png"
        fig.savefig(figure_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        outputs[metric] = str(figure_path)

    top_df = full_df.copy()
    top_df = top_df.sort_values(["eta_sigma_mean", "Psucc_mean"], ascending=[False, False])
    top_path = figure_root / "top_screening_points.csv"
    top_df[
        [
            "scan_label",
            "scan_block",
            "model_variant",
            "Pi_m",
            "Pi_f",
            "Pi_U",
            "Psucc_mean",
            "MFPT_mean",
            "eta_sigma_mean",
            "trap_time_mean",
            "result_json",
        ]
    ].head(12).to_csv(top_path, index=False)
    outputs["top_screening_points_csv"] = str(top_path)
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


def run_production_coarse_scan(
    project_root: str | Path,
    *,
    reference_scales_path: str | Path,
    output_root: str | Path | None = None,
    batch_size: int = 6,
    retry_limit: int = 1,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs"
    reference_scales_path = Path(reference_scales_path)
    reference_scales = load_reference_scales(reference_scales_path)

    tasks = build_production_coarse_tasks(reference_scales, batch_size=batch_size)
    manifest_result = write_coarse_scan_manifest(
        project_root,
        tasks=tasks,
        output_root=output_root,
        upstream_reference_scales_path=str(reference_scales_path),
    )

    completed_shards: list[str] = []
    failed_shards: list[dict[str, Any]] = []
    attempt_log: list[dict[str, Any]] = []
    for task in tasks:
        shard_id = f"batch_{task.batch_index:03d}"
        attempt = 0
        succeeded = False
        last_error: str | None = None
        while attempt <= retry_limit and not succeeded:
            attempt += 1
            try:
                run_coarse_scan_execute(
                    project_root,
                    manifest_path=manifest_result["manifest_path"],
                    output_root=output_root,
                    batch_index=task.batch_index,
                    upstream_reference_scales_path=str(reference_scales_path),
                )
                completed_shards.append(shard_id)
                attempt_log.append(
                    {
                        "shard_id": shard_id,
                        "task_id": task.task_id,
                        "attempt": attempt,
                        "status": "completed",
                    }
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

    summary_csv = output_root / "summaries" / "coarse_scan" / "summary.csv"
    summary_df = pd.read_csv(summary_csv)
    figure_root = output_root / "figures" / "coarse_scan_quicklook"
    quicklook_outputs = generate_quicklook_outputs(summary_df, figure_root)
    missing_outputs = collect_missing_outputs(summary_df)

    shard_report = {
        "scan_id": "coarse_scan",
        "manifest_path": manifest_result["manifest_path"],
        "summary_csv": str(summary_csv),
        "summary_parquet": str(output_root / "summaries" / "coarse_scan" / "summary.parquet"),
        "completed_shards": completed_shards,
        "failed_shards": failed_shards,
        "attempt_log": attempt_log,
        "retry_policy": {
            "retry_limit": retry_limit,
            "rule": "Retry each failed shard once immediately; if it still fails, leave it recorded as failed and do not start adaptive refinement.",
        },
        "missing_outputs": missing_outputs,
        "quicklook_outputs": quicklook_outputs,
    }
    shard_report_path = output_root / "summaries" / "coarse_scan" / "shard_execution_report.json"
    write_json(shard_report_path, shard_report)
    return {
        "manifest": manifest_result,
        "summary_df": summary_df,
        "quicklook_outputs": quicklook_outputs,
        "shard_report": shard_report,
        "shard_report_path": str(shard_report_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the first production coarse scan.")
    parser.add_argument(
        "--reference-scales-path",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json",
        help="Reference scales JSON used to dimensionalize the coarse production design.",
    )
    parser.add_argument("--output-root", type=Path, help="Override output root; defaults to project outputs.")
    parser.add_argument("--batch-size", type=int, default=6, help="Number of state points per shard.")
    parser.add_argument("--retry-limit", type=int, default=1, help="Immediate retries allowed per failed shard.")
    args = parser.parse_args(argv)

    result = run_production_coarse_scan(
        PROJECT_ROOT,
        reference_scales_path=args.reference_scales_path,
        output_root=args.output_root,
        batch_size=args.batch_size,
        retry_limit=args.retry_limit,
    )
    print(json.dumps(result["shard_report"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
