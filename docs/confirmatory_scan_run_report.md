# Confirmatory Scan Run Report

## Scope

This report records the local confirmatory scan launched around the resolved productive-memory ridge.

Constraints followed:

- no global search expansion was performed
- `Pi_f` stayed pinned to the supplied narrow band
- the base grid used `n_traj = 4096` for all points
- the final candidate set was resampled at `n_traj = 8192`
- legacy physics was not changed

Primary inputs:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)
- [precision_scan_run_report.md](file:///home/zhuguolong/aoup_model/docs/precision_scan_run_report.md)
- [precision_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/precision_scan_first_look.md)

## Confirmatory Design

Execution defaults:

- `dt = 0.0025`
- `Tmax = 30.0`
- base grid `n_traj = 4096`
- finalist resample `n_traj = 8192`

Reference scales used:

- `tau_g = 7.337257462686567`
- `l_g = 3.6686287313432837`
- `tau_p = 1.0`

Confirmatory grid:

- `Pi_f in {0.018, 0.02, 0.022, 0.025}`
- `Pi_m in {0.08, 0.1, 0.12, 0.15, 0.18, 0.2, 0.22}`
- `Pi_U in {0.1, 0.15, 0.2, 0.25, 0.3}`

Design counts:

- base grid points: `140`
- finalist resample points: `6`
- total executed rows: `146`
- completed shards: `30`

## Produced Outputs

Phase summaries:

- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.csv)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/metadata.json)
- [shard_execution_report.json](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/shard_execution_report.json)

Figures and tables:

- [Psucc_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/Psucc_mean.png)
- [MFPT_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/MFPT_mean.png)
- [eta_sigma_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/eta_sigma_mean.png)
- [trap_time_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/trap_time_mean.png)
- [Psucc_ci_width.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/Psucc_ci_width.png)
- [MFPT_ci_width.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/MFPT_ci_width.png)
- [eta_sigma_ci_width.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/eta_sigma_ci_width.png)
- [trap_time_ci_width.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/trap_time_ci_width.png)
- [objective_fronts.png](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/objective_fronts.png)
- [final_front_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/final_front_candidates.csv)
- [confirmatory_front_analysis.json](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/confirmatory_front_analysis.json)

Manifests:

- [task_manifest.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/task_manifest.json)
- [final_candidate_resample_manifest.json](file:///home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/final_candidate_resample_manifest.json)

## Execution Status

Final phase metadata:

- `status_completion = "completed"`
- `status_stage = "confirmatory_scan_execute"`
- `status_reason = null`
- `n_state_points = 146`
- `n_executed_state_points = 146`
- `n_generated_only_state_points = 0`

Shard summary:

- completed shards: `30`
- failed shards: `0`

## Front Comparison Summary

Best confirmatory success point:

- `Pi_m = 0.08`
- `Pi_f = 0.025`
- `Pi_U = 0.1`
- `Psucc_mean = 0.97412109375`

Best confirmatory efficiency point:

- `Pi_m = 0.18`
- `Pi_f = 0.018`
- `Pi_U = 0.15`
- `eta_sigma_mean = 6.685949490215236e-05`

Fastest confirmatory point:

- `Pi_m = 0.1`
- `Pi_f = 0.018`
- `Pi_U = 0.3`
- `MFPT_mean = 2.816089797639123`

Distinctness checks:

- distinct winner locations: `True`
- top-10 `Psucc_mean` vs `eta_sigma_mean` overlap: `0`
- top-10 `Psucc_mean` vs `MFPT_mean` overlap: `0`
- top-10 `eta_sigma_mean` vs `MFPT_mean` overlap: `0`
- all-three top-10 overlap: `0`

## Output Integrity

Status: `PASS`

Observed:

- `146 / 146` completed rows were checked for executed artifacts
- missing `result.json` paths: `0`
- missing `raw_summary.csv` paths: `0`
- the confirmatory candidate table exists
- the confirmatory front-analysis JSON exists

## Hand-Off

The detailed interpretation, including uncertainty-aware recommendations for the three objective fronts, is recorded in [confirmatory_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/confirmatory_scan_first_look.md).
