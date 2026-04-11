from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.configs.schema import RunConfig, SweepTask
from src.runners.run_coarse_scan import write_coarse_scan_manifest
from src.runners.run_coarse_scan_execute import run_coarse_scan_execute


def _make_config(*, index: int, U: float) -> RunConfig:
    return RunConfig(
        geometry_id="maze_v1",
        model_variant="full",
        v0=0.5,
        Dr=1.0,
        tau_v=0.6 + 0.1 * index,
        gamma0=1.0,
        gamma1=4.0,
        tau_f=0.3 + 0.05 * index,
        U=U,
        wall_thickness=0.04,
        gate_width=0.08,
        dt=0.0025,
        Tmax=4.0,
        n_traj=8,
        seed=20260600 + index,
        exit_radius=0.06,
        n_shell=1,
        grid_n=65,
        kf=3.0,
        flow_condition="zero_flow" if abs(U) <= 1e-15 else "with_flow",
        metadata={
            "L": 1.0,
            "workflow_stage": "coarse_scan_generation",
            "state_point_index": index,
        },
    )


def test_coarse_scan_execution_smoke(tmp_path: Path) -> None:
    upstream_path = tmp_path / "summaries" / "reference_scales" / "reference_scales.json"
    upstream_path.parent.mkdir(parents=True, exist_ok=True)
    upstream_path.write_text(
        json.dumps({"tau_g": 7.0, "ell_g": 3.5, "tau_p": 1.0}, indent=2),
        encoding="ascii",
    )

    config_a = _make_config(index=0, U=0.0)
    config_b = _make_config(index=1, U=0.125)
    config_c = _make_config(index=2, U=-0.125)
    tasks = (
        SweepTask(
            task_id="coarse_scan_batch_000",
            phase="coarse_scan",
            batch_index=0,
            config_list=(config_a, config_b),
            metadata={"batch_size": 2},
        ),
        SweepTask(
            task_id="coarse_scan_batch_001",
            phase="coarse_scan",
            batch_index=1,
            config_list=(config_c,),
            metadata={"batch_size": 1},
        ),
    )

    manifest = write_coarse_scan_manifest(
        PROJECT_ROOT,
        tasks=tasks,
        output_root=tmp_path,
        upstream_reference_scales_path=str(upstream_path),
    )
    result = run_coarse_scan_execute(
        PROJECT_ROOT,
        manifest_path=manifest["manifest_path"],
        output_root=tmp_path,
        batch_index=0,
    )

    assert len(result["executed_rows"]) == 2
    assert result["selected_task_ids"] == ["coarse_scan_batch_000"]
    assert result["selected_shards"] == ["batch_000"]

    summary_path = tmp_path / "summaries" / "coarse_scan" / "summary.csv"
    metadata_path = tmp_path / "summaries" / "coarse_scan" / "metadata.json"
    assert summary_path.exists()
    assert metadata_path.exists()
    assert Path(tmp_path / "logs" / "coarse_scan" / "coarse_scan_execute_batch_000.log").exists()

    summary_df = pd.read_csv(summary_path)
    executed_df = summary_df[summary_df["status_stage"] == "coarse_scan_execute"]
    generated_df = summary_df[summary_df["status_stage"] == "coarse_scan"]
    assert len(executed_df) == 2
    assert len(generated_df) == 1
    assert executed_df["status_completion"].eq("completed").all()
    assert generated_df["status_completion"].eq("generated_manifest_only").all()
    assert executed_df["raw_summary_kind"].eq("adapter_raw_summary_csv").all()
    assert executed_df["task_manifest_kind"].eq("task_manifest_json").all()
    assert executed_df["upstream_reference_scales_path"].eq(str(upstream_path)).all()
    assert executed_df["reference_tau_g"].eq(7.0).all()
    assert executed_df["reference_l_g"].eq(3.5).all()
    assert executed_df["reference_tau_p"].eq(1.0).all()
    assert executed_df["Pi_m"].notna().all()
    assert generated_df["raw_summary_kind"].eq("not_applicable_generation_only").all()

    for config in (config_a, config_b):
        run_dir = tmp_path / "runs" / "coarse_scan" / config.geometry_id / config.config_hash
        assert (run_dir / "result.json").exists()
        assert (run_dir / "raw_summary.csv").exists()
    config_c_run_dir = tmp_path / "runs" / "coarse_scan" / config_c.geometry_id / config_c.config_hash
    assert not (config_c_run_dir / "result.json").exists()

    result_payload = json.loads(
        (tmp_path / "runs" / "coarse_scan" / config_a.geometry_id / config_a.config_hash / "result.json").read_text(
            encoding="ascii"
        )
    )
    assert result_payload["status_stage"] == "coarse_scan_execute"
    assert result_payload["status_reason"] == "executed_from_manifest"
    assert result_payload["task_id"] == "coarse_scan_batch_000"
    assert result_payload["shard_id"] == "batch_000"
    assert result_payload["upstream_reference_scales_path"] == str(upstream_path)

    metadata = json.loads(metadata_path.read_text(encoding="ascii"))
    assert metadata["status_stage"] == "coarse_scan_execute"
    assert metadata["status_completion"] == "partially_completed"
    assert metadata["status_reason"] == "coarse_scan_partial_execution"
    assert metadata["n_executed_state_points"] == 2
    assert metadata["n_generated_only_state_points"] == 1
    assert metadata["selected_task_ids"] == ["coarse_scan_batch_000"]
    assert metadata["selected_shards"] == ["batch_000"]
    assert metadata["upstream_reference_scales_path"] == str(upstream_path)
