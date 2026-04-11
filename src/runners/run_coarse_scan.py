from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from src.configs.schema import RunConfig, SweepTask


def _variant_parameters(model_variant: str, base_gamma0: float) -> tuple[float, float]:
    if model_variant == "full":
        return 4.0 * base_gamma0, 3.0
    if model_variant == "no_memory":
        return 0.0, 3.0
    if model_variant == "no_feedback":
        return 4.0 * base_gamma0, 0.0
    if model_variant == "no_flow":
        return 4.0 * base_gamma0, 3.0
    raise ValueError(f"Unsupported coarse scan variant: {model_variant}")


def _lhs_linear(low: float, high: float, n: int, rng: np.random.Generator) -> np.ndarray:
    bins = (np.arange(n, dtype=float) + rng.random(n)) / n
    rng.shuffle(bins)
    return low + (high - low) * bins


def _lhs_log10(low: float, high: float, n: int, rng: np.random.Generator) -> np.ndarray:
    log_values = _lhs_linear(math.log10(low), math.log10(high), n, rng)
    return np.power(10.0, log_values)


def build_coarse_scan_configs(
    *,
    num_points: int = 24,
    model_variants: tuple[str, ...] = ("full",),
    base_seed: int = 20260411,
    geometry_id: str = "maze_v1",
    n_traj: int = 256,
    Tmax: float = 20.0,
    grid_n: int = 257,
    n_shell: int = 1,
) -> tuple[RunConfig, ...]:
    rng = np.random.default_rng(base_seed)
    Dr_values = _lhs_log10(0.2, 2.0, num_points, rng)
    tau_v_values = _lhs_log10(1e-2, 1e2, num_points, rng)
    tau_f_values = _lhs_log10(1e-2, 1e2, num_points, rng)
    U_values = _lhs_linear(-0.75, 0.75, num_points, rng)

    configs: list[RunConfig] = []
    config_index = 0
    for model_variant in model_variants:
        for point_index in range(num_points):
            gamma1, kf = _variant_parameters(model_variant, base_gamma0=1.0)
            U = float(U_values[point_index])
            if model_variant == "no_flow":
                U = 0.0
            configs.append(
                RunConfig(
                    geometry_id=geometry_id,
                    model_variant=model_variant,
                    v0=0.5,
                    Dr=float(Dr_values[point_index]),
                    tau_v=float(tau_v_values[point_index]),
                    gamma0=1.0,
                    gamma1=gamma1,
                    tau_f=float(tau_f_values[point_index]),
                    U=U,
                    wall_thickness=0.04,
                    gate_width=0.08,
                    dt=0.0025,
                    Tmax=Tmax,
                    n_traj=n_traj,
                    seed=base_seed + config_index,
                    exit_radius=0.06,
                    n_shell=n_shell,
                    grid_n=grid_n,
                    kf=kf,
                    metadata={
                        "L": 1.0,
                        "workflow_stage": "coarse_scan_generation",
                        "state_point_index": point_index,
                    },
                )
            )
            config_index += 1
    return tuple(configs)


def generate_coarse_scan_tasks(
    *,
    num_points: int = 24,
    batch_size: int = 8,
    model_variants: tuple[str, ...] = ("full",),
    base_seed: int = 20260411,
) -> tuple[SweepTask, ...]:
    configs = build_coarse_scan_configs(
        num_points=num_points,
        model_variants=model_variants,
        base_seed=base_seed,
    )
    tasks: list[SweepTask] = []
    for batch_index, offset in enumerate(range(0, len(configs), batch_size)):
        batch = configs[offset : offset + batch_size]
        tasks.append(
            SweepTask(
                task_id=f"coarse_scan_batch_{batch_index:03d}",
                phase="coarse_scan",
                batch_index=batch_index,
                config_list=batch,
                metadata={
                    "batch_size": len(batch),
                    "model_variants": list(model_variants),
                    "base_seed": base_seed,
                },
            )
        )
    return tuple(tasks)


def write_coarse_scan_manifest(
    project_root: str | Path,
    *,
    tasks: tuple[SweepTask, ...] | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    output_root = Path(output_root) if output_root is not None else project_root / "outputs" / "runs" / "coarse_scan"
    task_list = tasks or generate_coarse_scan_tasks()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / "task_manifest.json"
    payload = {"phase": "coarse_scan", "n_tasks": len(task_list), "tasks": [task.to_dict() for task in task_list]}
    with open(manifest_path, "w", encoding="ascii") as handle:
        json.dump(payload, handle, indent=2)
    return {"manifest_path": str(manifest_path), "n_tasks": len(task_list), "tasks": task_list}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate coarse scan tasks compatible with the legacy adapter.")
    parser.add_argument("--output-root", type=Path, help="Override manifest output directory.")
    parser.add_argument("--num-points", type=int, default=24, help="State points per model variant.")
    parser.add_argument("--batch-size", type=int, default=8, help="Configs per coarse scan task.")
    args = parser.parse_args(argv)

    tasks = generate_coarse_scan_tasks(num_points=args.num_points, batch_size=args.batch_size)
    result = write_coarse_scan_manifest(PROJECT_ROOT, tasks=tasks, output_root=args.output_root)
    print(json.dumps({"manifest_path": result["manifest_path"], "n_tasks": result["n_tasks"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
