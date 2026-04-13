# Intervention Dataset Run Report

## Scope

This report records the build of the intervention dataset for local mechanism-causality tests around the productive ridge.

Key outputs:

- [intervention_dataset](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset)
- [intervention_dataset](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset)
- [replay_validation.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/replay_validation.csv)

## Dataset Size

| quantity          |    value |
|:------------------|---------:|
| unique points     |       14 |
| slice memberships |       16 |
| trajectory rows   |    57344 |
| event rows        | 32228587 |
| gate rows         |       14 |

## Replay Validation

The refined replay preserves the upstream task metrics closely enough for local intervention ranking.

| metric                   |       value |
|:-------------------------|------------:|
| max_abs_delta_Psucc      | 0           |
| max_abs_delta_MFPT       | 0           |
| max_abs_delta_Sigma_drag | 1.13687e-13 |

## Slice Manifests

### delay_slice

| point_label             | canonical_match            |   Pi_m |   Pi_f |   Pi_U |   axis_value |   axis_delta_from_baseline | is_baseline   |
|:------------------------|:---------------------------|-------:|-------:|-------:|-------------:|---------------------------:|:--------------|
| IP_PM0p15_PF0p018_PU0p2 | nan                        |   0.15 |  0.018 |    0.2 |        0.018 |                     -0.002 | False         |
| IP_PM0p15_PF0p02_PU0p2  | OP_BALANCED_RIDGE_MID      |   0.15 |  0.02  |    0.2 |        0.02  |                      0     | True          |
| IP_PM0p15_PF0p022_PU0p2 | nan                        |   0.15 |  0.022 |    0.2 |        0.022 |                      0.002 | False         |
| IP_PM0p15_PF0p025_PU0p2 | OP_STALE_CONTROL_OFF_RIDGE |   0.15 |  0.025 |    0.2 |        0.025 |                      0.005 | False         |
### memory_slice

| point_label            | canonical_match       |   Pi_m |   Pi_f |   Pi_U |   axis_value |   axis_delta_from_baseline | is_baseline   |
|:-----------------------|:----------------------|-------:|-------:|-------:|-------------:|---------------------------:|:--------------|
| IP_PM0p08_PF0p02_PU0p2 | nan                   |   0.08 |   0.02 |    0.2 |         0.08 |                      -0.07 | False         |
| IP_PM0p1_PF0p02_PU0p2  | nan                   |   0.1  |   0.02 |    0.2 |         0.1  |                      -0.05 | False         |
| IP_PM0p12_PF0p02_PU0p2 | nan                   |   0.12 |   0.02 |    0.2 |         0.12 |                      -0.03 | False         |
| IP_PM0p15_PF0p02_PU0p2 | OP_BALANCED_RIDGE_MID |   0.15 |   0.02 |    0.2 |         0.15 |                       0    | True          |
| IP_PM0p18_PF0p02_PU0p2 | nan                   |   0.18 |   0.02 |    0.2 |         0.18 |                       0.03 | False         |
| IP_PM0p2_PF0p02_PU0p2  | nan                   |   0.2  |   0.02 |    0.2 |         0.2  |                       0.05 | False         |
| IP_PM0p22_PF0p02_PU0p2 | nan                   |   0.22 |   0.02 |    0.2 |         0.22 |                       0.07 | False         |
### flow_slice

| point_label             | canonical_match       |   Pi_m |   Pi_f |   Pi_U |   axis_value |   axis_delta_from_baseline | is_baseline   |
|:------------------------|:----------------------|-------:|-------:|-------:|-------------:|---------------------------:|:--------------|
| IP_PM0p15_PF0p02_PU0p1  | nan                   |   0.15 |   0.02 |   0.1  |         0.1  |                      -0.1  | False         |
| IP_PM0p15_PF0p02_PU0p15 | nan                   |   0.15 |   0.02 |   0.15 |         0.15 |                      -0.05 | False         |
| IP_PM0p15_PF0p02_PU0p2  | OP_BALANCED_RIDGE_MID |   0.15 |   0.02 |   0.2  |         0.2  |                       0    | True          |
| IP_PM0p15_PF0p02_PU0p25 | nan                   |   0.15 |   0.02 |   0.25 |         0.25 |                       0.05 | False         |
| IP_PM0p15_PF0p02_PU0p3  | nan                   |   0.15 |   0.02 |   0.3  |         0.3  |                       0.1  | False         |

## Leading Mechanism Signals By Slice

### delay_slice

| metric_name                    |   early_indicator_score |   first_step_rel_range |   monotonicity_score | direction_label   |
|:-------------------------------|------------------------:|-----------------------:|---------------------:|:------------------|
| wall_dwell_before_first_commit |              0.0243203  |               0.796206 |             0.466667 | increasing        |
| first_gate_commit_delay        |              0.0203579  |               0.752869 |             0.466667 | increasing        |
| residence_given_approach       |              0.00438086 |               0.375506 |             0.566667 | increasing        |
### memory_slice

| metric_name                    |   early_indicator_score |   first_step_rel_range |   monotonicity_score | direction_label   |
|:-------------------------------|------------------------:|-----------------------:|---------------------:|:------------------|
| trap_burden_mean               |              0.105671   |               0.46     |             0.229719 | mixed             |
| wall_dwell_before_first_commit |              0.00583442 |               0.394189 |             0.196429 | mixed             |
| first_gate_commit_delay        |              0.00521332 |               0.398668 |             0.196429 | mixed             |
### flow_slice

| metric_name                    |   early_indicator_score |   first_step_rel_range |   monotonicity_score | direction_label   |
|:-------------------------------|------------------------:|-----------------------:|---------------------:|:------------------|
| wall_dwell_before_first_commit |               0.170493  |               0.237527 |             1        | decreasing        |
| first_gate_commit_delay        |               0.154759  |               0.23341  |             1        | decreasing        |
| trap_burden_mean               |               0.0883883 |               0.5      |             0.176777 | mixed             |

## Generated Figures

- [delay_slice_metrics.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/delay_slice_metrics.png)
- [memory_slice_metrics.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/memory_slice_metrics.png)
- [flow_slice_metrics.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/flow_slice_metrics.png)
- [intervention_ordering_heatmap.png](file:///home/zhuguolong/aoup_model/outputs/figures/intervention_dataset/intervention_ordering_heatmap.png)

## Generated Tables

- [point_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/point_summary.csv)
- [slice_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/slice_summary.csv)
- [metric_ordering.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/metric_ordering.csv)
- [mechanism_ordering_aggregate.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/mechanism_ordering_aggregate.csv)
