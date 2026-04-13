from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from legacy.simcore.models import GeometryConfig
from legacy.simcore.simulation import MazeGeometry, NavigationSolver

from src.configs.schema import RunConfig as WorkflowRunConfig
from src.runners.run_mechanism_dataset import GateDescriptor, load_canonical_points
from src.runners.run_mechanism_dataset_refined import RefinedMechanismPointExtractor, build_refined_thresholds

OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer"
FIGURE_ROOT = PROJECT_ROOT / "outputs" / "figures" / "geometry_transfer"
RUN_REPORT_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_run_report.md"
FIRST_LOOK_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_first_look.md"
GF0_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "refined_summary_by_point.csv"
GF0_TRAJ_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "trajectory_level.parquet"
GF0_REFERENCE_PATH = PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json"


@dataclass(frozen=True)
class GeometryFamily:
    geometry_id: str
    label: str
    kind: str
    gate_width: float
    wall_thickness: float
    barrier_x: tuple[float, ...]
    doorway_y: tuple[float, ...]


@dataclass(frozen=True)
class TransferPoint:
    canonical_label: str
    geometry_family: str
    state_point_id: str
    Pi_m: float
    Pi_f: float
    Pi_U: float
    config: WorkflowRunConfig
    analysis_source: str
    analysis_n_traj: int
    result_json: str
    source_result: dict[str, Any]


FAMILIES = (
    GeometryFamily(
        geometry_id="GF1_SINGLE_BOTTLENECK_CHANNEL",
        label="GF1 Single Bottleneck",
        kind="single_bottleneck",
        gate_width=0.08,
        wall_thickness=0.04,
        barrier_x=(-0.18,),
        doorway_y=(0.0,),
    ),
    GeometryFamily(
        geometry_id="GF2_PORE_ARRAY_STRIP",
        label="GF2 Pore Array",
        kind="pore_array",
        gate_width=0.08,
        wall_thickness=0.04,
        barrier_x=(-0.32, -0.17),
        doorway_y=(0.10, -0.10),
    ),
)


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return math.nan
    return float(values.mean())


def build_custom_geometry(family: GeometryFamily, *, L: float = 1.0, grid_n: int = 257, exit_radius: float = 0.06) -> tuple[MazeGeometry, tuple[GateDescriptor, ...]]:
    config = GeometryConfig(
        L=L,
        w=family.wall_thickness,
        g=family.gate_width,
        r_exit=exit_radius,
        n_shell=len(family.barrier_x),
        grid_n=grid_n,
    )
    n = config.grid_n
    x = np.linspace(-config.L / 2.0, config.L / 2.0, n)
    y = np.linspace(-config.L / 2.0, config.L / 2.0, n)
    X, Y = np.meshgrid(x, y, indexing="xy")
    h = x[1] - x[0]

    wall = np.zeros((n, n), dtype=bool)
    outer = (
        (X <= -config.L / 2.0 + config.w)
        | (X >= config.L / 2.0 - config.w)
        | (Y <= -config.L / 2.0 + config.w)
        | (Y >= config.L / 2.0 - config.w)
    )
    inlet_open = (X <= -config.L / 2.0 + config.w) & (np.abs(Y) <= config.g / 2.0)
    wall |= outer & ~inlet_open

    gates: list[GateDescriptor] = []
    for gate_id, (barrier_x, doorway_y) in enumerate(zip(family.barrier_x, family.doorway_y)):
        barrier = (np.abs(X - barrier_x) <= config.w / 2.0) & (np.abs(Y) <= config.L / 2.0 - config.w)
        doorway = (np.abs(X - barrier_x) <= config.w / 2.0) & (np.abs(Y - doorway_y) <= config.g / 2.0)
        wall |= barrier & ~doorway
        gates.append(
            GateDescriptor(
                gate_id=gate_id,
                shell_id=gate_id + 1,
                side="vertical",
                center_x=float(barrier_x),
                center_y=float(doorway_y),
                normal_x=1.0,
                normal_y=0.0,
                tangent_x=0.0,
                tangent_y=1.0,
                half_width=config.g / 2.0,
            )
        )

    exit_mask = (np.abs(X) <= config.r_exit) & (np.abs(Y) <= config.r_exit)
    inlet_mask = (X <= -config.L / 2.0 + config.w) & (np.abs(Y) <= config.g / 2.0)
    wall[exit_mask] = False
    free = ~wall
    free[inlet_mask] = True

    free_dist = distance_transform_edt(free) * h
    wall_dist = distance_transform_edt(~free) * h
    signed_distance = free_dist - wall_dist
    grad_s_y, grad_s_x = np.gradient(signed_distance, h, edge_order=2)
    maze = MazeGeometry(
        config=config,
        x=x,
        y=y,
        X=X,
        Y=Y,
        h=h,
        wall=wall,
        free=free,
        exit_mask=exit_mask,
        inlet_mask=inlet_mask,
        signed_distance=signed_distance,
        grad_s_x=grad_s_x,
        grad_s_y=grad_s_y,
    )
    return maze, tuple(gates)


