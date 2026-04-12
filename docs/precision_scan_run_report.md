# Precision Scan Run Report

## Scope

This report records the targeted precision scan launched along the refined productive ridge.

Constraints followed:

- no global search expansion was performed
- the scan stayed inside the requested narrow ridge envelope
- the base grid used `n_traj = 2048` for all points
- the top `10` candidates were resampled at `n_traj = 4096`
- legacy physics was not changed

Primary inputs:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)
- [refinement_run_report.md](file:///home/zhuguolong/aoup_model/docs/refinement_run_report.md)
- [refinement_first_look.md](file:///home/zhuguolong/aoup_model/docs/refinement_first_look.md)

## Precision Design

Execution defaults:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 2048` for the base grid
- `n_traj = 4096` for the top-`10` resample

Precision envelope:

- `Pi_f in {0.02, 0.025, 0.03}`
- `Pi_m in {0.05, 0.08, 0.1, 0.12, 0.15, 0.18, 0.2, 0.25}`
- `Pi_U in {0.1, 0.15, 0.2, 0.25, 0.3}`

Design counts:

- base ridge grid: `120` points
- resample set: `10` points
- total executed state points: `130`
- completed shards: `17`
  - base grid shards: `15`
  - resample shards: `2`

## Produced Outputs

Phase summaries:

- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/precision_scan/summary.csv)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/precision_scan/summary.parquet)
- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/summaries/precision_scan/metadata.json)
- [shard_execution_report.json](file:///home/zhuguolong/aoup_model/outputs/summaries/precision_scan/shard_execution_report.json)

Figures and tables:

- [Psucc_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/Psucc_mean.png)
- [MFPT_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/MFPT_mean.png)
- [eta_sigma_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/eta_sigma_mean.png)
- [trap_time_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/trap_time_mean.png)
- [top_points_by_objective.csv](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/top_points_by_objective.csv)
- [resample_comparison.csv](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/resample_comparison.csv)
- [precision_front_analysis.json](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/precision_front_analysis.json)

Manifests:

- [task_manifest.json](file:///home/zhuguolong/aoup_model/outputs/runs/precision_scan/task_manifest.json)
- [top_candidate_resample_manifest.json](file:///home/zhuguolong/aoup_model/outputs/runs/precision_scan/top_candidate_resample_manifest.json)

## Execution Status

Final phase metadata:

- `status_completion = "completed"`
- `status_stage = "precision_scan_execute"`
- `status_reason = null`
- `n_state_points = 130`
- `n_executed_state_points = 130`
- `n_generated_only_state_points = 0`

Shard summary:

- completed shards: `17`
- failed shards: `0`
- retries used: `0`

Completed shards:

- base grid: `batch_000` through `batch_014`
- resample: `batch_100`, `batch_101`

## Output Integrity

Status: `PASS`

Observed:

- `130 / 130` completed rows were checked for executed artifacts
- missing `result.json` paths: `0`
- missing `raw_summary.csv` paths: `0`
- all requested precision figures exist
- the objective table exists
- the resample comparison table exists

## Front Comparison Summary

Best base-grid point by `Psucc_mean`:

- `Pi_m = 0.1`
- `Pi_f = 0.02`
- `Pi_U = 0.1`
- `Psucc_mean = 0.97900390625`

Best base-grid point by `eta_sigma_mean`:

- `Pi_m = 0.2`
- `Pi_f = 0.02`
- `Pi_U = 0.2`
- `eta_sigma_mean = 6.716089379588434e-05`

Best base-grid point by `MFPT_mean`:

- `Pi_m = 0.1`
- `Pi_f = 0.02`
- `Pi_U = 0.3`
- `MFPT_mean = 2.7478428650749582`

Top-`10` overlap counts:

- `Psucc_mean` vs `eta_sigma_mean`: `0`
- `Psucc_mean` vs `MFPT_mean`: `0`
- `eta_sigma_mean` vs `MFPT_mean`: `0`
- all three top-`10` sets: `0`

Interpretation:

- the three objectives do not collapse onto one compact optimum
- the precision scan resolves a structured front rather than a single locally flat winner

## Resample Note

The `4096`-trajectory resample confirms that the strongest ridge candidates remain in the same narrow parameter strip:

- `Pi_f = 0.02` to `0.025`
- `Pi_m = 0.1` to `0.18`
- `Pi_U = 0.15` to `0.2`

Example stable candidates:

- [resample_comparison.csv](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/resample_comparison.csv)

The resample does not indicate a front reversal large enough to invalidate the `2048`-trajectory ridge geometry.

## Hand-Off

The detailed first-look interpretation, including the ridge-vs-basin conclusion, is recorded in [precision_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/precision_scan_first_look.md).
