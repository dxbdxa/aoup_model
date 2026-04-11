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


def build_reference_run_config(
    *,
    geometry_id: str = "maze_v1",
    v0: float = 0.5,
    Dr: float = 1.0,
    dt: float = 0.0025,
    Tmax: float = 20.0,
    n_traj: int = 64,
    seed: int = 20260411,
    wall_thickness: float = 0.04,
    gate_width: float = 0.08,
    exit_radius: float = 0.06,
    n_shell: int = 1,
    grid_n: int = 257,
    metadata: dict[str, Any] | None = None,
) -> RunConfig:
    merged_metadata = {"L": 1.0, "workflow_stage": "reference_scale_extraction"}
    if metadata:
        merged_metadata.update(metadata)
    return RunConfig(
        geometry_id=geometry_id,
        model_variant="no_memory",
        v0=v0,
        Dr=Dr,
        tau_v=0.25,
        gamma0=1.0,
        gamma1=0.0,
        tau_f=0.0,
        U=0.0,
        wall_thickness=wall_thickness,
        gate_width=gate_width,
        dt=dt,
        Tmax=Tmax,
        n_traj=n_traj,
        seed=seed,
        exit_radius=exit_radius,
        n_shell=n_shell,
        grid_n=grid_n,
        kf=0.0,
        bootstrap_resamples=256,
        metadata=merged_metadata,
    )


def _write_table_with_optional_parquet(df: pd.DataFrame, csv_path: Path, parquet_path: Path) -> dict[str, str]:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    paths = {"csv": str(csv_path)}
    try:
        df.to_parquet(parquet_path, index=False)
        paths["parquet"] = str(parquet_path)
    except Exception:
        paths["parquet"] = ""
    return paths


def extract_reference_scales(
    project_root: str | Path,
    *,
    config: RunConfig | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs" / "reference"

    adapter = LegacySimcoreAdapter(project_root)
    run_config = config or build_reference_run_config()
    summary, traj_df, trap_df = adapter.run_point(run_config)
    result = adapter.summary_to_result(run_config, summary, traj_df=traj_df, trap_df=trap_df)

    tau_g = result.mfpt_mean if result.mfpt_mean is not None else run_config.Tmax
    ell_g = run_config.v0 * tau_g
    tau_p = 1.0 / run_config.Dr
    transition_df = traj_df.copy()
    transition_df["success"] = transition_df["success_flag"].astype(bool)
    transition_df["fpt"] = transition_df["t_exit_or_nan"]
    transition_df["wall_fraction"] = transition_df["boundary_contact_fraction_i"]
    transition_df["drag_dissipation"] = transition_df["Sigma_drag_i"]
    transition_df["scan_id"] = "reference_scale_baseline"
    transition_df["geometry_id"] = run_config.geometry_id
    transition_df["model_variant"] = run_config.model_variant

    output_root.mkdir(parents=True, exist_ok=True)
    table_paths = _write_table_with_optional_parquet(
        transition_df,
        output_root / "baseline_transition_stats.csv",
        output_root / "baseline_transition_stats.parquet",
    )
    scales = {
        "scan_id": "reference_scale_baseline",
        "geometry_id": run_config.geometry_id,
        "model_variant": run_config.model_variant,
        "ell_g": ell_g,
        "tau_g": tau_g,
        "tau_p": tau_p,
        "v0": run_config.v0,
        "Dr": run_config.Dr,
        "n_traj": result.n_traj,
        "n_success": result.n_success,
        "p_succ": result.p_succ,
        "config_hash": run_config.config_hash,
        "reference_config": run_config.to_dict(),
        "transition_stats": table_paths,
    }
    with open(output_root / "reference_scales.json", "w", encoding="ascii") as handle:
        json.dump(scales, handle, indent=2)
    scales["reference_scales_json"] = str(output_root / "reference_scales.json")
    return scales


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract reference scales using the legacy simcore adapter.")
    parser.add_argument("--output-root", type=Path, help="Override output directory for reference scales.")
    parser.add_argument("--n-traj", type=int, default=64, help="Trajectories for the baseline reference run.")
    parser.add_argument("--tmax", type=float, default=20.0, help="Maximum simulation time.")
    args = parser.parse_args(argv)

    config = build_reference_run_config(n_traj=args.n_traj, Tmax=args.tmax)
    result = extract_reference_scales(PROJECT_ROOT, config=config, output_root=args.output_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