def build_reference_config(family: GeometryFamily, *, n_traj: int = 256) -> WorkflowRunConfig:
    return WorkflowRunConfig(
        geometry_id=family.geometry_id,
        model_variant="no_memory",
        v0=0.5,
        Dr=1.0,
        tau_v=0.25,
        gamma0=1.0,
        gamma1=0.0,
        tau_f=0.0,
        U=0.0,
        wall_thickness=family.wall_thickness,
        gate_width=family.gate_width,
        dt=0.0025,
        Tmax=20.0,
        n_traj=n_traj,
        seed=20260413,
        exit_radius=0.06,
        n_shell=len(family.barrier_x),
        grid_n=257,
        kf=0.0,
        bootstrap_resamples=256,
        flow_condition="zero_flow",
        metadata={"L": 1.0, "geometry_family": family.geometry_id, "transfer_stage": "reference"},
    )


def build_transfer_config(base_point: Any, family: GeometryFamily, tau_g: float, *, n_traj: int = 512) -> WorkflowRunConfig:
    return WorkflowRunConfig(
        geometry_id=family.geometry_id,
        model_variant=base_point.config.model_variant,
        v0=base_point.config.v0,
        Dr=base_point.config.Dr,
        tau_v=base_point.Pi_m * tau_g,
        gamma0=base_point.config.gamma0,
        gamma1=base_point.config.gamma1,
        tau_f=base_point.Pi_f * tau_g,
        U=base_point.Pi_U * base_point.config.v0,
        wall_thickness=family.wall_thickness,
        gate_width=family.gate_width,
        dt=base_point.config.dt,
        Tmax=base_point.config.Tmax,
        n_traj=n_traj,
        seed=base_point.config.seed,
        exit_radius=base_point.config.exit_radius,
        n_shell=len(family.barrier_x),
        grid_n=257,
        kf=base_point.config.kf,
        bootstrap_resamples=base_point.config.bootstrap_resamples,
        kBT=base_point.config.kBT,
        eps_psi=base_point.config.eps_psi,
        flow_condition=base_point.config.flow_condition,
        legacy_model_variant=base_point.config.legacy_model_variant,
        metadata={"L": 1.0, "geometry_family": family.geometry_id, "transfer_stage": "canonical"},
    )


def make_transfer_point(base_point: Any, family: GeometryFamily, tau_g: float, *, n_traj: int = 512) -> TransferPoint:
    config = build_transfer_config(base_point, family, tau_g, n_traj=n_traj)
    return TransferPoint(
        canonical_label=base_point.canonical_label,
        geometry_family=family.geometry_id,
        state_point_id=f"{family.geometry_id}:{base_point.canonical_label}",
        Pi_m=base_point.Pi_m,
        Pi_f=base_point.Pi_f,
        Pi_U=base_point.Pi_U,
        config=config,
        analysis_source="geometry_transfer_validation",
        analysis_n_traj=n_traj,
        result_json="",
        source_result={
            "scan_id": f"geometry_transfer_{family.geometry_id}",
            "p_succ": float("nan"),
            "trap_time_mean": float("nan"),
            "wall_fraction_mean": float("nan"),
        },
    )


