# Extended Data Figure 5 Panel Manifest

## Scope

This note documents the panel logic for Extended Data Figure 5, which provides the family-specific support behind the main-text geometry-transfer verdict while keeping the claim ceiling at shape-level transfer plus coefficient renormalization.

Primary data sources:

- [extended_data_plan.md](file:///home/zhuguolong/aoup_model/docs/extended_data_plan.md)
- [geometry_family_spec.md](file:///home/zhuguolong/aoup_model/docs/geometry_family_spec.md)
- [geometry_transfer_plan.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_plan.md)
- [geometry_transfer_run_report.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_run_report.md)
- [geometry_transfer_first_look.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_first_look.md)
- [geometry_transfer_evidence_table.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_evidence_table.md)
- [geometry_transfer_claim_upgrade_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_claim_upgrade_note.md)
- [canonical_transfer_summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/geometry_transfer/canonical_transfer_summary.csv)
- [reference_extraction_summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/geometry_transfer/reference_extraction_summary.csv)
- [geometry_transfer_invariant_table.csv](file:///home/zhuguolong/aoup_model/outputs/tables/geometry_transfer_invariant_table.csv)
- [transfer_stress_figure.png](file:///home/zhuguolong/aoup_model/outputs/figures/geometry_transfer/transfer_stress_figure.png)
- [ED Figure 5 PNG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig5_geometry_transfer_detail.png)
- [ED Figure 5 SVG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig5_geometry_transfer_detail.svg)

## Figure-Level Message

- this figure exists to show family-specific support for the transfer verdict, not to expand the verdict beyond the tested GF0/GF1/GF2 family
- the transferable object remains the pre-commit backbone rather than full crossing completion
- shape survival and coefficient renormalization are both made explicit, so the reader can see why coefficient identity is not the right claim
- weaker transfer signals are kept visible but secondary

## Panel Logic

### Panel A

- title: `Compact geometry gallery for GF0, GF1, and GF2 with matched transfer object highlighted`
- purpose: show the three tested families and keep attention on the shared approach-residence-commit object rather than downstream completion
- quantitative note: all gallery cartoons carry the same five-state backbone `bulk -> wall -> approach -> residence -> commit`

### Panel B

- title: `Family-specific backbone ordering comparison`
- purpose: compare within-family shape profiles for commit delay, wall dwell, and arrival organization across the canonical operating-point order
- quantitative note: timing and wall-dwell retain the same canonical order in all three tested families, while arrival preserves the same discriminator ordering

### Panel C

- title: `Full invariant table visualization, including survives / renormalizes / weakens / fails`
- purpose: show the whole verdict package rather than only the strengthened rows
- quantitative note: counts are survives `3`, renormalizes `1`, weakens `2`, fails `1`

### Panel D

- title: `Coefficient-renormalization detail panel`
- purpose: make the difference between shape survival and coefficient identity visually explicit
- quantitative note: the largest displayed GF1/GF2 to GF0 ratio is `2.73`, with `GF1` commit events at `0.43` and `GF2` wall fraction at `1.78`

### Panel E

- title: `Weaker transfer signals such as trap burden and selectivity scalar behavior`
- purpose: retain weaker signals without allowing them to dominate the figure-level verdict
- quantitative note: trap matched-pair deltas are `2.50e-04`, `0`, and `-0.002` for GF0, GF1, and GF2 respectively

### Panel F

- title: `Optional scope note panel explicitly separating tested-family support from broader GF3-style stress claims`
- purpose: mark the boundary between what the tested family supports now and what remains deferred
- quantitative note: GF3 remains deferred and no unrestricted universality claim is upgraded by this figure

## Trusted Transfer Layer

- strongest support: canonical timing order, stale-vs-balanced timing penalty, and arrival-order backbone shape
- strengthened but renormalized: reference scales and local encounter coefficients
- weaker and kept secondary: single-scalar selectivity and trap burden as matched transfer signals

## Why this stays scoped

- the figure is centered on GF0/GF1/GF2 and the pre-commit backbone only
- coefficient-exact identity is shown as failed rather than quietly folded into the transfer claim
- GF3-style irregular-labyrinth universality remains explicitly outside the upgraded claim
- post-commit completion transfer is not promoted here

## Bottom Line

Extended Data Figure 5 is the detailed support layer behind the main-text geometry-transfer verdict. It shows that the pre-commit backbone survives across the tested family at the level of shape, that the absolute coefficients renormalize rather than match exactly, and that weaker signals stay visibly secondary while broader universality remains out of scope.
