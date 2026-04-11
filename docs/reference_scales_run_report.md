# Reference Scales Run Report

## Run Summary

Production reference-scale extraction completed successfully using the validated workflow contract and legacy adapter path.

Requested baseline:

- no memory
- no feedback
- `U = 0`

Persisted semantic encoding:

- `model_variant = "no_memory"`
- `kf = 0.0`
- `flow_condition = "zero_flow"`

Run configuration highlights:

- `n_traj = 1024`
- `bootstrap_resamples = 2000`
- `Tmax = 20.0`
- `dt = 0.0025`
- `grid_n = 257`
- `seed = 20260411`

## Primary Estimates

- `tau_g = 7.337257462686567`
- `tau_g` 95% bootstrap CI: `[6.668584930684339, 8.040714394403594]`
- `l_g = 3.6686287313432837`
- `l_g` propagated CI: `[3.3342924653421694, 4.020357197201797]`
- `tau_p = 1.0`
- `Psucc = 0.26171875`
- `Psucc` Wilson CI: `[0.23572172364306293, 0.289496882969758]`
- `n_success = 268 / 1024`

Secondary summary values:

- `MFPT_median = 5.82375`
- `FPT_q90 = 16.63125`
- `Sigma_drag_mean = 2416.1389998574487`
- `eta_sigma_mean = 5.416053257189286e-06`
- `wall_fraction_mean = 0.686416406981348`

## Stability Note

The production run used `1024` trajectories and `2000` bootstrap resamples.

Observed interval widths:

- `tau_g` CI width: `1.372129463719255`
- `tau_g` relative half-width: approximately `9.35%`
- `Psucc` CI width: `0.05377515932669507`

This is sufficient for a stable production reference-scale baseline at the current workflow stage.

## Required Output Artifacts

Confirmed output files:

- `outputs/summaries/reference_scales/reference_scales.json`
- `outputs/summaries/reference_scales/summary.csv`
- `outputs/summaries/reference_scales/summary.parquet`
- `outputs/summaries/reference_scales/baseline_transition_stats.csv`
- `outputs/summaries/reference_scales/baseline_transition_stats.parquet`
- `outputs/runs/reference_scales/maze_v1/adfd0022969defd877e738e28cb81df7decdbd5c6de76d98151b2843a010fadc/result.json`
- `outputs/runs/reference_scales/maze_v1/adfd0022969defd877e738e28cb81df7decdbd5c6de76d98151b2843a010fadc/raw_summary.csv`

Primary machine-readable reference file:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)

## Provenance Check

The resulting artifacts are internally consistent:

- `reference_scales.json` points to the exact `result.json`
- `result.json` points to the exact `raw_summary.csv`
- `summary.csv` uses the same `config_hash`
- `metadata.json` records the phase-level provenance and compatibility shims

Config hash:

- `adfd0022969defd877e738e28cb81df7decdbd5c6de76d98151b2843a010fadc`

## Notes

- The branch/flow semantic split is preserved in the persisted outputs:
  - branch identity: `no_memory`
  - flow semantics: `zero_flow`
- The requested no-feedback condition is carried numerically by `kf = 0.0` rather than overloading `model_variant`.
- No workflow contracts or legacy numerical logic were changed during this run.
