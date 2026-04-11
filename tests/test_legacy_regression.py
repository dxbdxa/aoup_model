from __future__ import annotations

import math
from pathlib import Path
import sys

import pandas as pd
import pandas.testing as pdt
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from legacy.simcore.models import DynamicsConfig, GeometryConfig, SweepPoint
from legacy.simcore.simulation import MazeBuilder, NavigationSolver, PointSimulator
from src.adapters.legacy_simcore_adapter import LegacySimcoreAdapter
from src.configs.schema import RunConfig


def _small_baseline_cases() -> list[RunConfig]:
    common = {
        "geometry_id": "maze_regression_small",
        "v0": 0.5,
        "Dr": 1.0,
        "gamma0": 1.0,
        "wall_thickness": 0.04,
        "gate_width": 0.08,
        "dt": 0.005,
        "Tmax": 6.0,
        "n_traj": 8,
        "exit_radius": 0.06,
        "n_shell": 1,
        "grid_n": 65,
        "bootstrap_resamples": 64,
        "metadata": {"L": 1.0},
    }
    return [
        RunConfig(
            **common,
            model_variant="full",
            tau_v=0.25,
            gamma1=4.0,
            tau_f=0.125,
            U=0.0,
            kf=3.0,
            seed=1101,
            flow_condition="explicit_no_flow_control",
            legacy_model_variant="no_flow",
        ),
        RunConfig(
            **common,
            model_variant="no_memory",
            tau_v=0.25,
            gamma1=0.0,
            tau_f=0.125,
            U=0.125,
            kf=3.0,
            seed=1102,
        ),
        RunConfig(
            **common,
            model_variant="no_feedback",
            tau_v=0.25,
            gamma1=4.0,
            tau_f=0.125,
            U=0.125,
            kf=0.0,
            seed=1103,
        ),
        RunConfig(
            **common,
            model_variant="full",
            tau_v=0.5,
            gamma1=4.0,
            tau_f=0.25,
            U=0.125,
            kf=3.0,
            seed=1104,
        ),
        RunConfig(
            **common,
            model_variant="full",
            tau_v=0.5,
            gamma1=4.0,
            tau_f=0.5,
            U=0.5,
            kf=3.0,
            seed=1105,
        ),
    ]


def _direct_control_label(config: RunConfig) -> str:
    if config.flow_condition == "explicit_no_flow_control":
        return "no_flow"
    labels = {
        "full": "coupled_baseline",
        "no_memory": "no_memory",
        "no_feedback": "no_feedback",
    }
    return labels[config.model_variant]


def _direct_legacy_run(config: RunConfig) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    geometry = GeometryConfig(
        L=float(config.metadata.get("L", 1.0)),
        w=config.wall_thickness,
        g=config.gate_width,
        r_exit=config.exit_radius,
        n_shell=config.n_shell,
        grid_n=config.grid_n,
    )
    dynamics = DynamicsConfig(
        gamma0=config.gamma0,
        gamma1_over_gamma0=(config.gamma1 / config.gamma0) if config.gamma0 != 0.0 else 0.0,
        Dr=config.Dr,
        v0=config.v0,
        kf=config.kf,
        kBT=config.kBT,
        dt=config.dt,
        Tmax=config.Tmax,
        eps_psi=config.eps_psi,
        bootstrap_resamples=config.bootstrap_resamples,
        n_traj=config.n_traj,
        seed=config.seed,
    )
    point = SweepPoint(
        sweep_id=f"{config.geometry_id}_{config.model_variant}_{config.config_hash[:8]}",
        figure_group="adapter_stub",
        control_label=_direct_control_label(config),
        tau_v=config.tau_v,
        tau_f=config.tau_f,
        U=config.U,
        gamma1_over_gamma0=(config.gamma1 / config.gamma0) if config.gamma0 != 0.0 else 0.0,
        kf=config.kf,
    )
    maze = MazeBuilder().build(geometry)
    navigation = NavigationSolver().solve(maze)
    simulator = PointSimulator(maze, navigation)
    return simulator.run(point, dynamics, point_seed=config.seed)


