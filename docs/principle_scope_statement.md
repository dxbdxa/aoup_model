# Principle Scope Statement

## Scope

This note defines what the current transport principle does and does not cover after the first geometry-transfer validation.

Primary inputs:

- [geometry_transfer_principle_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_principle_note.md)
- [geometry_transfer_run_report.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_run_report.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)

The goal is to separate supported scope from overclaim.

## Core Claim

The current principle is a pre-commit transport principle for delayed-memory guided search-and-commit systems.

It states that:

- productive operation is selected primarily by the structure of the pre-commit backbone
- delay, memory, and flow play geometry-robust qualitative roles in that backbone
- geometry changes coefficients and scales before it changes the backbone ordering logic

## Shape-Level Universality

Currently supported:

- the pre-commit backbone remains the first transferable mechanism across `GF0`, `GF1`, and `GF2`
- the speed branch is still the earliest-commit branch
- the success branch is still the strongest commitment-reach branch
- the stale branch is still the slower, more recycling-prone branch
- wall dwell before first commitment remains a robust stale-vs-productive signal

This is what is meant by shape-level universality:

- same ordering logic
- same qualitative control roles
- same mechanistic interpretation

This does not mean identical numbers.

## Coefficient-Level Renormalization

Currently supported:

- `tau_g` renormalizes by geometry
- `ell_g` renormalizes by geometry
- wall-contact baselines renormalize by geometry
- approach, residence, and commitment encounter statistics renormalize by geometry
- absolute recycling and commitment rates renormalize by geometry

Therefore the correct current reading is:

- the transport principle is universal at the level of backbone shape
- the coefficients are geometry-dependent and should not yet be treated as universal constants

## Untested Crossing-Specific Structure

Still outside the current principle:

- full post-commit crossing kinetics
- exact geometry-general success laws
- crossing-conditioned completion probabilities as a universal layer
- thermodynamic or transport-cost completion beyond the pre-commit backbone

So the present principle should not be advertised as:

- a full crossing theory
- a full efficiency theory
- a universal completion law for all gated geometries

## What transferred robustly across geometries?

The strongest robust transfer result is that the pre-commit organization survives across the tested family even though the absolute coefficients move.

Transferred robustly:

- commitment timing as the main speed discriminator
- commitment reach as the main success discriminator
- wall dwell before commitment as a stale-vs-productive discriminator
- precommit recycling as part of the stale signature
- the interpretation of the productive-memory ridge as a delay-admissible, memory-smoothed, flow-ordered backbone

## What still needs stress testing or finer renormalization?

Still needed:

- finer extraction of non-reference `tau_g` and `ell_g`, because the first pass is horizon-capped
- stress testing on more irregular geometries, especially `GF3_RANDOM_LABYRINTH_STRESS_TEST`
- a direct test of whether post-commit crossing structure also transfers
- a later test of whether efficiency can be split cleanly into pre-commit and post-commit transferable pieces

## Recommended Claim Language

Use language like:

> The current evidence supports a geometry-general pre-commit transport principle with shape-level universality and coefficient-level renormalization across the tested family.

Avoid language like:

- universal success law
- universal crossing law
- geometry-independent coefficients
- complete theory of all gated transport

## Bottom Line

The current scope boundary is sharp:

- universal enough to claim a transferable pre-commit transport principle
- not universal enough to claim coefficient-exact collapse or crossing-complete theory

That is the strongest statement justified by the current evidence.
