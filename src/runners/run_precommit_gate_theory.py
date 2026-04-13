from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFINED_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "refined_summary_by_point.csv"
EVENT_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "event_level.parquet"
DOC_PATH = PROJECT_ROOT / "docs" / "precommit_gate_theory_state_graph.md"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "gate_theory"
FIGURE_PATH = FIGURE_DIR / "precommit_state_graph.png"


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_df = pd.read_csv(REFINED_SUMMARY_PATH)
    event_df = pd.read_parquet(EVENT_PATH)
    return summary_df, event_df


def transition_matrix(event_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for label, group in event_df.groupby("canonical_label"):
        for src, sub in group.groupby("event_type"):
            total = len(sub)
            vc = sub["exited_to_event_type"].value_counts(normalize=True)
            for dst, prob in vc.items():
                rows.append(
                    {
                        "canonical_label": label,
                        "src": src,
                        "dst": dst,
                        "prob": float(prob),
                        "count": int((sub["exited_to_event_type"] == dst).sum()),
                        "total_from_src": int(total),
                    }
                )
    return pd.DataFrame(rows)


def pooled_transition_summary(transitions: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        transitions.groupby(["src", "dst"])
        .agg(
            mean_prob=("prob", "mean"),
            min_prob=("prob", "min"),
            max_prob=("prob", "max"),
            total_count=("count", "sum"),
            min_source_count=("total_from_src", "min"),
        )
        .reset_index()
    )
    return grouped.sort_values(["src", "total_count"], ascending=[True, False]).reset_index(drop=True)


def matched_pair_summary(summary_df: pd.DataFrame) -> dict[str, float]:
    balanced = summary_df[summary_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = summary_df[summary_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    return {
        "balanced_first_commit_delay": float(balanced["first_gate_commit_delay"]),
        "stale_first_commit_delay": float(stale["first_gate_commit_delay"]),
        "balanced_wall_dwell": float(balanced["wall_dwell_before_first_commit"]),
        "stale_wall_dwell": float(stale["wall_dwell_before_first_commit"]),
        "balanced_trap_burden": float(balanced["trap_burden_mean"]),
        "stale_trap_burden": float(stale["trap_burden_mean"]),
        "balanced_residence_commit": float(balanced["commit_given_residence"]),
        "stale_residence_commit": float(stale["commit_given_residence"]),
    }


def edge_prob(summary: pd.DataFrame, src: str, dst: str) -> float:
    row = summary[(summary["src"] == src) & (summary["dst"] == dst)]
    if row.empty:
        return 0.0
    return float(row["mean_prob"].iloc[0])


def draw_node(ax: plt.Axes, x: float, y: float, label: str, *, facecolor: str) -> None:
    node = Circle((x, y), radius=0.12, facecolor=facecolor, edgecolor="#2b2b2b", linewidth=1.2)
    ax.add_patch(node)
    ax.text(x, y, label, ha="center", va="center", fontsize=9)


def draw_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    text: str,
    color: str,
    rad: float = 0.0,
    linestyle: str = "-",
    linewidth: float = 1.8,
    text_offset: tuple[float, float] = (0.0, 0.0),
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=linewidth,
        color=color,
        linestyle=linestyle,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)
    mx = 0.5 * (start[0] + end[0]) + text_offset[0]
    my = 0.5 * (start[1] + end[1]) + text_offset[1]
    ax.text(mx, my, text, fontsize=8, color=color, ha="center", va="center")


def make_figure(summary_df: pd.DataFrame, pooled_df: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    pooled = pooled_df.set_index(["src", "dst"])
    precommit_commit = edge_prob(pooled_df, "gate_residence_precommit", "gate_commit")
    precommit_wall = edge_prob(pooled_df, "gate_residence_precommit", "wall_sliding")
    precommit_bulk = edge_prob(pooled_df, "gate_residence_precommit", "bulk_motion")
    wall_bulk = edge_prob(pooled_df, "wall_sliding", "bulk_motion")
    bulk_wall = edge_prob(pooled_df, "bulk_motion", "wall_sliding")
    approach_res = edge_prob(pooled_df, "gate_approach", "gate_residence_precommit")
    wall_approach = edge_prob(pooled_df, "wall_sliding", "gate_approach")
    bulk_approach = edge_prob(pooled_df, "bulk_motion", "gate_approach")
    commit_res = edge_prob(pooled_df, "gate_commit", "gate_residence_precommit")

    # Minimal model
    ax = axes[0]
    ax.set_title("Minimal Pre-Commit Model")
    positions = {
        "bulk": (0.18, 0.55),
        "wall": (0.42, 0.78),
        "res": (0.68, 0.55),
        "commit": (0.84, 0.30),
        "trap": (0.42, 0.18),
    }
    draw_node(ax, *positions["bulk"], "bulk", facecolor="#deebf7")
    draw_node(ax, *positions["wall"], "wall_sliding", facecolor="#c6dbef")
    draw_node(ax, *positions["res"], "gate_residence_precommit", facecolor="#c7e9c0")
    draw_node(ax, *positions["commit"], "gate_commit", facecolor="#74c476")
    draw_node(ax, *positions["trap"], "trap_episode", facecolor="#fcbba1")
    draw_arrow(ax, positions["bulk"], positions["wall"], text=f"{bulk_wall:.3f}", color="#3182bd", rad=0.12, text_offset=(0.0, 0.07))
    draw_arrow(ax, positions["wall"], positions["bulk"], text=f"{wall_bulk:.3f}", color="#3182bd", rad=0.12, text_offset=(0.0, -0.07))
    draw_arrow(ax, positions["wall"], positions["res"], text="effective arrival\nvia approach", color="#31a354", rad=-0.10, text_offset=(0.02, 0.08))
    draw_arrow(ax, positions["bulk"], positions["res"], text="rare direct\nnear-mouth arrival", color="#74c476", rad=-0.10, linestyle="--", linewidth=1.5, text_offset=(0.06, -0.07))
    draw_arrow(ax, positions["res"], positions["commit"], text=f"{precommit_commit:.3f}", color="#006d2c", text_offset=(0.02, 0.05))
    draw_arrow(ax, positions["res"], positions["wall"], text=f"{precommit_wall:.3f}", color="#31a354", rad=0.20, text_offset=(-0.02, 0.05))
    draw_arrow(ax, positions["res"], positions["bulk"], text=f"{precommit_bulk:.3f}", color="#31a354", rad=-0.18, text_offset=(0.0, -0.07))
    draw_arrow(ax, positions["commit"], positions["res"], text=f"{commit_res:.3f}", color="#e6550d", text_offset=(-0.02, -0.05))
    draw_arrow(ax, positions["wall"], positions["trap"], text="rare stale\nentry", color="#cb181d", linestyle="--", linewidth=1.5, text_offset=(-0.06, 0.0))
    draw_arrow(ax, positions["res"], positions["trap"], text="defer:\ninsufficient counts", color="#fb6a4a", linestyle="--", linewidth=1.5, text_offset=(0.06, 0.0))
    ax.text(0.03, 0.03, "Trustworthy now: timing to commit, residence->commit,\nresidence->bulk/wall recycling, trap burden as occupancy only.", transform=ax.transAxes, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Richer model
    ax = axes[1]
    ax.set_title("Slightly Richer Pre-Commit Model")
    positions = {
        "bulk": (0.14, 0.58),
        "wall": (0.34, 0.82),
        "approach": (0.56, 0.70),
        "res": (0.72, 0.48),
        "commit": (0.86, 0.22),
        "trap": (0.42, 0.16),
    }
    draw_node(ax, *positions["bulk"], "bulk", facecolor="#deebf7")
    draw_node(ax, *positions["wall"], "wall_sliding", facecolor="#c6dbef")
    draw_node(ax, *positions["approach"], "gate_approach", facecolor="#bae4b3")
    draw_node(ax, *positions["res"], "gate_residence_precommit", facecolor="#74c476")
    draw_node(ax, *positions["commit"], "gate_commit", facecolor="#238b45")
    draw_node(ax, *positions["trap"], "trap_episode", facecolor="#fcbba1")
    draw_arrow(ax, positions["bulk"], positions["wall"], text=f"{bulk_wall:.3f}", color="#3182bd", rad=0.10, text_offset=(0.0, 0.05))
    draw_arrow(ax, positions["wall"], positions["bulk"], text=f"{wall_bulk:.3f}", color="#3182bd", rad=0.10, text_offset=(0.0, -0.05))
    draw_arrow(ax, positions["wall"], positions["approach"], text=f"{wall_approach:.3f}", color="#31a354", text_offset=(-0.02, 0.05))
    draw_arrow(ax, positions["bulk"], positions["approach"], text=f"{bulk_approach:.3f}", color="#74c476", text_offset=(0.02, 0.05))
    draw_arrow(ax, positions["approach"], positions["res"], text=f"{approach_res:.3f}", color="#238b45", text_offset=(0.02, 0.05))
    draw_arrow(ax, positions["approach"], positions["bulk"], text=f"{edge_prob(pooled_df, 'gate_approach', 'bulk_motion'):.3f}", color="#31a354", rad=-0.15, text_offset=(-0.02, -0.07))
    draw_arrow(ax, positions["approach"], positions["wall"], text=f"{edge_prob(pooled_df, 'gate_approach', 'wall_sliding'):.3f}", color="#31a354", rad=0.18, text_offset=(-0.02, 0.03))
    draw_arrow(ax, positions["res"], positions["commit"], text=f"{precommit_commit:.3f}", color="#006d2c", text_offset=(0.02, 0.05))
    draw_arrow(ax, positions["res"], positions["wall"], text=f"{precommit_wall:.3f}", color="#31a354", rad=0.20, text_offset=(-0.04, 0.02))
    draw_arrow(ax, positions["res"], positions["bulk"], text=f"{precommit_bulk:.3f}", color="#31a354", rad=-0.18, text_offset=(0.02, -0.05))
    draw_arrow(ax, positions["res"], positions["approach"], text=f"{edge_prob(pooled_df, 'gate_residence_precommit', 'gate_approach'):.3f}", color="#74c476", text_offset=(-0.02, 0.06))
    draw_arrow(ax, positions["commit"], positions["res"], text=f"{commit_res:.3f}", color="#e6550d", text_offset=(-0.02, -0.05))
    draw_arrow(ax, positions["commit"], positions["wall"], text="defer crossing-\nspecific branch", color="#fb6a4a", linestyle="--", linewidth=1.5, rad=-0.25, text_offset=(0.06, -0.06))
    draw_arrow(ax, positions["wall"], positions["trap"], text="rare", color="#cb181d", linestyle="--", linewidth=1.5, text_offset=(-0.05, 0.0))
    ax.text(0.03, 0.03, "Richer model keeps approach explicit.\nStill stop theory at commit: crossing remains too sparse.", transform=ax.transAxes, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_doc(summary_df: pd.DataFrame, pooled_df: pd.DataFrame) -> None:
    matched = matched_pair_summary(summary_df)
    success = summary_df.set_index("canonical_label").loc["OP_SUCCESS_TIP"]
    speed = summary_df.set_index("canonical_label").loc["OP_SPEED_TIP"]
    efficiency = summary_df.set_index("canonical_label").loc["OP_EFFICIENCY_TIP"]
    balanced = summary_df.set_index("canonical_label").loc["OP_BALANCED_RIDGE_MID"]
    stale = summary_df.set_index("canonical_label").loc["OP_STALE_CONTROL_OFF_RIDGE"]

    robust_rows = pooled_df[
        pooled_df["src"].isin(["bulk_motion", "wall_sliding", "gate_approach", "gate_residence_precommit", "gate_commit"])
        & pooled_df["dst"].isin(["bulk_motion", "wall_sliding", "gate_approach", "gate_residence_precommit", "gate_commit"])
        & (pooled_df["total_count"] >= 1000)
    ][["src", "dst", "mean_prob", "min_prob", "max_prob", "total_count"]]

    lines = [
        "# Precommit Gate Theory State Graph",
        "",
        "## Scope",
        "",
        "This note defines the first coarse-grained gate theory around the pre-commit bottleneck only. It uses the refined mechanism dataset and stops the reduced theory at `gate_commit` rather than forcing an early doorway-crossing model.",
        "",
        f"- refined summary source: {_path_link(REFINED_SUMMARY_PATH)}",
        f"- refined event source: {_path_link(EVENT_PATH)}",
        f"- state-graph figure: {_path_link(FIGURE_PATH)}",
        "",
        "## Minimal Pre-Commit State Graph",
        "",
        "Minimal robust model:",
        "",
        "- `bulk`",
        "- `wall_sliding`",
        "- `gate_residence_precommit`",
        "- `gate_commit`",
        "- `trap_episode`",
        "",
        "Interpretation:",
        "",
        "- `gate_approach` is collapsed into an effective arrival layer between non-gate search and precommit residence.",
        "- `trap_episode` is retained as an occupancy sink for stale burden, but its entry and escape transitions are too sparse to center the first theory.",
        "",
        "## Slightly Richer Pre-Commit State Graph",
        "",
        "Slightly richer model:",
        "",
        "- `bulk`",
        "- `wall_sliding`",
        "- `gate_approach`",
        "- `gate_residence_precommit`",
        "- `gate_commit`",
        "- `trap_episode`",
        "",
        "This richer model is still pre-crossing, but it preserves the arrival funnel into the doorway mouth.",
        "",
        "## Mapping Trustworthy Observables Onto The Graph",
        "",
        "- `first_gate_commit_delay`: first-passage observable from pre-commit search (`bulk`, `wall_sliding`, and optionally `gate_approach`) to `gate_commit`.",
        "- `wall_dwell_before_first_commit`: residence-time observable on the wall-guided branch before first entry into `gate_commit`.",
        "- `trap_burden_mean`: occupancy burden of the rare stale sink `trap_episode`, not yet a reliable transition-rate object.",
        "- `commit_given_residence`: robust transition fraction from `gate_residence_precommit` to `gate_commit`.",
        "- `residence_given_approach`: robust transition fraction from `gate_approach` to `gate_residence_precommit` in the richer model.",
        "- `return_to_wall_after_precommit_rate`: recycling from `gate_residence_precommit` back to wall-guided search.",
        "",
        "## Which Transitions Can Be Estimated Robustly Now?",
        "",
        robust_rows.to_markdown(index=False),
        "",
        "Robust now:",
        "",
        "- `bulk <-> wall_sliding`: dominant search-cycle backbone.",
        "- `wall_sliding -> gate_approach` and `bulk -> gate_approach`: robust approach-entry traffic in the richer model.",
        "- `gate_approach -> gate_residence_precommit`: robust precommit residence entry.",
        "- `gate_residence_precommit -> gate_commit`: robust commitment step.",
        "- `gate_residence_precommit -> bulk` and `gate_residence_precommit -> wall_sliding`: robust recycling out of the mouth before commitment.",
        "- `gate_commit -> gate_residence_precommit`: robust evidence that the present commit state is a pre-crossing preparation state rather than a crossing state.",
        "",
        "Not robust enough yet:",
        "",
        "- `trap_episode` entry and escape transitions as fitted rates, because total counts remain tiny.",
        "- any transition involving `gate_crossing`, because the crossing branch remains too sparse.",
        "",
        "## Why the first reduced theory should stop at gate commitment",
        "",
        "The refined mechanism analysis shows that the current front structure is already explained before the final transit step. Three observations make `gate_commit` the correct stopping point for the first reduced theory:",
        "",
        "- `crossing_given_commit` is still extremely small, so a crossing-rate theory would be numerically fragile.",
        "- `gate_commit -> gate_residence_precommit` is overwhelmingly dominant, which means the current commit state is still a preparation/recycling state rather than a resolved crossing state.",
        f"- the main canonical ordering already appears in `first_gate_commit_delay`: speed `{speed['first_gate_commit_delay']:.4f}`, balanced `{balanced['first_gate_commit_delay']:.4f}`, efficiency `{efficiency['first_gate_commit_delay']:.4f}`, success `{success['first_gate_commit_delay']:.4f}`.",
        "",
        "The first reduced theory should therefore explain commitment timing and precommit recycling, while explicitly deferring the final transit branch.",
        "",
        "## Which parts of the productive-memory ridge are explained before crossing?",
        "",
        "Most of the currently trustworthy ridge structure.",
        "",
        f"- `OP_SPEED_TIP` reaches commit fastest (`{speed['first_gate_commit_delay']:.4f}`) and has the shortest wall dwell before commit (`{speed['wall_dwell_before_first_commit']:.4f}`).",
        f"- `OP_SUCCESS_TIP` reaches commit slowest (`{success['first_gate_commit_delay']:.4f}`) and has the longest wall dwell before commit (`{success['wall_dwell_before_first_commit']:.4f}`).",
        f"- `OP_EFFICIENCY_TIP` stays between those extremes (`{efficiency['first_gate_commit_delay']:.4f}`), which fits the ridge tradeoff without invoking a crossing-rate hierarchy.",
        f"- the matched ridge-vs-stale difference is also precommit-dominated: delay `{matched['balanced_first_commit_delay']:.4f}` -> `{matched['stale_first_commit_delay']:.4f}`, wall dwell `{matched['balanced_wall_dwell']:.4f}` -> `{matched['stale_wall_dwell']:.4f}`.",
        f"- trap burden adds a small off-ridge penalty: `{matched['balanced_trap_burden']:.6f}` on the balanced ridge point vs `{matched['stale_trap_burden']:.6f}` at the stale-control point.",
        "",
        "What is not yet explained before crossing:",
        "",
        "- final transit success conditional on strong commitment",
        "- any post-crossing state sequence",
        "- crossing-specific rate asymmetries",
        "",
        "## Where ridge-vs-stale separation is encoded in the reduced graph",
        "",
        "Mainly in observables attached to search-to-commit timing, not in currently measured commitment probabilities.",
        "",
        f"- `time to first commit`: clear matched-pair shift (`{matched['balanced_first_commit_delay']:.4f}` vs `{matched['stale_first_commit_delay']:.4f}`)",
        f"- `probability of reaching commit` from precommit residence: almost unchanged (`{matched['balanced_residence_commit']:.4f}` vs `{matched['stale_residence_commit']:.4f}`)",
        "- `wall-to-residence cycling`: populated and meaningful, but only weakly different in the matched pair",
        "- `residence-to-trap recycling`: conceptually important for stale control, but still too sparse to estimate as a central transition object",
        "",
        "This means the first reduced theory should encode ridge-vs-stale separation primarily through a slower effective approach-to-commit clock plus a rare stale sink, not through a large change in commitment probability itself.",
        "",
        "## Proposed Models",
        "",
        "**Minimal model**",
        "",
        "- states: `bulk`, `wall_sliding`, `gate_residence_precommit`, `gate_commit`, `trap_episode`",
        "- use when the goal is a robust five-state precommit theory with maximal interpretability",
        "- treat `gate_approach` as an unresolved fast substep folded into the effective arrival process",
        "",
        "**Slightly richer model**",
        "",
        "- states: `bulk`, `wall_sliding`, `gate_approach`, `gate_residence_precommit`, `gate_commit`, `trap_episode`",
        "- use when the goal is to preserve doorway-mouth arrival explicitly while still stopping before crossing",
        "- this is the better candidate for later rate fitting once more precommit statistics are accumulated",
        "",
        "## Deferred Until Later Crossing-Specific Analysis",
        "",
        "- `gate_commit -> gate_crossing`",
        "- any transition beginning from `gate_crossing`",
        "- any full doorway-crossing success model",
        "- trap entry and trap escape rates as fitted kinetic parameters",
        "",
        "## Practical Conclusion",
        "",
        "The first robust gate theory should be a precommit bottleneck theory: trajectories separate mainly by how long they circulate between bulk, wall-guided motion, and precommit mouth residence before strong commitment. The productive-memory ridge is already largely explained by that precommit organization, while the final crossing step should be deferred to a later, crossing-specific analysis.",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_outputs() -> dict[str, str]:
    summary_df, event_df = load_inputs()
    transitions = transition_matrix(event_df)
    pooled_df = pooled_transition_summary(transitions)
    make_figure(summary_df, pooled_df)
    write_doc(summary_df, pooled_df)
    return {
        "doc": str(DOC_PATH),
        "figure": str(FIGURE_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the first pre-commit coarse-grained gate theory note.")
    parser.parse_args(argv)
    result = build_outputs()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
