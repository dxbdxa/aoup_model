# Coarse-Scan Execution Smoke Report

## Scope

This smoke test validates executed coarse-scan workflow support on a tiny full-branch subset only.

Constraints followed:

- no full coarse scan was launched
- legacy physics was not changed
- coarse manifest generation remained generation-only
- exactly one tiny batch was executed from the generated manifest

Reference inputs:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)
- [benchmark_mini_scan_report.md](file:///home/zhuguolong/aoup_model/docs/benchmark_mini_scan_report.md)
- [coarse_scan_execution_design.md](file:///home/zhuguolong/aoup_model/docs/coarse_scan_execution_design.md)

## Smoke-Test Design

Output root:

- `outputs/examples/coarse_scan_execution_smoke/`

Reference scales used:

- `tau_g = 7.337257462686567`
- `l_g = 3.6686287313432837`

Full-branch manifest points:

- batch `000`
  - `Pi_m = 0.3`, `Pi_f = 0.1`, `Pi_U = 0.0`
  - `Pi_m = 0.3`, `Pi_f = 0.1`, `Pi_U = 0.25`
- batch `001`
  - `Pi_m = 1.0`, `Pi_f = 0.3`, `Pi_U = 0.0`
  - `Pi_m = 1.0`, `Pi_f = 0.3`, `Pi_U = 0.25`

Execution defaults encoded in the manifest:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 512`

Execution action:

- generated a 4-point manifest
- executed exactly one batch: `batch_000`
- left `batch_001` unexecuted to preserve a mixed generated/executed summary state

## Produced Artifacts

Manifest and summaries:

- [task_manifest.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/task_manifest.json)
- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/summaries/coarse_scan/summary.csv)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/summaries/coarse_scan/summary.parquet)
- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/summaries/coarse_scan/metadata.json)

Executed per-config artifacts:

- [result.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/maze_v1/8e3588ef4af7e56d36977f2de1dfe115bfdcbf0d365a22f7384f5d345e7e0a91/result.json)
- [raw_summary.csv](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/maze_v1/8e3588ef4af7e56d36977f2de1dfe115bfdcbf0d365a22f7384f5d345e7e0a91/raw_summary.csv)
- [result.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/maze_v1/8031b0dbe0fd05db37efd209dc21705dd0f58df01062530413126b2bbb6e6a7b/result.json)
- [raw_summary.csv](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/maze_v1/8031b0dbe0fd05db37efd209dc21705dd0f58df01062530413126b2bbb6e6a7b/raw_summary.csv)

## Validation Checks

### 1. Very small full-branch manifest was generated

Status: `PASS`

Observed:

- manifest contains `2` tasks
- manifest contains `4` total full-branch state points
- parameter targets are centered on the productive-memory region requested for the smoke test

Evidence:

- [task_manifest.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/task_manifest.json)

### 2. Exactly one shard / one tiny batch was executed

Status: `PASS`

Observed:

- selected task: `coarse_scan_batch_000`
- selected shard: `batch_000`
- executed state points: `2`
- unexecuted state points remaining generation-only: `2`

Evidence:

- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/summaries/coarse_scan/metadata.json)

### 3. Per-config `result.json` exists for executed points

Status: `PASS`

Observed:

- `2` executed `result.json` files exist
- no `result.json` was written for the unexecuted batch

Evidence:

- [result.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/maze_v1/8e3588ef4af7e56d36977f2de1dfe115bfdcbf0d365a22f7384f5d345e7e0a91/result.json)
- [result.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/runs/coarse_scan/maze_v1/8031b0dbe0fd05db37efd209dc21705dd0f58df01062530413126b2bbb6e6a7b/result.json)

### 4. `raw_summary.csv` exists where applicable

Status: `PASS`

Observed:

- `2` executed `raw_summary.csv` files exist
- executed rows report:
  - `raw_summary_kind = "adapter_raw_summary_csv"`
  - `raw_summary_status = "available"`
- unexecuted rows report:
  - `raw_summary_kind = "not_applicable_generation_only"`
  - `raw_summary_status = "not_applicable"`

### 5. Summary rows updated correctly

Status: `PASS`

Observed in [summary.csv](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/summaries/coarse_scan/summary.csv):

- `4` total rows remain in the phase summary
- `2` rows use:
  - `status_completion = "completed"`
  - `status_stage = "coarse_scan_execute"`
  - `status_reason = "executed_from_manifest"`
- `2` rows remain:
  - `status_completion = "generated_manifest_only"`
  - `status_stage = "coarse_scan"`
  - `status_reason = "coarse_scan_generation_only"`
- executed rows include:
  - `normalized_result_path`
  - `raw_summary_path`
  - `reference_tau_g`
  - `reference_l_g`
  - `Pi_m`
  - `Pi_f`
  - `Pi_U`

### 6. Metadata and status fields are correct

Status: `PASS`

Observed in [metadata.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_execution_smoke/summaries/coarse_scan/metadata.json):

- `status_stage = "coarse_scan_execute"`
- `status_completion = "partially_completed"`
- `status_reason = "coarse_scan_partial_execution"`
- `n_state_points = 4`
- `n_executed_state_points = 2`
- `n_generated_only_state_points = 2`
- `selected_task_ids = ["coarse_scan_batch_000"]`
- `selected_shards = ["batch_000"]`

### 7. Executed outputs are distinguishable from generation-only outputs

Status: `PASS`

Observed:

- executed rows carry per-config artifact paths and execution-stage status
- generation-only rows keep explicit generation-only artifact markers
- both row classes coexist in one shared coarse summary without ambiguity

## Concise Outcome

The executed coarse-scan smoke test passes. The workflow now supports:

- generating a tiny coarse manifest near the productive-memory region
- executing exactly one selected batch
- writing per-config executed artifacts
- preserving explicit generation-only semantics for unexecuted points
- exposing the mixed execution state through phase summary and metadata sidecars

No full coarse scan was launched in this step.
