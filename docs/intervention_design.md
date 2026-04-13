# Intervention Design

## Scope

This note defines the local intervention dataset used for mechanism-causality tests around the productive ridge.

Primary inputs:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- [canonical_operating_points.md](file:///home/zhuguolong/aoup_model/docs/canonical_operating_points.md)
- [mechanism_first_look_refined.md](file:///home/zhuguolong/aoup_model/docs/mechanism_first_look_refined.md)
- [precommit_gate_theory_fit_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_fit_report.md)

Selection policy:

- use only the finished confirmatory ridge grid
- use only the local base-grid `4096`-trajectory points
- do not reopen the search
- anchor all three slices on the balanced ridge midpoint `(Pi_m, Pi_f, Pi_U) = (0.15, 0.020, 0.20)`

## Slice Construction

| slice_name   | axis_name   | fixed_controls             |   baseline_value |   n_points |
|:-------------|:------------|:---------------------------|-----------------:|-----------:|
| delay_slice  | Pi_f        | Pi_m = 0.150, Pi_U = 0.200 |             0.02 |          4 |
| memory_slice | Pi_m        | Pi_f = 0.020, Pi_U = 0.200 |             0.15 |          7 |
| flow_slice   | Pi_U        | Pi_m = 0.150, Pi_f = 0.020 |             0.2  |          5 |

## Measured Observables

Mechanism observables:

- `first_gate_commit_delay`
- `wall_dwell_before_first_commit`
- `trap_burden_mean`
- `residence_given_approach`
- `commit_given_residence`

Task and efficiency observables:

- `Psucc_mean`
- `MFPT_mean`
- `eta_sigma_mean`
- `eta_completion_drag`
- `eta_trap_drag`

Mechanism observables come from a refined replay using the existing gate-state extractor. Task and efficiency observables are taken from the persisted confirmatory summary so the intervention tables stay aligned with the frozen scan outputs.

## Ordering Rule

For each metric on each slice, the ordering package records three ingredients:

1. `first_step_rel_range`: the mean absolute change at the nearest off-ridge intervention points, normalized by the full slice range.
2. `monotonicity_score`: the average of absolute Spearman ordering and signed step-consistency.
3. `relative_range`: the slice range scaled by the metric magnitude and capped at `1`.

The combined early-indicator score is

`early_indicator_score = first_step_rel_range * monotonicity_score * relative_range`

Higher scores indicate that a quantity responds near the ridge and keeps a cleaner one-direction ordering under that control-axis intervention.

## Output Package

Dataset tables:

- [point_manifest.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/point_manifest.csv)
- [point_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/point_summary.csv)
- [slice_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/slice_summary.csv)
- [metric_ordering.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/metric_ordering.csv)

Trajectory-level replay outputs:

- [trajectory_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/trajectory_level.parquet)
- [event_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/event_level.parquet)
- [gate_conditioned.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/gate_conditioned.parquet)

Figures:

- [delay_slice_metrics.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/delay_slice_metrics.png)
- [memory_slice_metrics.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/memory_slice_metrics.png)
- [flow_slice_metrics.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/flow_slice_metrics.png)
- [intervention_ordering_heatmap.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/intervention_ordering_heatmap.png)
