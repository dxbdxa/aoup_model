from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.gridspec import GridSpec

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.runners.run_front_analysis import (
    compute_front_distance_summary,
    compute_topk_overlap,
    extract_fronts,
    load_front_dataset,
    pareto_candidates,
    sort_for_objective,
    winner_row,
)

MAIN_FIGURE_ROOT = PROJECT_ROOT / "outputs" / "figures" / "main_figures"
FIGURE_PLAN_PATH = PROJECT_ROOT / "docs" / "figure_plan_v3.md"
CAPTION_DRAFTS_PATH = PROJECT_ROOT / "docs" / "figure_caption_drafts_v2.md"
PANEL_MANIFEST_PATH = MAIN_FIGURE_ROOT / "panel_sources_manifest.json"
REFERENCE_SCALES_PATH = PROJECT_ROOT / "outputs" / "summaries" / "reference_scales" / "reference_scales.json"

OBJECTIVE_LABELS = {
    "Psucc_mean": "Success",
    "eta_sigma_mean": "Efficiency",
    "MFPT_mean": "Speed",
}

OBJECTIVE_COLORS = {
    "Psucc_mean": "tab:blue",
    "eta_sigma_mean": "tab:green",
    "MFPT_mean": "tab:red",
}

SCAN_SUMMARY_PATHS = {
    "coarse_scan": PROJECT_ROOT / "outputs" / "summaries" / "coarse_scan" / "summary.parquet",
    "refinement_scan": PROJECT_ROOT / "outputs" / "summaries" / "refinement_scan" / "summary.parquet",
    "precision_scan": PROJECT_ROOT / "outputs" / "summaries" / "precision_scan" / "summary.parquet",
    "confirmatory_scan": PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet",
}

FIGURE_PATHS = {
    "figure1": MAIN_FIGURE_ROOT / "figure1_model_overview.png",
    "figure2": MAIN_FIGURE_ROOT / "figure2_localization_to_ridge.png",
    "figure3": MAIN_FIGURE_ROOT / "figure3_pareto_like_ridge.png",
    "figure4": MAIN_FIGURE_ROOT / "figure4_mechanism_tradeoff.png",
}


def load_reference_scales(path: Path = REFERENCE_SCALES_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="ascii"))


def load_scan_summary(scan_name: str) -> pd.DataFrame:
    df = pd.read_parquet(SCAN_SUMMARY_PATHS[scan_name]).copy()
    df["scan_name"] = scan_name
    return df


def normalize_series(values: pd.Series, *, invert: bool = False) -> pd.Series:
    values = values.astype(float)
    if values.nunique() <= 1:
        return pd.Series(np.ones(len(values)) * 0.5, index=values.index)
    normalized = (values - values.min()) / (values.max() - values.min())
    if invert:
        normalized = 1.0 - normalized
    return normalized


