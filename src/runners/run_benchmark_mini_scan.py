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


def _variant_parameters(model_variant: str) -> tuple[float, float]:
    if model_variant == "full":
        return 4.0, 3.0
    if model_variant == "no_memory":
        return 0.0, 3.0
    if model_variant == "no_feedback":
        return 4.0, 0.0
    raise ValueError(f"Unsupported benchmark mini-scan variant: {model_variant}")


def build_benchmark_mini_scan_configs(
    *,
    geometry_id: str = "maze_v1",
    variants: tuple[str, ...] = ("full", "no_memory", "no_feedback"),
    Dr_values: tuple[float, ...] = (2.0, 1.0, 0.5),
    tau_v_values: tuple[float, ...] = (0.25, 0.5, 1.0),
    tau_f_values: tuple[float, ...] = (0.125, 0.25, 0.5),
    U_values: tuple[float, ...] = (0.0, 0.125, 0.25),
    base_seed: int = 20260411,
    n_traj: int = 64,
    Tmax: float = 20.0,
    grid_n: int = 257,
    n_shell: int = 1,
) -> tuple[RunConfig, ...]:
    if not (len(Dr_values) == len(tau_v_values) == len(tau_f_values) == len(U_values)):
        raise ValueError("Mini-scan control tuples must have matching lengths.")

    configs: list[RunConfig] = []
    point_index = 0
    for variant in variants:
        gamma1, kf = _variant_parameters(variant)
        for Dr, tau_v, tau_f, U in zip(Dr_values, tau_v_values, tau_f_values, U_values):
            configs.append(
                RunConfig(
                    geometry_id=geometry_id,
                    model_variant=variant,
                    v0=0.5,
                    Dr=Dr,
                    tau_v=tau_v,
                    gamma0=1.0,
                    gamma1=gamma1,
                    tau_f=tau_f,
                    U=U,
                    wall_thickness=0.04,
                    gate_width=0.08,
                    dt=0.0025,
                    Tmax=Tmax,
                    n_traj=n_traj,
                    seed=base_seed + point_index,
                    exit_radius=0.06,
                    n_shell=n_shell,
                    grid_n=grid_n,
                    kf=kf,
                    metadata={
                        "L": 1.0,
                        "workflow_stage": "benchmark_mini_scan",
                        "state_point_index": point_index,
                    },
                )
            )
            point_index += 1
    return tuple(configs)


def run_benchmark_mini_scan(
    project_root: str | Path,
    *,
    configs: tuple[RunConfig, ...] | None = None,
    output_root: str | Path | None = None,
    max_configs: int | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs" / "summaries" / "benchmark_mini_scan"
    scan_configs = configs or build_benchmark_mini_scan_configs()
    if max_configs is not None:
        scan_configs = scan_configs[:max_configs]

    adapter = LegacySimcoreAdapter(project_root)
    rows: list[dict[str, Any]] = []
    for config in scan_configs:
        result = adapter.run_config(config)
        row = result.to_dict()
        row["seed"] = config.seed
        row["tau_v"] = config.tau_v
        row["tau_f"] = config.tau_f
        row["U"] = config.U
        row["Dr"] = config.Dr
        row["v0"] = config.v0
        rows.append(row)

    summary_df = pd.DataFrame(rows)
    output_root.mkdir(parents=True, exist_ok=True)
    summary_csv = output_root / "summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    metadata = {
        "scan_id": "benchmark_mini_scan",
        "n_configs": len(scan_configs),
        "summary_csv": str(summary_csv),
        "model_variants": sorted({config.model_variant for config in scan_configs}),
        "geometry_ids": sorted({config.geometry_id for config in scan_configs}),
    }
    with open(output_root / "metadata.json", "w", encoding="ascii") as handle:
        json.dump(metadata, handle, indent=2)
    metadata["metadata_json"] = str(output_root / "metadata.json")
    return {"summary_df": summary_df, "metadata": metadata}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a benchmark mini-scan through the legacy simcore adapter.")
    parser.add_argument("--output-root", type=Path, help="Override output directory.")
    parser.add_argument("--max-configs", type=int, help="Only run the first N mini-scan configurations.")
    parser.add_argument("--n-traj", type=int, default=64, help="Trajectories per mini-scan point.")
    args = parser.parse_args(argv)

    configs = build_benchmark_mini_scan_configs(n_traj=args.n_traj)
    result = run_benchmark_mini_scan(PROJECT_ROOT, configs=configs, output_root=args.output_root, max_configs=args.max_configs)
    print(json.dumps(result["metadata"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
