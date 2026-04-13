from __future__ import annotations

from src.runners.run_geometry_transfer_stress_table import build_claim_scope_table, build_invariant_table, load_inputs


def test_invariant_table_has_expected_transfer_classifications() -> None:
    canonical_summary, reference_summary, _ = load_inputs()

    invariant_table = build_invariant_table(canonical_summary, reference_summary).set_index("invariant_id")

    assert invariant_table.loc["INV1", "classification"] == "survives"
    assert invariant_table.loc["INV2", "classification"] == "survives"
    assert invariant_table.loc["INV3", "classification"] == "survives"
    assert invariant_table.loc["INV4", "classification"] == "weakens"
    assert invariant_table.loc["INV5", "classification"] == "renormalizes"
    assert invariant_table.loc["INV6", "classification"] == "fails"
    assert invariant_table.loc["INV7", "classification"] == "weakens"


def test_claim_scope_table_marks_scope_boundary_cleanly() -> None:
    scope = build_claim_scope_table().set_index("claim_name")

    assert scope.loc["Shape-level pre-commit backbone transfer", "claim_status"] == "strengthened"
    assert scope.loc["Coefficient renormalization reading", "claim_status"] == "strengthened"
    assert scope.loc["Coefficient-exact collapse", "claim_status"] == "ruled_out"
    assert scope.loc["Post-commit completion transfer", "claim_status"] == "out_of_scope"
