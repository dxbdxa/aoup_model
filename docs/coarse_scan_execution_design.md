# Coarse-Scan Execution Design

## Scope

This note adds executed coarse-scan workflow support without changing:

- legacy physics
- legacy stepping
- legacy geometry logic
- generation-only manifest semantics already used by `src/runners/run_coarse_scan.py`

The new execution entry point is:

- [run_coarse_scan_execute.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan_execute.py)

## Design Goals

The executed coarse-scan layer must:

- read the existing `task_manifest.json` contract without requiring a new manifest format
- execute one selected batch or shard of state points through `LegacySimcoreAdapter`
- keep unexecuted points explicit as generation-only rows
- write the same per-config artifacts already used by other executed phases
- update the shared coarse-scan summary and metadata sidecar in place

## Preserved Generation Semantics

Manifest generation remains unchanged:

- `src/runners/run_coarse_scan.py` still writes:
  - `outputs/runs/coarse_scan/task_manifest.json`
  - `outputs/summaries/coarse_scan/summary.csv`
  - `outputs/summaries/coarse_scan/metadata.json`
- generated-only rows still use:
  - `status_completion = "generated_manifest_only"`
  - `status_reason = "coarse_scan_generation_only"`
  - `raw_summary_kind = "not_applicable_generation_only"`
  - `normalized_result_kind = "not_applicable_generation_only"`

This preserves the previously validated contract for design generation.

## Execution Entry Point

The executor reads the manifest and reconstructs:

- `SweepTask`
- `RunConfig`

Supported selectors:

- `task_id`
- `batch_index`
- `shard_id` using the existing `batch_###` label

Selection is intentionally manifest-native so the execution runner does not need a second task-dispatch schema.

## Execution Defaults

The benchmark recommendation for first coarse execution is:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 512`

These are the intended execution defaults for newly prepared coarse manifests.

The executor itself does not silently mutate manifest configs after loading them. It executes the serialized `RunConfig` values from the manifest so that:

- `config_hash`
- `state_point_id`
- summary-row provenance
- per-config artifact traceability

remain exact and stable.

## Executed Output Semantics

For executed coarse-scan rows and per-config artifacts:

- `status_stage = "coarse_scan_execute"`
- `status_completion = "completed"`
- `status_reason = "executed_from_manifest"`
- `task_manifest_path` remains populated so every executed row still points back to its source manifest

Per-config executed artifacts match the other executed phases:

- `outputs/runs/coarse_scan/<geometry_id>/<config_hash>/result.json`
- `outputs/runs/coarse_scan/<geometry_id>/<config_hash>/raw_summary.csv`

Artifact meanings remain:

- `raw_summary.csv`: adapter-written one-config raw summary snapshot
- `result.json`: normalized workflow-facing per-config result

## Summary Merge Behavior

The phase summary stays phase-level and mixed-state by design:

- previously generated-only rows remain present for unexecuted points
- executed rows overwrite the matching `state_point_id`
- new execution-only fields are added column-wise when first needed

This makes one phase summary usable as:

- a manifest-progress tracker
- a coarse aggregation table
- a provenance index across generated and executed states

## Metadata Semantics

Phase metadata is updated after each execution pass.

When only part of the manifest has been executed:

- `status_stage = "coarse_scan_execute"`
- `status_completion = "partially_completed"`
- `status_reason = "coarse_scan_partial_execution"`

When all state points in the phase summary have been executed:

- `status_completion = "completed"`
- `status_reason = null`

The metadata also records:

- selected task ids
- selected shard labels
- executed vs generated-only state-point counts
- upstream reference scales path
- reference-scale values when available

## Reference-Scale Fields

If `upstream_reference_scales_path` is available from the manifest or execution call, executed coarse rows are augmented with:

- `reference_tau_g`
- `reference_l_g`
- `reference_tau_p`
- `tau_v_over_tau_g`
- `tau_f_over_tau_g`
- `U_tau_g_over_l_g`
- `Pi_m`
- `Pi_f`
- `Pi_U`

This supports coarse-scan screening in the same normalized language used by the benchmark mini-scan.

## Testing Strategy

Smoke coverage is added in:

- [test_coarse_scan_execution_smoke.py](file:///home/zhuguolong/aoup_model/tests/test_coarse_scan_execution_smoke.py)

The smoke test validates:

- manifest generation stays generation-only
- one selected batch executes successfully
- executed rows and unexecuted rows coexist correctly in the same summary
- per-config `result.json` and `raw_summary.csv` are written only for executed points
- metadata switches to explicit execution-stage semantics

## Example Bundle

A small real example bundle is stored under:

- `outputs/examples/coarse_scan_execution_smoke/`

This example is meant only to validate the workflow shape and provenance behavior, not to support physics claims.
