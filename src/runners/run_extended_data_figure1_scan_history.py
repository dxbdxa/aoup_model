from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCAN_PATHS = {
    "coarse_scan": PROJECT_ROOT / "outputs" / "summaries" / "coarse_scan" / "summary.parquet",
    "refinement_scan": PROJECT_ROOT / "outputs" / "summaries" / "refinement_scan" / "summary.parquet",
    "precision_scan": PROJECT_ROOT / "outputs" / "summaries" / "precision_scan" / "summary.parquet",
    "confirmatory_scan": PROJECT_ROOT / "outputs" / "summaries" / "confirmatory_scan" / "summary.parquet",
}

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "extended_data"
PNG_PATH = OUTPUT_DIR / "ed_fig1_scan_localization_history.png"
SVG_PATH = OUTPUT_DIR / "ed_fig1_scan_localization_history.svg"
MANIFEST_DOC_PATH = PROJECT_ROOT / "docs" / "ed_fig1_panel_manifest.md"

PANEL_ORDER = ["coarse_scan", "refinement_scan", "precision_scan", "confirmatory_scan"]
PANEL_TITLES = {
    "coarse_scan": "Coarse scan overview and outer search frame",
    "refinement_scan": "Refinement scan within the low-Pi_f target window",
    "precision_scan": "Precision scan around the local ridge family",
    "confirmatory_scan": "Confirmatory scan with uncertainty-reduced local structure",
}
WINDOW_COLORS = {
    "refinement_scan": "#ff7f0e",
    "precision_scan": "#9467bd",
    "confirmatory_scan": "#111111",
}
WINDOW_STYLES = {
    "refinement_scan": "--",
    "precision_scan": "-.",
    "confirmatory_scan": ":",
}
OBJECTIVE_COLORS = {
    "Psucc_mean": "#1f77b4",
    "eta_sigma_mean": "#2ca02c",
    "MFPT_mean": "#d62728",
}
OBJECTIVE_LABELS = {
    "Psucc_mean": "success",
    "eta_sigma_mean": "efficiency",
    "MFPT_mean": "speed",
}
PANEL_NOTES = {
    "coarse_scan": "Broad initial search. Boxes mark later localization windows.",
    "refinement_scan": "The active search contracts toward the low-Pi_f productive family.",
    "precision_scan": "The local window resolves distinct success, efficiency, and speed tips.",
    "confirmatory_scan": "Stars mark 8192-trajectory anchors used to reduce local uncertainty.",
}
SCALE_MODES = {
    "coarse_scan": ("log", "log"),
    "refinement_scan": ("log", "log"),
    "precision_scan": ("log", "log"),
    "confirmatory_scan": ("log", "log"),
}
AXIS_LIMITS = {
    "coarse_scan": {"xlim": (0.03, 10.5), "ylim": (0.018, 3.3)},
    "refinement_scan": {"xlim": (0.028, 3.2), "ylim": (0.018, 0.34)},
    "precision_scan": {"xlim": (0.045, 0.255), "ylim": (0.0195, 0.0305)},
    "confirmatory_scan": {"xlim": (0.078, 0.222), "ylim": (0.0177, 0.0253)},
}


def load_scan(name: str) -> pd.DataFrame:
    df = pd.read_parquet(SCAN_PATHS[name]).copy()
    df["scan_name"] = name
    return df


def normalize_series(values: pd.Series, *, invert: bool = False) -> pd.Series:
    values = values.astype(float)
    if values.nunique() <= 1:
        out = pd.Series(np.full(len(values), 0.5), index=values.index)
    else:
        out = (values - values.min()) / (values.max() - values.min())
    if invert:
        out = 1.0 - out
    return out


def add_stage_screening_score(df: pd.DataFrame) -> pd.DataFrame:
    stage = df.copy()
    stage["score_success"] = normalize_series(stage["Psucc_mean"])
    stage["score_efficiency"] = normalize_series(stage["eta_sigma_mean"])
    stage["score_speed"] = normalize_series(stage["MFPT_mean"], invert=True)
    stage["search_score"] = stage[["score_success", "score_efficiency", "score_speed"]].mean(axis=1)
    return stage


def objective_sort(df: pd.DataFrame, objective: str) -> pd.DataFrame:
    if objective == "MFPT_mean":
        return df.sort_values(["MFPT_mean", "Psucc_mean", "eta_sigma_mean"], ascending=[True, False, False]).copy()
    return df.sort_values([objective, "Psucc_mean", "eta_sigma_mean"], ascending=[False, False, False]).copy()


