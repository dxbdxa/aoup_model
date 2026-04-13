# Extended Data Figure 3 Panel Manifest

## Scope

This note documents the panel logic for Extended Data Figure 3, which validates the robustness of the mechanism package while keeping audit detail out of the main figures.

Primary data sources:

- [mechanism_event_classification_note.md](file:///home/zhuguolong/aoup_model/docs/mechanism_event_classification_note.md)
- [mechanism_dataset_audit.md](file:///home/zhuguolong/aoup_model/docs/mechanism_dataset_audit.md)
- [mechanism_metric_alignment_note.md](file:///home/zhuguolong/aoup_model/docs/mechanism_metric_alignment_note.md)
- [gate_state_refinement_note.md](file:///home/zhuguolong/aoup_model/docs/gate_state_refinement_note.md)
- [mechanism_refined_run_report.md](file:///home/zhuguolong/aoup_model/docs/mechanism_refined_run_report.md)
- [threshold_sensitivity_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/threshold_sensitivity_summary.csv)
- [trap_metric_alignment.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/trap_metric_alignment.csv)
- [conditioning_alignment.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/conditioning_alignment.csv)
- [old_vs_refined_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/old_vs_refined_summary.csv)
- [refined_summary_by_point.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_summary_by_point.csv)
- [event_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined/event_level.parquet)
- [ED Figure 3 PNG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig3_mechanism_audit_and_thresholds.png)
- [ED Figure 3 SVG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig3_mechanism_audit_and_thresholds.svg)

## Figure-Level Message

- this figure exists to validate robustness of the mechanism package rather than to carry the main-text principle claim
- the strongest audited observables remain pre-commit timing plus source-aligned trap burden
- proxy-conditioned gate-local observables are shown explicitly, but kept separate from the trustworthy pre-commit layer
- post-commit crossing remains sparse and is not promoted to the leading mechanism variable

## Panel Logic

### Panel A

- title: `Event-classification thresholds and refined state graph`
- purpose: summarize the refined threshold rules and the coarse event-graph occupancy / exit structure
- quantitative note: `bulk` plus `wall` occupy `91.3%` of event rows, while `commit -> crossing` is only `0.0065%` of commit exits

### Panel B

- title: `Trap metric alignment: source-compatible and raw event durations`
- purpose: show that source-compatible trap burden is recovered by aligned event durations and episode-conditioned trajectory totals, while raw event duration undercounts the trap episode
- quantitative note: only the success tip and stale-control point carry nonzero trap episodes in the current canonical set

### Panel C

- title: `Old and refined gate-state definitions on the matched pair`
- purpose: compare the original proxy capture state with the refined residence / commit split on the balanced ridge versus stale-control pair
- quantitative note: the refined graph raises timing observables slightly but drives post-commit return fractions far below the old proxy capture return values

### Panel D

- title: `Threshold sensitivity of classifier-near event shares`
- purpose: report how much of each classified event family sits close to the operative thresholds
- quantitative note: wall-sliding near-threshold shares stay near `0.05`, gate-capture depth shares near `0.54`, and trap-duration shares appear only where confirmed traps exist

### Panel E

- title: `Trusted ridge-versus-stale observables in the refined audit`
- purpose: isolate the robust matched-pair discriminators already promoted into the refined mechanism reading
- quantitative note: the trusted layer is `first_gate_commit_delay`, `wall_dwell_before_first_commit`, and source-aligned `trap_burden_mean`

### Panel F

- title: `Proxy-conditioned gate-local observables and compatibility`
- purpose: keep the compatible but weaker gate-local proxy observables visible without promoting them into the leading mechanism argument
- quantitative note: crossing probabilities remain on the order of `1e-4` or smaller and therefore stay secondary

## Trusted Versus Proxy-Conditioned Observables

- trustworthy now: `first_gate_commit_delay`, `wall_dwell_before_first_commit`, and source-compatible `trap_burden_mean`
- weaker or proxy-conditioned: `capture_given_approach`, `residence_given_approach`, `commit_given_residence`, `crossing_given_capture`, `crossing_given_commit`, and the return-to-wall fractions tied to those proxy states

## Why this stays pre-commit

- the figure keeps the decisive mechanism on the pre-commit side by separating trusted timing observables from sparse post-commit crossing quantities
- post-commit crossing is shown mainly to justify why it is not the headline mechanism variable

## Bottom Line

Extended Data Figure 3 is the robustness layer behind the pre-commit mechanism package. It shows that the event classification, trap bookkeeping, refined gate-state split, and matched-pair audits are coherent enough to support the pre-commit reading while keeping proxy-conditioned and post-commit quantities explicitly secondary.
