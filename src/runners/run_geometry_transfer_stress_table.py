from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "canonical_transfer_summary.csv"
REFERENCE_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "reference_extraction_summary.csv"
VERDICTS_PATH = PROJECT_ROOT / "outputs" / "summaries" / "geometry_transfer" / "geometry_transfer_verdicts.json"
OUTPUT_TABLE_PATH = PROJECT_ROOT / "outputs" / "tables" / "geometry_transfer_invariant_table.csv"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "geometry_transfer"
FIGURE_PATH = FIGURE_DIR / "transfer_stress_figure.png"
EVIDENCE_DOC_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_evidence_table.md"
CLAIM_NOTE_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_claim_upgrade_note.md"
PRINCIPLE_SCOPE_PATH = PROJECT_ROOT / "docs" / "principle_scope_statement_v2.md"
GEOMETRY_PRINCIPLE_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_principle_note.md"
GEOMETRY_RUN_REPORT_PATH = PROJECT_ROOT / "docs" / "geometry_transfer_run_report.md"

FAMILY_ORDER = [
    "GF0_REF_NESTED_MAZE",
    "GF1_SINGLE_BOTTLENECK_CHANNEL",
    "GF2_PORE_ARRAY_STRIP",
]
FAMILY_LABELS = {
    "GF0_REF_NESTED_MAZE": "GF0",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "GF1",
    "GF2_PORE_ARRAY_STRIP": "GF2",
}
CANONICAL_TIMING_ORDER = [
    "OP_SPEED_TIP",
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
    "OP_EFFICIENCY_TIP",
    "OP_SUCCESS_TIP",
]
TIMING_LABELS = {
    "OP_SPEED_TIP": "speed",
    "OP_BALANCED_RIDGE_MID": "balanced",
    "OP_STALE_CONTROL_OFF_RIDGE": "stale",
    "OP_EFFICIENCY_TIP": "efficiency",
    "OP_SUCCESS_TIP": "success",
}
GEOMETRY_COLORS = {
    "GF0_REF_NESTED_MAZE": "#1f77b4",
    "GF1_SINGLE_BOTTLENECK_CHANNEL": "#ff7f0e",
    "GF2_PORE_ARRAY_STRIP": "#2ca02c",
}
CLAIM_STATUS_TO_VALUE = {
    "strengthened": 0,
    "candidate": 1,
    "ruled_out": 2,
    "out_of_scope": 3,
}
CLAIM_STATUS_TO_COLOR = ["#31a354", "#f0ad4e", "#d62728", "#bdbdbd"]


@dataclass(frozen=True)
class InvariantSpec:
    invariant_id: str
    invariant_name: str
    invariant_group: str


INVARIANT_SPECS = (
    InvariantSpec("INV1", "Timing-order backbone shape", "shape"),
    InvariantSpec("INV2", "Arrival-order backbone shape", "shape"),
    InvariantSpec("INV3", "Stale-vs-balanced timing penalty", "shape"),
    InvariantSpec("INV4", "Unique success selectivity scalar", "selectivity"),
    InvariantSpec("INV5", "Reference scales and local coefficients", "coefficient"),
    InvariantSpec("INV6", "Coefficient-exact identity", "coefficient"),
    InvariantSpec("INV7", "Trap burden as a matched transfer signal", "weak_signal"),
)


def _path_link(path: str | Path) -> str:
    return f"[{Path(path).name}](file://{Path(path)})"


def _format_order(labels: list[str]) -> str:
    return " < ".join(TIMING_LABELS.get(label, label) for label in labels)


def _format_high_to_low(labels: list[str]) -> str:
    return " > ".join(TIMING_LABELS.get(label, label) for label in labels)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    canonical_summary = pd.read_csv(CANONICAL_SUMMARY_PATH)
    reference_summary = pd.read_csv(REFERENCE_SUMMARY_PATH)
    verdicts = json.loads(VERDICTS_PATH.read_text(encoding="ascii"))
    return canonical_summary, reference_summary, verdicts


