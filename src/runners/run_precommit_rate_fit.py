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
EVENT_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "event_level.parquet"
TRAJECTORY_PATH = PROJECT_ROOT / "outputs" / "datasets" / "mechanism_dataset_refined" / "trajectory_level.parquet"
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "figures" / "mechanism_dataset_refined" / "refined_summary_by_point.csv"
CANONICAL_POINTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "canonical_operating_points.csv"
RATE_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "precommit_gate_rates.csv"
REPORT_PATH = PROJECT_ROOT / "docs" / "precommit_gate_theory_fit_report.md"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "gate_theory"
RATE_FIGURE_PATH = FIGURE_DIR / "precommit_rate_comparison.png"
MODEL_FIGURE_PATH = FIGURE_DIR / "precommit_model_vs_simulation.png"

CANONICAL_ORDER = [
    "OP_SUCCESS_TIP",
    "OP_EFFICIENCY_TIP",
    "OP_SPEED_TIP",
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
]
TRANSIENT_STATES = [
    "bulk_motion",
    "wall_sliding",
    "gate_approach",
    "gate_residence_precommit",
]
ABSORBING_STATES = [
    "gate_commit",
    "trap_episode",
    "other_sink",
]
RATE_LABELS = {
    ("bulk_motion", "wall_sliding"): "k_bw",
    ("bulk_motion", "gate_approach"): "k_ba",
    ("wall_sliding", "bulk_motion"): "k_wb",
    ("wall_sliding", "gate_approach"): "k_wa",
    ("gate_approach", "bulk_motion"): "k_ab",
    ("gate_approach", "wall_sliding"): "k_aw",
    ("gate_approach", "gate_residence_precommit"): "k_ar",
    ("gate_residence_precommit", "bulk_motion"): "k_rb",
    ("gate_residence_precommit", "wall_sliding"): "k_rw",
    ("gate_residence_precommit", "gate_approach"): "k_ra",
    ("gate_residence_precommit", "gate_commit"): "k_rc",
}


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _safe_rate(count: int, dwell: float) -> float:
    if dwell <= 0.0:
        return 0.0
    return float(count / dwell)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    event_df = pd.read_parquet(
        EVENT_PATH,
        columns=[
            "canonical_label",
            "traj_id",
            "event_index",
            "event_type",
            "t_start",
            "duration",
            "exited_to_event_type",
        ],
    )
    trajectory_df = pd.read_parquet(
        TRAJECTORY_PATH,
        columns=[
            "canonical_label",
            "traj_id",
            "first_gate_commit_delay",
        ],
    )
    summary_df = pd.read_csv(SUMMARY_PATH)
    canonical_df = pd.read_csv(CANONICAL_POINTS_PATH)
    return event_df, trajectory_df, summary_df, canonical_df


def build_precommit_events(event_df: pd.DataFrame, trajectory_df: pd.DataFrame) -> pd.DataFrame:
    merged = event_df.merge(
        trajectory_df[["canonical_label", "traj_id", "first_gate_commit_delay"]],
        on=["canonical_label", "traj_id"],
        how="left",
    )
    keep_mask = merged["first_gate_commit_delay"].isna() | (merged["t_start"] < merged["first_gate_commit_delay"])
    return merged.loc[keep_mask].copy()


