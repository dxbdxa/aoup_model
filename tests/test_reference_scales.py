from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_reference_scales import build_reference_run_config, extract_reference_scales


def test_extract_reference_scales_writes_expected_outputs(tmp_path: Path) -> None:
    config = build_reference_run_config(
        n_traj=8,
        Tmax=4.0,
        grid_n=65,
        metadata={"test_case": "reference_scales"},
    )

    result = extract_reference_scales(PROJECT_ROOT, config=config, output_root=tmp_path)

    assert result["geometry_id"] == config.geometry_id
    assert result["model_variant"] == config.model_variant
    assert result["ell_g"] >= 0.0
    assert result["tau_g"] >= 0.0
    assert result["config_hash"] == config.config_hash
    assert Path(result["reference_scales_json"]).exists()
    assert Path(result["transition_stats"]["csv"]).exists()
    assert Path(result["summary_tables"]["summary_csv"]).exists()
    assert Path(result["result_json"]).exists()
    assert Path(result["raw_summary_path"]).exists()
    assert Path(tmp_path / "runs" / "reference_scales" / config.geometry_id / config.config_hash / "result.json").exists()
    assert Path(tmp_path / "summaries" / "reference_scales" / "summary.csv").exists()
    assert Path(tmp_path / "logs" / "reference_scales" / "reference_scale_extraction.log").exists()
    assert Path(result["compatibility_shims"]["legacy_reference_scales_json"]).exists()
    result_payload = json.loads(Path(result["result_json"]).read_text(encoding="ascii"))
    assert result_payload["scan_id"] == "reference_scales"
    assert result_payload["task_id"] == "reference_scale_extraction"
    assert result_payload["state_point_id"] == config.config_hash
    assert result_payload["raw_summary_kind"] == "adapter_raw_summary_csv"
    assert result_payload["raw_summary_status"] == "available"
    assert result_payload["normalized_result_kind"] == "normalized_result_json"

    summary_df = pd.read_csv(result["summary_tables"]["summary_csv"])
    assert summary_df.loc[0, "scan_id"] == "reference_scales"
    assert summary_df.loc[0, "task_id"] == "reference_scale_extraction"
    assert summary_df.loc[0, "state_point_id"] == config.config_hash
    assert summary_df.loc[0, "raw_summary_kind"] == "adapter_raw_summary_csv"
    assert summary_df.loc[0, "raw_summary_status"] == "available"
    assert summary_df.loc[0, "phase_summary_kind"] == "phase_summary_table"
    assert summary_df.loc[0, "metadata_sidecar_kind"] == "metadata_json_sidecar"
    assert pd.isna(summary_df.loc[0, "upstream_reference_scales_path"])

    metadata = json.loads(Path(tmp_path / "summaries" / "reference_scales" / "metadata.json").read_text(encoding="ascii"))
    assert metadata["scan_id"] == "reference_scales"
    assert metadata["task_id"] == "reference_scale_extraction"
    assert metadata["status_completion"] == "completed"
