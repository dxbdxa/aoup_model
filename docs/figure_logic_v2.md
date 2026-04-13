# Figure Logic V2

## Purpose

This document defines the main-figure logic for a broad-reader manuscript centered on one physical question and one main principle.

Primary framing source:

- [storyline_reset_master.md](/home/zhuguolong/aoup_model/docs/storyline_reset_master.md)

Evidence sources:

- [front_analysis_report.md](/home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [canonical_operating_points.md](/home/zhuguolong/aoup_model/docs/canonical_operating_points.md)
- [mechanism_discriminators_refined.md](/home/zhuguolong/aoup_model/docs/mechanism_discriminators_refined.md)
- [precommit_gate_theory_state_graph.md](/home/zhuguolong/aoup_model/docs/precommit_gate_theory_state_graph.md)
- [geometry_transfer_plan.md](/home/zhuguolong/aoup_model/docs/geometry_transfer_plan.md)
- [thermodynamic_upgrade_discussion.md](/home/zhuguolong/aoup_model/docs/thermodynamic_upgrade_discussion.md)

## Figure Philosophy

Each main figure should answer one step in the same argument:

1. There is a real tradeoff structure to explain.
2. That structure is selected before final crossing.
3. The organizing object survives geometry change at the level of shape.
4. The principle survives improved cost accounting.

This keeps the figures cumulative rather than episodic.

## Recommended Main-Figure Set

Use four main figures. If a fifth figure is allowed, reserve it for a synthesis schematic. Otherwise fold the synthesis into the final panel of Figure 4.

## Figure 1: The transport landscape contains a Pareto-like ridge, not a single optimum

### Story job

Introduce the system, define the performance question, and establish the central structural discovery.

### Claim

Transport performance occupies an extended Pareto-like ridge, with distinct success, efficiency, and speed tips, rather than collapsing to a single best operating point.

### Recommended panels

- System schematic showing constrained transport and the final barrier-crossing geometry
- Control-space view showing the narrow productive region
- Pareto/front view showing distinct objective tips
- Compact projection showing narrow `Pi_f` support and `Pi_U` ordering

### Caption logic

The caption should make two things immediately clear:

- the system does not choose one optimum
- the ridge is narrow in delay and ordered mainly by flow

### What this figure must prove

- there is a coherent phenomenon to explain
- the ridge is real and extended
- the front tips are separated enough to justify speaking about tradeoffs

### What to move to SI

- scan chronology
- full overlap tables
- CI tables
- extra projections and candidate lists

## Figure 2: Performance is selected on a pre-commit backbone before final crossing

### Story job

Answer the central manuscript question directly.

### Claim

The decisive tradeoff structure is already visible before final crossing and is organized by a pre-commit backbone.

### Recommended panels

- Intuitive coarse-grained state graph with the pre-commit backbone highlighted
- Canonical-point comparison across success, efficiency, speed, and balanced ridge states
- Pre-commit observables that separate branches, especially first-commit delay and wall dwell
- Balanced-ridge versus stale-control comparison showing slower pre-commit timing and weak trap burden off ridge

### Caption logic

The caption should say plainly that final crossing is not where the main sorting first appears.

### What this figure must prove

- early selection is visible before crossing
- the ridge can be understood in terms of one named object: the pre-commit backbone
- delay, memory, and flow play distinct physical roles within that backbone

### Broad-reader translation rule

Avoid letting this figure look like a specialist rate-fitting panel set. The visual emphasis should be on where selection occurs, not on all fitted details.

### What to move to SI

- full transition probabilities
- threshold definitions
- alternative coarse grainings
- complete fit diagnostics
- sparse post-commit evidence

## Figure 3: The first transferable object is backbone shape

### Story job

Show that the principle is not confined to one geometry, while staying explicit about scope.

### Claim

Across `GF0`, `GF1`, and `GF2`, the pre-commit backbone survives at the level of shape and ordering logic, while coefficients renormalize.

### Recommended panels

- Compact schematics of the tested geometry family
- Geometry-by-geometry comparison of the same backbone observables
- Summary panel distinguishing shape survival from coefficient renormalization
- Optional small panel showing the canonical-point replay logic

### Caption logic

The caption should emphasize that the transferable object is not full completion success and not coefficient identity.

### What this figure must prove

- the paper has moved beyond one geometry
- the correct generality claim is structural rather than coefficient-exact
- geometry transfer strengthens the same principle instead of launching a new story

### What to move to SI

- geometry-family specification details
- calibration tables
- local renormalization slices
- extended replay data
- deferred stress-test geometry material

## Figure 4: The ridge survives thermodynamic upgrade even though the efficient branch shifts

### Story job

Show that the structural principle survives improved cost bookkeeping.

### Claim

The Pareto-like ridge persists under the current thermodynamic upgrade, although the preferred efficient branch changes.

### Recommended panels

- Screening view using `eta_sigma`
- Upgraded view using `eta_completion_drag`
- Mechanism-facing refinement using `eta_trap_drag`
- Final synthesis panel: selection occurs before crossing, the ridge survives transfer and upgrade, and the claim remains scoped

### Caption logic

The caption should reinforce that better cost accounting changes branch preference but not the deeper organizing structure.

### What this figure must prove

- the paper is not tied to one screening metric
- the branch shift is physically meaningful rather than embarrassing
- thermodynamic upgrade is a strengthening test of the same principle

### What to move to SI

- full metric definitions
- bookkeeping derivations
- proxy caveats
- extra ranking tables
- alternative metric comparisons

## Optional Figure 5: Synthesis and scope

Use this figure only if journal length permits. Otherwise merge its content into Figure 4.

### Story job

Leave the broad reader with one compact conceptual picture.

### Claim

Performance is selected before final crossing by a pre-commit backbone that creates a Pareto-like ridge, within explicit tested-family and bookkeeping limits.

### Recommended panels

- Selection-timing cartoon contrasting pre-commit organization with final crossing
- One-line statement of the principle
- Scope box listing the explicit exclusions

### Explicit exclusions to display if this figure exists

- not a full crossing-completion law
- not unrestricted universality
- not coefficient-exact geometry collapse
- not full thermodynamic closure

## Extended Data / SI Figure Logic

Extended Data and SI figures should support, not compete with, the main figures.

Recommended support roles:

- Extended Data 1: uncertainty and overlap support for the ridge
- Extended Data 2: additional canonical-point comparisons and mechanism discriminators
- Extended Data 3: full pre-commit state-graph and fitting details
- Extended Data 4: geometry-transfer calibration and renormalization detail
- Extended Data 5: thermodynamic metric definitions and ranking robustness

## Final Figure Ordering Rule

If a figure does not help answer the question "when is performance selected?" or does not strengthen the resulting principle, it should not be a main figure.