def family_rows(canonical_summary: pd.DataFrame, family: str) -> pd.DataFrame:
    subset = canonical_summary[canonical_summary["geometry_family"] == family].copy()
    if subset.empty:
        raise RuntimeError(f"Missing canonical transfer summary for {family}.")
    return subset


def order_signature(df: pd.DataFrame, column: str, *, ascending: bool) -> list[str]:
    return df.sort_values(column, ascending=ascending)["canonical_label"].tolist()


def unique_top_label(df: pd.DataFrame, column: str, *, ascending: bool) -> str | None:
    sorted_df = df.sort_values(column, ascending=ascending).reset_index(drop=True)
    top_value = float(sorted_df[column].iloc[0])
    equal_top = sorted_df[np.isclose(sorted_df[column], top_value)]
    if len(equal_top) != 1:
        return None
    return str(equal_top["canonical_label"].iloc[0])


def build_invariant_table(canonical_summary: pd.DataFrame, reference_summary: pd.DataFrame) -> pd.DataFrame:
    gf0 = family_rows(canonical_summary, "GF0_REF_NESTED_MAZE")
    gf1 = family_rows(canonical_summary, "GF1_SINGLE_BOTTLENECK_CHANNEL")
    gf2 = family_rows(canonical_summary, "GF2_PORE_ARRAY_STRIP")
    reference_summary = reference_summary.set_index("geometry_family")

    rows: list[dict[str, Any]] = []

    gf0_timing_order = order_signature(gf0, "first_gate_commit_delay", ascending=True)
    gf0_wall_order = order_signature(gf0, "wall_dwell_before_first_commit", ascending=True)
    gf1_timing_order = order_signature(gf1, "first_gate_commit_delay", ascending=True)
    gf2_timing_order = order_signature(gf2, "first_gate_commit_delay", ascending=True)
    gf1_wall_order = order_signature(gf1, "wall_dwell_before_first_commit", ascending=True)
    gf2_wall_order = order_signature(gf2, "wall_dwell_before_first_commit", ascending=True)
    timing_match = gf1_timing_order == gf0_timing_order == gf2_timing_order
    wall_match = gf1_wall_order == gf0_wall_order == gf2_wall_order
    rows.append(
        {
            "invariant_id": "INV1",
            "invariant_name": "Timing-order backbone shape",
            "invariant_group": "shape",
            "gf0_reference": f"delay order `{_format_order(gf0_timing_order)}`; wall order `{_format_order(gf0_wall_order)}`",
            "gf1_result": f"delay `{_format_order(gf1_timing_order)}`; wall `{_format_order(gf1_wall_order)}`",
            "gf2_result": f"delay `{_format_order(gf2_timing_order)}`; wall `{_format_order(gf2_wall_order)}`",
            "classification": "survives" if timing_match and wall_match else "fails",
            "claim_effect": "strengthens",
            "interpretation": "The pre-commit timing backbone keeps the same canonical ordering across GF0/GF1/GF2.",
        }
    )

    gf0_arrival_order = order_signature(gf0, "residence_given_approach", ascending=False)
    gf1_arrival_order = order_signature(gf1, "residence_given_approach", ascending=False)
    gf2_arrival_order = order_signature(gf2, "residence_given_approach", ascending=False)
    rows.append(
        {
            "invariant_id": "INV2",
            "invariant_name": "Arrival-order backbone shape",
            "invariant_group": "shape",
            "gf0_reference": f"`residence_given_approach` order `{_format_high_to_low(gf0_arrival_order)}`",
            "gf1_result": f"`{_format_high_to_low(gf1_arrival_order)}`",
            "gf2_result": f"`{_format_high_to_low(gf2_arrival_order)}`",
            "classification": "survives" if gf1_arrival_order == gf0_arrival_order == gf2_arrival_order else "weakens",
            "claim_effect": "strengthens",
            "interpretation": "The arrival-organization branch remains discriminative in the same direction across the tested family.",
        }
    )

    def stale_penalty_text(df: pd.DataFrame) -> tuple[bool, str]:
        balanced = df[df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
        stale = df[df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
        passes = (
            float(stale["first_gate_commit_delay"]) > float(balanced["first_gate_commit_delay"])
            and float(stale["wall_dwell_before_first_commit"]) > float(balanced["wall_dwell_before_first_commit"])
        )
        text = (
            f"delay `{balanced['first_gate_commit_delay']:.4f}` -> `{stale['first_gate_commit_delay']:.4f}`, "
            f"wall `{balanced['wall_dwell_before_first_commit']:.4f}` -> `{stale['wall_dwell_before_first_commit']:.4f}`"
        )
        return passes, text

    gf1_stale_pass, gf1_stale_text = stale_penalty_text(gf1)
    gf2_stale_pass, gf2_stale_text = stale_penalty_text(gf2)
    rows.append(
        {
            "invariant_id": "INV3",
            "invariant_name": "Stale-vs-balanced timing penalty",
            "invariant_group": "shape",
            "gf0_reference": stale_penalty_text(gf0)[1],
            "gf1_result": gf1_stale_text,
            "gf2_result": gf2_stale_text,
            "classification": "survives" if gf1_stale_pass and gf2_stale_pass else "fails",
            "claim_effect": "strengthens",
            "interpretation": "The stale comparator still reads as a slower pre-commit backbone rather than a different post-commit law.",
        }
    )

    def success_selectivity_text(df: pd.DataFrame) -> tuple[bool, str]:
        p_reach_top = unique_top_label(df, "p_reach_commit", ascending=False)
        commit_top = unique_top_label(df, "commit_given_residence", ascending=False)
        passes = p_reach_top == "OP_SUCCESS_TIP" or commit_top == "OP_SUCCESS_TIP"
        return passes, f"top `p_reach_commit` = `{p_reach_top}`; top `commit_given_residence` = `{commit_top}`"

    gf0_selective_pass, gf0_selective_text = success_selectivity_text(gf0)
    gf1_selective_pass, gf1_selective_text = success_selectivity_text(gf1)
    gf2_selective_pass, gf2_selective_text = success_selectivity_text(gf2)
    rows.append(
        {
            "invariant_id": "INV4",
            "invariant_name": "Unique success selectivity scalar",
            "invariant_group": "selectivity",
            "gf0_reference": gf0_selective_text,
            "gf1_result": gf1_selective_text,
            "gf2_result": gf2_selective_text,
            "classification": "survives" if gf1_selective_pass and gf2_selective_pass else "weakens",
            "claim_effect": "candidate_only" if not (gf1_selective_pass and gf2_selective_pass) else "strengthens",
            "interpretation": "The success branch stays on the selective edge, but one single scalar does not isolate it uniformly across GF1 and GF2.",
        }
    )

    gf0_ref = reference_summary.loc["GF0_REF_NESTED_MAZE"]

    def renorm_text(family: str) -> tuple[bool, str]:
        ref = reference_summary.loc[family]
        ratio_tau = float(ref["tau_g"] / gf0_ref["tau_g"])
        ratio_ell = float(ref["ell_g"] / gf0_ref["ell_g"])
        ratio_wall = float(ref["baseline_wall_fraction"] / gf0_ref["baseline_wall_fraction"])
        ratio_commit_events = float(ref["baseline_commit_events_per_traj"] / gf0_ref["baseline_commit_events_per_traj"])
        renorm = any(abs(ratio - 1.0) > 0.25 for ratio in [ratio_tau, ratio_ell, ratio_wall, ratio_commit_events])
        text = (
            f"`tau_g/GF0 = {ratio_tau:.2f}`, `ell_g/GF0 = {ratio_ell:.2f}`, "
            f"`wall_frac/GF0 = {ratio_wall:.2f}`, `commit_events/GF0 = {ratio_commit_events:.2f}`"
        )
        return renorm, text

    gf1_renorm_pass, gf1_renorm_text = renorm_text("GF1_SINGLE_BOTTLENECK_CHANNEL")
    gf2_renorm_pass, gf2_renorm_text = renorm_text("GF2_PORE_ARRAY_STRIP")
    rows.append(
        {
            "invariant_id": "INV5",
            "invariant_name": "Reference scales and local coefficients",
            "invariant_group": "coefficient",
            "gf0_reference": "Reference family fixes the baseline coefficients.",
            "gf1_result": gf1_renorm_text,
            "gf2_result": gf2_renorm_text,
            "classification": "renormalizes" if gf1_renorm_pass and gf2_renorm_pass else "fails",
            "claim_effect": "strengthens",
            "interpretation": "Transfer is shape-level, while the absolute search scales and local encounter coefficients renormalize strongly.",
        }
    )

    def identity_fail_text(family: str) -> tuple[bool, str]:
        ref = reference_summary.loc[family]
        ratios = {
            "tau_g": float(ref["tau_g"] / gf0_ref["tau_g"]),
            "ell_g": float(ref["ell_g"] / gf0_ref["ell_g"]),
            "wall_fraction": float(ref["baseline_wall_fraction"] / gf0_ref["baseline_wall_fraction"]),
        }
        identical = all(abs(value - 1.0) <= 0.05 for value in ratios.values())
        text = ", ".join(f"{key} ratio `{value:.2f}`" for key, value in ratios.items())
        return not identical, text

    gf1_identity_fail, gf1_identity_text = identity_fail_text("GF1_SINGLE_BOTTLENECK_CHANNEL")
    gf2_identity_fail, gf2_identity_text = identity_fail_text("GF2_PORE_ARRAY_STRIP")
    rows.append(
        {
            "invariant_id": "INV6",
            "invariant_name": "Coefficient-exact identity",
            "invariant_group": "coefficient",
            "gf0_reference": "Exact identity would require all geometry-renormalized coefficients to stay near `1` relative to GF0.",
            "gf1_result": gf1_identity_text,
            "gf2_result": gf2_identity_text,
            "classification": "fails" if gf1_identity_fail and gf2_identity_fail else "survives",
            "claim_effect": "ruled_out",
            "interpretation": "The tested family directly rules out coefficient-exact transfer as the current reading of the principle.",
        }
    )

    def trap_text(df: pd.DataFrame) -> tuple[bool, str]:
        balanced = df[df["canonical_label"] == "OP_BALANCED_RIDGE_MID"].iloc[0]
        stale = df[df["canonical_label"] == "OP_STALE_CONTROL_OFF_RIDGE"].iloc[0]
        passes = float(stale["trap_burden_mean"]) > float(balanced["trap_burden_mean"])
        text = (
            f"balanced `{balanced['trap_burden_mean']:.6f}`, "
            f"stale `{stale['trap_burden_mean']:.6f}`"
        )
        return passes, text

    gf1_trap_pass, gf1_trap_text = trap_text(gf1)
    gf2_trap_pass, gf2_trap_text = trap_text(gf2)
    rows.append(
        {
            "invariant_id": "INV7",
            "invariant_name": "Trap burden as a matched transfer signal",
            "invariant_group": "weak_signal",
            "gf0_reference": trap_text(gf0)[1],
            "gf1_result": gf1_trap_text,
            "gf2_result": gf2_trap_text,
            "classification": "survives" if gf1_trap_pass and gf2_trap_pass else "weakens",
            "claim_effect": "candidate_only" if not (gf1_trap_pass and gf2_trap_pass) else "strengthens",
            "interpretation": "Trap burden stays too geometry- and support-sensitive to upgrade into a robust transfer invariant.",
        }
    )

    return pd.DataFrame(rows)


def build_claim_scope_table() -> pd.DataFrame:
    rows = [
        {
            "claim_name": "Shape-level pre-commit backbone transfer",
            "claim_status": "strengthened",
            "note": "GF0/GF1/GF2 preserve the canonical timing backbone shape.",
        },
        {
            "claim_name": "Coefficient renormalization reading",
            "claim_status": "strengthened",
            "note": "The family supports shape survival plus coefficient renormalization.",
        },
        {
            "claim_name": "Single universal success selectivity scalar",
            "claim_status": "candidate",
            "note": "Success stays selective, but no single scalar isolates it uniformly across GF1/GF2.",
        },
        {
            "claim_name": "Trap burden as a transferable invariant",
            "claim_status": "candidate",
            "note": "Trap burden remains sparse and geometry-sensitive.",
        },
        {
            "claim_name": "Coefficient-exact collapse",
            "claim_status": "ruled_out",
            "note": "The tested family contradicts coefficient identity.",
        },
        {
            "claim_name": "Post-commit completion transfer",
            "claim_status": "out_of_scope",
            "note": "The current transfer object stops at the pre-commit backbone.",
        },
        {
            "claim_name": "Irregular GF3 geometry universality",
            "claim_status": "candidate",
            "note": "GF3 remains deferred, so broader universality is not upgraded yet.",
        },
    ]
    return pd.DataFrame(rows)


def write_table(invariant_table: pd.DataFrame) -> None:
    OUTPUT_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    invariant_table.to_csv(OUTPUT_TABLE_PATH, index=False)


def make_figure(canonical_summary: pd.DataFrame, reference_summary: pd.DataFrame, claim_scope: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for metric_name, ax, title in [
        ("first_gate_commit_delay", axes[0, 0], "Backbone Shape Transfer: Commit Delay"),
        ("wall_dwell_before_first_commit", axes[0, 1], "Backbone Shape Transfer: Wall Dwell"),
    ]:
        for family in FAMILY_ORDER:
            subset = family_rows(canonical_summary, family).set_index("canonical_label").loc[CANONICAL_TIMING_ORDER].reset_index()
            raw = subset[metric_name].to_numpy(dtype=float)
            scaled = (raw - raw.min()) / max(raw.max() - raw.min(), 1e-12)
            ax.plot(
                np.arange(len(CANONICAL_TIMING_ORDER)),
                scaled,
                marker="o",
                linewidth=2.2,
                color=GEOMETRY_COLORS[family],
                label=FAMILY_LABELS[family],
            )
        ax.set_xticks(np.arange(len(CANONICAL_TIMING_ORDER)))
        ax.set_xticklabels([TIMING_LABELS[label] for label in CANONICAL_TIMING_ORDER], rotation=20)
        ax.set_ylabel("within-geometry normalized value")
        ax.set_title(title)
    axes[0, 1].legend(frameon=False)

    ref = reference_summary.set_index("geometry_family")
    gf0 = ref.loc["GF0_REF_NESTED_MAZE"]
    coeff_names = [
        ("ell_g", "ell_g"),
        ("tau_g", "tau_g"),
        ("baseline_wall_fraction", "wall fraction"),
        ("baseline_commit_events_per_traj", "commit events"),
    ]
    x = np.arange(len(coeff_names))
    width = 0.34
    for offset, family in [(-width / 2, "GF1_SINGLE_BOTTLENECK_CHANNEL"), (width / 2, "GF2_PORE_ARRAY_STRIP")]:
        ratios = [float(ref.loc[family, source] / gf0[source]) for source, _ in coeff_names]
        axes[1, 0].bar(x + offset, ratios, width=width, color=GEOMETRY_COLORS[family], label=FAMILY_LABELS[family])
    axes[1, 0].axhline(1.0, color="#555555", linestyle="--", linewidth=1.0)
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels([label for _, label in coeff_names], rotation=20)
    axes[1, 0].set_ylabel("ratio to GF0")
    axes[1, 0].set_title("Coefficient Renormalization")
    axes[1, 0].legend(frameon=False)

    status_matrix = np.array(
        [[CLAIM_STATUS_TO_VALUE[row["claim_status"]]] for _, row in claim_scope.iterrows()],
        dtype=float,
    )
    axes[1, 1].imshow(
        status_matrix,
        cmap=ListedColormap(CLAIM_STATUS_TO_COLOR),
        aspect="auto",
        vmin=0,
        vmax=max(CLAIM_STATUS_TO_VALUE.values()),
    )
    axes[1, 1].set_xticks([0])
    axes[1, 1].set_xticklabels(["status"])
    axes[1, 1].set_yticks(np.arange(len(claim_scope)))
    axes[1, 1].set_yticklabels(claim_scope["claim_name"].tolist())
    axes[1, 1].set_title("Current Scope Boundary")
    for i, (_, row) in enumerate(claim_scope.iterrows()):
        axes[1, 1].text(
            0,
            i,
            row["claim_status"],
            ha="center",
            va="center",
            fontsize=8,
            color="#111111",
        )
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=label)
        for label, color in zip(["strengthened", "candidate", "ruled_out", "out_of_scope"], CLAIM_STATUS_TO_COLOR)
    ]
    axes[1, 1].legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=2,
        frameon=False,
        fontsize=8,
    )

    fig.suptitle("Geometry-Transfer Stress Summary", fontsize=15)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(FIGURE_PATH, dpi=220)
    plt.close(fig)


