# Intervention Mechanism Ordering

## Scope

This note identifies which observables move first and most monotonically under the three local ridge interventions.

## Aggregate Mechanism Ordering

| metric_name                    |   mean_early_indicator_score |   max_early_indicator_score |   mean_monotonicity_score |   mean_first_step_rel_range |   top2_count |   top1_count |
|:-------------------------------|-----------------------------:|----------------------------:|--------------------------:|----------------------------:|-------------:|-------------:|
| wall_dwell_before_first_commit |                   0.0668827  |                  0.170493   |                  0.554365 |                    0.475974 |            3 |            2 |
| trap_burden_mean               |                   0.0646863  |                  0.105671   |                  0.431265 |                    0.32     |            1 |            1 |
| first_gate_commit_delay        |                   0.0601099  |                  0.154759   |                  0.554365 |                    0.461649 |            2 |            0 |
| residence_given_approach       |                   0.0129009  |                  0.0295297  |                  0.73254  |                    0.262315 |            0 |            0 |
| commit_given_residence         |                   0.00139989 |                  0.00302351 |                  0.269841 |                    0.350207 |            0 |            0 |

## Slice-Level Leaders

## delay_slice

| metric_name                    |   early_indicator_score |   first_step_rel_range |   monotonicity_score | direction_label   |
|:-------------------------------|------------------------:|-----------------------:|---------------------:|:------------------|
| wall_dwell_before_first_commit |              0.0243203  |               0.796206 |             0.466667 | increasing        |
| first_gate_commit_delay        |              0.0203579  |               0.752869 |             0.466667 | increasing        |
| residence_given_approach       |              0.00438086 |               0.375506 |             0.566667 | increasing        |
| commit_given_residence         |              0.00302351 |               0.5      |             0.366667 | mixed             |

Raising delay away from the ridge midpoint first lengthens the pre-commit clock: `first_gate_commit_delay` rises from `1.6677` at `Pi_f = 0.020` to `1.7675` at `Pi_f = 0.022`, and `wall_dwell_before_first_commit` rises from `0.5026` to `0.5367` over the same first step. `trap_burden_mean` stays zero until the highest-delay stale point, where it turns on at `0.000250`. So delay intervention shows timing first, trapping later.
## memory_slice

| metric_name                    |   early_indicator_score |   first_step_rel_range |   monotonicity_score | direction_label   |
|:-------------------------------|------------------------:|-----------------------:|---------------------:|:------------------|
| trap_burden_mean               |              0.105671   |               0.46     |             0.229719 | mixed             |
| wall_dwell_before_first_commit |              0.00583442 |               0.394189 |             0.196429 | mixed             |
| first_gate_commit_delay        |              0.00521332 |               0.398668 |             0.196429 | mixed             |
| residence_given_approach       |              0.00479223 |               0.136644 |             0.630952 | increasing        |

The memory slice is weaker and less one-directional in raw timing, but `residence_given_approach` is the cleanest smooth signal: it rises from `0.2217` at `Pi_m = 0.08` to `0.2328` at `Pi_m = 0.20` before easing slightly at the edge. `commit_given_residence` stays near `0.533` across the slice, while trap burden appears only intermittently rather than as a smooth monotone trend. So memory intervention is better read through approach-to-residence organization than through residence-to-commit conversion.
## flow_slice

| metric_name                    |   early_indicator_score |   first_step_rel_range |   monotonicity_score | direction_label   |
|:-------------------------------|------------------------:|-----------------------:|---------------------:|:------------------|
| wall_dwell_before_first_commit |               0.170493  |               0.237527 |             1        | decreasing        |
| first_gate_commit_delay        |               0.154759  |               0.23341  |             1        | decreasing        |
| trap_burden_mean               |               0.0883883 |               0.5      |             0.176777 | mixed             |
| residence_given_approach       |               0.0295297 |               0.274796 |             1        | increasing        |

The flow slice produces the clearest monotone contraction of the pre-commit search budget: `first_gate_commit_delay` falls from `2.6353` at `Pi_U = 0.10` to `1.3998` at `Pi_U = 0.30`, and `wall_dwell_before_first_commit` falls from `0.8281` to `0.4189`. `residence_given_approach` rises from `0.2119` to `0.2361`, but `commit_given_residence` remains nearly flat around `0.533`. So flow orders the ridge mainly by how quickly trajectories reach and prepare for commitment.

## Concise Conclusion

Across the three local ridge interventions, the strongest early indicators are the pre-commit timing variables `wall_dwell_before_first_commit` and `first_gate_commit_delay`. `residence_given_approach` is the cleaner secondary mechanism signal, especially on the memory and flow slices. `trap_burden_mean` behaves mostly as a late or punctate stale flag rather than a smooth leading coordinate, and `commit_given_residence` stays comparatively flat, making it a late correlate rather than an early indicator.