def _assert_summary_matches(expected: dict[str, object], actual: dict[str, object]) -> None:
    assert set(actual) == set(expected)
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, float):
            if math.isnan(expected_value):
                assert isinstance(actual_value, float) and math.isnan(actual_value), key
            else:
                assert actual_value == pytest.approx(expected_value), key
        else:
            assert actual_value == expected_value, key


def _direct_metrics(traj_df: pd.DataFrame, trap_df: pd.DataFrame) -> dict[str, float | None]:
    finite_exit = traj_df["t_exit_or_nan"].dropna()
    if trap_df.empty:
        trap_count_mean = 0.0
    else:
        trap_count_mean = float(trap_df.groupby("traj_id").size().mean())
    return {
        "mfpt_median": float(finite_exit.median()) if not finite_exit.empty else None,
        "mfpt_q90": float(finite_exit.quantile(0.9)) if not finite_exit.empty else None,
        "trap_count_mean": trap_count_mean,
    }


BASELINE_CASES = _small_baseline_cases()


@pytest.mark.parametrize("config", BASELINE_CASES, ids=[cfg.model_variant + "_" + str(index) for index, cfg in enumerate(BASELINE_CASES)])
def test_adapter_run_point_matches_direct_legacy_run(config: RunConfig) -> None:
    adapter = LegacySimcoreAdapter(PROJECT_ROOT)

    direct_summary, direct_traj, direct_trap = _direct_legacy_run(config)
    adapter_summary, adapter_traj, adapter_trap = adapter.run_point(config)

    _assert_summary_matches(direct_summary, adapter_summary)
    pdt.assert_frame_equal(direct_traj, adapter_traj)
    pdt.assert_frame_equal(direct_trap, adapter_trap)


@pytest.mark.parametrize(
    "config",
    BASELINE_CASES,
    ids=[cfg.model_variant + "_result_" + str(index) for index, cfg in enumerate(BASELINE_CASES)],
)
def test_adapter_run_config_matches_direct_legacy_metrics(config: RunConfig) -> None:
    adapter = LegacySimcoreAdapter(PROJECT_ROOT)

    direct_summary, direct_traj, direct_trap = _direct_legacy_run(config)
    direct_metrics = _direct_metrics(direct_traj, direct_trap)
    result = adapter.run_config(config)

    assert abs(result.p_succ - float(direct_summary["Psucc"])) < 0.02
    assert result.n_traj == int(direct_summary["n_traj"])
    assert result.n_success == int(direct_summary["n_success"])
    assert result.sigma_drag_mean == pytest.approx(float(direct_summary["sigma_drag"]))
    assert result.wall_fraction_mean == pytest.approx(float(direct_summary["boundary_contact_fraction"]))
    assert result.trap_time_mean == pytest.approx(float(direct_summary["mean_trap_residence"]))
    assert result.trap_count_mean == pytest.approx(direct_metrics["trap_count_mean"])

    expected_mfpt = direct_summary["MFPT_success_only"]
    if isinstance(expected_mfpt, float) and math.isnan(expected_mfpt):
        assert result.mfpt_mean is None
        assert result.mfpt_median is None
        assert result.mfpt_q90 is None
    else:
        assert result.mfpt_mean == pytest.approx(float(expected_mfpt), rel=0.05)
        assert result.mfpt_median == pytest.approx(direct_metrics["mfpt_median"])
        assert result.mfpt_q90 == pytest.approx(direct_metrics["mfpt_q90"])

    expected_eta = float(direct_summary["eta_sigma"])
    if math.isnan(expected_eta):
        assert result.eta_sigma is None
    else:
        assert result.eta_sigma == pytest.approx(expected_eta, rel=0.10)