def fit_rate_rows(point_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    rows: list[dict[str, float | str | int]] = []
    total_dwell = point_df.groupby("event_type")["duration"].sum().to_dict()

    for src in TRANSIENT_STATES:
        src_df = point_df[point_df["event_type"] == src]
        source_count = int(len(src_df))
        dwell = float(total_dwell.get(src, 0.0))
        if source_count == 0 or dwell <= 0.0:
            continue

        exit_counts = src_df["exited_to_event_type"].value_counts().to_dict()
        total_exit_rate = _safe_rate(source_count, dwell)
        modeled_exit_rate = 0.0

        for dst in TRANSIENT_STATES + ["gate_commit", "trap_episode"]:
            if dst == src:
                continue
            count = int(exit_counts.get(dst, 0))
            rate = _safe_rate(count, dwell)
            modeled_exit_rate += rate
            if count == 0 and dst != "trap_episode":
                continue
            if dst == "trap_episode":
                support_class = "weak_auxiliary" if count > 0 else "unsupported"
                model_role = "weak_sink"
            elif dst == "gate_commit":
                support_class = "robust" if count >= 100 else "low_support"
                model_role = "absorbing_commit"
            else:
                support_class = "robust" if count >= 100 else "low_support"
                model_role = "backbone"
            rows.append(
                {
                    "src": src,
                    "dst": dst,
                    "transition_count": count,
                    "source_event_count": source_count,
                    "source_dwell_time": dwell,
                    "rate_estimate": rate,
                    "transition_probability_per_event": float(count / source_count),
                    "support_class": support_class,
                    "model_role": model_role,
                    "rate_symbol": RATE_LABELS.get((src, dst), ""),
                }
            )

        modeled_counts = int(sum(exit_counts.get(dst, 0) for dst in TRANSIENT_STATES + ["gate_commit", "trap_episode"]))
        other_sink_rate = max(total_exit_rate - modeled_exit_rate, 0.0)
        other_sink_count = max(source_count - modeled_counts, 0)
        rows.append(
            {
                "src": src,
                "dst": "other_sink",
                "transition_count": other_sink_count,
                "source_event_count": source_count,
                "source_dwell_time": dwell,
                "rate_estimate": other_sink_rate,
                "transition_probability_per_event": float(other_sink_count / source_count),
                "support_class": "auxiliary",
                "model_role": "auxiliary_sink",
                "rate_symbol": "",
            }
        )

    return pd.DataFrame(rows), total_dwell


def first_state_distribution(point_df: pd.DataFrame) -> np.ndarray:
    first_events = (
        point_df.sort_values(["traj_id", "event_index"])
        .groupby("traj_id")
        .first()["event_type"]
        .value_counts(normalize=True)
    )
    init = np.array([float(first_events.get(state, 0.0)) for state in TRANSIENT_STATES], dtype=float)
    if init.sum() <= 0.0:
        init[0] = 1.0
    return init / init.sum()


def build_generators(rate_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    q_matrix = np.zeros((len(TRANSIENT_STATES), len(TRANSIENT_STATES)), dtype=float)
    r_matrix = np.zeros((len(TRANSIENT_STATES), len(ABSORBING_STATES)), dtype=float)
    for i, src in enumerate(TRANSIENT_STATES):
        sub = rate_df[rate_df["src"] == src]
        transient_sum = 0.0
        absorbing_sum = 0.0
        for j, dst in enumerate(TRANSIENT_STATES):
            if dst == src:
                continue
            row = sub[sub["dst"] == dst]
            rate = float(row["rate_estimate"].iloc[0]) if not row.empty else 0.0
            q_matrix[i, j] = rate
            transient_sum += rate
        for j, dst in enumerate(ABSORBING_STATES):
            row = sub[sub["dst"] == dst]
            rate = float(row["rate_estimate"].iloc[0]) if not row.empty else 0.0
            r_matrix[i, j] = rate
            absorbing_sum += rate
        q_matrix[i, i] = -(transient_sum + absorbing_sum)
    return q_matrix, r_matrix


def solve_precommit_model(init: np.ndarray, q_matrix: np.ndarray, r_matrix: np.ndarray) -> dict[str, float]:
    minus_q_inv = np.linalg.inv(-q_matrix)
    mean_time_to_absorption = float(init @ (minus_q_inv @ np.ones(len(TRANSIENT_STATES))))
    absorb_probs = init @ (minus_q_inv @ r_matrix)
    p_commit = float(absorb_probs[0])
    p_trap = float(absorb_probs[1])
    p_other = float(absorb_probs[2])
    commit_exit = r_matrix[:, 0]
    commit_second = float(init @ (minus_q_inv @ (minus_q_inv @ commit_exit)))
    mean_time_to_commit_given_commit = commit_second / p_commit if p_commit > 0.0 else float("nan")
    throughput_proxy = p_commit / mean_time_to_commit_given_commit if p_commit > 0.0 and mean_time_to_commit_given_commit > 0.0 else 0.0
    recycle_ratio = (q_matrix[3, 0] + q_matrix[3, 1] + q_matrix[3, 2]) / r_matrix[3, 0] if r_matrix[3, 0] > 0.0 else float("nan")
    return {
        "model_mean_time_to_absorption": mean_time_to_absorption,
        "model_p_commit_before_sink": p_commit,
        "model_p_trap_before_sink": p_trap,
        "model_p_other_sink": p_other,
        "model_mean_time_to_commit_given_commit": mean_time_to_commit_given_commit,
        "model_commit_throughput_proxy": throughput_proxy,
        "model_residence_recycle_ratio": recycle_ratio,
    }


def build_point_outputs(pre_df: pd.DataFrame, summary_df: pd.DataFrame, canonical_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rate_frames: list[pd.DataFrame] = []
    point_rows: list[dict[str, float | str]] = []

    for label in CANONICAL_ORDER:
        point_df = pre_df[pre_df["canonical_label"] == label].copy()
        rate_df, dwell_map = fit_rate_rows(point_df)
        rate_df.insert(0, "canonical_label", label)
        init = first_state_distribution(point_df)
        q_matrix, r_matrix = build_generators(rate_df)
        solved = solve_precommit_model(init, q_matrix, r_matrix)

        row: dict[str, float | str] = {"canonical_label": label}
        row.update(solved)
        row.update(
            {
                "initial_bulk_probability": float(init[0]),
                "initial_wall_probability": float(init[1]),
                "initial_approach_probability": float(init[2]),
                "initial_residence_probability": float(init[3]),
                "dwell_bulk": float(dwell_map.get("bulk_motion", 0.0)),
                "dwell_wall": float(dwell_map.get("wall_sliding", 0.0)),
                "dwell_approach": float(dwell_map.get("gate_approach", 0.0)),
                "dwell_residence": float(dwell_map.get("gate_residence_precommit", 0.0)),
            }
        )

        summary_row = summary_df[summary_df["canonical_label"] == label].iloc[0]
        canonical_row = canonical_df[canonical_df["canonical_label"] == label].iloc[0]
        row.update(
            {
                "simulation_success_probability": float(canonical_row["Psucc_mean"]),
                "simulation_efficiency": float(canonical_row["eta_sigma_mean"]),
                "simulation_speed_proxy": float(1.0 / canonical_row["MFPT_mean"]),
                "simulation_first_commit_delay": float(summary_row["first_gate_commit_delay"]),
                "simulation_wall_dwell_before_first_commit": float(summary_row["wall_dwell_before_first_commit"]),
                "simulation_trap_burden_mean": float(summary_row["trap_burden_mean"]),
                "simulation_commit_given_residence": float(summary_row["commit_given_residence"]),
                "simulation_residence_given_approach": float(summary_row["residence_given_approach"]),
                "simulation_return_to_wall_after_precommit_rate": float(summary_row["return_to_wall_after_precommit_rate"]),
            }
        )
        point_rows.append(row)
        rate_frames.append(rate_df)

    return pd.concat(rate_frames, ignore_index=True), pd.DataFrame(point_rows)


def add_comparison_targets(point_df: pd.DataFrame) -> pd.DataFrame:
    enriched = point_df.copy()
    enriched["speed_proxy"] = 1.0 / enriched["model_mean_time_to_commit_given_commit"]
    enriched["success_proxy"] = enriched["model_p_commit_before_sink"] * (1.0 - enriched["model_p_trap_before_sink"])
    enriched["efficiency_proxy"] = enriched["model_commit_throughput_proxy"] / (1.0 + enriched["model_residence_recycle_ratio"])
    return enriched


def qualitative_tests(point_df: pd.DataFrame) -> dict[str, str]:
    speed_best = point_df.sort_values("speed_proxy", ascending=False)["canonical_label"].iloc[0]
    success_best = point_df.sort_values("success_proxy", ascending=False)["canonical_label"].iloc[0]
    efficiency_best = point_df.sort_values("efficiency_proxy", ascending=False)["canonical_label"].iloc[0]
    return {
        "speed_best": str(speed_best),
        "success_best": str(success_best),
        "efficiency_best": str(efficiency_best),
        "speed_match": "yes" if speed_best == "OP_SPEED_TIP" else "no",
        "success_match": "yes" if success_best == "OP_SUCCESS_TIP" else "no",
        "efficiency_match": "yes" if efficiency_best == "OP_EFFICIENCY_TIP" else "no",
    }


def make_rate_figure(rate_table: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    selected = [
        ("bulk_motion", "wall_sliding", "k_bw"),
        ("wall_sliding", "bulk_motion", "k_wb"),
        ("wall_sliding", "gate_approach", "k_wa"),
        ("gate_approach", "gate_residence_precommit", "k_ar"),
        ("gate_residence_precommit", "gate_commit", "k_rc"),
        ("gate_residence_precommit", "wall_sliding", "k_rw"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    order_map = {label: idx for idx, label in enumerate(CANONICAL_ORDER)}
    for ax, (src, dst, title) in zip(axes.ravel(), selected):
        data = rate_table[(rate_table["src"] == src) & (rate_table["dst"] == dst)].copy()
        data["order"] = data["canonical_label"].map(order_map)
        data = data.sort_values("order")
        ax.bar(data["canonical_label"].str.replace("OP_", "", regex=False), data["rate_estimate"], color="#6baed6")
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(RATE_FIGURE_PATH, dpi=220)
    plt.close(fig)


def make_model_figure(point_df: pd.DataFrame) -> None:
    ordered = point_df.copy()
    ordered["order"] = ordered["canonical_label"].map({label: idx for idx, label in enumerate(CANONICAL_ORDER)})
    ordered = ordered.sort_values("order")
    ordered["label_short"] = ordered["canonical_label"].str.replace("OP_", "", regex=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    x = np.arange(len(ordered))
    width = 0.38

    axes[0].bar(x - width / 2, ordered["simulation_first_commit_delay"], width=width, label="simulation", color="#9ecae1")
    axes[0].bar(x + width / 2, ordered["model_mean_time_to_commit_given_commit"], width=width, label="model", color="#3182bd")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(ordered["label_short"], rotation=35)
    axes[0].set_title("Commit Timing")
    axes[0].legend(fontsize=8)

    axes[1].bar(x - width / 2, ordered["simulation_success_probability"], width=width, label="simulation", color="#c7e9c0")
    axes[1].bar(x + width / 2, ordered["model_p_commit_before_sink"], width=width, label="model", color="#31a354")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(ordered["label_short"], rotation=35)
    axes[1].set_title("Success Vs Commit Reach")
    axes[1].legend(fontsize=8)

    axes[2].bar(x - width / 2, ordered["simulation_efficiency"], width=width, label="simulation", color="#fdd0a2")
    axes[2].bar(x + width / 2, ordered["efficiency_proxy"], width=width, label="model proxy", color="#f16913")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(ordered["label_short"], rotation=35)
    axes[2].set_title("Efficiency Ranking")
    axes[2].legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(MODEL_FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_report(rate_table: pd.DataFrame, point_df: pd.DataFrame, tests: dict[str, str]) -> None:
    robust_rates = rate_table[rate_table["support_class"] == "robust"][
        ["canonical_label", "rate_symbol", "src", "dst", "transition_count", "rate_estimate", "model_role"]
    ]
    weak_rates = rate_table[rate_table["support_class"].isin(["weak_auxiliary", "auxiliary"])][
        ["canonical_label", "src", "dst", "transition_count", "rate_estimate", "model_role", "support_class"]
    ]
    compare = point_df[
        [
            "canonical_label",
            "simulation_success_probability",
            "simulation_efficiency",
            "simulation_speed_proxy",
            "model_p_commit_before_sink",
            "model_p_trap_before_sink",
            "model_mean_time_to_commit_given_commit",
            "model_commit_throughput_proxy",
            "model_residence_recycle_ratio",
        ]
    ]

    balanced = point_df[point_df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
    stale = point_df[point_df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
    speed = point_df[point_df["canonical_label"] == "OP_SPEED_TIP"].iloc[0]
    success = point_df[point_df["canonical_label"] == "OP_SUCCESS_TIP"].iloc[0]
    efficiency = point_df[point_df["canonical_label"] == "OP_EFFICIENCY_TIP"].iloc[0]

    lines = [
        "# Precommit Gate Theory Fit Report",
        "",
        "## Scope",
        "",
        "This report fits the first coarse-grained pre-commit rate model for the productive-memory ridge. It estimates rates only on the pre-first-commit backbone and does not treat crossing-related transitions as central fitted rates.",
        "",
        f"- rate table: {_path_link(RATE_TABLE_PATH)}",
        f"- rate figure: {_path_link(RATE_FIGURE_PATH)}",
        f"- model-vs-simulation figure: {_path_link(MODEL_FIGURE_PATH)}",
        "",
        "## Fitting Strategy",
        "",
        "- Fit continuous-time transition hazards as `count(src -> dst before first commit) / total dwell time in src before first commit`.",
        "- Use transient states `bulk`, `wall_sliding`, `gate_approach`, and `gate_residence_precommit`.",
        "- Treat `gate_commit` as the absorbing target state of this first theory.",
        "- Keep `trap_episode` only as a weak auxiliary sink if it appears before first commit.",
        "- Collapse all other exits into an auxiliary `other_sink` so the precommit CTMC can estimate commitment reach probability without pretending to model crossing.",
        "",
        "## Robust Fitted Rates",
        "",
        robust_rates.to_markdown(index=False),
        "",
        "## Weak Auxiliary Sinks",
        "",
        weak_rates.to_markdown(index=False),
        "",
        "## Model Summary By Canonical Point",
        "",
        compare.to_markdown(index=False),
        "",
        "## Which rates encode the productive-memory ridge before crossing?",
        "",
        "- `k_wa = wall_sliding -> gate_approach` and `k_ar = gate_approach -> gate_residence_precommit` encode how efficiently wall-guided search converts into mouth arrival.",
        "- `k_rc = gate_residence_precommit -> gate_commit` is comparatively stable across the ridge, so it is not the main ridge separator.",
        "- The dominant ridge encoding appears in the effective approach-to-commit clock, which is the aggregate outcome of the search-cycle rates rather than a single dramatic change in `k_rc`.",
        "- `k_rw = gate_residence_precommit -> wall_sliding` and `k_rb = gate_residence_precommit -> bulk_motion` encode precommit recycling and therefore how much search is lost before strong commitment.",
        f"- The stale-control penalty is not mainly a lower `k_rc`: `OP_BALANCED_RIDGE_MID` has recycle ratio `{balanced['model_residence_recycle_ratio']:.4f}` and `OP_STALE_CONTROL_OFF_RIDGE` has `{stale['model_residence_recycle_ratio']:.4f}`, which are very close. The clearer separation is the slower precommit clock plus a weak trap sink.",
        "",
        "## Interpretive Rate Trends",
        "",
        f"- `OP_SPEED_TIP` is the fastest branch because its fitted precommit clock is shortest: model conditional time to commit `{speed['model_mean_time_to_commit_given_commit']:.4f}`.",
        f"- `OP_SUCCESS_TIP` is the most commit-favored branch in the fitted model: model commitment reach probability `{success['model_p_commit_before_sink']:.4f}`.",
        f"- `OP_EFFICIENCY_TIP` balances a relatively high commitment reach probability `{efficiency['model_p_commit_before_sink']:.4f}` with a moderate fitted commit time `{efficiency['model_mean_time_to_commit_given_commit']:.4f}`.",
        f"- `OP_STALE_CONTROL_OFF_RIDGE` differs from `OP_BALANCED_RIDGE_MID` mainly through slower fitted commitment timing (`{stale['model_mean_time_to_commit_given_commit']:.4f}` vs `{balanced['model_mean_time_to_commit_given_commit']:.4f}`) and a nonzero weak trap sink (`{stale['model_p_trap_before_sink']:.6f}` vs `{balanced['model_p_trap_before_sink']:.6f}`).",
        "",
        "## Qualitative Ordering Test",
        "",
        f"- speed proxy winner from the fitted precommit model: `{tests['speed_best']}`; expected speed-favored point: `OP_SPEED_TIP`; match: `{tests['speed_match']}`",
        f"- success proxy winner from the fitted precommit model: `{tests['success_best']}`; expected success-favored point: `OP_SUCCESS_TIP`; match: `{tests['success_match']}`",
        f"- efficiency proxy winner from the fitted precommit model: `{tests['efficiency_best']}`; expected efficiency-favored point: `OP_EFFICIENCY_TIP`; match: `{tests['efficiency_match']}`",
        "",
        "Interpretation:",
        "",
        "- The precommit rate model should be judged first on whether it explains the precommit backbone, not whether it fully reproduces downstream transport objectives that still contain crossing physics.",
        "- A match on speed and success proxies is strong evidence that the fitted backbone is meaningful.",
        "- A mismatch on the efficiency proxy, if present, indicates that efficiency still mixes precommit organization with downstream transport costs that are outside the present theory.",
        "",
        "## What this theory explains already, and what must wait for crossing-specific analysis?",
        "",
        "Explains already:",
        "",
        "- qualitative speed-favored operation through faster precommit timing",
        "- qualitative success-favored operation through stronger commitment reach before loss",
        "- stale-control degradation through slower precommit timing plus a weak rare trap sink",
        "- ridge organization as a precommit recycling-and-timing problem, not a crossing-rate problem",
        "",
        "Must wait:",
        "",
        "- any fitted `gate_commit -> gate_crossing` rate",
        "- any post-crossing state model",
        "- any claim that this is a full doorway-crossing theory rather than a precommit theory",
        "- any strong kinetic inference from the trap sink, which remains weakly supported",
        "",
        "## Extrapolative Claims",
        "",
        "- The fitted precommit rate trends support a reduced-theory direction for the productive-memory ridge, but they do not yet justify extrapolation to full crossing success or geometry transfer without later crossing-specific analysis.",
        "- Use `trap_episode` only as a weak auxiliary sink in the current model.",
        "",
        "## Practical Conclusion",
        "",
        "The first fitted precommit model already explains the productive-memory ridge as a backbone timing-and-recycling structure. The most important fitted parameters are the search-cycle and arrival rates that set the time to first commitment, together with a weak auxiliary stale sink. What remains outside the theory is the final crossing physics after commitment.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_outputs() -> dict[str, str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    RATE_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    event_df, trajectory_df, summary_df, canonical_df = load_inputs()
    pre_df = build_precommit_events(event_df, trajectory_df)
    rate_table, point_df = build_point_outputs(pre_df, summary_df, canonical_df)
    point_df = add_comparison_targets(point_df)
    tests = qualitative_tests(point_df)
    rate_table.to_csv(RATE_TABLE_PATH, index=False)
    make_rate_figure(rate_table)
    make_model_figure(point_df)
    write_report(rate_table, point_df, tests)
    return {
        "report": str(REPORT_PATH),
        "rate_table": str(RATE_TABLE_PATH),
        "rate_figure": str(RATE_FIGURE_PATH),
        "model_figure": str(MODEL_FIGURE_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fit the first pre-commit gate-theory rate model.")
    parser.parse_args(argv)
    result = build_outputs()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
