# Thermodynamic Bookkeeping

## Scope

This note defines the current thermodynamic bookkeeping for the delayed active transport model. Its purpose is not to claim a completed stochastic-thermodynamic theory, but to state clearly which cost channels are already represented, which are only proxies, and which are still missing.

Primary inputs:

- [theory_compression_note.md](file:///home/zhuguolong/aoup_model/docs/theory_compression_note.md)
- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [geometry_transfer_principle_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_principle_note.md)
- [principle_scope_statement.md](file:///home/zhuguolong/aoup_model/docs/principle_scope_statement.md)
- [simulation.py](file:///home/zhuguolong/aoup_model/legacy/simcore/simulation.py#L211-L223)
- [simulation.py](file:///home/zhuguolong/aoup_model/legacy/simcore/simulation.py#L468-L471)
- [simulation.py](file:///home/zhuguolong/aoup_model/legacy/simcore/simulation.py#L543-L564)
- [legacy_output_map.md](file:///home/zhuguolong/aoup_model/docs/legacy_output_map.md#L45-L48)
- [legacy_parameter_map.md](file:///home/zhuguolong/aoup_model/docs/legacy_parameter_map.md#L50-L55)
- [legacy_parameter_map.md](file:///home/zhuguolong/aoup_model/docs/legacy_parameter_map.md#L137-L139)

The current strongest physics claim remains a geometry-tested pre-commit transport principle. Thermodynamic interpretation must therefore be organized around what can be said rigorously about pre-commit organization, without overclaiming a full completion-layer entropy budget.

## Current Implemented Efficiency Metric

The model currently computes:

- `J_proxy = Psucc / Tmax`
- `Sigma_drag_i = (1 / Tmax) \int_0^{Tmax} dt gamma0 ||v - flow||^2 / kBT` in discrete form
- `sigma_drag = mean_i(Sigma_drag_i)`
- `eta_sigma = J_proxy / max(sigma_drag, sigma_floor)`

In code terms, the implemented drag accumulation is the trajectory sum

`dt * gamma0 * ||v - flow||^2 / kBT`

and the point-level efficiency is the transport proxy divided by the mean drag-dissipation proxy.

This makes `eta_sigma` a dissipation-normalized screening metric, not a full thermodynamic efficiency in the first-principles sense.

## Which cost channels are already modeled, and which are only proxies?

The cleanest bookkeeping is to separate four channels.

### 1. Active propulsion dissipation

What is present:

- active self-propulsion is part of the dynamics through `v0`
- trajectories move because of active drive, flow, wall repulsion, noise, and delayed steering

What is not separately booked:

- no explicit chemical or internal active-fuel work term
- no explicit propulsion-power integral separated from drag
- no propulsion efficiency comparing active input work to transport output

So active propulsion is dynamically present, but not thermodynamically isolated as its own computed cost channel.

### 2. Medium or drag dissipation

What is present:

- this is the one cost channel that is explicitly accumulated
- the proxy is based on motion relative to the background flow, `||v - flow||^2`
- the coefficient `gamma0` sets the instantaneous drag scale
- the result is recorded as `Sigma_drag_i`, aggregated as `sigma_drag`, and used in `eta_sigma`

What this means physically:

- the current bookkeeping already measures a medium-coupled dissipative burden associated with translational motion through the environment
- it is best read as a drag-rate proxy or medium-dissipation proxy

What it does not mean:

- it is not automatically equal to total entropy production
- it does not include all hidden controller, memory, or internal active-drive costs

### 3. Controller or steering cost proxy

What is present:

- kinematic controller diagnostics do exist
- `phase_lag_steering_mean` measures motion-angle minus controller steering-angle lag
- alignment observables measure how motion aligns with gate normals or wall tangents
- the refined mechanism dataset records `steering_lag_at_commit_mean`, `alignment_at_gate_mean`, and related directional diagnostics

What is missing:

- no energetic controller-work term is accumulated
- no explicit work-like penalty for turning, heading correction, or steering updates is computed
- no separate dissipation term associated with delayed steering actuation exists in the current outputs

So controller burden is only represented kinematically, not energetically.

### 4. Information-rate or update-cost proxy

What is present:

- delayed feedback and memory timescales enter the dynamics and organize performance
- lag observables reveal stale versus coherent guidance
- event-level structure tells us whether updates appear productively synchronized or stale

What is missing:

- no explicit information rate
- no update-frequency cost
- no bit-rate, sampling-cost, or control-bandwidth penalty
- no thermodynamic information-processing term

So information or update burden is not yet a computed cost channel; it is only indirectly proxied by delay- and lag-sensitive kinematics.

## Bookkeeping Table

The current model can therefore be summarized as follows.

- explicitly modeled as a cost proxy: medium or drag dissipation
- dynamically present but not separately costed: active propulsion
- partially represented through observables only: controller or steering burden
- not yet modeled as a cost term: information-rate or update cost
- not yet modeled as a cost term: memory-bath or viscoelastic dissipation beyond the drag proxy
- not yet cleanly separated: pre-commit versus post-commit drag spending

## Why eta_sigma is useful, and why it is not yet the full thermodynamic answer

`eta_sigma` is useful because it does three practical things already.

First:

- it penalizes transport strategies that move expensively relative to the medium without producing proportionate transport success

Second:

- it allows consistent ranking across parameter sets even when fastest and most successful operation differ

Third:

- it gives a screening-level efficiency coordinate that is already informative enough to expose a speed-efficiency separation and a productive-memory ridge

But it is not yet the full thermodynamic answer for equally clear reasons.

It is not a full answer because:

- the numerator is a transport proxy, `Psucc / Tmax`, not a thermodynamic output flux derived from first-principles work or free-energy conversion
- the denominator contains only the currently implemented drag-dissipation proxy
- there is no explicit bookkeeping for active internal work, steering actuation work, memory-kernel dissipation, or information/update costs
- post-commit completion costs are not separated from pre-commit search costs
- no total entropy-production decomposition is computed

So `eta_sigma` is best understood as a rigorously defined model-internal screening metric, not as total thermodynamic efficiency.

## How the pre-commit backbone changes the thermodynamic reading of efficiency

The pre-commit backbone changes the reading of efficiency in an important way.

Without the mechanism picture, one might read efficiency only as:

- success per unit drag proxy

With the pre-commit backbone in hand, one can say more:

- a substantial part of the efficiency ranking is already controlled by how costly it is to reach strong commitment, not only by what happens after commitment
- stale operation wastes cost before commitment through prolonged wall dwell, recycling, revisit structure, and delayed or weak conversion from residence to commitment
- productive operation improves the drag-normalized reading partly by organizing search, wall-guided approach, and commitment on a shorter or cleaner pre-commit path

That changes the interpretation of efficiency from a purely outcome-based metric to a mechanism-aware one:

- pre-commit organization already determines a large share of whether drag spending is productive or wasteful
- post-commit completion can still matter, but it is not the first place where the efficiency ordering is created

This is fully consistent with the present geometry-tested principle: the transferable object is the pre-commit backbone, so the first thermodynamic reading of efficiency should also be organized around pre-commit cost wasting versus pre-commit productive conversion.

## Pre-Commit Costs Versus Completion Costs

The model supports a qualitative cost split, but not yet a full quantitative one.

### Costs that are already interpretable as mainly pre-commit

These are the parts of the current picture that can already be discussed rigorously at the mechanism level:

- wall dwell before first commitment
- first-gate-commit delay
- residence-to-commit conversion quality
- return-to-wall after precommit recycling
- trap burden when it appears before or around failed commitment organization

These do not yet form a separated thermodynamic integral, but they do identify where drag spending is likely being wasted before commitment.

### Costs that still belong partly or mainly to post-commit completion

These are not yet thermodynamically resolved:

- drag spending after commitment but before completed exit
- final crossing-conditioned success or failure
- any extra energetic burden associated with post-commit recirculation or partial crossings
- geometry-specific completion costs that may differ even when the pre-commit backbone transfers

So the current bookkeeping can support a pre-commit thermodynamic reading qualitatively, but it cannot yet produce a full pre-commit versus post-commit dissipation decomposition numerically.

## Missing Terms That Must Stay Explicit

The following missing terms should be stated openly whenever thermodynamic language is used.

Missing or unresolved terms:

- internal active-propulsion work or chemical-fuel consumption
- memory-kernel or viscoelastic bath dissipation as a separate energetic channel
- controller actuation work
- information-rate, update-rate, or sensing cost
- rotational-noise-related entropy bookkeeping as a full thermodynamic contribution
- post-commit and completion-layer dissipation separated from pre-commit drag burden
- a total entropy-production balance

A practical additional warning is that some legacy fields linked to memory-side sigma bookkeeping are documented as unused in the current kernel, so they should not be cited as already implemented thermodynamic terms.

## What Can Already Be Discussed Rigorously

Rigorous now:

- the model contains a well-defined drag-dissipation proxy
- `eta_sigma` is a well-defined drag-normalized transport proxy
- mechanism observables can identify where efficiency gains or losses are being organized on the pre-commit backbone
- the speed-efficiency separation is meaningful at the level of this proxy bookkeeping
- the pre-commit principle already changes how efficiency should be interpreted mechanistically

Not rigorous yet:

- total entropy production
- thermodynamic efficiency in the strong first-principles sense
- energetic controller optimality
- information-thermodynamic claims
- a full decomposition of efficiency into pre-commit and post-commit cost budgets

## Bottom Line

The current model already supports a useful but incomplete thermodynamic bookkeeping:

- one explicit cost proxy is medium or drag dissipation
- active propulsion is dynamically present but not separately costed
- steering and update burdens are visible only through kinematic proxies
- `eta_sigma` is therefore a drag-normalized transport-screening metric, not a total thermodynamic efficiency
- the pre-commit backbone makes that metric more interpretable, because it shows where costs become productive or wasteful before completion