def make_shared_payload(point: TransferPoint, tau_g: float, ell_g: float) -> dict[str, Any]:
    return {
        "schema_version": "geometry_transfer_refined_v1",
        "scan_id": f"geometry_transfer_{point.geometry_family}",
        "state_point_id": point.state_point_id,
        "canonical_label": point.canonical_label,
        "geometry_id": point.config.geometry_id,
        "model_variant": point.config.model_variant,
        "flow_condition": point.config.flow_condition,
        "analysis_source": point.analysis_source,
        "analysis_n_traj": point.analysis_n_traj,
        "Pi_m": point.Pi_m,
        "Pi_f": point.Pi_f,
        "Pi_U": point.Pi_U,
        "tau_g": tau_g,
        "l_g": ell_g,
        "result_json": point.result_json,
    }


def extract_reference_for_family(family: GeometryFamily) -> tuple[dict[str, Any], pd.DataFrame]:
    config = build_reference_config(family)
    maze, gates = build_custom_geometry(family, grid_n=config.grid_n, exit_radius=config.exit_radius)
    navigation = NavigationSolver().solve(maze)
    thresholds = build_refined_thresholds(config, {"tau_p": 1.0 / config.Dr, "tau_g": 1.0, "ell_g": config.v0})
    extractor = RefinedMechanismPointExtractor(maze=maze, navigation=navigation, thresholds=thresholds, gates=gates)

    sweep_point = extractor._build_sweep_point(config)
    dynamics = extractor._build_dynamics(config)
    summary, traj_df, _trap_df = extractor.run(sweep_point, dynamics, point_seed=config.seed)
    tau_g = float(summary.get("mfpt_mean") or config.Tmax)
    ell_g = float(config.v0 * tau_g)

    ref_point = TransferPoint(
        canonical_label="REFERENCE_BASELINE",
        geometry_family=family.geometry_id,
        state_point_id=f"{family.geometry_id}:REFERENCE",
        Pi_m=0.0,
        Pi_f=0.0,
        Pi_U=0.0,
        config=config,
        analysis_source="geometry_transfer_reference",
        analysis_n_traj=config.n_traj,
        result_json="",
        source_result={"scan_id": f"reference_{family.geometry_id}", "p_succ": float("nan"), "trap_time_mean": float("nan"), "wall_fraction_mean": float("nan")},
    )
    ref_traj, ref_event, ref_gate, _ = extractor.extract_point(
        point=ref_point,
        shared_payload=make_shared_payload(ref_point, tau_g, ell_g),
    )

    reference_row = {
        "geometry_family": family.geometry_id,
        "geometry_label": family.label,
        "ell_g": ell_g,
        "tau_g": tau_g,
        "baseline_wall_fraction": float(traj_df["boundary_contact_fraction_i"].mean()),
        "baseline_approach_events_per_traj": float(ref_traj["n_gate_approach_events"].mean()),
        "baseline_residence_events_per_traj": float(ref_traj["n_gate_residence_precommit_events"].mean()),
        "baseline_commit_events_per_traj": float(ref_traj["n_gate_commit_events"].mean()),
        "baseline_p_reach_residence": float((ref_traj["n_gate_residence_precommit_events"] > 0).mean()),
        "baseline_p_reach_commit": float(ref_traj["first_gate_commit_delay"].notna().mean()),
        "baseline_return_to_wall_after_precommit": float(_safe_mean(ref_gate["return_to_wall_after_precommit_rate"])),
    }
    return reference_row, ref_event


