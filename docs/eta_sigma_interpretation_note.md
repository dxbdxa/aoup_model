# eta_sigma Interpretation Note

## Scope

This note explains exactly where `eta_sigma` fits in the current model and why it should be used carefully.

Primary inputs:

- [thermodynamic_bookkeeping.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_bookkeeping.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [geometry_transfer_principle_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_principle_note.md)
- [simulation.py](file:///home/zhuguolong/aoup_model/legacy/simcore/simulation.py#L543-L564)
- [legacy_output_map.md](file:///home/zhuguolong/aoup_model/docs/legacy_output_map.md#L45-L48)

## Definition

The current model defines:

- `J_proxy = Psucc / Tmax`
- `eta_sigma = J_proxy / max(sigma_drag, sigma_floor)`

with `sigma_drag` the mean drag-dissipation proxy accumulated from relative motion through the medium.

So `eta_sigma` is best read as:

- successful transport rate per unit drag proxy

not as:

- total thermodynamic efficiency
- total entropy-production inverse
- a complete work-to-output conversion efficiency

## Why eta_sigma is useful, and why it is not yet the full thermodynamic answer

Useful:

- it combines a transport-side outcome with a cost-side penalty in one scalar ranking metric
- it distinguishes fastest transport from drag-efficient transport
- it has already been strong enough to reveal a nontrivial productive-memory ridge and a speed-efficiency separation
- it remains comparable across the currently tested geometry family when interpreted as a proxy metric

Not yet the full answer:

- it uses a proxy numerator rather than a first-principles output flux
- it uses only drag dissipation in the denominator
- it omits active internal work, controller work, memory-bath losses, and information/update costs
- it mixes pre-commit and post-commit spending into one trajectory-level quantity
- it therefore cannot be promoted to total thermodynamic efficiency without additional bookkeeping

## How the pre-commit backbone changes the thermodynamic reading of efficiency

The pre-commit backbone sharpens the interpretation of `eta_sigma`.

Before the backbone analysis, a high `eta_sigma` value could only be read as a good global tradeoff between transport success rate and drag proxy.

After the backbone analysis, one can say more:

- high `eta_sigma` often reflects a productive pre-commit organization, not merely a favorable final completion step
- lower `eta_sigma` can arise because the system spends too much time in wall-guided recycling, stale residence cycles, or delayed commitment before any final crossing advantage matters
- the geometry-transfer result strengthens this reading because the pre-commit ordering survives across `GF1` and `GF2` even when absolute coefficients renormalize

So the main thermodynamic interpretation now is:

- `eta_sigma` is partially diagnosing whether drag spending before commitment is organized productively or wasted through stale pre-commit search

That is a stronger and more mechanistic statement than a plain outcome ratio, but it is still not a full thermodynamic closure.

## What eta_sigma can support right now

It can support:

- screening and ranking of operating points
- comparison of speed-favored and drag-efficient regimes
- mechanism-aware interpretation of why some regimes are efficient proxies and others are wasteful proxies
- geometry-tested discussion of structural efficiency trends at the level of the pre-commit backbone

It cannot by itself support:

- total entropy-production claims
- energetic optimal-control claims
- information-thermodynamic claims
- exact attribution of efficiency gains to pre-commit versus post-commit energetic channels

## Relationship to Geometry Transfer

The first geometry-transfer validation matters for `eta_sigma` interpretation because it shows that the efficiency story is not purely tied to one geometry-specific layout.

What transferred:

- the pre-commit ordering logic that makes some drag spending productive and some wasteful

What renormalized:

- absolute geometric scales and local encounter coefficients

What remains outside scope:

- whether the full post-commit completion layer also collapses thermodynamically across geometries

So `eta_sigma` can now be discussed as part of a geometry-tested structural principle, but only at the level of pre-commit transport organization plus drag normalization.

## Recommended Claim Language

Good current language:

> `eta_sigma` is a model-internal, drag-normalized transport-efficiency proxy that is useful for screening, ranking, and interpreting how pre-commit transport organization makes dissipation productive or wasteful.

Language to avoid:

- total entropy-production efficiency
- full thermodynamic efficiency
- complete energetic efficiency of the controller
- universal efficiency law

## Bottom Line

`eta_sigma` is valuable because it is already sensitive to the right competition between transport output and drag-like cost, and the pre-commit backbone now explains why. But it remains a partial bookkeeping quantity, not the final thermodynamic answer.
