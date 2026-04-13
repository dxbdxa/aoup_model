# General Principle Candidates

## Scope

This note lists compact principle statements suggested by the fitted pre-commit gate theory. The goal is not to claim final theory, but to propose transport-principle candidates that are already supported by the current reduced model.

Primary sources:

- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [precommit_gate_theory_fit_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_fit_report.md)
- [theory_compression_note.md](file:///home/zhuguolong/aoup_model/docs/theory_compression_note.md)

## Candidate A: Commitment-Backbone Principle

Competitive gated transport is selected primarily by the pre-commit backbone rather than by the final crossing event.

Statement:

> A transport controller is productive when it converts bulk and wall-guided search into gate-local residence and strong commitment faster than it recycles or stalls.

What this captures:

- speed as fast commitment
- success as reliable commitment reach
- stale degradation as slower commitment plus rare stale loss

Why it is useful:

- it is already supported by the fitted reduced model
- it is phrased in state-graph terms rather than in one-geometry optimization language

## Candidate B: Delay-Admissible Commitment Principle

The productive ridge exists only when delay remains small enough that the pre-commit backbone stays synchronized.

Statement:

> Delay acts as a commitment-admissibility condition: once feedback lag is too large, the search-to-residence-to-commit backbone loses coherence and the point drops out of the productive family.

What this adds:

- gives a dynamical interpretation to the narrow `Pi_f` strip
- explains why the ridge is lost before crossing-specific modeling is needed

## Candidate C: Productive-Memory Smoothing Principle

Memory helps only when it smooths the pre-commit backbone without making it stale.

Statement:

> Memory is productive only in the band where it regularizes pre-commit search and residence dynamics faster than it corrupts them through stale guidance.

What this adds:

- explains why the productive memory band is low but non-minimal
- makes the ridge a phase-matched smoothing regime rather than a monotone memory benefit

## Candidate D: Flow-Ordering Principle

Flow orders which branch of the pre-commit backbone is favored.

Statement:

> Within the admissible delay and memory band, flow selects whether the pre-commit backbone favors reliable commitment, balanced throughput, or the fastest commitment clock.

Interpretation:

- lower flow preserves the most selective branch
- higher flow favors the fastest branch
- intermediate flow participates in the efficiency branch but does not determine it completely within the current theory

## Preferred Composite Principle

The strongest current composite statement is:

> The productive-memory ridge is a delay-admissible, memory-smoothed, flow-ordered commitment backbone. Points on the ridge remain competitive because they reach gate commitment through efficient pre-commit cycling before stale recycling and trapping dominate.

Why this is the best current candidate:

- it includes the three control roles directly
- it explains why the ridge is visible before crossing
- it is broad enough to guide geometry transfer and later theory upgrades
- it does not overclaim a full crossing theory

## What must remain outside the current principle

The following should remain explicitly deferred:

- final crossing kinetics
- post-commit transport completion
- thermodynamic upgrade beyond the current dissipation-normalized proxy
- geometry-transfer claims stronger than the state-graph logic itself

## Recommended Use

Use the composite principle as the main transport statement, and use the others as unpacking sentences:

- Candidate A for mechanism framing
- Candidate B for delay interpretation
- Candidate C for memory interpretation
- Candidate D for ridge ordering by flow

## Bottom Line

The most compact general statement currently supported is:

> Productive transport in delayed-memory guidance systems is selected before crossing, by a commitment backbone that must remain delay-admissible, memory-smoothed, and flow-ordered strongly enough to outrun recycling and stale trapping.
