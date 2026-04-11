from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_benchmark_mini_scan import build_benchmark_mini_scan_configs, run_benchmark_mini_scan
from src.runners.run_coarse_scan import generate_coarse_scan_tasks, write_coarse_scan_manifest


def test_benchmark_mini_scan_smoke(tmp_path: Path) -> None:
    configs = build_benchmark_mini_scan_configs(n_traj=8, Tmax=4.0, grid_n=65)
    upstream = str(tmp_path / "summaries" / "reference_scales" / "reference_scales.json")
    result = run_benchmark_mini_scan(
        PROJECT_ROOT,
        configs=configs,
        output_root=tmp_path,
        max_configs=2,
        upstream_reference_scales_path=upstream,
    )

    assert len(configs) == 9
    assert len(result["summary_df"]) == 2
    assert Path(result["metadata"]["summary_csv"]).exists()
    assert Path(result["metadata"]["metadata_json"]).exists()
    assert Path(result["metadata"]["summary_parquet"]).exists() or result["metadata"]["summary_parquet"] == ""
    assert Path(tmp_path / "runs" / "benchmark_mini_scan" / configs[0].geometry_id / configs[0].config_hash / "result.json").exists()
    assert Path(tmp_path / "logs" / "benchmark_mini_scan" / "benchmark_mini_scan.log").exists()
    result_payload = json.loads(
        Path(tmp_path / "runs" / "benchmark_mini_scan" / configs[0].geometry_id / configs[0].config_hash / "result.json").read_text(
            encoding="ascii"
        )
    )
    assert result_payload["scan_id"] == "benchmark_mini_scan"
    assert result_payload["upstream_reference_scales_path"] == upstream
    assert result_payload["raw_summary_kind"] == "adapter_raw_summary_csv"
    assert result_payload["normalized_result_kind"] == "normalized_result_json"
    assert "config_hash" in result["summary_df"].columns
    assert "state_point_id" in result["summary_df"].columns
    assert "task_id" in result["summary_df"].columns
    assert "flow_condition" in result["summary_df"].columns
    assert "upstream_reference_scales_path" in result["summary_df"].columns
    assert "raw_summary_kind" in result["summary_df"].columns
    assert result["summary_df"].iloc[0]["upstream_reference_scales_path"] == upstream

    metadata = json.loads(Path(result["metadata"]["metadata_json"]).read_text(encoding="ascii"))
    assert metadata["scan_id"] == "benchmark_mini_scan"
    assert metadata["upstream_reference_scales_path"] == upstream


def test_coarse_scan_task_generation_smoke(tmp_path: Path) -> None:
    tasks = generate_coarse_scan_tasks(num_points=6, batch_size=4, model_variants=("full", "no_memory"))
    upstream = str(tmp_path / "summaries" / "reference_scales" / "reference_scales.json")
    manifest = write_coarse_scan_manifest(PROJECT_ROOT, tasks=tasks, output_root=tmp_path, upstream_reference_scales_path=upstream)

    total_configs = sum(len(task.config_list) for task in tasks)
    assert total_configs == 12
    assert len(tasks) == 3
    assert Path(manifest["manifest_path"]).exists()
    assert Path(manifest["summary_csv"]).exists()
    assert Path(tmp_path / "logs" / "coarse_scan" / "generate_coarse_scan_tasks.log").exists()

    payload = json.loads(Path(manifest["manifest_path"]).read_text(encoding="ascii"))
    first_config = payload["tasks"][0]["config_list"][0]
    assert first_config["config_hash"]
    assert payload["scan_id"] == "coarse_scan"
    assert payload["status_completion"] == "generated_manifest_only"
    assert payload["upstream_reference_scales_path"] == upstream

    summary_df = pd.read_csv(manifest["summary_csv"])
    assert "task_id" in summary_df.columns
    assert "shard_id" in summary_df.columns
    assert "status_completion" in summary_df.columns
    assert summary_df.iloc[0]["raw_summary_kind"] == "not_applicable_generation_only"
    assert summary_df.iloc[0]["raw_summary_status"] == "not_applicable"
    assert summary_df.iloc[0]["task_manifest_kind"] == "task_manifest_json"
    assert summary_df.iloc[0]["upstream_reference_scales_path"] == upstream

    metadata = json.loads(Path(manifest["metadata_json"]).read_text(encoding="ascii"))
    assert metadata["scan_id"] == "coarse_scan"
    assert metadata["manifest_path"] == manifest["manifest_path"]
