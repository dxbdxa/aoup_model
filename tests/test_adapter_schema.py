from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from legacy.simcore.models import DynamicsConfig, GeometryConfig, SimulationTask, SweepPoint
from src.adapters.catalog_bridge import CatalogBridge
from src.adapters.legacy_simcore_adapter import LegacySimcoreAdapter, legacy_task_point_to_run_config
from src.configs.schema import RunConfig, RunResult
from src.utils.workflow_schema import normalize_persisted_artifact_payload


def make_run_config() -> RunConfig:
    return RunConfig(
        geometry_id="maze_v1",
        model_variant="full",
        v0=0.5,
        Dr=1.0,
        tau_v=0.5,
        gamma0=1.0,
        gamma1=4.0,
        tau_f=0.25,
        U=0.125,
        wall_thickness=0.04,
        gate_width=0.08,
        dt=0.0025,
        Tmax=20.0,
        n_traj=16,
        seed=123,
        metadata={"L": 1.0},
    )


def test_run_config_round_trip_and_hash_is_stable() -> None:
    config = make_run_config()
    payload = config.to_dict()
    rebuilt = RunConfig.from_dict(payload)

    assert rebuilt == config
    assert rebuilt.config_hash == config.config_hash
    assert len(config.config_hash) == 64
    assert payload["config_hash"] == config.config_hash
    assert payload["flow_condition"] == "with_flow"


def test_adapter_builds_legacy_components_without_changing_physics_files() -> None:
    adapter = LegacySimcoreAdapter("/home/zhuguolong/aoup_model")
    config = make_run_config()

    geometry = adapter.build_geometry_config(config)
    dynamics = adapter.build_dynamics_config(config)
    point = adapter.build_sweep_point(config)
    task = adapter.build_simulation_task(config)

    assert geometry.w == config.wall_thickness
    assert geometry.g == config.gate_width
    assert dynamics.gamma1_over_gamma0 == 4.0
    assert point.control_label == "coupled_baseline"
    assert task.points[0].sweep_id.startswith(config.geometry_id)


def test_summary_to_result_normalizes_legacy_fields() -> None:
    adapter = LegacySimcoreAdapter("/home/zhuguolong/aoup_model")
    config = make_run_config()
    summary = {
        "Psucc": 0.5,
        "Psucc_ci_low": 0.3,
        "Psucc_ci_high": 0.7,
        "MFPT_success_only": 3.0,
        "MFPT_ci_low": 2.5,
        "MFPT_ci_high": 3.5,
        "J_proxy_ci_low": 0.01,
        "J_proxy_ci_high": 0.04,
        "sigma_drag": 0.2,
        "sigma_drag_ci_low": 0.15,
        "sigma_drag_ci_high": 0.25,
        "eta_sigma": 0.8,
        "eta_sigma_ci_low": 0.6,
        "eta_sigma_ci_high": 1.0,
        "mean_trap_residence": 1.5,
        "boundary_contact_fraction": 0.25,
        "n_traj": 4,
        "n_success": 2,
    }
    traj_df = pd.DataFrame({"t_exit_or_nan": [2.0, 4.0, float("nan"), float("nan")]})
    trap_df = pd.DataFrame({"traj_id": [0, 0, 1], "trap_duration": [1.0, 2.0, 1.5]})

    result = adapter.summary_to_result(
        config,
        summary,
        traj_df=traj_df,
        trap_df=trap_df,
        artifact_paths={"summary_csv": "outputs/runs/example.csv"},
    )

    assert result.p_succ == 0.5
    assert result.mfpt_median == 3.0
    assert result.mfpt_q90 == 3.8
    assert result.trap_count_mean == 1.5
    assert result.raw_summary_path == "outputs/runs/example.csv"


