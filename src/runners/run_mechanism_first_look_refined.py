from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFINED_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "refined_summary_by_point.csv"
REFINED_COMPARE_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "old_vs_refined_summary.csv"
FIRST_LOOK_DOC_PATH = PROJECT_ROOT / "docs" / "mechanism_first_look_refined.md"
DISCRIMINATOR_DOC_PATH = PROJECT_ROOT / "docs" / "mechanism_discriminators_refined.md"
FIGURE_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "mechanism_discriminator_summary.png"


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def load_refined_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_df = pd.read_csv(REFINED_SUMMARY_PATH)
    compare_df = pd.read_csv(REFINED_COMPARE_PATH)
    return summary_df, compare_df


def build_candidate_discriminators(summary_df: pd.DataFrame) -> pd.DataFrame:
    balanced = summary_df[summary_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = summary_df[summary_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    candidates = [
        ("first_gate_commit_delay", "First Commit Delay", True),
        ("wall_dwell_before_first_commit", "Wall Dwell Before Commit", True),
        ("trap_burden_mean", "Trap Burden", True),
        ("steering_lag_at_commit_mean", "Steering Lag At Commit", False),
        ("signed_wall_tangent_mean", "Signed Wall Tangent", False),
        ("signed_gate_approach_angle_mean", "Signed Gate Approach Angle", False),
        ("local_recirculation_polarity_mean", "Gate Recirculation Polarity", False),
        ("wall_circulation_signed_mean", "Wall Circulation Signed", False),
    ]
    rows: list[dict[str, float | str | bool]] = []
    for column, label, trustworthy in candidates:
        series = summary_df[column].astype(float)
        spread = float(series.max() - series.min())
        delta = float(stale[column] - balanced[column])
        normalized = abs(delta) / spread if spread > 0.0 else 0.0
        rows.append(
            {
                "column": column,
                "label": label,
                "trustworthy_now": trustworthy,
                "balanced_value": float(balanced[column]),
                "stale_value": float(stale[column]),
                "delta_stale_minus_balanced": delta,
                "range_across_points": spread,
                "matched_pair_range_fraction": normalized,
            }
        )
    return pd.DataFrame(rows).sort_values("matched_pair_range_fraction", ascending=False).reset_index(drop=True)


def make_figure(summary_df: pd.DataFrame, discriminator_df: pd.DataFrame) -> None:
    ordered = summary_df.copy()
    ordered["label_short"] = ordered["canonical_label"].str.replace("OP_", "", regex=False)
    matched = ordered[ordered["canonical_label"].isin(["OP_BALANCED_RIDGE_MID", "OP_STALE_CONTROL_OFF_RIDGE"])].copy()
    trust = discriminator_df[discriminator_df["trustworthy_now"]].copy()
    caution = discriminator_df[~discriminator_df["trustworthy_now"]].copy()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))

    ax = axes[0]
    x = np.arange(len(ordered))
    width = 0.38
    ax.bar(x - width / 2, ordered["first_gate_commit_delay"], width=width, label="First Commit Delay", color="#3182bd")
    ax.bar(x + width / 2, ordered["wall_dwell_before_first_commit"], width=width, label="Wall Dwell Before Commit", color="#6baed6")
    ax.set_xticks(x)
    ax.set_xticklabels(ordered["label_short"], rotation=35)
    ax.set_title("Pre-Commit Timing")
    ax.legend(fontsize=8)

    ax = axes[1]
    metrics = [
        ("first_gate_commit_delay", "Delay"),
        ("wall_dwell_before_first_commit", "Wall Dwell"),
        ("trap_burden_mean", "Trap Burden"),
    ]
    x = np.arange(len(metrics))
    ax.bar(x - width / 2, [float(matched.iloc[0][m[0]]) for m in metrics], width=width, color="#74c476", label="Balanced Ridge")
    ax.bar(x + width / 2, [float(matched.iloc[1][m[0]]) for m in metrics], width=width, color="#fb6a4a", label="Stale Control")
    ax.set_xticks(x)
    ax.set_xticklabels([m[1] for m in metrics], rotation=25)
    ax.set_title("Matched Ridge Vs Stale")
    ax.legend(fontsize=8)

    ax = axes[2]
    y = np.arange(len(discriminator_df))
    colors = ["#238b45" if trustworthy else "#9e9ac8" for trustworthy in discriminator_df["trustworthy_now"]]
    ax.barh(y, discriminator_df["matched_pair_range_fraction"], color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels(discriminator_df["label"])
    ax.invert_yaxis()
    ax.set_title("Matched-Pair Discriminator Strength")
    ax.set_xlabel("|stale - ridge| / range")

    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_first_look_doc(summary_df: pd.DataFrame, discriminator_df: pd.DataFrame) -> None:
    ordered = summary_df.set_index("canonical_label")
    trustworthy = discriminator_df[discriminator_df["trustworthy_now"]].copy()
    balanced = ordered.loc["OP_BALANCED_RIDGE_MID"]
    stale = ordered.loc["OP_STALE_CONTROL_OFF_RIDGE"]
    success = ordered.loc["OP_SUCCESS_TIP"]
    efficiency = ordered.loc["OP_EFFICIENCY_TIP"]
    speed = ordered.loc["OP_SPEED_TIP"]

    lines = [
        "# Mechanism First Look Refined",
        "",
        "## Scope",
        "",
        "This note gives the first robust mechanism reading from the refined canonical-only mechanism dataset, using only observables that are already trustworthy enough for interpretation.",
        "",
        f"- refined summary source: {_path_link(REFINED_SUMMARY_PATH)}",
        f"- refined comparison source: {_path_link(REFINED_COMPARE_PATH)}",
        f"- discriminator figure: {_path_link(FIGURE_PATH)}",
        "",
        "Excluded from the central mechanism argument:",
        "",
        "- `crossing_given_commit` as a primary explanatory rate, because the refined gate-crossing counts remain too sparse for a committed crossing-rate theory.",
        "",
        "## Canonical Mechanism Comparison",
        "",
        "The five canonical points already separate cleanly in pre-commit timing, while post-commit crossing remains too sparse to explain the front structure directly.",
        "",
        f"- `OP_SPEED_TIP` is the earliest committing branch: first commit delay `{speed['first_gate_commit_delay']:.4f}`, wall dwell before first commit `{speed['wall_dwell_before_first_commit']:.4f}`.",
        f"- `OP_SUCCESS_TIP` is the latest and most deliberate branch: first commit delay `{success['first_gate_commit_delay']:.4f}`, wall dwell before first commit `{success['wall_dwell_before_first_commit']:.4f}`.",
        f"- `OP_EFFICIENCY_TIP` sits between success and balanced in commitment timing: first commit delay `{efficiency['first_gate_commit_delay']:.4f}`.",
        f"- `OP_BALANCED_RIDGE_MID` is the ridge reference: first commit delay `{balanced['first_gate_commit_delay']:.4f}`, wall dwell `{balanced['wall_dwell_before_first_commit']:.4f}`, zero trap burden.",
        f"- `OP_STALE_CONTROL_OFF_RIDGE` differs from the matched ridge point mainly through slower pre-commit timing and nonzero trap burden: first commit delay `{stale['first_gate_commit_delay']:.4f}`, wall dwell `{stale['wall_dwell_before_first_commit']:.4f}`, trap burden `{stale['trap_burden_mean']:.6f}`.",
        "",
        "## Which Observables Best Separate The Canonical Points?",
        "",
        "Most useful now:",
        "",
        f"- `first_gate_commit_delay`: spans from `{speed['first_gate_commit_delay']:.4f}` at `OP_SPEED_TIP` to `{success['first_gate_commit_delay']:.4f}` at `OP_SUCCESS_TIP`, and also separates the balanced ridge point from the stale-control point.",
        f"- `wall_dwell_before_first_commit`: follows the same ordering, from `{speed['wall_dwell_before_first_commit']:.4f}` to `{success['wall_dwell_before_first_commit']:.4f}`.",
        f"- `trap_burden_mean`: remains zero on the productive ridge points and rises only on the stale-control point (`{stale['trap_burden_mean']:.6f}`) and, weakly, on the success tip (`{success['trap_burden_mean']:.6f}`).",
        "",
        "Secondary but not central:",
        "",
        f"- `steering_lag_at_commit_mean`: small but nonzero across the set, with matched-pair values `{balanced['steering_lag_at_commit_mean']:.4f}` and `{stale['steering_lag_at_commit_mean']:.4f}`; useful as a cautionary secondary diagnostic, not as the main separator.",
        f"- signed directional observables: their matched-pair signs change in some cases, but their point-level means remain small enough that they are not yet as robust as the timing and trap signals.",
        "",
        "## Is the productive-memory ridge mainly a pre-commit phenomenon?",
        "",
        "Yes, in the first robust reading.",
        "",
        "The strongest trustworthy ordering across the success, efficiency, speed, ridge-mid, and stale-control points appears before strong gate commitment:",
        "",
        f"- speed corresponds to the shortest first-commit delay (`{speed['first_gate_commit_delay']:.4f}`) and shortest pre-commit wall dwell (`{speed['wall_dwell_before_first_commit']:.4f}`)",
        f"- success corresponds to the longest first-commit delay (`{success['first_gate_commit_delay']:.4f}`) and longest pre-commit wall dwell (`{success['wall_dwell_before_first_commit']:.4f}`)",
        f"- the balanced ridge and stale-control comparison is also dominated by a pre-commit shift: delay `{balanced['first_gate_commit_delay']:.4f}` -> `{stale['first_gate_commit_delay']:.4f}`, wall dwell `{balanced['wall_dwell_before_first_commit']:.4f}` -> `{stale['wall_dwell_before_first_commit']:.4f}`",
        "",
        "By contrast, the refined crossing probability from the commit state remains far too sparse to support a post-commit crossing-control explanation. The current front structure is therefore most plausibly read as a difference in how trajectories arrive at and prepare for commitment, not in how they traverse the doorway after commitment.",
        "",
        "## Matched Comparison: Balanced Ridge Vs Stale Control",
        "",
        f"- first gate commit delay: `{balanced['first_gate_commit_delay']:.4f}` vs `{stale['first_gate_commit_delay']:.4f}`",
        f"- wall dwell before first commit: `{balanced['wall_dwell_before_first_commit']:.4f}` vs `{stale['wall_dwell_before_first_commit']:.4f}`",
        f"- trap burden mean: `{balanced['trap_burden_mean']:.6f}` vs `{stale['trap_burden_mean']:.6f}`",
        f"- steering lag at commit mean: `{balanced['steering_lag_at_commit_mean']:.4f}` vs `{stale['steering_lag_at_commit_mean']:.4f}`",
        "",
        "This matched pair already supports a cautious mechanism statement: increasing `Pi_f` at fixed `Pi_m` and `Pi_U` primarily delays or prolongs pre-commit search and adds rare but real stale trapping, rather than cleanly changing a post-commit crossing rate.",
        "",
        "## Which mechanism signals are already robust enough for principle-building?",
        "",
        "- Robust now: `first_gate_commit_delay`, `wall_dwell_before_first_commit`, and source-aligned `trap_burden_mean`.",
        "- Useful but secondary: `steering_lag_at_commit_mean` when interpreted as a weak supporting diagnostic rather than a headline separator.",
        "- Not yet robust enough for central principle-building: the signed directional observables as leading signals, and any crossing-rate quantity derived from `gate_crossing`.",
        "",
        "## Practical Summary",
        "",
        "The current refined mechanism picture is that the productive-memory ridge is distinguished mainly by how trajectories organize wall-guided search before commitment. The success, efficiency, and speed tips differ primarily in the timing budget they spend before strong commitment, while the stale-control point differs from the balanced ridge point by slightly slower pre-commit timing and a small but source-aligned trap burden.",
    ]
    FIRST_LOOK_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_discriminator_doc(summary_df: pd.DataFrame, discriminator_df: pd.DataFrame) -> None:
    ordered = summary_df.set_index("canonical_label")
    balanced = ordered.loc["OP_BALANCED_RIDGE_MID"]
    stale = ordered.loc["OP_STALE_CONTROL_OFF_RIDGE"]
    trustworthy = discriminator_df[discriminator_df["trustworthy_now"]].copy()
    top = trustworthy.sort_values("matched_pair_range_fraction", ascending=False)

    lines = [
        "# Mechanism Discriminators Refined",
        "",
        "## Scope",
        "",
        "This note ranks the current refined mechanism observables by how useful they are for trustworthy interpretation, with the balanced-ridge versus stale-control comparison as the main test.",
        "",
        f"- refined summary source: {_path_link(REFINED_SUMMARY_PATH)}",
        f"- figure: {_path_link(FIGURE_PATH)}",
        "",
        "## Trusted Discriminator Ranking",
        "",
        top[["label", "balanced_value", "stale_value", "delta_stale_minus_balanced", "matched_pair_range_fraction"]].to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        f"- `Trap Burden` is the sharpest matched-pair discriminator because it stays at `{balanced['trap_burden_mean']:.6f}` on the balanced ridge point and rises to `{stale['trap_burden_mean']:.6f}` off ridge.",
        f"- `First Commit Delay` and `Wall Dwell Before First Commit` are the strongest smooth pre-commit discriminators and also explain the success-speed-efficiency ordering across the canonical front tips.",
        f"- `Steering Lag At Commit` is measurable but weaker and should remain a supporting signal rather than a primary mechanism axis.",
        "",
        "## Directional Observables",
        "",
        discriminator_df[~discriminator_df["trustworthy_now"]][["label", "balanced_value", "stale_value", "delta_stale_minus_balanced", "matched_pair_range_fraction"]].to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        "- The signed directional observables are useful because they now preserve polarity, but their point-level means remain small enough that they should be treated as exploratory diagnostics rather than firm mechanism discriminators.",
        "",
        "## Front-Tip Mechanism Ordering",
        "",
        "- `OP_SPEED_TIP`: shortest pre-commit timing budget; fastest branch, but lowest success.",
        "- `OP_EFFICIENCY_TIP`: intermediate-to-long pre-commit timing without visible trap burden; efficient but not as selective as the success tip.",
        "- `OP_SUCCESS_TIP`: longest pre-commit timing and largest wall dwell; slowest to commit, but highest success.",
        "- `OP_BALANCED_RIDGE_MID`: central ridge compromise with moderate pre-commit timing and no trap burden.",
        "- `OP_STALE_CONTROL_OFF_RIDGE`: close to the balanced ridge point in most gate-local means, but shifted toward slower pre-commit timing and rare stale trapping.",
        "",
        "## Mechanism Summary",
        "",
        "The first robust discriminator set supports a compact reduced-theory direction: use pre-commit timing plus trap burden as the main mechanism coordinates, and treat steering-lag and directional observables as secondary annotations rather than first-fit state rates.",
    ]
    DISCRIMINATOR_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_outputs() -> dict[str, str]:
    summary_df, compare_df = load_refined_inputs()
    del compare_df
    discriminator_df = build_candidate_discriminators(summary_df)
    make_figure(summary_df, discriminator_df)
    write_first_look_doc(summary_df, discriminator_df)
    write_discriminator_doc(summary_df, discriminator_df)
    return {
        "mechanism_first_look": str(FIRST_LOOK_DOC_PATH),
        "mechanism_discriminators": str(DISCRIMINATOR_DOC_PATH),
        "discriminator_figure": str(FIGURE_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the first robust refined mechanism note from trustworthy observables.")
    parser.parse_args(argv)
    result = build_outputs()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
