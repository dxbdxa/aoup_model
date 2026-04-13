# Geometry Family Spec

## Scope

This document defines the small family of geometries for the first geometry-transfer stage of principle testing. The purpose is not to reopen a broad search, but to test which parts of the current pre-commit transport principle survive transfer and which parts only renormalize.

Primary conceptual source:

- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [precommit_gate_theory_state_graph.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_state_graph.md)
- [precommit_gate_theory_fit_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_fit_report.md)
- [trae_active_transport_workflow.md](file:///home/zhuguolong/aoup_model/docs/trae_active_transport_workflow.md)

## Design Logic

The transferable object is the pre-commit backbone:

- `bulk`
- `wall_sliding`
- `gate_approach`
- `gate_residence_precommit`
- `gate_commit`

The geometry family is chosen to test this backbone under progressively stronger structural changes while keeping interpretation simple.

## Geometry Set

### `GF0_REF_NESTED_MAZE`

Role:

- reference geometry
- current source of the pre-commit principle

Interpretive use:

- baseline for all transfer comparisons
- defines the current reference values of `ell_g`, `tau_g`, and the canonical operating points

Structure:

- nested gated-shell maze
- repeated wall-guided approach opportunities before commitment
- strongest existing evidence for the pre-commit ridge

### `GF1_SINGLE_BOTTLENECK_CHANNEL`

Role:

- simplest interpretable transfer geometry
- minimal test of whether the pre-commit backbone survives when branching complexity is reduced

Interpretive use:

- asks whether the same delay-admissible, memory-smoothed commitment logic appears when there is only one dominant bottleneck and one main wall-guided approach corridor

Structure:

- one channel-like domain with a single narrowing bottleneck
- minimal repeated residence opportunities
- should preserve the meaning of commitment while stripping away much of the maze-specific shell topology

### `GF2_PORE_ARRAY_STRIP`

Role:

- repeated-commitment transfer geometry
- tests whether the same principle survives when commitment opportunities are repeated rather than nested

Interpretive use:

- asks whether the productive ridge depends on one particular shell sequence or instead on repeated local approach-residence-commit cycles

Structure:

- finite strip or short sequence of pores / chambers
- multiple comparable bottlenecks
- repeated local pre-commit funnels

### `GF3_RANDOM_LABYRINTH_STRESS_TEST`

Role:

- breakdown test, not first calibration target
- checks whether the principle still organizes behavior when local routes become irregular

Interpretive use:

- should be used only after transfer has been checked on `GF1` and `GF2`
- intended to distinguish genuine principle breakdown from simple renormalization

Structure:

- irregular labyrinth with one designated outlet family
- nonuniform wall-guided routes
- most likely geometry in the first family to induce partial breakdown

## Which Geometries Are In Scope For The First Transfer Stage?

Use only the following in the first stage:

- `GF0_REF_NESTED_MAZE`
- `GF1_SINGLE_BOTTLENECK_CHANNEL`
- `GF2_PORE_ARRAY_STRIP`

Defer:

- `GF3_RANDOM_LABYRINTH_STRESS_TEST`

Reason:

- the first question is whether the pre-commit backbone transfers under clean, interpretable structural changes
- the labyrinth should be used only after the renormalization logic is already understood

## Approximately Matched Geometric Quantities

The following quantities should be approximately matched or explicitly renormalized across the family.

### Primary Matched Quantities

- `ell_g`: geometry-specific gate-search length from the no-memory, no-delay, no-flow reference
- `tau_g`: geometry-specific commitment / gate timescale from the same reference
- effective bottleneck width ratio:
  - `Pi_W_local = w_eff / ell_g`
- wall interaction range ratio:
  - `Pi_B_local = delta_wall / ell_g`
- pre-commit approach depth:
  - `ell_pre / ell_g`
- local wall-to-gate turning severity:
  - classified qualitatively as low / medium / high when exact matching is not practical

### Quantities Intentionally Allowed To Vary

- number of commitment opportunities before exit
- global topology and branch multiplicity
- long-range route redundancy

These variations are allowed because they are part of the transfer test itself.

## Reference-Scale Extraction Per Geometry

For each geometry, compute the following before any transfer replay:

- `ell_g`
- `tau_g`
- baseline wall-contact fraction
- baseline approach / commitment encounter statistics in the reference no-memory, no-delay, no-flow case

This ensures that transfer is done in geometry-renormalized coordinates rather than by raw dimensional copying.

## Family Comparison Table

| Geometry | Main purpose | Commitment opportunities | Topology complexity | First-stage status |
|---|---|---:|---|---|
| `GF0_REF_NESTED_MAZE` | reference principle source | repeated nested | medium | required |
| `GF1_SINGLE_BOTTLENECK_CHANNEL` | simplest transfer test | single dominant | low | required |
| `GF2_PORE_ARRAY_STRIP` | repeated-local-cycle test | repeated serial | medium | required |
| `GF3_RANDOM_LABYRINTH_STRESS_TEST` | breakdown stress test | irregular | high | defer |

## What Counts As A Useful Transfer Family?

A geometry belongs in this family only if:

- it has a clear notion of approach, residence, and commitment before crossing
- wall-guided search remains meaningfully definable
- the pre-commit backbone can be represented without inventing a new state graph from scratch

If those conditions fail, the geometry is not yet a useful principle-transfer target.

## Bottom Line

The first geometry-transfer family should be deliberately small and interpretable. The central transferable object is not full crossing success, but the pre-commit backbone that carries trajectories from bulk and wall-guided search into gate-local residence and strong commitment.
