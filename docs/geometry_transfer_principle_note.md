# Geometry Transfer Principle Note

## Scope

This note states the strongest transport principle now supported by the first geometry-transfer validation. It is written at the level of general transport structure, not as a summary of one maze family.

Primary inputs:

- [geometry_transfer_run_report.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_run_report.md)
- [geometry_transfer_first_look.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_first_look.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [general_principle_candidates.md](file:///home/zhuguolong/aoup_model/docs/general_principle_candidates.md)
- [theory_compression_note.md](file:///home/zhuguolong/aoup_model/docs/theory_compression_note.md)

The transfer object is the pre-commit backbone. This note does not claim geometry-general final crossing kinetics or geometry-general full success laws.

## Principle Statement

The strongest current geometry-general statement is:

> Productive transport in delayed-memory guidance systems is organized first by a pre-commit commitment backbone whose shape is geometry-robust, while its coefficients are geometry-renormalized. Competitive operation is preserved when delay remains admissible, memory remains productively smoothing rather than stale, and flow orders whether the backbone favors reliable commitment or rapid commitment.

In compact terms:

- the universal object is the ordering structure of the pre-commit backbone
- the renormalized objects are the geometry-specific timescales, lengths, and local encounter coefficients
- the untested object is the crossing-specific completion layer after commitment

## What transferred robustly across geometries?

The first transfer validation supports shape-level universality of the pre-commit backbone across:

- `GF0_REF_NESTED_MAZE`
- `GF1_SINGLE_BOTTLENECK_CHANNEL`
- `GF2_PORE_ARRAY_STRIP`

What remained robust:

- the productive-memory picture is still organized before crossing, not primarily at the final crossing step
- the speed-favored operating point remains the one with the shortest first commitment delay
- the success-favored operating point remains the one with the strongest commitment reach or strongest residence-to-commit conversion
- stale-control degradation still appears as a slower pre-commit organization with stronger wall-mediated recycling
- wall dwell before first commitment remains a meaningful discriminator of whether the backbone is productive or stale
- `residence_given_approach`, `commit_given_residence`, and `return_to_wall_after_precommit_rate` remain interpretable as backbone observables rather than geometry-specific artifacts

So the geometry-robust claim is not that every number stays fixed. It is that the same pre-commit ordering logic continues to separate productive, balanced, and stale operation.

## Shape-Level Universality

The current evidence justifies a shape-level universality claim in the following restricted sense:

- the backbone still has the same mechanistic role across the tested geometries
- delay, memory, and flow still enter with the same qualitative roles
- the ridge is still selected by pre-commit timing, residence-to-commit organization, and recycling burden
- the matched ridge-vs-stale comparison remains readable in the same backbone coordinates

This is a universality of ordering and mechanism shape, not of exact coefficients.

More explicitly:

- delay still acts as an admissibility condition for coherent pre-commit organization
- memory still helps only in a productive band, rather than monotonically
- flow still orders which branch of the competitive backbone is favored

That is the strongest geometry-general content presently supported.

## Coefficient-Level Renormalization

The transfer results also show clear coefficient-level renormalization.

What renormalizes:

- absolute `tau_g`
- absolute `ell_g`
- baseline wall-contact fractions
- baseline approach, residence, and commitment encounter counts
- the absolute magnitudes of local recycling and commitment statistics

Interpretation:

- geometry changes the effective local search burden
- geometry changes how often wall-guided trajectories see and re-see gate neighborhoods
- geometry changes how quickly the same nondimensional control tuple samples the local pre-commit state graph

So the current principle should be read as:

- same state-graph logic
- different effective coefficients

This is exactly the distinction between shape-level universality and coefficient-level renormalization.

## Why this is a transport principle rather than a maze-specific summary

The note can now move beyond a maze-specific statement because the current claim is no longer tied to:

- one doorway layout
- one shell arrangement
- one absolute geometric scale

Instead, it is tied to:

- a pre-commit state-graph organization
- an admissibility role for delay
- a productive but non-monotone role for memory
- an ordering role for flow

That means the supported principle is about gated search-and-commit transport systems whose dynamics can be coarse-grained into a pre-commit backbone, not about one particular maze drawing.

## What is justified to claim now

Supported now:

- the productive-memory structure is not purely geometry-accidental within the tested family
- the first robust transferable object is the pre-commit backbone
- the strongest current universality claim is qualitative and structural, not coefficient-exact
- geometry mainly renormalizes scales and local coefficients before it destroys the backbone ordering
- the present evidence is already strong enough to support a geometry-general pre-commit transport principle across the tested family

Not yet justified:

- a geometry-general law for full crossing success
- a geometry-general law for post-commit crossing kinetics
- coefficient-exact collapse of all tested geometries onto one master curve
- a claim that all more complex labyrinthine geometries will preserve the same principle without further testing

## What still needs stress testing or finer renormalization?

Three open layers remain explicit.

First, finer renormalization:

- `GF1` and `GF2` reached `tau_g = Tmax` in the first pass, so their current `tau_g` and `ell_g` are conservative coarse scales rather than finely resolved full-exit scales
- a tighter reference extraction could sharpen how strongly the families collapse after renormalization
- a later tiny local renormalization slice may still be useful if a future geometry preserves the backbone but shifts one branch numerically

Second, stress testing:

- `GF3_RANDOM_LABYRINTH_STRESS_TEST` remains deferred
- stronger disorder, recirculation, or multiscale trapping could still reveal a genuine backbone breakdown
- broader geometry families are needed before making any claim stronger than tested-family generality

Third, crossing-specific structure:

- the current transfer result does not establish universality of `crossing_given_commit`
- the post-commit completion layer remains sparse and intentionally secondary
- full success, efficiency, and thermodynamic cost can still depend on geometry-specific post-commit physics that the present principle does not absorb

## Bottom Line

The first geometry-transfer validation upgrades the current claim from a one-geometry pre-commit principle to a tested-family transport principle:

- the pre-commit backbone transfers robustly in shape
- geometry renormalizes coefficients rather than destroying the ordering logic
- the most defensible universality claim is therefore structural, not coefficient-exact
- the crossing-specific completion layer remains outside the current principle and must be tested separately