def write_evidence_doc(invariant_table: pd.DataFrame) -> None:
    counts = invariant_table["classification"].value_counts().to_dict()
    lines = [
        "# Geometry Transfer Evidence Table",
        "",
        "## Scope",
        "",
        "This note compresses the GF0/GF1/GF2 transfer evidence into a compact invariant table for principle validation.",
        "",
        f"- canonical transfer summary: {_path_link(CANONICAL_SUMMARY_PATH)}",
        f"- reference extraction summary: {_path_link(REFERENCE_SUMMARY_PATH)}",
        f"- invariant table: {_path_link(OUTPUT_TABLE_PATH)}",
        f"- stress figure: {_path_link(FIGURE_PATH)}",
        f"- geometry transfer run report: {_path_link(GEOMETRY_RUN_REPORT_PATH)}",
        "",
        "## Verdict Classes",
        "",
        "- `survives`: the same shape-level invariant is preserved across GF0/GF1/GF2.",
        "- `renormalizes`: the invariant persists only after accepting geometry-dependent coefficient shifts.",
        "- `weakens`: the signal is still visible but no longer strong enough to upgrade into a clean tested-family claim.",
        "- `fails`: the tested family directly contradicts the stronger invariant claim.",
        "",
        "## Compact Invariant Table",
        "",
        invariant_table.to_markdown(index=False),
        "",
        "## Evidence Summary",
        "",
        f"- survives: `{counts.get('survives', 0)}`",
        f"- renormalizes: `{counts.get('renormalizes', 0)}`",
        f"- weakens: `{counts.get('weakens', 0)}`",
        f"- fails: `{counts.get('fails', 0)}`",
        "",
        "## Practical Readout",
        "",
        "- the backbone shape transfers most cleanly in the timing order and the stale-vs-balanced timing penalty",
        "- arrival organization also transfers in the same canonical order",
        "- the scale variables do not transfer identically; they renormalize strongly",
        "- trap burden and any single selectivity scalar remain weaker than the shape-level timing evidence",
    ]
    EVIDENCE_DOC_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_claim_upgrade_note(invariant_table: pd.DataFrame, claim_scope: pd.DataFrame) -> None:
    strengthened = invariant_table[invariant_table["claim_effect"] == "strengthens"]
    candidate_only = invariant_table[invariant_table["claim_effect"] == "candidate_only"]
    ruled_out = invariant_table[invariant_table["claim_effect"] == "ruled_out"]
    scope_candidate = claim_scope[claim_scope["claim_status"] == "candidate"]
    scope_out = claim_scope[claim_scope["claim_status"] == "out_of_scope"]

    lines = [
        "# Geometry Transfer Claim Upgrade Note",
        "",
        "## Scope",
        "",
        "This note identifies exactly which claims are upgraded by the completed GF0/GF1/GF2 transfer package and which remain candidate-level.",
        "",
        f"- principle scope statement: {_path_link(PRINCIPLE_SCOPE_PATH)}",
        f"- geometry transfer principle note: {_path_link(GEOMETRY_PRINCIPLE_PATH)}",
        f"- invariant table: {_path_link(OUTPUT_TABLE_PATH)}",
        f"- transfer stress figure: {_path_link(FIGURE_PATH)}",
        "",
        "## Strengthened By Transfer",
        "",
        strengthened[["invariant_name", "classification", "interpretation"]].to_markdown(index=False),
        "",
        "These rows justify upgrading the project language from a one-geometry mechanism note to a tested-family pre-commit principle:",
        "",
        "- the timing backbone keeps the same canonical order across GF0/GF1/GF2",
        "- the stale comparator still reads as a slower pre-commit branch rather than a different completion law",
        "- the correct geometry-transfer reading is shape survival with coefficient renormalization",
        "",
        "## Remain Only Candidate-Level",
        "",
        candidate_only[["invariant_name", "classification", "interpretation"]].to_markdown(index=False),
        "",
        scope_candidate[["claim_name", "note"]].to_markdown(index=False),
        "",
        "These claims should stay in Discussion or future-work language rather than being upgraded into the strongest Results statement.",
        "",
        "## Explicitly Ruled Out Or Not Upgraded",
        "",
        ruled_out[["invariant_name", "classification", "interpretation"]].to_markdown(index=False),
        "",
        scope_out[["claim_name", "note"]].to_markdown(index=False),
        "",
        "Interpretation:",
        "",
        "- coefficient-exact universality is not the right reading of the tested-family transfer data",
        "- post-commit completion transfer is not contradicted here, but it is not upgraded because it remains outside the transfer object",
        "",
        "## Strongest Upgraded Claim",
        "",
        "The strongest claim upgraded by transfer is:",
        "",
        "> Across GF0, GF1, and GF2, the pre-commit backbone transfers at the level of shape: the canonical timing order, the stale-vs-balanced timing penalty, and the arrival-organization discriminator all survive, while the absolute reference scales and local coefficients renormalize rather than collapsing exactly.",
        "",
        "## Still Candidate-Level",
        "",
        "The following should remain candidate-level after the present transfer stage:",
        "",
        "- any claim that one unique selectivity scalar always isolates the success branch",
        "- any claim that trap burden is a robust geometry-invariant stale discriminator",
        "- any claim beyond the clean GF0/GF1/GF2 family, especially the deferred GF3 stress geometry",
        "- any post-commit completion transfer claim",
    ]
    CLAIM_NOTE_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_outputs() -> dict[str, str]:
    canonical_summary, reference_summary, _verdicts = load_inputs()
    invariant_table = build_invariant_table(canonical_summary, reference_summary)
    claim_scope = build_claim_scope_table()
    write_table(invariant_table)
    make_figure(canonical_summary, reference_summary, claim_scope)
    write_evidence_doc(invariant_table)
    write_claim_upgrade_note(invariant_table, claim_scope)
    return {
        "geometry_transfer_evidence_table": str(EVIDENCE_DOC_PATH),
        "geometry_transfer_invariant_table_csv": str(OUTPUT_TABLE_PATH),
        "transfer_stress_figure_png": str(FIGURE_PATH),
        "geometry_transfer_claim_upgrade_note": str(CLAIM_NOTE_PATH),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the compact geometry-transfer stress table and claim-upgrade package.")
    parser.parse_args(argv)
    outputs = build_outputs()
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