def stage_winners(df: pd.DataFrame) -> dict[str, pd.Series]:
    return {objective: objective_sort(df, objective).iloc[0] for objective in OBJECTIVE_COLORS}


def stage_window(df: pd.DataFrame) -> dict[str, float]:
    return {
        "xmin": float(df["Pi_m"].min()),
        "xmax": float(df["Pi_m"].max()),
        "ymin": float(df["Pi_f"].min()),
        "ymax": float(df["Pi_f"].max()),
    }


def stage_sampling_label(df: pd.DataFrame) -> str:
    n_points = len(df)
    n_traj_values = sorted(int(value) for value in df["n_traj"].dropna().astype(int).unique())
    if not n_traj_values:
        traj_label = "trajectory count unavailable"
    elif len(n_traj_values) == 1:
        traj_label = f"{n_traj_values[0]} traj/point"
    else:
        traj_label = f"{n_traj_values[0]}-{n_traj_values[-1]} traj/point"
    return f"{n_points} points | {traj_label}"


def draw_window(ax: plt.Axes, bounds: dict[str, float], *, color: str, linestyle: str, label: str) -> None:
    rect = Rectangle(
        (bounds["xmin"], bounds["ymin"]),
        bounds["xmax"] - bounds["xmin"],
        bounds["ymax"] - bounds["ymin"],
        fill=False,
        edgecolor=color,
        linewidth=1.5,
        linestyle=linestyle,
        zorder=5,
    )
    ax.add_patch(rect)
    ax.text(
        bounds["xmin"],
        bounds["ymax"],
        label,
        color=color,
        fontsize=8,
        va="bottom",
        ha="left",
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none", "pad": 1.5},
    )


def make_locator_inset(ax: plt.Axes, current_bounds: dict[str, float], global_limits: dict[str, tuple[float, float]]) -> None:
    inset = ax.inset_axes([0.03, 0.72, 0.22, 0.22])
    inset.set_xscale("log")
    inset.set_yscale("log")
    inset.set_xlim(*global_limits["xlim"])
    inset.set_ylim(*global_limits["ylim"])
    rect = Rectangle(
        (current_bounds["xmin"], current_bounds["ymin"]),
        current_bounds["xmax"] - current_bounds["xmin"],
        current_bounds["ymax"] - current_bounds["ymin"],
        fill=False,
        edgecolor="#444444",
        linewidth=1.2,
    )
    inset.add_patch(rect)
    inset.set_xticks([])
    inset.set_yticks([])
    inset.set_facecolor("#fafafa")
    for spine in inset.spines.values():
        spine.set_edgecolor("#999999")
    inset.set_title("locator", fontsize=7, pad=1.5)


