# Mechanism Refined Run Report

## Scope

This report summarizes the refined gate-local mechanism replay on the frozen canonical operating points.

- canonical manifest: [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- refinement note: [gate_state_refinement_note.md](file:///home/zhuguolong/aoup_model/docs/gate_state_refinement_note.md)
- refined trajectory parquet: [trajectory_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined/trajectory_level.parquet)
- refined event parquet: [event_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined/event_level.parquet)
- refined gate-conditioned parquet: [gate_conditioned.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined/gate_conditioned.parquet)

## Canonical Replay Set

- `OP_SUCCESS_TIP`: state_point_id `ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378`, `(Pi_m, Pi_f, Pi_U)=(0.080, 0.025, 0.100)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378/result.json)
- `OP_EFFICIENCY_TIP`: state_point_id `9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8`, `(Pi_m, Pi_f, Pi_U)=(0.180, 0.018, 0.150)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8/result.json)
- `OP_SPEED_TIP`: state_point_id `d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7`, `(Pi_m, Pi_f, Pi_U)=(0.100, 0.018, 0.300)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7/result.json)
- `OP_BALANCED_RIDGE_MID`: state_point_id `181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b`, `(Pi_m, Pi_f, Pi_U)=(0.150, 0.020, 0.200)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b/result.json)
- `OP_STALE_CONTROL_OFF_RIDGE`: state_point_id `82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee`, `(Pi_m, Pi_f, Pi_U)=(0.150, 0.025, 0.200)`, source [result.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee/result.json)

## Refined Summary

| canonical_label            | state_point_id                                                   |   Pi_m |   Pi_f |   Pi_U |   n_traj |   success_probability |   first_gate_residence_delay |   first_gate_commit_delay |   wall_dwell_before_first_residence |   wall_dwell_before_first_commit |   trap_burden_mean |   trap_event_count_mean |   phase_lag_steering_mean |   signed_wall_tangent_mean |   signed_gate_approach_angle_mean |   local_recirculation_polarity_mean |   wall_circulation_signed_mean |   residence_given_approach |   commit_given_residence |   crossing_given_commit |   return_to_wall_after_precommit_rate |   return_to_wall_after_commit_rate |   steering_lag_at_commit_mean |   local_recirculation_at_gate_mean |
|:---------------------------|:-----------------------------------------------------------------|-------:|-------:|-------:|---------:|----------------------:|-----------------------------:|--------------------------:|------------------------------------:|---------------------------------:|-------------------:|------------------------:|--------------------------:|---------------------------:|----------------------------------:|------------------------------------:|-------------------------------:|---------------------------:|-------------------------:|------------------------:|--------------------------------------:|-----------------------------------:|------------------------------:|-----------------------------------:|
| OP_SPEED_TIP               | d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7 |   0.1  |  0.018 |   0.3  |     8192 |              0.868652 |                      1.06884 |                   1.375   |                            0.323856 |                         0.40057  |        0           |             0           |               -0.00640638 |               -0.000374289 |                       0.000173307 |                        -0.00043715  |                   -0.00013191  |                   0.233866 |                 0.533828 |             6.8377e-05  |                              0.150494 |                         0.00542913 |                   0.00630784  |                       -0.00208045  |
| OP_EFFICIENCY_TIP          | 9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8 |   0.18 |  0.018 |   0.15 |     4096 |              0.959229 |                      1.58325 |                   1.94096 |                            0.524654 |                         0.602276 |        0           |             0           |               -0.00553169 |               -0.000118119 |                      -0.00110508  |                        -0.000458623 |                   -0.000407591 |                   0.217385 |                 0.531756 |             7.10749e-05 |                              0.14952  |                         0.00516478 |                  -0.000778482 |                        0.000184763 |
| OP_BALANCED_RIDGE_MID      | 181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b |   0.15 |  0.02  |   0.2  |     4096 |              0.952393 |                      1.33403 |                   1.66767 |                            0.42652  |                         0.502555 |        0           |             0           |                0.0216213  |                0.000631799 |                      -0.0019973   |                        -0.00169858  |                   -0.000359866 |                   0.225603 |                 0.533008 |             7.5622e-05  |                              0.14723  |                         0.00572206 |                   0.00605502  |                        0.0012304   |
| OP_SUCCESS_TIP             | ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378 |   0.08 |  0.025 |   0.1  |     8192 |              0.974121 |                      2.28098 |                   2.83263 |                            0.748973 |                         0.869471 |        6.2561e-05  |             0.00012207  |               -0.00759122 |                0.000280739 |                      -0.000336633 |                         0.000263679 |                    0.000889484 |                   0.206493 |                 0.535909 |             5.50648e-05 |                              0.148046 |                         0.00423212 |                   0.00334093  |                       -0.000925289 |
| OP_STALE_CONTROL_OFF_RIDGE | 82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee |   0.15 |  0.025 |   0.2  |     4096 |              0.948486 |                      1.39158 |                   1.73561 |                            0.44611  |                         0.525013 |        0.000249634 |             0.000488281 |                0.0100793  |                0.000797086 |                      -0.0024083   |                         0.000879143 |                    0.000471636 |                   0.226994 |                 0.534282 |             7.50957e-05 |                              0.148741 |                         0.00503142 |                   0.00210349  |                       -0.00186998  |