def test_legacy_task_point_to_run_config_preserves_legacy_metadata() -> None:
    legacy_task = SimulationTask(
        task_id="stub_task",
        description="stub",
        mode="startup_matrix_block",
        run_id="stub_run",
        geometry=GeometryConfig(n_shell=2, grid_n=128),
        dynamics=DynamicsConfig(n_traj=10, Tmax=12.0, seed=77),
        points=(
            SweepPoint(
                sweep_id="p0",
                figure_group="fig2_flow_competition",
                control_label="no_feedback",
                tau_v=0.5,
                tau_f=0.25,
                U=0.125,
                gamma1_over_gamma0=4.0,
                kf=0.0,
            ),
        ),
        notes="legacy",
    )

    config = legacy_task_point_to_run_config(legacy_task, legacy_task.points[0])

    assert config.model_variant == "no_feedback"
    assert config.gamma1 == 4.0
    assert config.metadata["legacy_control_label"] == "no_feedback"
    assert config.metadata["legacy_task_id"] == "stub_task"


def test_catalog_bridge_translates_manual_legacy_task_to_sweep_task() -> None:
    legacy_task = SimulationTask(
        task_id="stub_task",
        description="stub",
        mode="adapter_stub",
        run_id="stub_run",
        geometry=GeometryConfig(),
        dynamics=DynamicsConfig(),
        points=(
            SweepPoint(
                sweep_id="p0",
                figure_group="adapter_stub",
                control_label="coupled_baseline",
                tau_v=0.5,
                tau_f=0.25,
                U=0.125,
                gamma1_over_gamma0=4.0,
                kf=3.0,
            ),
        ),
        notes="legacy",
    )

    sweep_task = CatalogBridge.legacy_task_to_sweep_task(legacy_task)
    payload = sweep_task.to_dict()

    assert sweep_task.task_id == "stub_task"
    assert len(sweep_task.config_list) == 1
    assert payload["config_list"][0]["model_variant"] == "full"
    assert json.loads(json.dumps(payload))["metadata"]["legacy_run_id"] == "stub_run"


def test_model_variant_compatibility_reads_old_and_new_payloads() -> None:
    old_payload = {
        "geometry_id": "maze_v1",
        "model_variant": "no_flow",
        "v0": 0.5,
        "Dr": 1.0,
        "tau_v": 0.5,
        "gamma0": 1.0,
        "gamma1": 4.0,
        "tau_f": 0.25,
        "U": 0.0,
        "wall_thickness": 0.04,
        "gate_width": 0.08,
        "dt": 0.0025,
        "Tmax": 20.0,
        "n_traj": 16,
        "seed": 123,
        "metadata": {"L": 1.0},
    }
    new_payload = {
        **old_payload,
        "model_variant": "full",
        "flow_condition": "explicit_no_flow_control",
        "legacy_model_variant": "no_flow",
    }

    old_config = RunConfig.from_dict(old_payload)
    new_config = RunConfig.from_dict(new_payload)
    normalized_row = normalize_persisted_artifact_payload({"model_variant": "no_flow", "U": 0.0})
    old_result = RunResult.from_dict(
        {
            "run_id": "r1",
            "config_hash": "abc",
            "geometry_id": "maze_v1",
            "model_variant": "no_flow",
            "p_succ": 0.1,
            "mfpt_mean": None,
            "mfpt_median": None,
            "mfpt_q90": None,
            "sigma_drag_mean": None,
            "eta_sigma": None,
            "trap_time_mean": None,
            "trap_count_mean": None,
            "wall_fraction_mean": None,
            "revisit_rate_mean": None,
            "n_traj": 4,
            "n_success": 0,
            "ci": {},
            "raw_summary_path": None,
            "metadata": {},
            "U": 0.0,
        }
    )

    assert old_config.model_variant == "full"
    assert old_config.flow_condition == "explicit_no_flow_control"
    assert old_config.legacy_model_variant == "no_flow"
    assert new_config.model_variant == "full"
    assert new_config.flow_condition == "explicit_no_flow_control"
    assert normalized_row["model_variant"] == "full"
    assert normalized_row["flow_condition"] == "explicit_no_flow_control"
    assert old_result.model_variant == "full"
    assert old_result.flow_condition == "explicit_no_flow_control"
