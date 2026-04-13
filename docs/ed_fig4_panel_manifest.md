# Extended Data Figure 4 Panel Manifest

## Scope

This note documents the panel logic for Extended Data Figure 4, which carries the full intervention and reduced-law detail that sits behind the compact main-text pre-commit law statement.

Primary data sources:

- [intervention_design.md](file:///home/zhuguolong/aoup_model/docs/intervention_design.md)
- [intervention_dataset_run_report.md](file:///home/zhuguolong/aoup_model/docs/intervention_dataset_run_report.md)
- [intervention_mechanism_ordering.md](file:///home/zhuguolong/aoup_model/docs/intervention_mechanism_ordering.md)
- [precommit_reduced_law_candidates.md](file:///home/zhuguolong/aoup_model/docs/precommit_reduced_law_candidates.md)
- [precommit_prediction_validation_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_prediction_validation_report.md)
- [point_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/point_summary.csv)
- [slice_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/slice_summary.csv)
- [metric_ordering.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/metric_ordering.csv)
- [prediction_vs_validation.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/prediction_vs_validation.png)
- [reduced_law_scope_map.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/reduced_law_scope_map.png)
- [ED Figure 4 PNG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig4_reduced_law_and_interventions.png)
- [ED Figure 4 SVG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig4_reduced_law_and_interventions.svg)

## Figure-Level Message

- this figure gives the full slice detail and validation detail that underlie the main-text reduced-law statement
- the law remains strictly pre-commit throughout the figure
- `trap_burden_mean` is kept visible as a punctate stale flag rather than promoted into a smooth kinetic coordinate
- no panel implies a post-commit completion or full crossing-closure law

## Panel Logic

### Panel A

- title: `Delay-slice response curves around the balanced midpoint`
- purpose: show that delay moves the timing budget first, while trap burden stays deferred to the stale edge
- quantitative note: the baseline timing minimum sits at `Pi_f = 0.020`, and trap burden turns on only at `Pi_f = 0.025`

### Panel B

- title: `Memory-slice response curves inside the productive band`
- purpose: show that memory acts more cleanly on `residence_given_approach` than on timing or commitment conversion
- quantitative note: `residence_given_approach` rises from `0.2217` at low memory to `0.2328` before the edge roll-off

### Panel C

- title: `Flow-slice response curves along the local ridge`
- purpose: show the monotone contraction of the pre-commit timing budget under increasing flow
- quantitative note: `first_gate_commit_delay` falls from `2.6353` at `Pi_U = 0.10` to `1.3998` at `Pi_U = 0.30`

### Panel D

- title: `Early-indicator versus late-correlate summary heatmap`
- purpose: summarize the slice-level early-indicator scores and direction labels across the reduced-law observables
- quantitative note: `commit_given_residence` is classified as `late`, while `trap_burden_mean` is classified as `stale flag`

### Panel E

- title: `Prediction-by-prediction validation summary`
- purpose: report the explicit validation checks and observed evidence for each reduced-law prediction
- quantitative note: `5` of `5` predictions are currently `supported`

### Panel F

- title: `Reduced-law scope: where it works and where failure is expected`
- purpose: show which tasks or regions are already in scope, only partly in scope, or expected to fail under the current reduced law
- quantitative note: the scope panel contains `2` `works_well`, `1` `works_with_limits`, and `3` `expected_failure` regions

## Why this stays pre-commit only

- slice panels A-C show timing, arrival, commitment, and trap responses only through the pre-commit mechanism variables
- panel F keeps post-commit completion and full efficiency ranking inside the explicit expected-failure scope column
- this figure therefore strengthens the reduced-law evidence package without quietly promoting a post-commit closure claim

## Bottom Line

Extended Data Figure 4 is the full evidence layer behind the reduced-law package: timing and arrival observables move first, commit conversion stays late and comparatively flat, trap burden behaves as a punctate stale flag, and the law remains deliberately bounded to pre-commit structure.