## Replay Validation

| canonical_label            | state_point_id                                                   |   source_p_succ |   replayed_p_succ |   delta_p_succ |   source_wall_fraction_mean |   replayed_wall_fraction_mean |   delta_wall_fraction_mean |   source_trap_time_mean |   replayed_episode_conditioned_trap_mean |
|:---------------------------|:-----------------------------------------------------------------|----------------:|------------------:|---------------:|----------------------------:|------------------------------:|---------------------------:|------------------------:|-----------------------------------------:|
| OP_SUCCESS_TIP             | ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378 |        0.974121 |          0.974121 |              0 |                    0.454775 |                      0.42262  |                 -0.032155  |                 0.5125  |                                  0.5125  |
| OP_EFFICIENCY_TIP          | 9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8 |        0.959229 |          0.959229 |              0 |                    0.459075 |                      0.427607 |                 -0.0314672 |                 0       |                                  0       |
| OP_SPEED_TIP               | d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7 |        0.868652 |          0.868652 |              0 |                    0.490133 |                      0.441886 |                 -0.048247  |                 0       |                                  0       |
| OP_BALANCED_RIDGE_MID      | 181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b |        0.952393 |          0.952393 |              0 |                    0.438244 |                      0.423615 |                 -0.014629  |                 0       |                                  0       |
| OP_STALE_CONTROL_OFF_RIDGE | 82a529b97c751b82c2e76d3832a6a14960f011b45ad6d37b8a91bcd9ec22c3ee |        0.948486 |          0.948486 |              0 |                    0.442467 |                      0.42951  |                 -0.0129576 |                 0.51125 |                                  0.51125 |

## Old Versus Refined Gate Definition

| canonical_label            |   old_gate_capture_delay |   first_gate_commit_delay |   old_wall_dwell_before_capture |   wall_dwell_before_first_commit |   old_gate_capture_probability |   commit_given_residence |   old_return_to_wall_after_capture_rate |   return_to_wall_after_commit_rate |
|:---------------------------|-------------------------:|--------------------------:|--------------------------------:|---------------------------------:|-------------------------------:|-------------------------:|----------------------------------------:|-----------------------------------:|
| OP_BALANCED_RIDGE_MID      |                  1.57651 |                   1.66767 |                        0.487486 |                         0.502555 |                       0.573727 |                 0.533008 |                                0.366703 |                         0.00572206 |
| OP_STALE_CONTROL_OFF_RIDGE |                  1.64619 |                   1.73561 |                        0.509537 |                         0.525013 |                       0.583724 |                 0.534282 |                                0.363914 |                         0.00503142 |

## Did the refined gate-state definition make stale-control more mechanistically distinguishable?

- First commit delay increases from 1.6677 on the balanced ridge point to 1.7356 on the stale-control point.
- Wall dwell before first commit increases from 0.5026 to 0.5250.
- Post-commit return-to-wall changes from 0.0057 to 0.0050.
- Trap burden changes from 0.000000 to 0.000250.
- Steering lag at commit changes from 0.0061 to 0.0021.

Verdict: only modestly. The refined matched comparison is more interpretable than the original proxy capture state, but the strongest improvements are in timing observables rather than in decisive gate-local transition separation.

## Is the refined state graph now clean enough for a first rate model?

- `commit_given_residence` at the balanced ridge point is 0.5330; at the stale-control point it is 0.5343.
- `crossing_given_commit` at the balanced ridge point is 0.0001; at the stale-control point it is 0.0001.
- The maximum `crossing_given_commit` across the refined canonical set is only 0.00008.
- Verdict: not yet. The refined graph is cleaner and the conditioning sets are now proper transition fractions, but gate crossing from the refined commit state remains too sparse for a reliable first rate fit.
- Use the refined dataset for diagnostic mechanism comparison and state-graph design, not yet for a committed coarse-grained gate-theory fit.

## Diagnostic Outputs

- [refined_gate_state_summary.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_gate_state_summary.png)
- [balanced_vs_stale_refined.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/balanced_vs_stale_refined.png)
- [old_vs_refined_balanced_stale.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/old_vs_refined_balanced_stale.png)
- [refined_summary_by_point.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_summary_by_point.csv)
- [old_vs_refined_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/old_vs_refined_summary.csv)
