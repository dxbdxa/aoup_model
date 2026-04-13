# Precommit Prediction Validation Report

## Scope

This report validates the explicit pre-commit reduced-law predictions against the local intervention dataset. The validation target is the pre-commit backbone only; no post-commit completion claim is made here.

- point summary: [point_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/point_summary.csv)
- slice summary: [slice_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/slice_summary.csv)
- metric ordering: [metric_ordering.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/metric_ordering.csv)
- prediction figure: [prediction_vs_validation.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/prediction_vs_validation.png)
- scope map: [reduced_law_scope_map.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/reduced_law_scope_map.png)

## Validation Strategy

Each prediction is scored by a small set of explicit slice-level checks. The checks use only local intervention responses already present in the intervention dataset:

- timing-budget extrema or monotonicity when the law predicts timing-first behavior
- relative early-indicator scores when the law predicts one observable should move before another
- direction labels and monotonicity scores when the law predicts ordered control response
- punctate-onset tests when the law predicts a stale flag rather than a smooth coordinate

## Prediction Table

| prediction_id   | short_title                               | control_axis   |   validation_score | status    |   checks_passed |   checks_total | observed_evidence                                                                                                                                                                                                                                                                |
|:----------------|:------------------------------------------|:---------------|-------------------:|:----------|----------------:|---------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| P1              | Delay Acts First On Timing                | Pi_f           |                  1 | supported |               4 |              4 | delay midpoint gives the local timing minimum: commit delay `1.6677` vs slice range `1.6677` to `1.7675`; wall dwell `0.5026` vs range `0.5026` to `0.5367`; `commit_given_residence` score `0.0030` stays below the timing scores; trap burden turns on only at `Pi_f = 0.025`. |
| P2              | Flow Orders The Timing Budget             | Pi_U           |                  1 | supported |               4 |              4 | commit delay falls from `2.6353` to `1.3998`, wall dwell falls from `0.8281` to `0.4189`, `residence_given_approach` rises from `0.2119` to `0.2361`, and `commit_given_residence` stays near `0.533`.                                                                           |
| P3              | Memory Acts First On Arrival Organization | Pi_m           |                  1 | supported |               5 |              5 | memory-slice monotonicity is highest for `residence_given_approach` (`0.631`) vs commit delay `0.196`, wall dwell `0.196`, and `commit_given_residence` `0.393`; `residence_given_approach` rises from `0.2217` at low memory to `0.2328` before the edge roll-off.              |
| P4              | Commit Conversion Is A Late Correlate     | all            |                  1 | supported |               4 |              4 | `commit_given_residence` has the smallest mean early-indicator score (`0.0014`) and low mean monotonicity (`0.270`); it never appears as a leading slice responder.                                                                                                              |
| P5              | Trap Burden Is A Punctate Stale Flag      | stale edge     |                  1 | supported |               4 |              4 | trap burden is positive at only `1` delay-slice point, `4` memory-slice points, and `1` flow-slice points; memory and flow directions remain `mixed` and `mixed`.                                                                                                                |

## Early Indicators, Late Correlates, And Stale Flags

| metric_name                    | classification              |   mean_early_indicator_score |   mean_monotonicity_score | reason                                                                      |
|:-------------------------------|:----------------------------|-----------------------------:|--------------------------:|:----------------------------------------------------------------------------|
| wall_dwell_before_first_commit | early_indicator             |                   0.0668827  |                  0.554365 | Dominant pre-commit timing discriminator.                                   |
| first_gate_commit_delay        | early_indicator             |                   0.0601099  |                  0.554365 | Dominant pre-commit timing discriminator.                                   |
| residence_given_approach       | early_indicator             |                   0.0129009  |                  0.73254  | Cleaner secondary early signal, especially on memory and flow slices.       |
| commit_given_residence         | late_correlate              |                   0.00139989 |                  0.269841 | Cross-slice response stays small and comparatively flat.                    |
| trap_burden_mean               | weak_or_punctate_stale_flag |                   0.0646863  |                  0.431265 | Appears mainly at stale edges or intermittently, with mixed directionality. |

## Where The Reduced Law Already Works Well

| region_or_task                          | law_status        | reason                                                                                                                    |
|:----------------------------------------|:------------------|:--------------------------------------------------------------------------------------------------------------------------|
| delay slice near balanced midpoint      | works_well        | Timing observables respond first and trap burden stays deferred to the stale edge.                                        |
| flow ordering along the ridge           | works_well        | Timing contraction is monotone and `commit_given_residence` stays flat.                                                   |
| memory variation inside productive band | works_with_limits | `residence_given_approach` is cleaner than timing, but the slice is weaker and not globally monotone in every observable. |

Supported strongly now:

- delay and flow acting first on the pre-commit timing budget
- memory acting more cleanly on approach-to-residence organization than on commitment conversion
- `commit_given_residence` remaining subleading across the local interventions

Mixed but still useful:

- the memory slice is informative, but weaker and less globally one-directional than the flow slice
- trap burden is useful only as a stale-flag variable, not as a smooth control law

## Where The Reduced Law Is Expected To Fail

| region_or_task                                   | law_status       | reason                                                                                                  |
|:-------------------------------------------------|:-----------------|:--------------------------------------------------------------------------------------------------------|
| trap kinetics as a fitted rate law               | expected_failure | Trap counts remain too sparse; trap burden is only an occupancy-level stale flag.                       |
| post-commit completion and full crossing success | expected_failure | The reduced law stops at `gate_commit` and does not claim a crossing-completion model.                  |
| full efficiency ranking                          | expected_failure | Efficiency still mixes pre-commit organization with downstream transport costs outside the reduced law. |

Interpretation:

- the reduced law should not be judged on post-commit completion
- it should not be expected to close the full efficiency story
- it should not be promoted into a smooth trap-kinetics theory from the present sparse counts

## Practical Conclusion

5 of 5 explicit predictions are supported outright by the intervention dataset, and 0 remain mixed rather than contradicted. The current reduced law already works as a local pre-commit Results statement because it correctly identifies which controls hit timing first, which control hits arrival organization first, and which observables should be treated as late correlates or punctate stale flags.
