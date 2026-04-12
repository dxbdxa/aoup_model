# Refinement Run Report

## Scope

This report records the first adaptive refinement scan launched after the completed production coarse scan.

Constraints followed:

- no global outer-frame expansion was performed
- the full branch remained the main target
- only a very small anchor set was kept outside the dense refinement box
- legacy physics was not changed

Primary inputs:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)
- [coarse_scan_run_report.md](file:///home/zhuguolong/aoup_model/docs/coarse_scan_run_report.md)
- [coarse_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/coarse_scan_first_look.md)

## Refinement Design

Execution defaults:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 1024`

Reference scales used:

- `tau_g = 7.337257462686567`
- `l_g = 3.6686287313432837`
- `tau_p = 1.0`

Dense refinement envelope:

- `Pi_m in {0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4}`
- `Pi_f in {0.02, 0.03, 0.05, 0.07, 0.1, 0.12}`
- `Pi_U in {0.0, 0.1, 0.2, 0.25, 0.3}`

Anchor points retained:

- `(Pi_m, Pi_f, Pi_U) = (0.6, 0.2, 0.0)`
- `(0.6, 0.2, 0.25)`
- `(1.0, 0.3, 0.0)`
- `(3.0, 0.1, 0.0)`

Design counts:

- `240` dense full-branch refinement points
- `4` full-branch anchor points
- `244` total state points
- `31` total shards with batch size `8`

## Produced Outputs

Phase summaries:

- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/summary.csv)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/summary.parquet)
- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/metadata.json)
- [shard_execution_report.json](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/shard_execution_report.json)

Quick-look outputs:

- [Psucc_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/refinement_quicklook/Psucc_mean.png)
- [MFPT_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/refinement_quicklook/MFPT_mean.png)
- [eta_sigma_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/refinement_quicklook/eta_sigma_mean.png)
- [trap_time_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/refinement_quicklook/trap_time_mean.png)
- [top_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/refinement_quicklook/top_candidates.csv)

Manifest:

- [task_manifest.json](file:///home/zhuguolong/aoup_model/outputs/runs/refinement_scan/task_manifest.json)

## Execution Status

Final phase metadata:

- `status_completion = "completed"`
- `status_stage = "refinement_scan_execute"`
- `status_reason = null`
- `n_state_points = 244`
- `n_executed_state_points = 244`
- `n_generated_only_state_points = 0`

Shard execution summary:

- completed shards: `31`
- failed shards: `0`
- retries used: `0`

Retry policy recorded in [shard_execution_report.json](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/shard_execution_report.json):

- retry limit: `1`
- rule: retry a failed shard once immediately, then record failure without expanding the outer frame

## Output Integrity

Status: `PASS`

Observed:

- `244 / 244` completed rows were checked for executed artifacts
- missing `result.json` paths: `0`
- missing `raw_summary.csv` paths: `0`
- refinement summary parquet exists
- all four requested quick-look figure files exist
- top-candidate screening table exists

## Top-Level Outcome

Operationally, the first adaptive refinement scan completed cleanly and fully. The result set is ready for candidate comparison by:

- `Psucc_mean`
- `MFPT_mean`
- `eta_sigma_mean`
- `trap_time_mean`

The detailed interpretation is recorded in [refinement_first_look.md](file:///home/zhuguolong/aoup_model/docs/refinement_first_look.md).
