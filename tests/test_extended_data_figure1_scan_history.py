from __future__ import annotations

import pandas as pd

from src.runners.run_extended_data_figure1_scan_history import (
    add_stage_screening_score,
    stage_sampling_label,
    stage_window,
)


def test_add_stage_screening_score_stays_bounded_and_orders_extremes() -> None:
    df = pd.DataFrame(
        [
            {"Pi_m": 0.1, "Pi_f": 0.02, "Pi_U": 0.1, "Psucc_mean": 0.90, "eta_sigma_mean": 5.0, "MFPT_mean": 4.0, "n_traj": 1024},
            {"Pi_m": 0.2, "Pi_f": 0.02, "Pi_U": 0.2, "Psucc_mean": 0.95, "eta_sigma_mean": 6.0, "MFPT_mean": 3.0, "n_traj": 1024},
            {"Pi_m": 0.3, "Pi_f": 0.03, "Pi_U": 0.3, "Psucc_mean": 0.80, "eta_sigma_mean": 4.0, "MFPT_mean": 6.0, "n_traj": 1024},
        ]
    )

    scored = add_stage_screening_score(df)

    assert scored["search_score"].between(0.0, 1.0).all()
    assert scored.loc[1, "search_score"] > scored.loc[0, "search_score"]
    assert scored.loc[0, "search_score"] > scored.loc[2, "search_score"]


def test_stage_sampling_label_formats_constant_and_range_counts() -> None:
    constant_df = pd.DataFrame({"n_traj": [512, 512, 512]})
    range_df = pd.DataFrame({"n_traj": [2048, 4096, 2048]})

    assert stage_sampling_label(constant_df) == "3 points | 512 traj/point"
    assert stage_sampling_label(range_df) == "3 points | 2048-4096 traj/point"


def test_stage_window_returns_expected_bounds() -> None:
    df = pd.DataFrame(
        [
            {"Pi_m": 0.05, "Pi_f": 0.025},
            {"Pi_m": 0.20, "Pi_f": 0.020},
            {"Pi_m": 0.10, "Pi_f": 0.030},
        ]
    )

    bounds = stage_window(df)

    assert bounds == {"xmin": 0.05, "xmax": 0.2, "ymin": 0.02, "ymax": 0.03}
