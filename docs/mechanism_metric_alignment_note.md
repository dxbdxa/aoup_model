# Mechanism Metric Alignment Note

## Metric Definitions

- `phase_lag_navigation_mean`: circular mean of `motion_angle - navigation_angle`, wrapped to `(-pi, pi]`; positive values mean the velocity direction is rotated counterclockwise relative to the local navigation field.
- `phase_lag_steering_mean`: circular mean of `motion_angle - steering_angle`, where `steering_angle` is the delayed controller target `theta_star` when the delayed navigation gradient is resolved, and falls back to the local navigation angle otherwise.
- `alignment_at_gate_mean`: mean of `u . n_gate` on gate-local rows; the doorway normal points inward through the shell doorway, so positive values indicate doorway-forward motion and values near `1` indicate strong forward alignment.
- `alignment_on_wall_mean`: mean of `|u . t_wall|` on wall-sliding rows; it is an unsigned tangentiality measure, so it quantifies how strongly the motion follows the wall but does not preserve clockwise/counterclockwise direction.

## Trap Alignment

- Legacy/source `trap_time_mean` is a mean over confirmed trap episodes, not a mean over all trajectories.
- `trajectory_level.parquet` already stores source-compatible total trap burden via `trap_time_total` and `n_trap_events`; use `sum(trap_time_total) / sum(n_trap_events)` when comparing to the canonical source trap metric.
- `event_level.parquet` originally stored trap-row `duration` only from the confirmation step onward. The updated parquet now adds onset-aligned fields:
  - `trap_confirmation_backshift = 0.4975`
  - `t_start_aligned`
  - `duration_aligned`
- Use `duration_aligned` for any event-level trap aggregation intended to match legacy/source trap durations.

## Conditioning Compatibility

- `gate_capture_probability` is computed as `capture_given_approach` on the current gate-local proxy state definitions.
- `return_to_wall_after_capture_rate` is computed on the set of `gate_capture` rows only.
- These conditioning sets are internally compatible with one another, but they are not yet equivalent to a clean doorway Markov chain because `gate_capture` behaves like a gate-mouth residence proxy while `gate_crossing` is a much stricter sign-change event.
- For immediate interpretive use, treat `gate_capture_probability` and `return_to_wall_after_capture_rate` as proxy-conditioned observables rather than final gate-transition probabilities.

## Changelog

- Updated `event_level.parquet` to add `t_start_aligned`, `duration_aligned`, and `trap_confirmation_backshift` for source-compatible trap aggregation.
