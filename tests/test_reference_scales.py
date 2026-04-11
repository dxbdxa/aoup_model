from __future__ import annotations

from pathlib import Path
import sys

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
    assert Path(result["reference_scales_json"]).exists()
    assert Path(result["transition_stats"]["csv"]).exists()
