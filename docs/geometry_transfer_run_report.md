# Geometry Transfer Run Report

## Scope

This report summarizes the first geometry-transfer validation for the pre-commit backbone.

- family spec: [geometry_family_spec.md](file:///home/zhuguolong/aoup_model/docs/geometry_family_spec.md)
- transfer plan: [geometry_transfer_plan.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_plan.md)
- summary directory: [geometry_transfer](file:///home/zhuguolong/aoup_model/outputs/summaries/geometry_transfer)

## Reference Extraction

| geometry_family               | geometry_label        |    ell_g |    tau_g |   baseline_wall_fraction |   baseline_approach_events_per_traj |   baseline_residence_events_per_traj |   baseline_commit_events_per_traj |   baseline_p_reach_residence |   baseline_p_reach_commit |   baseline_return_to_wall_after_precommit |
|:------------------------------|:----------------------|---------:|---------:|-------------------------:|------------------------------------:|-------------------------------------:|----------------------------------:|-----------------------------:|--------------------------:|------------------------------------------:|
| GF0_REF_NESTED_MAZE           | GF0 Reference Nested  |  3.66863 |  7.33726 |                 0.429964 |                             20.7948 |                             20.897   |                          11.2331  |                     0.979632 |                  0.973772 |                                  0.148806 |
| GF1_SINGLE_BOTTLENECK_CHANNEL | GF1 Single Bottleneck | 10       | 20       |                 0.661557 |                             10.0508 |                              8.82812 |                           4.77734 |                     0.652344 |                  0.585938 |                                  0.15177  |
| GF2_PORE_ARRAY_STRIP          | GF2 Pore Array        | 10       | 20       |                 0.76531  |                             22.7148 |                             19.2461  |                          10.0938  |                     0.773438 |                  0.675781 |                                  0.159621 |

The non-reference families reach `tau_g = Tmax` in this first pass, so `tau_g` and `ell_g` act here as conservative coarse renormalization scales rather than finely resolved full-exit scales. The verdicts below are therefore based primarily on pre-commit observables, not on crossing completion.

## Canonical Transfer Summary

| geometry_family               | geometry_label        | canonical_label            |   first_gate_commit_delay |   wall_dwell_before_first_commit |   p_reach_commit |   commit_given_residence |   residence_given_approach |   return_to_wall_after_precommit_rate |   trap_burden_mean |   n_traj |
|:------------------------------|:----------------------|:---------------------------|--------------------------:|---------------------------------:|-----------------:|-------------------------:|---------------------------:|--------------------------------------:|-------------------:|---------:|
| GF0_REF_NESTED_MAZE           | GF0 Reference Nested  | OP_SPEED_TIP               |                   1.375   |                         0.40057  |         0.976318 |                 0.533828 |                   0.233866 |                              0.150494 |        0           |     8192 |
| GF0_REF_NESTED_MAZE           | GF0 Reference Nested  | OP_EFFICIENCY_TIP          |                   1.94096 |                         0.602276 |         0.966797 |                 0.531756 |                   0.217385 |                              0.14952  |        0           |     4096 |
| GF0_REF_NESTED_MAZE           | GF0 Reference Nested  | OP_BALANCED_RIDGE_MID      |                   1.66767 |                         0.502555 |         0.971924 |                 0.533008 |                   0.225603 |                              0.14723  |        0           |     4096 |
| GF0_REF_NESTED_MAZE           | GF0 Reference Nested  | OP_SUCCESS_TIP             |                   2.83263 |                         0.869471 |         0.978882 |                 0.535909 |                   0.206493 |                              0.148046 |        6.2561e-05  |     8192 |
| GF0_REF_NESTED_MAZE           | GF0 Reference Nested  | OP_STALE_CONTROL_OFF_RIDGE |                   1.73561 |                         0.525013 |         0.967285 |                 0.534282 |                   0.226994 |                              0.148741 |        0.000249634 |     4096 |
| GF1_SINGLE_BOTTLENECK_CHANNEL | GF1 Single Bottleneck | OP_BALANCED_RIDGE_MID      |                   2.85842 |                         0.742202 |         1        |                 0.549079 |                   0.221235 |                              0.144007 |        0           |      512 |
| GF1_SINGLE_BOTTLENECK_CHANNEL | GF1 Single Bottleneck | OP_EFFICIENCY_TIP          |                   3.41306 |                         0.896277 |         0.994141 |                 0.5514   |                   0.209984 |                              0.143895 |        0           |      512 |
| GF1_SINGLE_BOTTLENECK_CHANNEL | GF1 Single Bottleneck | OP_SPEED_TIP               |                   2.33665 |                         0.579331 |         1        |                 0.538753 |                   0.235638 |                              0.153794 |        0           |      512 |
| GF1_SINGLE_BOTTLENECK_CHANNEL | GF1 Single Bottleneck | OP_STALE_CONTROL_OFF_RIDGE |                   2.99636 |                         0.773319 |         0.996094 |                 0.561729 |                   0.223817 |                              0.145971 |        0           |      512 |
| GF1_SINGLE_BOTTLENECK_CHANNEL | GF1 Single Bottleneck | OP_SUCCESS_TIP             |                   3.89518 |                         0.940273 |         1        |                 0.545588 |                   0.198747 |                              0.146632 |        0           |      512 |
| GF2_PORE_ARRAY_STRIP          | GF2 Pore Array        | OP_BALANCED_RIDGE_MID      |                   2.6434  |                         0.911235 |         1        |                 0.519482 |                   0.217474 |                              0.157845 |        0.00215332  |      512 |
| GF2_PORE_ARRAY_STRIP          | GF2 Pore Array        | OP_EFFICIENCY_TIP          |                   2.94354 |                         1.02515  |         1        |                 0.522095 |                   0.212131 |                              0.153404 |        0           |      512 |
| GF2_PORE_ARRAY_STRIP          | GF2 Pore Array        | OP_SPEED_TIP               |                   2.05968 |                         0.688335 |         1        |                 0.526134 |                   0.232745 |                              0.155183 |        0.00230469  |      512 |
| GF2_PORE_ARRAY_STRIP          | GF2 Pore Array        | OP_STALE_CONTROL_OFF_RIDGE |                   2.70488 |                         0.934727 |         1        |                 0.516228 |                   0.228593 |                              0.160826 |        0           |      512 |
| GF2_PORE_ARRAY_STRIP          | GF2 Pore Array        | OP_SUCCESS_TIP             |                   3.53521 |                         1.19497  |         0.996094 |                 0.527561 |                   0.197058 |                              0.159734 |        0           |      512 |

## Which aspects transferred, and which renormalized?

- `GF1_SINGLE_BOTTLENECK_CHANNEL`: `same_principle`. Speed-favored earliest commit, success-favored strongest commit reach, and stale degradation through slower wall-mediated recycling all survive.
- `GF2_PORE_ARRAY_STRIP`: `same_principle`. Speed-favored earliest commit, success-favored strongest commit reach, and stale degradation through slower wall-mediated recycling all survive.

Transferred first:

- pre-commit timing structure
- wall dwell before commitment
- commitment reach as `p_reach_commit`
- precommit recycling through `commit_given_residence` and `return_to_wall_after_precommit_rate`

Renormalized where needed:

- absolute `tau_g`
- absolute `ell_g`
- the precise magnitude of approach and commitment rates in non-reference geometries

No local renormalization slice was needed: the frozen canonical set already preserved the pre-commit ordering signals in the tested families.

## Did any geometry show genuine breakdown of the pre-commit principle?

Only geometries classified as `breakdown` should be taken as genuine failures. In this first stage, that verdict is reserved for cases where the pre-commit backbone itself ceases to organize the comparison, not for simple rate rescaling.

## Figures

- [reference_scale_transfer.png](file:///home/zhuguolong/aoup_model/outputs/figures/geometry_transfer/reference_scale_transfer.png)
- [precommit_transfer_comparison.png](file:///home/zhuguolong/aoup_model/outputs/figures/geometry_transfer/precommit_transfer_comparison.png)
- [balanced_vs_stale_transfer.png](file:///home/zhuguolong/aoup_model/outputs/figures/geometry_transfer/balanced_vs_stale_transfer.png)
