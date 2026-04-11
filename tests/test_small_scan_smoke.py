from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_benchmark_mini_scan import build_benchmark_mini_scan_configs, run_benchmark_mini_scan
from src.runners.run_coarse_scan import generate_coarse_scan_tasks, write_coarse_scan_manifest


def test_benchmark_mini_scan_smoke(tmp_path: Path) -> None:
    configs = build_benchmark_mini_scan_configs(n_traj=8, Tmax=4.0, grid_n=65)
    result = run_benchmark_mini_scan(PROJECT_ROOT, configs=configs, output_root=tmp_path, max_configs=2)

    assert len(configs) == 9
    assert len(result["summary_df"]) == 2
    assert Path(result["metadata"]["summary_csv"]).exists()
    assert Path(result["metadata"]["metadata_json"]).exists()


def test_coarse_scan_task_generation_smoke(tmp_path: Path) -> None:
    tasks = generate_coarse_scan_tasks(num_points=6, batch_size=4, model_variants=("full", "no_memory"))
    manifest = write_coarse_scan_manifest(PROJECT_ROOT, tasks=tasks, output_root=tmp_path)

    total_configs = sum(len(task.config_list) for task in tasks)
    assert total_configs == 12
    assert len(tasks) == 3
    assert Path(manifest["manifest_path"]).exists()
