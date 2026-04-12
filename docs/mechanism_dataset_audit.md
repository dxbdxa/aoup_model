# Mechanism Dataset Audit

## Scope

This audit checks the built mechanism dataset against the canonical source semantics before any strong mechanism interpretation.

- canonical manifest: [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- trajectory dataset: [trajectory_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset/trajectory_level.parquet)
- event dataset: [event_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset/event_level.parquet)
- gate-conditioned dataset: [gate_conditioned.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset/gate_conditioned.parquet)
- metric alignment note: [mechanism_metric_alignment_note.md](file:///home/zhuguolong/aoup_model/docs/mechanism_metric_alignment_note.md)

## Main Findings

- The source/replay trap mismatch is primarily a definition mismatch plus confirmed-trap bookkeeping, not a physics replay failure.
- Source `trap_time_mean` is an episode-conditioned mean. Comparing it to trajectory-mean `trap_time_total` artificially suppresses the replayed value by a factor of approximately the trap-event rarity.
- The original event-table trap rows undercounted trap duration because `duration` started at confirmation rather than onset. This audit adds onset-aligned trap fields to `event_level.parquet`.
- `phase_lag_navigation_mean`, `phase_lag_steering_mean`, and `alignment_at_gate_mean` use signed conventions; `alignment_on_wall_mean` is unsigned by construction.
- `gate_capture_probability` and `return_to_wall_after_capture_rate` are internally compatible on their present proxy-conditioned sets, but they are not yet clean gate-transition probabilities because `gate_crossing` is extremely sparse relative to `gate_capture`.

## Trap Metric Audit

| canonical_label            |   source_trap_time_mean |   trajectory_mean_trap_time_total |   trajectory_episode_mean_from_totals |   event_duration_raw_mean |   event_duration_aligned_mean |   n_trap_events |
|:---------------------------|------------------------:|----------------------------------:|--------------------------------------:|--------------------------:|------------------------------:|----------------:|
| OP_SUCCESS_TIP             |                 0.5125  |                       6.2561e-05  |                               0.5125  |                   0.015   |                       0.5125  |               1 |
| OP_EFFICIENCY_TIP          |                 0       |                       0           |                               0       |                   0       |                       0       |               0 |
| OP_SPEED_TIP               |                 0       |                       0           |                               0       |                   0       |                       0       |               0 |
| OP_BALANCED_RIDGE_MID      |                 0       |                       0           |                               0       |                   0       |                       0       |               0 |
| OP_STALE_CONTROL_OFF_RIDGE |                 0.51125 |                       0.000249634 |                               0.51125 |                   0.01375 |                       0.51125 |               2 |

Interpretation:

- `trajectory_episode_mean_from_totals` matches the canonical source trap metric, which shows that the trajectory-level trap totals are already source-compatible.
- `event_duration_raw_mean` is the bookkeeping mismatch: it captures only the post-confirmation tail of a trap episode.
- `event_duration_aligned_mean` restores the source-compatible duration by adding the deterministic confirmation backshift.

## Sign And Meaning Audit

- `phase_lag_navigation_mean`: signed circular lag in radians relative to the navigation field; positive is counterclockwise relative to the navigation direction.
- `phase_lag_steering_mean`: signed circular lag in radians relative to the delayed steering target; same sign convention.
- `alignment_at_gate_mean`: signed cosine-like gate-forward alignment; positive means inward through-door motion.
- `alignment_on_wall_mean`: unsigned wall tangentiality in `[0, 1]`; it cannot distinguish opposite circulation senses.

## Conditioning Audit

| canonical_label            |   capture_given_approach |   crossing_given_capture |   return_to_wall_after_capture_rate |   capture_exit_to_bulk_motion |   capture_exit_to_gate_approach |   capture_exit_to_wall_sliding |   capture_exit_to_gate_crossing |   n_capture_events |
|:---------------------------|-------------------------:|-------------------------:|------------------------------------:|------------------------------:|--------------------------------:|-------------------------------:|--------------------------------:|-------------------:|
| OP_BALANCED_RIDGE_MID      |                 0.573727 |              5.72705e-05 |                            0.366703 |                      0.622568 |                      0.0106714  |                       0.366703 |                     5.72705e-05 |              52383 |
| OP_EFFICIENCY_TIP          |                 0.561982 |              5.37702e-05 |                            0.369276 |                      0.62058  |                      0.0100909  |                       0.369276 |                     5.37702e-05 |              55793 |
| OP_SPEED_TIP               |                 0.599627 |              6.21446e-05 |                            0.363587 |                      0.626594 |                      0.0097567  |                       0.363587 |                     6.21446e-05 |              96549 |
| OP_STALE_CONTROL_OFF_RIDGE |                 0.583724 |              5.68645e-05 |                            0.363914 |                      0.626173 |                      0.00985651 |                       0.363914 |                     5.68645e-05 |              52757 |
| OP_SUCCESS_TIP             |                 0.565259 |              5.3383e-05  |                            0.367945 |                      0.621651 |                      0.0103504  |                       0.367945 |                     5.3383e-05  |             168593 |

Interpretation:

- `capture_given_approach` and `return_to_wall_after_capture_rate` are computed on compatible current gate-proxy states.
- The large bulk-motion and wall-sliding exit fractions, together with the tiny `crossing_given_capture`, show that current `gate_capture` is best treated as gate-mouth residence rather than a committed shell-transition state.

## Which current observables are trustworthy enough for gate theory, and which need caution?

- Trustworthy now: success probability, source-compatible trap burden from `trap_time_total` and `n_trap_events`, wall-contact fraction from the replay, first-capture delay as a gate-proxy timing observable, and wall dwell before first capture as a pre-capture residence observable.
- Use with caution: `phase_lag_navigation_mean` and `phase_lag_steering_mean` are well-defined but currently weak ridge-vs-stale discriminators because their point-level means stay close to zero.
- Use with caution: `alignment_at_gate_mean` is interpretable, but only on the current gate-local proxy conditioning set.
- Use with caution: `alignment_on_wall_mean` is robust as tangentiality magnitude, but not as a directional wall-circulation observable because the sign is discarded.
- Not yet trustworthy as final gate-theory rates: `gate_capture_probability`, `crossing_given_capture`, and `return_to_wall_after_capture_rate` because the present `gate_capture`/`gate_crossing` pair does not yet form a clean transition chain.

## Can the stale-control point already be distinguished mechanistically with confidence?

- Not with high confidence from the current gate-local proxy metrics alone. `capture_given_approach` is 0.5737 for the balanced ridge point and 0.5837 for the stale-control point, while `return_to_wall_after_capture_rate` is 0.3667 vs 0.3639; these are too close for a strong mechanistic separation.
- The stale-control point does show a somewhat larger first-capture delay (1.6462 vs 1.5765) and wall dwell before capture (0.5095 vs 0.4875), but the differences are moderate rather than decisive.
- Trap burden is suggestive but sparse: the balanced ridge point has mean trap burden 0.000000, while the stale-control point has 0.000250. This supports cautionary qualitative separation, not yet a strong quantitative mechanism claim.

## Changelog

- Updated `event_level.parquet` to add `t_start_aligned`, `duration_aligned`, and `trap_confirmation_backshift` for source-compatible trap aggregation.

## Audit Outputs

- [trap_metric_alignment.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/trap_metric_alignment.png)
- [capture_exit_partition.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/capture_exit_partition.png)
- [ridge_vs_stale_audit.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/ridge_vs_stale_audit.png)
- [trap_metric_alignment.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/trap_metric_alignment.csv)
- [conditioning_alignment.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/conditioning_alignment.csv)
- [observable_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_audit/observable_summary.csv)
