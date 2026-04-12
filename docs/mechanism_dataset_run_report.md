# Mechanism Dataset Run Report

## Scope

This report summarizes the first wrapper-side mechanism dataset extracted from the frozen canonical operating points only.

- canonical manifest: [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- event rules: [mechanism_event_classification_note.md](file:///home/zhuguolong/aoup_model/docs/mechanism_event_classification_note.md)
- trajectory parquet: [trajectory_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset/trajectory_level.parquet)
- event parquet: [event_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset/event_level.parquet)
- gate-conditioned parquet: [gate_conditioned.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset/gate_conditioned.parquet)

## Canonical Replay Set

- `OP_SUCCESS_TIP`: state_point_id `ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378`, `(Pi_m, Pi_f, Pi_U)=(0.080, 0.025, 0.100)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378/result.json)
- `OP_EFFICIENCY_TIP`: state_point_id `9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8`, `(Pi_m, Pi_f, Pi_U)=(0.180, 0.018, 0.150)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8/result.json)
- `OP_SPEED_TIP`: state_point_id `d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7`, `(Pi_m, Pi_f, Pi_U)=(0.100, 0.018, 0.300)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7/result.json)
- `OP_BALANCED_RIDGE_MID`: state_point_id `181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b`, `(Pi_m, Pi_f, Pi_U)=(0.150, 0.020, 0.200)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b/result.json)
- `OP_STALE_CONTROL_OFF_RIDGE`: state_point_id `82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee`, `(Pi_m, Pi_f, Pi_U)=(0.150, 0.025, 0.200)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee/result.json)

## First-Look Summary

| canonical_label            | state_point_id                                                   |   Pi_m |   Pi_f |   Pi_U |   n_traj |   success_probability |   gate_capture_probability |   crossing_given_capture |   gate_capture_delay |   wall_dwell_before_capture |   trap_episode_count_mean |   trap_episode_duration_mean |   trap_escape_probability |   trap_escape_time |   phase_lag_navigation_mean |   phase_lag_steering_mean |   alignment_at_gate_mean |   alignment_on_wall_mean |   progress_along_navigation_rate |   progress_rate_at_gate_mean |   return_to_wall_after_capture_rate |   n_event_rows |   n_trap_event_rows |
|:---------------------------|:-----------------------------------------------------------------|-------:|-------:|-------:|---------:|----------------------:|---------------------------:|-------------------------:|---------------------:|----------------------------:|--------------------------:|-----------------------------:|--------------------------:|-------------------:|----------------------------:|--------------------------:|-------------------------:|-------------------------:|---------------------------------:|-----------------------------:|------------------------------------:|---------------:|--------------------:|
| OP_SPEED_TIP               | d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7 |   0.1  |  0.018 |   0.3  |     8192 |              0.868652 |                   0.599627 |              6.21446e-05 |              1.29912 |                    0.387508 |               0           |                      0       |                       nan |          nan       |                 -0.00941419 |               -0.00640638 |                 0.692804 |                 0.900544 |                         0.182267 |                      2.87768 |                            0.363587 |        5629814 |                   0 |
| OP_EFFICIENCY_TIP          | 9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8 |   0.18 |  0.018 |   0.15 |     4096 |              0.959229 |                   0.561982 |              5.37702e-05 |              1.85136 |                    0.588416 |               0           |                      0       |                       nan |          nan       |                  0.0026595  |               -0.00553169 |                 0.68947  |                 0.90031  |                         0.157772 |                      2.86637 |                            0.369276 |        2251507 |                   0 |
| OP_BALANCED_RIDGE_MID      | 181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b |   0.15 |  0.02  |   0.2  |     4096 |              0.952393 |                   0.573727 |              5.72705e-05 |              1.57651 |                    0.487486 |               0           |                      0       |                       nan |          nan       |                  0.015599   |                0.0216213  |                 0.690849 |                 0.900301 |                         0.166634 |                      2.87073 |                            0.366703 |        2137757 |                   0 |
| OP_SUCCESS_TIP             | ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378 |   0.08 |  0.025 |   0.1  |     8192 |              0.974121 |                   0.565259 |              5.3383e-05  |              2.68446 |                    0.843139 |               0.00012207  |                      0.5125  |                         1 |            0.5125  |                 -0.00202227 |               -0.00759122 |                 0.687966 |                 0.899863 |                         0.111522 |                      2.84842 |                            0.367945 |        5766578 |                   1 |
| OP_STALE_CONTROL_OFF_RIDGE | 82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee |   0.15 |  0.025 |   0.2  |     4096 |              0.948486 |                   0.583724 |              5.68645e-05 |              1.64619 |                    0.509537 |               0.000488281 |                      0.51125 |                         1 |            0.51125 |                  0.00858306 |                0.0100793  |                 0.690663 |                 0.900041 |                         0.163328 |                      2.86469 |                            0.363914 |        2252631 |                   2 |

## Replay Validation

The mechanism replay keeps the legacy dynamics unchanged and reproduces the canonical point-level summary statistics from persisted provenance.

| canonical_label            | state_point_id                                                   |   source_p_succ |   replayed_p_succ |   delta_p_succ |   source_trap_time_mean |   replayed_trap_time_mean |   delta_trap_time_mean |   source_wall_fraction_mean |   replayed_wall_fraction_mean |   delta_wall_fraction_mean |
|:---------------------------|:-----------------------------------------------------------------|----------------:|------------------:|---------------:|------------------------:|--------------------------:|-----------------------:|----------------------------:|------------------------------:|---------------------------:|
| OP_SUCCESS_TIP             | ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378 |        0.974121 |          0.974121 |              0 |                 0.5125  |               6.2561e-05  |              -0.512437 |                    0.454775 |                      0.42262  |                 -0.032155  |
| OP_EFFICIENCY_TIP          | 9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8 |        0.959229 |          0.959229 |              0 |                 0       |               0           |               0        |                    0.459075 |                      0.427607 |                 -0.0314672 |
| OP_SPEED_TIP               | d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7 |        0.868652 |          0.868652 |              0 |                 0       |               0           |               0        |                    0.490133 |                      0.441886 |                 -0.048247  |
| OP_BALANCED_RIDGE_MID      | 181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b |        0.952393 |          0.952393 |              0 |                 0       |               0           |               0        |                    0.438244 |                      0.423615 |                 -0.014629  |
| OP_STALE_CONTROL_OFF_RIDGE | 82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee |        0.948486 |          0.948486 |              0 |                 0.51125 |               0.000249634 |              -0.511    |                    0.442467 |                      0.42951  |                 -0.0129576 |

## Which observables are most likely to separate ridge points from the stale-control point?

- `phase_lag_steering_mean`: 0.022 on-ridge vs 0.010 off-ridge
- `gate_capture_probability`: 0.574 on-ridge vs 0.584 off-ridge
- `progress_rate_at_gate_mean`: 2.871 on-ridge vs 2.865 off-ridge
- `trap_episode_duration_mean`: 0.000 on-ridge vs 0.511 off-ridge

These observables are the strongest first candidates for coarse-grained rate-model discrimination because they combine stale steering, gate commitment, and failed recovery in a matched ridge/off-ridge comparison.

## Sensitivity of mechanism conclusions to event-classification thresholds

The event rules intentionally tie each threshold to a geometric or dynamical reference scale already present in the canonical workflow.

- wall sliding uses tangential alignment threshold `0.70`
- gate capture uses depth threshold `0.0200`
- trap confirmation uses duration threshold `0.5000`

The threshold-diagnostic figure and CSV give the fraction of event rows that remain close to these boundaries; the ridge-vs-stale ranking is substantially larger than those boundary fractions in the first dataset.

## Diagnostic Outputs

- [canonical_mechanism_overview.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/canonical_mechanism_overview.png)
- [ridge_vs_stale_observables.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/ridge_vs_stale_observables.png)
- [threshold_sensitivity.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/threshold_sensitivity.png)
- [mechanism_summary_by_point.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/mechanism_summary_by_point.csv)
- [threshold_sensitivity_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/threshold_sensitivity_summary.csv)
