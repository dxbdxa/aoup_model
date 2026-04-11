# Artifact Provenance Policy

## Scope

This policy defines the semantic meaning and traceability rules for persisted workflow artifacts.

Constraints preserved:

- no changes to legacy physics
- no changes to stepping, geometry, or random-number logic
- no changes to the schema-aligned output path contract
- coarse scan remains generation-only in this step

## Policy Goal

Every persisted workflow record must make it clear:

- what artifact it points to
- whether that artifact is per-config or phase-level
- whether that artifact is available, not applicable, or pending
- how a summary row traces back to normalized per-config output and any upstream reference scales

## Artifact Roles

### 1. Adapter-written raw summary

Definition:

- a one-row CSV snapshot of the legacy summary dictionary for exactly one `RunConfig`
- written by the adapter-facing workflow layer
- stored per config under the schema-aligned run directory

Canonical role fields:

- `raw_summary_path`
- `raw_summary_kind = "adapter_raw_summary_csv"`
- `raw_summary_status = "available"`

Important clarification:

- this is **not** a phase summary table
- this is **not** a legacy task manifest
- this is **not** a normalized workflow result

### 2. Normalized per-config result

Definition:

- the workflow-facing `result.json` for exactly one config
- contains normalized fields from `RunResult` plus provenance fields

Canonical role fields:

- `normalized_result_path`
- `normalized_result_kind = "normalized_result_json"`

In existing payloads this is also mirrored by:

- `result_json`

### 3. Phase-level summary table

Definition:

- the aggregated table for one workflow phase
- stored at:
  - `outputs/summaries/{phase}/summary.csv`
  - `outputs/summaries/{phase}/summary.parquet`

Canonical role fields in summary rows:

- `phase_summary_path`
- `phase_summary_kind = "phase_summary_table"`

### 4. Task manifest

Definition:

- a phase-level manifest that enumerates planned work rather than executed per-config results
- currently relevant for coarse-scan generation

Canonical role fields:

- `task_manifest_path`
- `task_manifest_kind = "task_manifest_json"`

### 5. Metadata sidecar

Definition:

- phase-level `metadata.json`
- describes the phase outputs, generation context, seed policy, upstream links, and status

Canonical role fields:

- `metadata_sidecar_path`
- `metadata_sidecar_kind = "metadata_json_sidecar"`

## Formal Definition of `raw_summary_path`

`raw_summary_path` means:

- the path to the adapter-written one-row CSV snapshot of the raw legacy summary dictionary
- scoped to one config only
- located inside `outputs/runs/{phase}/{geometry_id}/{config_hash}/`

`raw_summary_path` does **not** mean:

- the path to `summary.csv`
- the path to `summary.parquet`
- the path to `metadata.json`
- the path to `task_manifest.json`

## Required Provenance Semantics By Phase

### Executed phases

Applies to:

- `reference_scales`
- `benchmark_mini_scan`

Required semantics:

- `raw_summary_path` must be present
- `raw_summary_kind` must be `"adapter_raw_summary_csv"`
- `raw_summary_status` must be `"available"`
- `normalized_result_path` must be present
- `normalized_result_kind` must be `"normalized_result_json"`
- `phase_summary_path` must be present
- `metadata_sidecar_path` must be present
- `upstream_reference_scales_path` must be explicit:
  - `null` when no upstream reference scales apply
  - a path string when they do apply

### Generation-only phases

Applies to:

- `coarse_scan`

Required semantics:

- `raw_summary_path` must remain explicit but not ambiguous
- `raw_summary_kind` must be `"not_applicable_generation_only"`
- `raw_summary_status` must be `"not_applicable"`
- `normalized_result_path` must be explicit and absent
- `normalized_result_kind` must be `"not_applicable_generation_only"`
- `task_manifest_path` must be present
- `task_manifest_kind` must be `"task_manifest_json"`
- `phase_summary_path` and `metadata_sidecar_path` must still be present

This phase must not pretend that per-config execution artifacts exist.

## Traceability Rules

### Summary row to per-config artifacts

For an executed phase summary row, the trace chain is:

1. identify the row by:
   - `scan_id`
   - `task_id`
   - `state_point_id`
   - `config_hash`
2. read:
   - `normalized_result_path`
   - `raw_summary_path`
   - `metadata_sidecar_path`
   - `phase_summary_path`
3. verify consistency:
   - row `config_hash` matches `result.json`
   - row `raw_summary_path` matches `result.json`
   - row `upstream_reference_scales_path` matches `result.json`

### Summary row to upstream reference scales

If the phase depends on upstream references:

- `upstream_reference_scales_path` must be present in:
  - summary rows
  - `result.json`
  - `metadata.json`

If the phase does not depend on upstream references:

- the field must still be explicit and null

### Generation-only traceability

For coarse-scan generation:

1. identify the row by `state_point_id` / `config_hash`
2. use `task_manifest_path` to find the serialized config in the manifest
3. do not infer missing raw or normalized per-config artifacts
4. use `raw_summary_kind` and `normalized_result_kind` to recognize that those artifacts are not applicable

## JSON and Nullability Policy

- JSON artifacts must be strict JSON
- non-finite values such as `NaN` and `Inf` must serialize as `null`
- unavailable-but-meaningful fields should remain explicit with `null` rather than being omitted
- not-applicable artifact roles must use explicit kind/status markers rather than a silent missing field

## Implementation Notes

Relevant implementation points:

- [RunResult](file:///home/zhuguolong/aoup_model/src/configs/schema.py#L59-L93)
- [write_result_bundle](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py#L70-L117)
- [build_phase_metadata](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py#L120-L169)
- [build_state_point_record](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py#L181-L284)

## Machine-Readable Trace Example

Trace example:

- [artifact_trace_example.json](file:///home/zhuguolong/aoup_model/outputs/examples/artifact_trace_example.json)

This example includes:

- an executed-phase trace for `benchmark_mini_scan`
- a generation-only trace for `coarse_scan`

## Small Validation Note

Validated trace path for one benchmark mini-scan summary row:

- row in `outputs/summaries/benchmark_mini_scan/summary.csv`
- points to `normalized_result_path`
- points to `raw_summary_path`
- points to `metadata_sidecar_path`
- points to `upstream_reference_scales_path`

The machine-readable trace confirms:

- summary-row `config_hash` matches `result.json`
- summary-row `raw_summary_path` matches `result.json`
- summary-row upstream reference path matches `result.json`

For coarse-scan generation, the trace confirms the opposite semantic:

- no raw per-config summary is claimed
- no normalized per-config result is claimed
- the manifest remains the authoritative artifact
