from __future__ import annotations

import pandas as pd

from src.configs.schema import RunConfig
from src.runners.run_mechanism_dataset import add_event_alignment_columns, build_gate_descriptors, build_thresholds
from src.runners.run_mechanism_dataset_refined import build_refined_thresholds


def build_config() -> RunConfig:
    return RunConfig(
        geometry_id="maze_v1",
        model_variant="full",
        v0=0.5,
        Dr=1.0,
        tau_v=1.0,
        gamma0=1.0,
        gamma1=4.0,
        tau_f=0.15,
        U=0.1,
        wall_thickness=0.04,
        gate_width=0.08,
        dt=0.0025,
        Tmax=30.0,
        n_traj=16,
        seed=123,
        exit_radius=0.06,
        n_shell=1,
        grid_n=257,
        kf=3.0,
        metadata={"L": 1.0},
    )


def test_build_gate_descriptors_matches_single_shell_left_gate() -> None:
    config = build_config()

    gates = build_gate_descriptors(config)

    assert len(gates) == 1
    gate = gates[0]
    assert gate.gate_id == 0
    assert gate.side == "left"
    assert gate.center_x == -0.3
    assert gate.center_y == 0.0
    assert gate.normal_x == 1.0
    assert gate.tangent_y == 1.0


def test_build_thresholds_tracks_geometry_and_reference_scale() -> None:
    config = build_config()

    thresholds = build_thresholds(config, {"tau_p": 1.0, "tau_g": 7.0, "ell_g": 3.5})

    assert thresholds.wall_contact_distance == 0.04
    assert thresholds.gate_lane_half_width == 0.06
    assert thresholds.gate_capture_depth == 0.02
    assert thresholds.trap_progress_window == 0.25
    assert thresholds.trap_min_duration == 0.5


def test_add_event_alignment_columns_backshifts_trap_rows_only() -> None:
    event_df = pd.DataFrame(
        {
            "event_type": ["bulk_motion", "trap_episode"],
            "t_start": [1.0, 2.0],
            "duration": [0.25, 0.015],
        }
    )

    aligned = add_event_alignment_columns(event_df, dt=0.0025, trap_min_duration=0.5)

    assert aligned.loc[0, "t_start_aligned"] == 1.0
    assert aligned.loc[0, "duration_aligned"] == 0.25
    assert aligned.loc[0, "trap_confirmation_backshift"] == 0.0
    assert aligned.loc[1, "trap_confirmation_backshift"] == 0.4975
    assert aligned.loc[1, "t_start_aligned"] == 1.5025
    assert aligned.loc[1, "duration_aligned"] == 0.5125


def test_build_refined_thresholds_narrows_commit_band() -> None:
    config = build_config()

    thresholds = build_refined_thresholds(config, {"tau_p": 1.0, "tau_g": 7.0, "ell_g": 3.5})

    assert thresholds.gate_commit_lane_half_width < thresholds.gate_lane_half_width
    assert thresholds.gate_residence_depth < thresholds.gate_approach_depth
    assert thresholds.gate_commit_progress_min > thresholds.gate_progress_min
    assert thresholds.gate_commit_alignment_min > 0.3