def annotate_panel_letter(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.12,
        1.02,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def plot_panel(
    ax: plt.Axes,
    df: pd.DataFrame,
    *,
    scan_name: str,
    panel_letter: str,
    global_limits: dict[str, tuple[float, float]],
    scan_windows: dict[str, dict[str, float]],
    overlay_windows: list[str],
    label_winners: bool,
    mark_anchors: bool,
) -> Any:
    scale_x, scale_y = SCALE_MODES[scan_name]
    ax.set_xscale(scale_x)
    ax.set_yscale(scale_y)
    ax.set_xlim(*AXIS_LIMITS[scan_name]["xlim"])
    ax.set_ylim(*AXIS_LIMITS[scan_name]["ylim"])

    scatter = ax.scatter(
        df["Pi_m"],
        df["Pi_f"],
        c=df["search_score"],
        cmap="viridis",
        vmin=0.0,
        vmax=1.0,
        s=52,
        edgecolors="white",
        linewidths=0.35,
        alpha=0.95,
        zorder=2,
    )

    top_n = min(12, len(df))
    top_df = df.nlargest(top_n, "search_score")
    ax.scatter(
        top_df["Pi_m"],
        top_df["Pi_f"],
        facecolors="none",
        edgecolors="#222222",
        s=92,
        linewidths=0.9,
        zorder=3,
    )

    winners = stage_winners(df)
    for objective, row in winners.items():
        ax.scatter(
            float(row["Pi_m"]),
            float(row["Pi_f"]),
            color=OBJECTIVE_COLORS[objective],
            marker="D",
            s=110,
            edgecolors="black",
            linewidths=0.8,
            zorder=4,
        )
        if label_winners:
            ax.annotate(
                OBJECTIVE_LABELS[objective],
                (float(row["Pi_m"]), float(row["Pi_f"])),
                textcoords="offset points",
                xytext=(6, 4),
                fontsize=8,
            )

    if mark_anchors:
        anchors = df[df["n_traj"].astype(float) >= 8192].copy()
        if not anchors.empty:
            ax.scatter(
                anchors["Pi_m"],
                anchors["Pi_f"],
                marker="*",
                s=220,
                facecolors="none",
                edgecolors="#111111",
                linewidths=1.2,
                zorder=5,
            )

    for overlay_name in overlay_windows:
        bounds = scan_windows[overlay_name]
        draw_window(
            ax,
            bounds,
            color=WINDOW_COLORS[overlay_name],
            linestyle=WINDOW_STYLES[overlay_name],
            label=overlay_name.replace("_", " ").replace("scan", "window"),
        )

    bounds = stage_window(df)
    make_locator_inset(ax, bounds, global_limits)

    ax.set_xlabel("Pi_m")
    ax.set_ylabel("Pi_f")
    ax.set_title(PANEL_TITLES[scan_name], fontsize=12)
    ax.grid(alpha=0.22, linewidth=0.6)
    ax.text(
        0.03,
        0.05,
        f"{stage_sampling_label(df)}\n{PANEL_NOTES[scan_name]}",
        transform=ax.transAxes,
        fontsize=8.5,
        bbox={"facecolor": "white", "alpha": 0.88, "edgecolor": "0.8"},
    )
    annotate_panel_letter(ax, panel_letter)
    return scatter


def build_figure(scan_dfs: dict[str, pd.DataFrame]) -> None:
    scan_windows = {name: stage_window(df) for name, df in scan_dfs.items()}
    global_limits = {
        "xlim": (
            min(float(df["Pi_m"].min()) for df in scan_dfs.values()) * 0.95,
            max(float(df["Pi_m"].max()) for df in scan_dfs.values()) * 1.05,
        ),
        "ylim": (
            min(float(df["Pi_f"].min()) for df in scan_dfs.values()) * 0.95,
            max(float(df["Pi_f"].max()) for df in scan_dfs.values()) * 1.05,
        ),
    }

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    fig.subplots_adjust(left=0.08, right=0.91, bottom=0.14, top=0.88, wspace=0.28, hspace=0.30)

    scatter = None
    config = {
        "coarse_scan": {"overlay": ["refinement_scan", "precision_scan", "confirmatory_scan"], "label_winners": False, "mark_anchors": False},
        "refinement_scan": {"overlay": ["precision_scan", "confirmatory_scan"], "label_winners": False, "mark_anchors": False},
        "precision_scan": {"overlay": ["confirmatory_scan"], "label_winners": True, "mark_anchors": False},
        "confirmatory_scan": {"overlay": [], "label_winners": True, "mark_anchors": True},
    }

    for panel_letter, ax, scan_name in zip(("A", "B", "C", "D"), axes, PANEL_ORDER):
        scatter = plot_panel(
            ax,
            scan_dfs[scan_name],
            scan_name=scan_name,
            panel_letter=panel_letter,
            global_limits=global_limits,
            scan_windows=scan_windows,
            overlay_windows=config[scan_name]["overlay"],
            label_winners=config[scan_name]["label_winners"],
            mark_anchors=config[scan_name]["mark_anchors"],
        )

    if scatter is not None:
        cbar = fig.colorbar(scatter, ax=axes.tolist(), shrink=0.86, pad=0.02)
        cbar.set_label("stage-local composite screening score")

    legend_handles = [
        plt.Line2D([0], [0], marker="D", color="w", label=label, markerfacecolor=color, markeredgecolor="black", markersize=8)
        for label, color in [("success winner", OBJECTIVE_COLORS["Psucc_mean"]), ("efficiency winner", OBJECTIVE_COLORS["eta_sigma_mean"]), ("speed winner", OBJECTIVE_COLORS["MFPT_mean"])]
    ]
    legend_handles.extend(
        [
            plt.Line2D([0], [0], marker="o", color="#222222", label="top stage-local screening candidates", markerfacecolor="none", markersize=8, linewidth=0),
            plt.Line2D([0], [0], marker="*", color="#111111", label="8192 anchor re-evaluations", markerfacecolor="none", markersize=10, linewidth=0),
        ]
    )
    fig.legend(handles=legend_handles, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.02), fontsize=8)

    fig.suptitle("Extended Data Figure 1. Scan Localization Chronology and Numerical Search History", fontsize=17, fontweight="bold")
    fig.text(
        0.5,
        0.94,
        "Search-history figure only: stage-local screening maps document how the numerical search narrowed toward the final local window.",
        ha="center",
        fontsize=10,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=220, bbox_inches="tight")
    fig.savefig(SVG_PATH, bbox_inches="tight")
    plt.close(fig)