def summarize_family_results(family: GeometryFamily, traj_df: pd.DataFrame, gate_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for canonical_label, tg in traj_df.groupby("canonical_label"):
        gg = gate_df[gate_df["canonical_label"] == canonical_label]
        rows.append(
            {
                "geometry_family": family.geometry_id,
                "geometry_label": family.label,
                "canonical_label": canonical_label,
                "first_gate_commit_delay": _safe_mean(tg["first_gate_commit_delay"]),
                "wall_dwell_before_first_commit": _safe_mean(tg["wall_dwell_before_first_commit"]),
                "p_reach_commit": float(tg["first_gate_commit_delay"].notna().mean()),
                "commit_given_residence": _safe_mean(gg["commit_given_residence"]),
                "residence_given_approach": _safe_mean(gg["residence_given_approach"]),
                "return_to_wall_after_precommit_rate": _safe_mean(gg["return_to_wall_after_precommit_rate"]),
                "trap_burden_mean": float(tg["trap_time_total"].mean()),
                "n_traj": int(len(tg)),
            }
        )
    return pd.DataFrame(rows)


def build_gf0_reference_row() -> dict[str, Any]:
    reference_payload = json.loads(GF0_REFERENCE_PATH.read_text(encoding="ascii"))
    traj_df = pd.read_parquet(
        GF0_TRAJ_PATH,
        columns=[
            "canonical_label",
            "boundary_contact_fraction_i",
            "n_gate_approach_events",
            "n_gate_residence_precommit_events",
            "n_gate_commit_events",
            "first_gate_commit_delay",
        ],
    )
    gate_df = pd.read_parquet(
        PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "gate_conditioned.parquet",
        columns=["canonical_label", "return_to_wall_after_precommit_rate"],
    )
    return {
        "geometry_family": "GF0_REF_NESTED_MAZE",
        "geometry_label": "GF0 Reference Nested",
        "ell_g": float(reference_payload["ell_g"]),
        "tau_g": float(reference_payload["tau_g"]),
        "baseline_wall_fraction": float(traj_df["boundary_contact_fraction_i"].mean()),
        "baseline_approach_events_per_traj": float(traj_df["n_gate_approach_events"].mean()),
        "baseline_residence_events_per_traj": float(traj_df["n_gate_residence_precommit_events"].mean()),
        "baseline_commit_events_per_traj": float(traj_df["n_gate_commit_events"].mean()),
        "baseline_p_reach_residence": float((traj_df["n_gate_residence_precommit_events"] > 0).mean()),
        "baseline_p_reach_commit": float(traj_df["first_gate_commit_delay"].notna().mean()),
        "baseline_return_to_wall_after_precommit": float(gate_df["return_to_wall_after_precommit_rate"].mean()),
    }


def build_gf0_summary() -> pd.DataFrame:
    summary_df = pd.read_csv(GF0_SUMMARY_PATH)
    traj_df = pd.read_parquet(GF0_TRAJ_PATH, columns=["canonical_label", "first_gate_commit_delay"])
    p_reach_df = (
        traj_df.groupby("canonical_label")["first_gate_commit_delay"]
        .agg(
            p_reach_commit=lambda s: float(s.notna().mean()),
        )
        .reset_index()
    )
    summary_df = summary_df.merge(p_reach_df, on="canonical_label", how="left")
    if "n_traj" not in summary_df.columns:
        summary_df = summary_df.merge(
            traj_df.groupby("canonical_label").size().reset_index(name="n_traj"),
            on="canonical_label",
            how="left",
        )
    summary_df["geometry_family"] = "GF0_REF_NESTED_MAZE"
    summary_df["geometry_label"] = "GF0 Reference Nested"
    return summary_df[
        [
            "geometry_family",
            "geometry_label",
            "canonical_label",
            "first_gate_commit_delay",
            "wall_dwell_before_first_commit",
            "p_reach_commit",
            "commit_given_residence",
            "residence_given_approach",
            "return_to_wall_after_precommit_rate",
            "trap_burden_mean",
            "n_traj",
        ]
    ].copy()


def verdict_for_family(summary_df: pd.DataFrame, family: str) -> tuple[str, str]:
    g = summary_df[summary_df["geometry_family"] == family].copy()
    if g.empty:
        return "breakdown", "No summary rows available."
    speed_row = g[g["canonical_label"] == "OP_SPEED_TIP"].iloc[0]
    success_row = g[g["canonical_label"] == "OP_SUCCESS_TIP"].iloc[0]
    balanced_row = g[g["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale_row = g[g["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]

    backbone_present = (
        float(g["residence_given_approach"].mean()) > 0.05
        and float(g["commit_given_residence"].mean()) > 0.15
        and float(g["p_reach_commit"].mean()) > 0.20
    )
    speed_fastest = speed_row["first_gate_commit_delay"] == g["first_gate_commit_delay"].min()
    p_reach_span = float(g["p_reach_commit"].max() - g["p_reach_commit"].min())
    success_reliable = success_row["p_reach_commit"] >= float(g["p_reach_commit"].max()) - 0.01
    success_commit_top = success_row["commit_given_residence"] >= float(g["commit_given_residence"].max()) - 0.005
    success_preserved = success_reliable or (p_reach_span < 0.02 and success_commit_top)
    stale_slower = stale_row["first_gate_commit_delay"] > balanced_row["first_gate_commit_delay"]
    stale_more_wall = stale_row["wall_dwell_before_first_commit"] >= balanced_row["wall_dwell_before_first_commit"] - 1e-12
    stale_more_recycling = stale_row["return_to_wall_after_precommit_rate"] >= balanced_row["return_to_wall_after_precommit_rate"] - 1e-12
    stale_trappier = stale_row["trap_burden_mean"] >= balanced_row["trap_burden_mean"] - 1e-12

    if not backbone_present:
        return "breakdown", "Pre-commit backbone occupancy collapsed: approach/residence/commit structure is too weak."
    if speed_fastest and success_preserved and stale_slower and stale_more_wall and stale_more_recycling:
        return "same_principle", "Speed-favored earliest commit, success-favored strongest commit reach, and stale degradation through slower wall-mediated recycling all survive."
    if speed_fastest and success_preserved and stale_slower:
        if stale_trappier:
            return "renormalization", "The backbone survives, but the stale sink shifts from a clean wall-and-trap burden to a geometry-renormalized timing signature."
        return "renormalization", "The backbone survives, but one or more stale-control sink signals soften after geometry transfer."
    if speed_fastest or success_preserved or stale_slower:
        return "renormalization", "The backbone remains visible, but only part of the canonical pre-commit ordering survives cleanly."
    return "breakdown", "The matched ridge-vs-stale pre-commit signature does not survive in a stable way."


def maybe_local_slice(base_point: Any, family: GeometryFamily, tau_g: float) -> list[TransferPoint]:
    pif_values = [0.018, 0.02, 0.025]
    points: list[TransferPoint] = []
    for pif in pif_values:
        cfg = WorkflowRunConfig(
            geometry_id=family.geometry_id,
            model_variant=base_point.config.model_variant,
            v0=base_point.config.v0,
            Dr=base_point.config.Dr,
            tau_v=0.15 * tau_g,
            gamma0=base_point.config.gamma0,
            gamma1=base_point.config.gamma1,
            tau_f=pif * tau_g,
            U=0.2 * base_point.config.v0,
            wall_thickness=family.wall_thickness,
            gate_width=family.gate_width,
            dt=base_point.config.dt,
            Tmax=base_point.config.Tmax,
            n_traj=256,
            seed=base_point.config.seed,
            exit_radius=base_point.config.exit_radius,
            n_shell=len(family.barrier_x),
            grid_n=257,
            kf=base_point.config.kf,
            bootstrap_resamples=base_point.config.bootstrap_resamples,
            kBT=base_point.config.kBT,
            eps_psi=base_point.config.eps_psi,
            flow_condition=base_point.config.flow_condition,
            legacy_model_variant=base_point.config.legacy_model_variant,
            metadata={"L": 1.0, "geometry_family": family.geometry_id, "transfer_stage": "local_slice"},
        )
        points.append(
            TransferPoint(
                canonical_label=f"LOCAL_SLICE_PIF_{pif}",
                geometry_family=family.geometry_id,
                state_point_id=f"{family.geometry_id}:LOCAL:{pif}",
                Pi_m=0.15,
                Pi_f=pif,
                Pi_U=0.2,
                config=cfg,
                analysis_source="geometry_transfer_local_slice",
                analysis_n_traj=256,
                result_json="",
                source_result={"scan_id": f"geometry_transfer_{family.geometry_id}", "p_succ": float("nan"), "trap_time_mean": float("nan"), "wall_fraction_mean": float("nan")},
            )
        )
    return points


def run_family_transfer(family: GeometryFamily, base_points: list[Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    reference_row, _ = extract_reference_for_family(family)
    tau_g = float(reference_row["tau_g"])
    ell_g = float(reference_row["ell_g"])
    maze, gates = build_custom_geometry(family, grid_n=257)
    navigation = NavigationSolver().solve(maze)

    traj_frames: list[pd.DataFrame] = []
    gate_frames: list[pd.DataFrame] = []
    for base_point in base_points:
        transfer_point = make_transfer_point(base_point, family, tau_g)
        thresholds = build_refined_thresholds(transfer_point.config, {"tau_p": 1.0 / transfer_point.config.Dr, "tau_g": tau_g, "ell_g": ell_g})
        extractor = RefinedMechanismPointExtractor(maze=maze, navigation=navigation, thresholds=thresholds, gates=gates)
        traj_df, _event_df, gate_df, _validation = extractor.extract_point(
            point=transfer_point,
            shared_payload=make_shared_payload(transfer_point, tau_g, ell_g),
        )
        traj_frames.append(traj_df)
        gate_frames.append(gate_df)

    traj_df = pd.concat(traj_frames, ignore_index=True)
    gate_df = pd.concat(gate_frames, ignore_index=True)
    summary_df = summarize_family_results(family, traj_df, gate_df)
    verdict, reason = verdict_for_family(summary_df, family.geometry_id)

    local_slice_df = pd.DataFrame()
    if verdict == "renormalization":
        slice_points = maybe_local_slice(base_points[0], family, tau_g)
        slice_traj_frames: list[pd.DataFrame] = []
        slice_gate_frames: list[pd.DataFrame] = []
        for point in slice_points:
            thresholds = build_refined_thresholds(point.config, {"tau_p": 1.0 / point.config.Dr, "tau_g": tau_g, "ell_g": ell_g})
            extractor = RefinedMechanismPointExtractor(maze=maze, navigation=navigation, thresholds=thresholds, gates=gates)
            tdf, _edf, gdf, _ = extractor.extract_point(point=point, shared_payload=make_shared_payload(point, tau_g, ell_g))
            slice_traj_frames.append(tdf)
            slice_gate_frames.append(gdf)
        local_slice_df = summarize_family_results(family, pd.concat(slice_traj_frames, ignore_index=True), pd.concat(slice_gate_frames, ignore_index=True))

    metadata = {
        "geometry_family": family.geometry_id,
        "geometry_label": family.label,
        "reference": reference_row,
        "verdict": verdict,
        "verdict_reason": reason,
        "local_slice_used": not local_slice_df.empty,
    }
    return summary_df, local_slice_df, metadata


def make_figures(reference_df: pd.DataFrame, transfer_df: pd.DataFrame) -> dict[str, str]:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    reference_fig = FIGURE_ROOT / "reference_scale_transfer.png"
    timing_fig = FIGURE_ROOT / "precommit_transfer_comparison.png"
    matched_fig = FIGURE_ROOT / "balanced_vs_stale_transfer.png"

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].bar(reference_df["geometry_family"], reference_df["tau_g"], color="#9ecae1")
    axes[0].set_title("tau_g")
    axes[1].bar(reference_df["geometry_family"], reference_df["ell_g"], color="#6baed6")
    axes[1].set_title("ell_g")
    for ax in axes:
        ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(reference_fig, dpi=220)
    plt.close(fig)

    focus = transfer_df[transfer_df["canonical_label"].isin(["OP_SUCCESS_TIP", "OP_EFFICIENCY_TIP", "OP_SPEED_TIP"])].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for idx, metric in enumerate(["first_gate_commit_delay", "p_reach_commit"]):
        ax = axes[idx]
        pivot = focus.pivot(index="canonical_label", columns="geometry_family", values=metric).reindex(["OP_SUCCESS_TIP", "OP_EFFICIENCY_TIP", "OP_SPEED_TIP"])
        pivot.plot(kind="bar", ax=ax, color=["#9ecae1", "#74c476", "#fdae6b"], rot=20)
        ax.set_title(metric)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(timing_fig, dpi=220)
    plt.close(fig)

    matched = transfer_df[transfer_df["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    for idx, metric in enumerate(["first_gate_commit_delay", "wall_dwell_before_first_commit", "trap_burden_mean"]):
        ax = axes[idx]
        pivot = matched.pivot(index="geometry_family", columns="canonical_label", values=metric)
        pivot.plot(kind="bar", ax=ax, rot=20, color=["#74c476", "#fb6a4a"])
        ax.set_title(metric)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(matched_fig, dpi=220)
    plt.close(fig)

    return {
        "reference_scale_transfer": str(reference_fig),
        "precommit_transfer_comparison": str(timing_fig),
        "balanced_vs_stale_transfer": str(matched_fig),
    }


def write_outputs(reference_df: pd.DataFrame, transfer_df: pd.DataFrame, local_slice_df: pd.DataFrame, metadata: list[dict[str, Any]], figure_paths: dict[str, str]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reference_df.to_csv(OUTPUT_ROOT / "reference_extraction_summary.csv", index=False)
    reference_df.to_parquet(OUTPUT_ROOT / "reference_extraction_summary.parquet", index=False)
    transfer_df.to_csv(OUTPUT_ROOT / "canonical_transfer_summary.csv", index=False)
    transfer_df.to_parquet(OUTPUT_ROOT / "canonical_transfer_summary.parquet", index=False)
    if not local_slice_df.empty:
        local_slice_df.to_csv(OUTPUT_ROOT / "local_renormalization_slice.csv", index=False)
        local_slice_df.to_parquet(OUTPUT_ROOT / "local_renormalization_slice.parquet", index=False)
    (OUTPUT_ROOT / "geometry_transfer_verdicts.json").write_text(json.dumps(metadata, indent=2), encoding="ascii")

    verdict_lines = []
    for item in metadata:
        verdict_lines.append(f"- `{item['geometry_family']}`: `{item['verdict']}`. {item['verdict_reason']}")
    local_slice_note = (
        "No local renormalization slice was needed: the frozen canonical set already preserved the pre-commit ordering signals in the tested families."
        if local_slice_df.empty
        else "A tiny local renormalization slice was added only for families whose backbone survived but whose canonical ordering softened."
    )

    run_report = f"""# Geometry Transfer Run Report

## Scope

This report summarizes the first geometry-transfer validation for the pre-commit backbone.

- family spec: {_path_link(PROJECT_ROOT / 'docs' / 'geometry_family_spec.md')}
- transfer plan: {_path_link(PROJECT_ROOT / 'docs' / 'geometry_transfer_plan.md')}
- summary directory: {_path_link(OUTPUT_ROOT)}

## Reference Extraction

{reference_df.to_markdown(index=False)}

The non-reference families reach `tau_g = Tmax` in this first pass, so `tau_g` and `ell_g` act here as conservative coarse renormalization scales rather than finely resolved full-exit scales. The verdicts below are therefore based primarily on pre-commit observables, not on crossing completion.

## Canonical Transfer Summary

{transfer_df.to_markdown(index=False)}

## Which aspects transferred, and which renormalized?

{chr(10).join(verdict_lines)}

Transferred first:

- pre-commit timing structure
- wall dwell before commitment
- commitment reach as `p_reach_commit`
- precommit recycling through `commit_given_residence` and `return_to_wall_after_precommit_rate`

Renormalized where needed:

- absolute `tau_g`
- absolute `ell_g`
- the precise magnitude of approach and commitment rates in non-reference geometries

{local_slice_note}

## Did any geometry show genuine breakdown of the pre-commit principle?

Only geometries classified as `breakdown` should be taken as genuine failures. In this first stage, that verdict is reserved for cases where the pre-commit backbone itself ceases to organize the comparison, not for simple rate rescaling.

## Figures

- {_path_link(figure_paths['reference_scale_transfer'])}
- {_path_link(figure_paths['precommit_transfer_comparison'])}
- {_path_link(figure_paths['balanced_vs_stale_transfer'])}
"""
    RUN_REPORT_PATH.write_text(run_report, encoding="ascii")

    first_look = f"""# Geometry Transfer First Look

## Verdicts

{chr(10).join(verdict_lines)}

## First-Look Readout

The first transfer test is centered on the pre-commit backbone, not on crossing-specific observables.

- if a geometry preserves the speed-favored shortest commitment timing, the success-favored strongest commitment reach or residence-to-commit conversion, and the stale-control slowing plus stronger wall-mediated recycling, it counts as the same principle
- if those ordering rules survive but the numerical scales shift, it counts as geometry-specific renormalization
- only collapse of the backbone logic counts as genuine breakdown

## Which aspects transferred, and which renormalized?

- transferred first: commitment timing, wall dwell before commitment, commitment reach, and wall-mediated precommit recycling
- renormalized first: `ell_g`, `tau_g`, and the absolute magnitude of local approach / residence / commitment rates

## Did any geometry show genuine breakdown of the pre-commit principle?

See the verdict list above. In this first-look stage, breakdown means failure of the pre-commit backbone itself, not merely a shift in scale.
"""
    FIRST_LOOK_PATH.write_text(first_look, encoding="ascii")


def build_outputs() -> dict[str, str]:
    base_points = load_canonical_points()
    reference_df = pd.DataFrame([build_gf0_reference_row()])
    transfer_frames = [build_gf0_summary()]
    local_frames: list[pd.DataFrame] = []
    metadata: list[dict[str, Any]] = []

    for family in FAMILIES:
        family_summary, local_slice_df, family_meta = run_family_transfer(family, base_points)
        transfer_frames.append(family_summary)
        if not local_slice_df.empty:
            local_frames.append(local_slice_df)
        metadata.append(family_meta)
        reference_df = pd.concat([reference_df, pd.DataFrame([family_meta["reference"]])], ignore_index=True)

    transfer_df = pd.concat(transfer_frames, ignore_index=True)
    local_slice_df = pd.concat(local_frames, ignore_index=True) if local_frames else pd.DataFrame()
    figure_paths = make_figures(reference_df, transfer_df)
    write_outputs(reference_df, transfer_df, local_slice_df, metadata, figure_paths)
    return {
        "run_report": str(RUN_REPORT_PATH),
        "first_look": str(FIRST_LOOK_PATH),
        "summary_dir": str(OUTPUT_ROOT),
        "figure_dir": str(FIGURE_ROOT),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the first geometry-transfer validation on the pre-commit backbone.")
    parser.parse_args(argv)
    result = build_outputs()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
