from __future__ import annotations

import argparse
import os
from pathlib import Path

from .catalog import TaskCatalog
from .models import RuntimePaths, TaskOverride
from .simulation import SimulationTaskRunner


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run production-style viscoelastic maze simulation tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available simulation tasks.")
    list_parser.add_argument("--verbose", action="store_true", help="Show task notes and point counts.")

    run_parser = subparsers.add_parser("run", help="Run one named simulation task.")
    run_parser.add_argument("task_id", help="Task identifier from the task catalog.")
    run_parser.add_argument("--run-id", help="Override the task run id.")
    run_parser.add_argument("--point-limit", type=int, help="Only run the first N points.")
    run_parser.add_argument("--n-traj", type=int, help="Override trajectories per point.")
    run_parser.add_argument("--tmax", type=float, help="Override Tmax.")
    run_parser.add_argument("--n-shell", type=int, help="Override the number of maze shells.")
    run_parser.add_argument("--grid-n", type=int, help="Override the maze grid resolution.")
    run_parser.add_argument("--seed", type=int, help="Override the base RNG seed.")
    run_parser.add_argument("--bootstrap-resamples", type=int, help="Override bootstrap resamples.")
    run_parser.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing run directory.")
    return parser


def build_override_from_args(args: argparse.Namespace) -> TaskOverride:
    return TaskOverride(
        run_id=args.run_id,
        point_limit=args.point_limit,
        n_traj=args.n_traj,
        Tmax=args.tmax,
        n_shell=args.n_shell,
        grid_n=args.grid_n,
        seed=args.seed,
        bootstrap_resamples=args.bootstrap_resamples,
        overwrite=args.overwrite,
    )


def list_tasks(verbose: bool = False) -> int:
    catalog = TaskCatalog(PROJECT_ROOT)
    for task in catalog.list_tasks():
        print(f"{task.task_id}: {task.description}")
        if verbose:
            print(f"  run_id={task.run_id} points={len(task.points)} grid={task.geometry.grid_n} n_shell={task.geometry.n_shell}")
            if task.notes:
                print(f"  notes={task.notes}")
    return 0


def run_task(task_id: str, override: TaskOverride | None = None, *, paths: RuntimePaths | None = None) -> int:
    catalog = TaskCatalog(PROJECT_ROOT)
    task = catalog.get(task_id)
    effective_task = override.apply(task) if override else task
    runner = SimulationTaskRunner(paths or RuntimePaths.default(PROJECT_ROOT))
    result = runner.run(effective_task, overwrite=override.overwrite if override else False)
    print(f"Completed task {effective_task.task_id}")
    print(f"Run id: {effective_task.run_id}")
    print(f"Summary CSV: {result.artifact_paths['summary_csv']}")
    if result.detectability is not None:
        print(f"Detectability: {result.detectability}")
    return 0


def legacy_env_main(task_id: str) -> int:
    override = TaskOverride(
        point_limit=_optional_int("PILOT_POINT_LIMIT"),
        n_traj=_optional_int("PILOT_N_TRAJ"),
        Tmax=_optional_float("PILOT_TMAX"),
        n_shell=_optional_int("PILOT_N_SHELL"),
        grid_n=_optional_int("PILOT_GRID_N"),
        seed=_optional_int("PILOT_SEED"),
        bootstrap_resamples=_optional_int("PILOT_BOOTSTRAP_RESAMPLES"),
        overwrite=_optional_bool("PILOT_OVERWRITE"),
    )
    return run_task(task_id, override=override)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        return list_tasks(verbose=args.verbose)
    if args.command == "run":
        return run_task(args.task_id, override=build_override_from_args(args))
    raise ValueError(f"Unsupported command {args.command}")


def _optional_int(key: str) -> int | None:
    value = os.getenv(key)
    return None if value is None else int(value)


def _optional_float(key: str) -> float | None:
    value = os.getenv(key)
    return None if value is None else float(value)


def _optional_bool(key: str) -> bool:
    value = os.getenv(key)
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}
