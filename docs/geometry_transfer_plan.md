# Geometry Transfer Plan

## Scope

This document defines the first geometry-transfer stage for principle testing. It is designed to test generality of the pre-commit transport principle without reopening a broad global search.

Primary references:

- [geometry_family_spec.md](file:///home/zhuguolong/aoup_model/docs/geometry_family_spec.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [precommit_gate_theory_state_graph.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_state_graph.md)
- [precommit_gate_theory_fit_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_fit_report.md)

## Transfer Objective

The transfer question is:

> Does the delay-admissible, memory-smoothed, flow-ordered commitment backbone survive across a small family of geometries after geometry-specific renormalization?

The first stage is not trying to prove full geometry collapse. It is trying to separate three outcomes:

- same principle
- geometry-specific renormalization
- genuine breakdown

## Central Transfer Object

The central transferable object is the pre-commit backbone:

- `bulk`
- `wall_sliding`
- `gate_approach`
- `gate_residence_precommit`
- `gate_commit`

Everything in the first transfer stage should be organized around whether this backbone remains the dominant explanatory object.

## First Observables To Transfer

Transfer these observables first, in this order:

1. `first_gate_commit_delay`
2. `wall_dwell_before_first_commit`
3. `commit_given_residence`
4. `residence_given_approach`
5. `return_to_wall_after_precommit_rate`
6. `trap_burden_mean`

Rationale:

- the first two are the strongest current timing invariants
- the next three measure pre-commit structure directly
- trap burden is weaker, but it is the clearest stale-control sink signature

Do not prioritize first:

- `crossing_given_commit`
- any post-commit sequence observable
- any fully crossing-conditioned success decomposition

## What invariants should survive geometry transfer?

The following are the first invariants that should survive if the current principle is genuinely general.

### Structural invariants

- the dominant reduced object remains the pre-commit backbone rather than a crossing-rate hierarchy
- `gate_commit` remains the correct stopping point for the first reduced theory
- stale degradation still appears first as slower commitment and weak stale trapping, not as a clean collapse of commitment probability

### Ordering invariants

- speed-favored operation still corresponds to the shortest effective pre-commit timing
- success-favored operation still corresponds to the highest effective commitment reach before loss
- the balanced-vs-stale comparison is still dominated by pre-commit delay and wall dwell rather than by a large change in `commit_given_residence`

### Renormalized quantitative invariants

- the productive regime still occupies a narrow delay-admissible strip when expressed in geometry-specific `Pi_f = tau_f / tau_g`
- the productive memory band remains low but non-minimal when expressed in geometry-specific `Pi_m = tau_mem / tau_g`
- flow still orders the front branch along the surviving ridge family

These should survive approximately, not exactly.

## Why pre-commit structure should transfer before crossing structure

Pre-commit structure should transfer earlier and more robustly than crossing structure because it is built from the broadest and best-sampled part of the dynamics.

Why:

- the approach / residence / commitment backbone has high event counts and already supports a reduced-state fit
- the crossing branch is still sparse even in the reference geometry
- geometry changes are most likely to renormalize final-transit details before they destroy the larger search-to-commit backbone
- the current transport principle is already supported by pre-commit timing and recycling, so those should be the first quantities tested under transfer

Therefore:

- pre-commit timing and recycling are the first transfer targets
- crossing-specific analysis should be postponed until after the pre-commit principle either survives or fails

## Transfer Outcome Classes

### Same principle

Count the result as the same principle if all of the following hold:

- the pre-commit backbone remains the dominant explanatory graph
- speed remains associated with the shortest commitment timing
- success remains associated with the largest commitment reach before loss
- stale degradation remains visible as slower pre-commit timing plus weak sink growth
- the productive regime remains confined to a narrow delay-admissible region after geometry-specific renormalization

Numerical rates may shift. Exact ridge location may shift. Those do not by themselves invalidate the principle.

### Geometry-specific renormalization

Count the result as renormalization if:

- the same pre-commit backbone survives
- the same ordering logic survives
- but the absolute rates or the precise location of the ridge move systematically

Examples:

- `k_wa`, `k_ar`, and `k_rc` all rescale because bottleneck width or turning severity changed
- the balanced ridge point shifts in `Pi_m` or `Pi_f`, but the same timing-versus-recycling competition still organizes the front

This is an expected and scientifically useful outcome.

### Genuine breakdown

Count the result as breakdown only if one of the following occurs:

- the dominant explanatory object is no longer the pre-commit backbone
- commitment timing no longer separates speed and success structure
- stale degradation is no longer expressed as slower pre-commit timing plus weak sink growth
- the productive regime disappears or ceases to be associated with a narrow delay-admissible strip after proper renormalization
- crossing becomes the primary bottleneck immediately, with no stable pre-commit organization

This threshold should be conservative. Breakdown should not be declared merely because numerical values move.

## Minimal Transfer Program

### Stage G0. Geometry reference extraction

For each geometry:

- compute `ell_g`
- compute `tau_g`
- compute baseline wall-contact and commitment timing observables in the no-memory, no-delay, no-flow reference

Purpose:

- define geometry-specific renormalization before any transfer replay

### Stage G1. Canonical-point replay on `GF1_SINGLE_BOTTLENECK_CHANNEL`

Replay only the frozen canonical operating points:

- `OP_SUCCESS_TIP`
- `OP_EFFICIENCY_TIP`
- `OP_SPEED_TIP`
- `OP_BALANCED_RIDGE_MID`
- `OP_STALE_CONTROL_OFF_RIDGE`

Evaluate only:

- `first_gate_commit_delay`
- `wall_dwell_before_first_commit`
- `commit_given_residence`
- `residence_given_approach`
- `trap_burden_mean`

Purpose:

- simplest test of same principle vs breakdown

### Stage G2. Canonical-point replay on `GF2_PORE_ARRAY_STRIP`

Repeat the same canonical transfer on the repeated-bottleneck geometry.

Purpose:

- determine whether the pre-commit principle survives when commitment opportunities are repeated rather than nested

### Stage G3. Minimal local renormalization slice if needed

Only if G1 or G2 show clear backbone survival but shifted location, run one tiny local renormalization check:

- one `Pi_f` admissibility slice near the transferred balanced point
- one `Pi_U` ordering slice spanning success-balanced-speed flow levels

Purpose:

- distinguish shifted ridge from genuine breakdown

This is the only planned refinement step in the first transfer stage.

### Stage G4. Deferred stress test

Use `GF3_RANDOM_LABYRINTH_STRESS_TEST` only after G1-G3 are understood.

Purpose:

- determine whether the principle breaks under irregular topology
- not part of the minimal first generality test

## Decision Logic

After G1 and G2:

- if backbone structure and ordering both survive, declare provisional geometry robustness
- if timing structure survives but ridge location shifts, declare renormalization
- if neither survives, declare breakdown candidate and inspect whether commitment is no longer the right stopping point

After G3:

- if a tiny local slice restores the same ordering logic, the result is renormalization, not breakdown
- if even the local slice fails, the geometry likely changes the governing principle

## Minimal Data Budget

Do not reopen broad global scans.

Use this budget logic instead:

- replay only the five frozen canonical operating points on `GF1` and `GF2`
- add only one tiny local renormalization slice per geometry if needed
- defer all broader mapping until the first principle test is answered

That is the minimum plan that can still distinguish survival, renormalization, and breakdown.

## Practical Conclusion

The first geometry-transfer stage should test whether the pre-commit backbone is a general transport object. The smallest credible plan is:

- reference extraction on each geometry
- canonical replay on one simplification geometry and one repeated-bottleneck geometry
- one local renormalization slice only if needed
- defer irregular-labyrinth stress testing and all crossing-specific transfer claims

This keeps the transfer stage interpretable, principle-centered, and tightly scoped.