def write_manifest(scan_dfs: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# Extended Data Figure 1 Panel Manifest",
        "",
        "## Scope",
        "",
        "This note documents the panel logic for Extended Data Figure 1, which is about scan localization chronology and numerical search history rather than about the final principle claim.",
        "",
        "Primary data sources:",
        "",
        f"- [coarse summary.parquet](file://{SCAN_PATHS['coarse_scan']})",
        f"- [refinement summary.parquet](file://{SCAN_PATHS['refinement_scan']})",
        f"- [precision summary.parquet](file://{SCAN_PATHS['precision_scan']})",
        f"- [confirmatory summary.parquet](file://{SCAN_PATHS['confirmatory_scan']})",
        f"- [ED Figure 1 PNG](file://{PNG_PATH})",
        f"- [ED Figure 1 SVG](file://{SVG_PATH})",
        "",
        "## Visual Language",
        "",
        "- every panel uses log-scaled `Pi_m` on the x-axis and log-scaled `Pi_f` on the y-axis",
        "- point color encodes a stage-local composite screening score built from normalized `Psucc_mean`, `eta_sigma_mean`, and inverse `MFPT_mean`",
        "- open black circles mark the top stage-local screening candidates",
        "- blue, green, and red diamonds mark the stage-local success, efficiency, and speed winners",
        "- dashed chronology boxes show the next-stage search windows",
        "- locator insets show each panel's zoom level within the full search frame",
        "- stars in the confirmatory panel mark `8192`-trajectory re-evaluations",
        "- per-panel note boxes report the number of state points and the trajectory count used at that stage",
        "",
        "## Panel Logic",
        "",
        "### Panel A",
        "",
        f"- title: `{PANEL_TITLES['coarse_scan']}`",
        "- purpose: show the broad initial productive region with outer-frame context",
        "- chronology overlays: refinement, precision, and confirmatory search windows",
        "- emphasis: broad search coverage rather than final ridge interpretation",
        "",
        "### Panel B",
        "",
        f"- title: `{PANEL_TITLES['refinement_scan']}`",
        "- purpose: show contraction toward the low-`Pi_f` productive family",
        "- chronology overlays: precision and confirmatory search windows",
        "- emphasis: narrowing of the active search region rather than final front geometry",
        "",
        "### Panel C",
        "",
        f"- title: `{PANEL_TITLES['precision_scan']}`",
        "- purpose: show local resolution of success, efficiency, and speed tips on the narrowed ridge family",
        "- chronology overlays: confirmatory search window",
        "- emphasis: local objective-tip separation before uncertainty-reduced confirmation",
        "",
        "### Panel D",
        "",
        f"- title: `{PANEL_TITLES['confirmatory_scan']}`",
        "- purpose: show the uncertainty-reduced final local search structure",
        "- chronology overlays: none",
        "- emphasis: re-evaluated anchor points and final local refinement, not the full principle claim",
        "",
        "## Why this does not duplicate Main Figure 2",
        "",
        "- this extended-data figure uses `Pi_m`-`Pi_f` search maps with stage-local screening scores and chronology boxes",
        "- main Figure 2 uses the confirmatory ridge itself, front-tip overlap, and objective-space separation to make the core structural claim",
        "- Extended Data Figure 1 is therefore about how the search converged, not about the final ceiling claim",
        "",
        "## Dataset Sizes",
        "",
    ]
    for scan_name in PANEL_ORDER:
        df = scan_dfs[scan_name]
        lines.append(f"- `{scan_name}`: `{len(df)}` state points, `Pi_m` in `[{df['Pi_m'].min():.3f}, {df['Pi_m'].max():.3f}]`, `Pi_f` in `[{df['Pi_f'].min():.3f}, {df['Pi_f'].max():.3f}]`")
    lines.extend(
        [
            "",
            "## Bottom Line",
            "",
            "Extended Data Figure 1 exists to show the narrowing of the numerical search process from a broad coarse scan to a resolved local confirmatory structure. It supports confidence in the convergence history without competing with the main-text ridge and principle figures.",
            "",
        ]
    )
    MANIFEST_DOC_PATH.write_text("\n".join(lines), encoding="ascii")


def build_outputs() -> dict[str, str]:
    scan_dfs = {name: add_stage_screening_score(load_scan(name)) for name in PANEL_ORDER}
    build_figure(scan_dfs)
    write_manifest(scan_dfs)
    return {
        "png": str(PNG_PATH),
        "svg": str(SVG_PATH),
        "manifest_doc": str(MANIFEST_DOC_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Extended Data Figure 1: scan localization chronology and numerical search history.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
