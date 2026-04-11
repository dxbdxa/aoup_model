# Reference Scales Method

## Scope

This note documents the production reference-scale extraction used to populate:

- `outputs/summaries/reference_scales/reference_scales.json`
- `outputs/summaries/reference_scales/summary.csv`
- `outputs/summaries/reference_scales/summary.parquet`
- `outputs/summaries/reference_scales/baseline_transition_stats.csv`
- `outputs/summaries/reference_scales/baseline_transition_stats.parquet`
- per-config `result.json`
- per-config `raw_summary.csv`

No legacy physics, geometry, stepping, or RNG logic was modified for this run.

## Baseline Configuration

The requested baseline is:

- no memory
- no feedback
- `U = 0`

Under the current schema semantics, this is represented as:

- `model_variant = "no_memory"`
- `kf = 0.0`
- `U = 0.0`
- `flow_condition = "zero_flow"`

This keeps ablation branch identity and flow condition semantics separate while preserving the intended numerical control state.

## Estimator Definitions

### `tau_g`

`tau_g` is taken from the legacy summary field `MFPT_success_only`.

Operationally:

- run all trajectories up to `Tmax`
- identify successful exit trajectories
- compute the mean first-passage time over successful exits only

In the normalized workflow outputs:

- `tau_g = result.mfpt_mean`

### `l_g`

`l_g` is defined as:

```text
l_g = v0 * tau_g
```

with `v0` fixed by the reference configuration.

## Filtering And Exclusion Rules

- All launched trajectories are retained in the trajectory-level output tables.
- No trajectories are manually dropped.
- Trajectories that do not reach the exit before `Tmax` are treated as non-success trajectories.
- Non-success trajectories contribute to:
  - `n_traj`
  - `n_success`
  - `Psucc`
  - trajectory-level transition statistics
- Non-success trajectories are excluded from `tau_g` because `tau_g` is defined from `MFPT_success_only`.
- `l_g` inherits the same success-only filtering because it is a direct scaling of `tau_g`.

## Confidence Interval Method

### Success probability

The legacy code reports a Wilson interval for `Psucc`:

- `Psucc_ci_low`
- `Psucc_ci_high`

### `tau_g`

The legacy code reports a bootstrap confidence interval for `MFPT_success_only`:

- `MFPT_ci_low`
- `MFPT_ci_high`

For the production run, the bootstrap resample count was increased to `2000` to stabilize the interval estimate while keeping the underlying numerical model unchanged.

### `l_g`

Because `l_g = v0 * tau_g` and `v0` is fixed for the run, the `l_g` interval is obtained by scaling the `tau_g` interval by `v0`:

```text
l_g_ci_low = v0 * tau_g_ci_low
l_g_ci_high = v0 * tau_g_ci_high
```

No additional approximation is introduced beyond the legacy bootstrap interval for `tau_g`.

## Production Run Settings

- `n_traj = 1024`
- `bootstrap_resamples = 2000`
- `Tmax = 20.0`
- `dt = 0.0025`
- `grid_n = 257`
- `n_shell = 1`
- `seed = 20260411`

## Output Traceability

The state-point summary row traces to:

- per-config normalized output:
  - `outputs/runs/reference_scales/maze_v1/adfd0022969defd877e738e28cb81df7decdbd5c6de76d98151b2843a010fadc/result.json`
- per-config raw summary snapshot:
  - `outputs/runs/reference_scales/maze_v1/adfd0022969defd877e738e28cb81df7decdbd5c6de76d98151b2843a010fadc/raw_summary.csv`

The phase-level outputs are:

- `outputs/summaries/reference_scales/summary.csv`
- `outputs/summaries/reference_scales/summary.parquet`
- `outputs/summaries/reference_scales/baseline_transition_stats.csv`
- `outputs/summaries/reference_scales/baseline_transition_stats.parquet`
- `outputs/summaries/reference_scales/reference_scales.json`
