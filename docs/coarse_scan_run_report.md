# Coarse-Scan Run Report

## Scope

This report records the first production coarse scan launched after the executed coarse-scan smoke test passed.

Constraints followed:

- no adaptive refinement was started
- legacy physics was not changed
- benchmark-approved execution defaults were used
- the full branch was the main scan target
- `no_memory` and `no_feedback` were included only as sparse validation controls

Primary inputs:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)
- [benchmark_mini_scan_report.md](file:///home/zhuguolong/aoup_model/docs/benchmark_mini_scan_report.md)
- [coarse_scan_execution_smoke_report.md](file:///home/zhuguolong/aoup_model/docs/coarse_scan_execution_smoke_report.md)

## Production Design

Execution defaults:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 512`

Reference scales used:

- `tau_g = 7.337257462686567`
- `l_g = 3.6686287313432837`
- `tau_p = 1.0`

Design structure:

- `48` full-branch dense inner-box points
- `8` full-branch outer-frame points
- `4` sparse validation-control points
- `60` total state points
- `10` total shards with batch size `6`

Inner box:

- `Pi_m in {0.1, 0.3, 0.6, 1.0}`
- `Pi_f in {0.05, 0.1, 0.2, 0.3}`
- `Pi_U in {-0.1, 0.0, 0.25}`

Outer frame:

- extends to `Pi_m = 3, 10`
- extends to `Pi_f = 1, 3`
- extends to `Pi_U = -0.5, 0.5`

Sparse controls:

- `no_memory` at `Pi_m = 1.0`, `Pi_f = 0.3`, `Pi_U in {0.0, 0.25}`
- `no_feedback` at `Pi_m = 1.0`, `Pi_f = 0.3`, `Pi_U in {0.0, 0.25}`

## Produced Outputs

Phase summaries:

- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/summary.csv)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/summary.parquet)
- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/metadata.json)
- [shard_execution_report.json](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/shard_execution_report.json)

Quick-look outputs:

- [Psucc_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/coarse_scan_quicklook/Psucc_mean.png)
- [MFPT_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/coarse_scan_quicklook/MFPT_mean.png)
- [eta_sigma_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/coarse_scan_quicklook/eta_sigma_mean.png)
- [trap_time_mean.png](file:///home/zhuguolong/aoup_model/outputs/figures/coarse_scan_quicklook/trap_time_mean.png)
- [top_screening_points.csv](file:///home/zhuguolong/aoup_model/outputs/figures/coarse_scan_quicklook/top_screening_points.csv)

Manifest:

- [task_manifest.json](file:///home/zhuguolong/aoup_model/outputs/runs/coarse_scan/task_manifest.json)

## Execution Status

Final phase metadata:

- `status_completion = "completed"`
- `status_stage = "coarse_scan_execute"`
- `status_reason = null`
- `n_state_points = 60`
- `n_executed_state_points = 60`
- `n_generated_only_state_points = 0`

Shard execution summary:

- completed shards: `10`
- failed shards: `0`
- attempts requiring retry: `0`

Completed shards:

- `batch_000`
- `batch_001`
- `batch_002`
- `batch_003`
- `batch_004`
- `batch_005`
- `batch_006`
- `batch_007`
- `batch_008`
- `batch_009`

Failed shards:

- none

Retry policy recorded in [shard_execution_report.json](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/shard_execution_report.json):

- retry limit: `1`
- rule: retry a failed shard once immediately, then leave it recorded as failed without starting adaptive refinement

## Output Integrity

Status: `PASS`

Observed:

- `60 / 60` completed rows were checked for executed artifacts
- missing `result.json` paths: `0`
- missing `raw_summary.csv` paths: `0`
- phase summary parquet exists
- quick-look figure directory exists and contains all requested metric plots

## Notes

- The canonical coarse-scan paths under `outputs/summaries/coarse_scan/` now contain the first completed production coarse scan.
- `eta_sigma_mean` should still be read as a screening signal at this stage, not as a final precision ranking metric.
- No adaptive refinement was triggered or prepared in this run.