def best_by_axis(df: pd.DataFrame, axis: str, metric: str, goal: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for axis_value, group in df.groupby(axis):
        if goal == "max":
            row = group.sort_values(metric, ascending=False).iloc[0]
        else:
            row = group.sort_values(metric, ascending=True).iloc[0]
        rows.append(
            {
                axis: float(axis_value),
                metric: float(row[metric]),
                "Pi_m": float(row["Pi_m"]),
                "Pi_f": float(row["Pi_f"]),
                "Pi_U": float(row["Pi_U"]),
                "analysis_source": row.get("analysis_source", "scan_summary"),
            }
        )
    return pd.DataFrame(rows).sort_values(axis)


def localization_panel(ax: plt.Axes, df: pd.DataFrame, scan_name: str) -> None:
    ax.scatter(df["Pi_m"], df["Pi_f"], color="0.82", s=18, alpha=0.85)

    top_eta = sort_for_objective(df, "eta_sigma_mean").head(min(18, len(df)))
    scatter = ax.scatter(
        top_eta["Pi_m"],
        top_eta["Pi_f"],
        c=top_eta["Pi_U"],
        cmap="viridis",
        s=70,
        edgecolors="black",
        linewidths=0.4,
        zorder=3,
    )

    for objective in ("Psucc_mean", "eta_sigma_mean", "MFPT_mean"):
        row = sort_for_objective(df, objective).iloc[0]
        ax.scatter(
            row["Pi_m"],
            row["Pi_f"],
            color=OBJECTIVE_COLORS[objective],
            s=110,
            marker="D",
            edgecolors="black",
            linewidths=0.8,
            zorder=4,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Pi_m")
    ax.set_ylabel("Pi_f")
    ax.set_title(f"{scan_name.replace('_', ' ').title()} ({len(df)} pts)")
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.text(
        0.04,
        0.95,
        "colored: top eta_sigma_mean\nmarkers: success / efficiency / speed winners",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "0.8"},
    )
    return scatter


def figure1_model_overview(reference_scales: dict[str, Any], output_path: Path) -> None:
    fig = plt.figure(figsize=(13.5, 9.2))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.1, 1.0], width_ratios=[1.15, 1.0])

    ax_geom = fig.add_subplot(gs[0, 0])
    ax_refs = fig.add_subplot(gs[0, 1])
    ax_model = fig.add_subplot(gs[1, 0])
    ax_controls = fig.add_subplot(gs[1, 1])

    for axis in (ax_geom, ax_refs, ax_model, ax_controls):
        axis.set_axis_off()

    chamber_y = 0.45
    chamber_h = 0.22
    segments = [(0.05, 0.22), (0.33, 0.22), (0.61, 0.22)]
    for x0, width in segments:
        ax_geom.add_patch(
            patches.FancyBboxPatch(
                (x0, chamber_y),
                width,
                chamber_h,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=2.0,
                edgecolor="black",
                facecolor="#f7f7f7",
            )
        )
    for gate_x in (0.29, 0.57):
        ax_geom.add_patch(patches.Rectangle((gate_x, 0.52), 0.04, 0.08, facecolor="#d9edf7", edgecolor="black"))
    ax_geom.annotate("", xy=(0.88, 0.56), xytext=(0.12, 0.56), arrowprops={"arrowstyle": "->", "lw": 2.0, "color": "tab:orange"})
    ax_geom.text(0.5, 0.62, "background flow U", ha="center", color="tab:orange", fontsize=11)
    ax_geom.annotate("", xy=(0.36, 0.50), xytext=(0.24, 0.43), arrowprops={"arrowstyle": "->", "lw": 2.0, "color": "tab:blue"})
    ax_geom.text(0.2, 0.4, "active heading", color="tab:blue", fontsize=10)
    ax_geom.annotate("", xy=(0.45, 0.80), xytext=(0.45, 0.61), arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "tab:red", "linestyle": "--"})
    ax_geom.text(0.47, 0.79, "delayed steering", color="tab:red", fontsize=10, va="bottom")
    ax_geom.text(0.14, 0.82, "A. Gated transport geometry", fontsize=12, fontweight="bold")
    ax_geom.text(0.07, 0.15, "Narrow gates set the reference search length l_g and crossing time tau_g.", fontsize=10)
    ax_geom.set_xlim(0, 1)
    ax_geom.set_ylim(0, 1)

    tau_g = float(reference_scales["tau_g"])
    ell_g = float(reference_scales["ell_g"])
    tau_p = float(reference_scales["tau_p"])
    bars = [
        ("tau_g", tau_g, "#6baed6"),
        ("l_g", ell_g, "#9ecae1"),
        ("tau_p", tau_p, "#c6dbef"),
    ]
    ax_refs.text(0.02, 0.95, "B. Reference scales", fontsize=12, fontweight="bold", va="top")
    max_bar = max(value for _, value, _ in bars)
    for index, (label, value, color) in enumerate(bars):
        y = 0.72 - index * 0.18
        width = 0.72 * (value / max_bar)
        ax_refs.add_patch(patches.Rectangle((0.08, y), width, 0.08, facecolor=color, edgecolor="black"))
        ax_refs.text(0.02, y + 0.04, label, va="center", fontsize=10)
        ax_refs.text(0.83, y + 0.04, f"{value:.3f}", va="center", fontsize=10)
    ax_refs.text(0.08, 0.18, "Reference extraction uses the no-memory, no-feedback, U=0 baseline.", fontsize=10)
    ax_refs.text(0.08, 0.10, f"tau_g = {tau_g:.3f}, l_g = {ell_g:.3f}, tau_p = {tau_p:.3f}", fontsize=10)
    ax_refs.set_xlim(0, 1)
    ax_refs.set_ylim(0, 1)

    ax_model.text(0.02, 0.95, "C. Minimal model ingredients", fontsize=12, fontweight="bold", va="top")
    model_lines = [
        "Active propulsion sets the intrinsic search motion.",
        "Delayed alignment follows the local navigation field.",
        "Viscoelastic memory retains a filtered motion history.",
        "Wall repulsion and gates encode the constrained geometry.",
        "Uniform flow biases downstream transport.",
    ]
    for i, line in enumerate(model_lines):
        ax_model.text(0.06, 0.78 - 0.13 * i, f"- {line}", fontsize=10)
    ax_model.text(0.06, 0.08, "The figure package uses standardized notation across all panels.", fontsize=10)

    ax_controls.text(0.02, 0.95, "D. Dimensionless controls", fontsize=12, fontweight="bold", va="top")
    controls = [
        ("Pi_m", "tau_mem / tau_g", "memory-to-gate ratio"),
        ("Pi_f", "tau_f / tau_g", "delay-to-gate ratio"),
        ("Pi_U", "U / v0", "flow-to-swim ratio"),
    ]
    for i, (symbol, formula, meaning) in enumerate(controls):
        y = 0.75 - 0.2 * i
        ax_controls.add_patch(patches.FancyBboxPatch((0.05, y - 0.07), 0.9, 0.12, boxstyle="round,pad=0.02", facecolor="#f7f7f7", edgecolor="0.7"))
        ax_controls.text(0.10, y, symbol, fontsize=12, fontweight="bold")
        ax_controls.text(0.30, y, formula, fontsize=11, family="monospace")
        ax_controls.text(0.62, y, meaning, fontsize=10)
    ax_controls.text(0.05, 0.12, "Working picture:", fontsize=10, fontweight="bold")
    ax_controls.text(0.05, 0.05, "Pi_f selects admissibility, Pi_m selects the productive band, Pi_U orders the task tradeoff.", fontsize=10)

    fig.suptitle("Figure 1. Model Overview, Reference Scales, and Dimensionless Controls", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def figure2_localization_to_ridge(scan_dfs: dict[str, pd.DataFrame], output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 10.5))
    fig.subplots_adjust(left=0.08, right=0.92, bottom=0.09, top=0.90, wspace=0.28, hspace=0.28)
    order = ["coarse_scan", "refinement_scan", "precision_scan", "confirmatory_scan"]
    last_scatter = None
    for axis, scan_name in zip(axes.flatten(), order):
        last_scatter = localization_panel(axis, scan_dfs[scan_name], scan_name)
    if last_scatter is not None:
        colorbar = fig.colorbar(last_scatter, ax=axes.ravel().tolist(), shrink=0.85, label="Pi_U")
        colorbar.ax.tick_params(labelsize=9)
    fig.suptitle("Figure 2. Localization From Coarse Scan to Confirmed Productive-Memory Ridge", fontsize=16, fontweight="bold")
    fig.text(0.5, 0.02, "The localization history narrows from a broad search to a thin low-delay ridge.", ha="center", fontsize=11)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def figure3_pareto_like_ridge(confirmatory_df: pd.DataFrame, output_path: Path) -> None:
    pareto_df = pareto_candidates(confirmatory_df)
    fronts = extract_fronts(confirmatory_df, top_k=20)
    overlap_df = compute_topk_overlap(fronts, ks=(5, 10, 20))
    distance_df = compute_front_distance_summary(confirmatory_df)

    fig = plt.figure(figsize=(14.5, 10.0))
    gs = GridSpec(2, 2, figure=fig, width_ratios=[1.55, 1.0], height_ratios=[1.0, 1.0])

    ax_main = fig.add_subplot(gs[:, 0])
    ax_strip = fig.add_subplot(gs[0, 1])
    ax_sep = fig.add_subplot(gs[1, 1])

    ax_main.scatter(confirmatory_df["Pi_U"], confirmatory_df["Pi_m"], color="0.85", s=20, alpha=0.75, label="confirmatory points")
    ax_main.plot(pareto_df["Pi_U"], pareto_df["Pi_m"], color="black", linewidth=1.5, alpha=0.8, zorder=2)
    ax_main.scatter(
        pareto_df["Pi_U"],
        pareto_df["Pi_m"],
        c=pareto_df["Pi_f"],
        cmap="plasma",
        s=70,
        edgecolors="black",
        linewidths=0.4,
        zorder=3,
        label="Pareto candidates",
    )
    for objective in ("Psucc_mean", "eta_sigma_mean", "MFPT_mean"):
        row = winner_row(confirmatory_df, objective)
        ax_main.scatter(
            row["Pi_U"],
            row["Pi_m"],
            color=OBJECTIVE_COLORS[objective],
            marker="D",
            s=135,
            edgecolors="black",
            linewidths=0.9,
            zorder=4,
        )
        ax_main.annotate(
            f"{OBJECTIVE_LABELS[objective]}\n(Pi_m={row['Pi_m']:.3g}, Pi_f={row['Pi_f']:.3g}, Pi_U={row['Pi_U']:.3g})",
            (row["Pi_U"], row["Pi_m"]),
            textcoords="offset points",
            xytext=(8, 8),
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.88, "edgecolor": "0.8"},
        )
    ax_main.set_xlabel("Pi_U")
    ax_main.set_ylabel("Pi_m")
    ax_main.set_title("A. Confirmatory Pareto ridge ordered by Pi_U")
    ax_main.grid(alpha=0.25, linewidth=0.6)
    ax_main.text(
        0.03,
        0.04,
        "Ridge, not basin:\n20 non-dominated points\nTop-10 overlap = 0 for all pairs",
        transform=ax_main.transAxes,
        va="bottom",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.75"},
    )

    scatter = ax_strip.scatter(
        confirmatory_df["Pi_m"],
        confirmatory_df["Pi_f"],
        c=confirmatory_df["Pi_U"],
        cmap="viridis",
        s=35,
        alpha=0.55,
        edgecolors="none",
    )
    ax_strip.scatter(
        pareto_df["Pi_m"],
        pareto_df["Pi_f"],
        color="black",
        s=60,
        facecolors="none",
        linewidths=1.1,
        label="Pareto candidates",
    )
    for objective in ("Psucc_mean", "eta_sigma_mean", "MFPT_mean"):
        row = winner_row(confirmatory_df, objective)
        ax_strip.scatter(row["Pi_m"], row["Pi_f"], color=OBJECTIVE_COLORS[objective], s=115, marker="D", edgecolors="black", linewidths=0.9)
    ax_strip.set_xlabel("Pi_m")
    ax_strip.set_ylabel("Pi_f")
    ax_strip.set_title("B. Narrow delay-admissibility strip")
    ax_strip.grid(alpha=0.25, linewidth=0.6)
    ax_strip.text(
        0.05,
        0.92,
        "Pareto family stays inside Pi_f = 0.018 to 0.025",
        transform=ax_strip.transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.88, "edgecolor": "0.8"},
    )
    fig.colorbar(scatter, ax=ax_strip, shrink=0.9, label="Pi_U")

    pair_labels = ["P/E", "P/F", "E/F"]
    distances = distance_df["normalized_distance"].astype(float).tolist()
    ax_sep.bar(pair_labels, distances, color=["#6baed6", "#9ecae1", "#c6dbef"], edgecolor="black")
    ax_sep.set_ylabel("Normalized winner distance")
    ax_sep.set_title("C. Winner separation is geometric and uncertainty-aware")
    ax_sep.grid(axis="y", alpha=0.25, linewidth=0.6)
    overlap_text = (
        "Top-k overlap counts\n"
        f"k=5:  {', '.join(str(int(x)) for x in overlap_df[overlap_df['k'] == 5]['overlap_count'])}\n"
        f"k=10: {', '.join(str(int(x)) for x in overlap_df[overlap_df['k'] == 10]['overlap_count'])}\n"
        f"k=20: {', '.join(str(int(x)) for x in overlap_df[overlap_df['k'] == 20]['overlap_count'])}\n"
        "CI-aware pair checks: all separated"
    )
    ax_sep.text(
        0.58,
        0.96,
        overlap_text,
        transform=ax_sep.transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "0.8"},
    )

    fig.suptitle("Figure 3. Pareto-Like Ridge With Distinct Success, Efficiency, and Speed Front Tips", fontsize=17, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def figure4_mechanism_tradeoff(confirmatory_df: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 10.5))
    ax_pf, ax_pm, ax_pu, ax_tradeoff = axes.flatten()

    profiles = {
        "Psucc_mean": ("max", "Pi_f", ax_pf),
        "eta_sigma_mean": ("max", "Pi_f", ax_pf),
        "MFPT_mean": ("min", "Pi_f", ax_pf),
    }
    for objective, (goal, axis_name, axis) in profiles.items():
        profile = best_by_axis(confirmatory_df, axis_name, objective, goal)
        values = normalize_series(profile[objective], invert=(objective == "MFPT_mean"))
        axis.plot(profile[axis_name], values, marker="o", color=OBJECTIVE_COLORS[objective], label=OBJECTIVE_LABELS[objective])
    ax_pf.axvspan(0.018, 0.025, color="#fee391", alpha=0.35)
    ax_pf.set_xlabel("Pi_f")
    ax_pf.set_ylabel("Normalized best-by-Pi_f score")
    ax_pf.set_title("A. Delay admissibility strip")
    ax_pf.grid(alpha=0.25, linewidth=0.6)
    ax_pf.legend(loc="lower left", frameon=False)

    for objective, color in OBJECTIVE_COLORS.items():
        goal = "max" if objective != "MFPT_mean" else "min"
        profile = best_by_axis(confirmatory_df, "Pi_m", objective, goal)
        values = normalize_series(profile[objective], invert=(objective == "MFPT_mean"))
        ax_pm.plot(profile["Pi_m"], values, marker="o", color=color, label=OBJECTIVE_LABELS[objective])
    ax_pm.axvspan(0.08, 0.2, color="#c7e9c0", alpha=0.35)
    ax_pm.set_xlabel("Pi_m")
    ax_pm.set_ylabel("Normalized best-by-Pi_m score")
    ax_pm.set_title("B. Low productive memory band")
    ax_pm.grid(alpha=0.25, linewidth=0.6)

    for objective, color in OBJECTIVE_COLORS.items():
        goal = "max" if objective != "MFPT_mean" else "min"
        profile = best_by_axis(confirmatory_df, "Pi_U", objective, goal)
        values = normalize_series(profile[objective], invert=(objective == "MFPT_mean"))
        ax_pu.plot(profile["Pi_U"], values, marker="o", color=color, linewidth=2.0, label=OBJECTIVE_LABELS[objective])
        winner = winner_row(confirmatory_df, objective)
        ax_pu.scatter(winner["Pi_U"], values.iloc[(profile["Pi_U"] - winner["Pi_U"]).abs().argmin()], color=color, s=110, marker="D", edgecolors="black", linewidths=0.8)
    ax_pu.set_xlabel("Pi_U")
    ax_pu.set_ylabel("Normalized objective optimum")
    ax_pu.set_title("C. Flow ordering along the ridge")
    ax_pu.grid(alpha=0.25, linewidth=0.6)
    ax_pu.text(
        0.05,
        0.93,
        "Low Pi_U -> success\nModerate Pi_U -> efficiency\nHigh Pi_U -> speed",
        transform=ax_pu.transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "0.8"},
    )

    pareto_df = pareto_candidates(confirmatory_df)
    scatter = ax_tradeoff.scatter(
        pareto_df["MFPT_mean"],
        pareto_df["Psucc_mean"],
        c=pareto_df["Pi_U"],
        cmap="viridis",
        s=80,
        edgecolors="black",
        linewidths=0.45,
    )
    for objective in ("Psucc_mean", "eta_sigma_mean", "MFPT_mean"):
        row = winner_row(confirmatory_df, objective)
        ax_tradeoff.scatter(
            row["MFPT_mean"],
            row["Psucc_mean"],
            color=OBJECTIVE_COLORS[objective],
            s=130,
            marker="D",
            edgecolors="black",
            linewidths=0.8,
        )
        ax_tradeoff.annotate(
            OBJECTIVE_LABELS[objective],
            (row["MFPT_mean"], row["Psucc_mean"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=9,
        )
    ax_tradeoff.set_xlabel("MFPT_mean")
    ax_tradeoff.set_ylabel("Psucc_mean")
    ax_tradeoff.set_title("D. Transport-task tradeoff on the Pareto family")
    ax_tradeoff.grid(alpha=0.25, linewidth=0.6)
    fig.colorbar(scatter, ax=ax_tradeoff, shrink=0.88, label="Pi_U")

    fig.suptitle("Figure 4. Physical Mechanism and Transport-Task Tradeoff Interpretation", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_panel_manifest() -> dict[str, Any]:
    return {
        "notation": {
            "Pi_m": "tau_mem / tau_g",
            "Pi_f": "tau_f / tau_g",
            "Pi_U": "U / v0",
            "tau_g": "gate-crossing time",
            "l_g": "gate-search length",
        },
        "primary_quantitative_source": str(SCAN_SUMMARY_PATHS["confirmatory_scan"]),
        "localization_history_sources": {key: str(value) for key, value in SCAN_SUMMARY_PATHS.items()},
        "front_analysis_sources": {
            "report": str(PROJECT_ROOT / "docs" / "front_analysis_report.md"),
            "pareto_candidates": str(PROJECT_ROOT / "outputs" / "figures" / "front_analysis" / "pareto_candidates.csv"),
            "front_distance_summary": str(PROJECT_ROOT / "outputs" / "figures" / "front_analysis" / "front_distance_summary.csv"),
        },
        "figures": {
            "figure1_model_overview": {
                "output": str(FIGURE_PATHS["figure1"]),
                "source_files": [
                    str(REFERENCE_SCALES_PATH),
                    str(PROJECT_ROOT / "docs" / "reference_scales_run_report.md"),
                ],
                "panels": {
                    "A": "stylized gated geometry and transport ingredients",
                    "B": "reference scales tau_g, l_g, tau_p",
                    "C": "minimal model ingredient summary",
                    "D": "standardized dimensionless controls Pi_m, Pi_f, Pi_U",
                },
            },
            "figure2_localization_to_ridge": {
                "output": str(FIGURE_PATHS["figure2"]),
                "source_files": [str(path) for path in SCAN_SUMMARY_PATHS.values()],
                "panels": {
                    "A": "coarse scan localization context",
                    "B": "refinement scan narrowing",
                    "C": "precision ridge localization",
                    "D": "confirmatory ridge confirmation",
                },
            },
            "figure3_pareto_like_ridge": {
                "output": str(FIGURE_PATHS["figure3"]),
                "source_files": [
                    str(SCAN_SUMMARY_PATHS["confirmatory_scan"]),
                    str(PROJECT_ROOT / "outputs" / "figures" / "front_analysis" / "pareto_candidates.csv"),
                    str(PROJECT_ROOT / "outputs" / "figures" / "front_analysis" / "front_distance_summary.csv"),
                    str(PROJECT_ROOT / "docs" / "front_analysis_report.md"),
                ],
                "panels": {
                    "A": "confirmatory Pareto ridge ordered by Pi_U",
                    "B": "narrow Pi_f strip showing ridge-vs-basin conclusion",
                    "C": "top-k overlap and winner-distance separation summary",
                },
            },
            "figure4_mechanism_tradeoff": {
                "output": str(FIGURE_PATHS["figure4"]),
                "source_files": [
                    str(SCAN_SUMMARY_PATHS["confirmatory_scan"]),
                    str(PROJECT_ROOT / "docs" / "theory_compression_note.md"),
                    str(PROJECT_ROOT / "docs" / "physics_storyline_v1.md"),
                    str(PROJECT_ROOT / "docs" / "ridge_control_law_candidates.md"),
                ],
                "panels": {
                    "A": "delay admissibility profile along Pi_f",
                    "B": "productive memory band profile along Pi_m",
                    "C": "flow ordering profile along Pi_U",
                    "D": "Pareto-family tradeoff interpretation in objective space",
                },
            },
        },
    }


def write_figure_plan(reference_scales: dict[str, Any]) -> None:
    text = f"""# Figure Plan V3

## Overall Strategy

This package builds the manuscript main-figure set around one central claim: the productive-memory structure is best described as a Pareto-like ridge rather than a single optimum.

Standardized notation used in all panels:

- `Pi_m = tau_mem / tau_g`
- `Pi_f = tau_f / tau_g`
- `Pi_U = U / v0`
- `tau_g = {reference_scales['tau_g']:.3f}`
- `l_g = {reference_scales['ell_g']:.3f}`

Source policy:

- final quantitative claims use `confirmatory_scan`
- coarse / refinement / precision scans are used only as localization history
- front separation and ridge-vs-basin inference use the confirmatory front-analysis package

## Figure 1

Title:

- Model, geometry, reference scales, and dimensionless controls

Role:

- define the geometry-level transport problem
- fix the notation before the scan history begins
- show how `tau_g` and `l_g` anchor `Pi_m`, `Pi_f`, and `Pi_U`

## Figure 2

Title:

- Localization from coarse scan to confirmed productive-memory ridge

Role:

- show how the search contracts from a broad parameter region to a narrow low-delay ridge
- make it visually clear that the final claim does not come from the coarse scan alone
- connect coarse, refinement, precision, and confirmatory stages in one localization sequence

## Figure 3

Title:

- Pareto-like ridge with distinct success / efficiency / speed front tips

Role:

- centerpiece figure
- use `confirmatory_scan` as the main quantitative source
- make the ridge-vs-basin conclusion explicit
- show distinct front tips, top-k separation, and parameter-space separation

Required takeaways:

- the front is extended, not point-like
- the top-10 objective sets do not overlap
- `Pi_f` remains tightly pinned
- `Pi_U` orders the front tips

## Figure 4

Title:

- Physical mechanism and transport-task tradeoff interpretation

Role:

- convert the confirmed ridge into a compact physical reading
- present delay admissibility, productive memory band, and flow ordering as the organizing interpretation
- keep the distinction clear between confirmed numerical structure and mechanistic interpretation

## Visual Hierarchy

- Figure 3 is the quantitative centerpiece
- Figure 2 provides localization history
- Figure 4 provides the physical reading
- Figure 1 standardizes notation and reference scales
"""
    FIGURE_PLAN_PATH.write_text(text, encoding="ascii")


def write_caption_drafts() -> None:
    text = """# Figure Caption Drafts V2

## Figure 1

Figure 1 | Model overview, reference scales, and standardized dimensionless controls. A stylized gated geometry defines the transport problem and the reference search length `l_g` and gate-crossing time `tau_g`. The active particle experiences delayed steering, viscoelastic memory, wall interactions, and uniform background flow. The manuscript uses the same nondimensional controls throughout: `Pi_m = tau_mem / tau_g`, `Pi_f = tau_f / tau_g`, and `Pi_U = U / v0`.

## Figure 2

Figure 2 | Localization from coarse scan to confirmed productive-memory ridge. The coarse scan identifies a broad productive region, refinement and precision progressively contract that region, and the confirmatory scan resolves the final narrow ridge. Colored points show the strongest local `eta_sigma_mean` candidates, while markers identify the best success, efficiency, and speed points at each stage. The localization history shows that the final claim is a local ridge confirmation rather than a reopened global search.

## Figure 3

Figure 3 | The productive-memory structure is a Pareto-like ridge, not a compact basin. Confirmatory results define an extended non-dominated family with distinct success, efficiency, and speed front tips. The Pareto candidates remain confined to a narrow `Pi_f` strip, while `Pi_U` orders the front from low-flow success to moderate-flow efficiency to high-flow speed. Top-`10` overlap counts are zero for all objective pairs, and each winner remains separated from the others under CI-aware comparison, making the ridge-vs-basin conclusion explicit.

## Figure 4

Figure 4 | Physical mechanism and transport-task tradeoff interpretation. The confirmed front structure is consistent with a narrow delay-admissibility strip in `Pi_f`, a low productive memory band in `Pi_m`, and a flow-ordering coordinate in `Pi_U`. Low positive flow favors success, moderate positive flow favors dissipation-normalized efficiency, and stronger positive flow favors minimum first-passage time. The panel converts the confirmed quantitative ridge into a compact physical reading without claiming an exact reduced theory.
"""
    CAPTION_DRAFTS_PATH.write_text(text, encoding="ascii")


def build_main_figure_package() -> dict[str, str]:
    reference_scales = load_reference_scales()
    scan_dfs = {scan_name: load_scan_summary(scan_name) for scan_name in SCAN_SUMMARY_PATHS}
    confirmatory_df = load_front_dataset(SCAN_SUMMARY_PATHS["confirmatory_scan"])

    figure1_model_overview(reference_scales, FIGURE_PATHS["figure1"])
    figure2_localization_to_ridge(scan_dfs, FIGURE_PATHS["figure2"])
    figure3_pareto_like_ridge(confirmatory_df, FIGURE_PATHS["figure3"])
    figure4_mechanism_tradeoff(confirmatory_df, FIGURE_PATHS["figure4"])

    manifest = build_panel_manifest()
    PANEL_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PANEL_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="ascii")

    write_figure_plan(reference_scales)
    write_caption_drafts()

    return {
        "figure1": str(FIGURE_PATHS["figure1"]),
        "figure2": str(FIGURE_PATHS["figure2"]),
        "figure3": str(FIGURE_PATHS["figure3"]),
        "figure4": str(FIGURE_PATHS["figure4"]),
        "panel_manifest": str(PANEL_MANIFEST_PATH),
        "figure_plan": str(FIGURE_PLAN_PATH),
        "caption_drafts": str(CAPTION_DRAFTS_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Produce the manuscript main-figure package.")
    parser.parse_args(argv)
    result = build_main_figure_package()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
