# Schema Alignment Report

## Scope

This report covers the workflow-schema contract fixes requested after the integration audit.

Applied constraints:

- no changes to legacy physics files
- no changes to stepping, geometry, or random-number logic
- documented workflow schema is now the primary output contract
- backward compatibility is preserved where practical

Files updated:

- `src/configs/schema.py`
- `src/utils/workflow_schema.py`
- `src/runners/run_reference_scales.py`
- `src/runners/run_benchmark_mini_scan.py`
- `src/runners/run_coarse_scan.py`
- `tests/test_adapter_schema.py`
- `tests/test_reference_scales.py`
- `tests/test_small_scan_smoke.py`

## What Changed

### 1. `RunConfig` serialization now preserves `config_hash`

`RunConfig.to_dict()` now includes `config_hash`, and `RunConfig.from_dict()` ignores a serialized `config_hash` field for backward compatibility.

Result:

- persisted config payloads now carry the stable identifier required by the workflow contract
- coarse-scan manifest payloads now preserve `config_hash`
- existing deserialization remains compatible with older payloads and newer payloads

Relevant code:

- [schema.py](file:///home/zhuguolong/aoup_model/src/configs/schema.py#L13-L57)

### 2. All workflow runners now use shared schema-aware path construction

A new helper module centralizes the workflow output contract:

- `outputs/runs/{phase}/...`
- `outputs/summaries/{phase}/...`
- `outputs/logs/{phase}/...`

It also standardizes:

- per-config run directories under `outputs/runs/{phase}/{geometry_id}/{config_hash}/`
- `result.json`
- `raw_summary.csv`
- `summary.csv`
- optional `summary.parquet`

Relevant code:

- [workflow_schema.py](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py)

### 3. Reference-scale extraction now uses the documented schema as primary

Primary outputs:

- `outputs/runs/reference_scales/{geometry_id}/{config_hash}/result.json`
- `outputs/summaries/reference_scales/summary.csv`
- `outputs/summaries/reference_scales/summary.parquet` when parquet support is available
- `outputs/logs/reference_scales/reference_scale_extraction.log`

Phase-specific persisted extras retained:

- `outputs/summaries/reference_scales/reference_scales.json`
- `outputs/summaries/reference_scales/baseline_transition_stats.csv`
- `outputs/summaries/reference_scales/baseline_transition_stats.parquet`

Relevant code:

- [run_reference_scales.py](file:///home/zhuguolong/aoup_model/src/runners/run_reference_scales.py)

### 4. Benchmark mini-scan now writes per-config results plus phase summary tables

Primary outputs:

- `outputs/runs/benchmark_mini_scan/{geometry_id}/{config_hash}/result.json`
- `outputs/summaries/benchmark_mini_scan/summary.csv`
- `outputs/summaries/benchmark_mini_scan/summary.parquet` when parquet support is available
- `outputs/logs/benchmark_mini_scan/benchmark_mini_scan.log`

Retained metadata sidecar:

- `outputs/summaries/benchmark_mini_scan/metadata.json`

Relevant code:

- [run_benchmark_mini_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_benchmark_mini_scan.py)

### 5. Coarse-scan generation now writes schema-aligned summaries and preserves hashes in manifests

Primary outputs:

- `outputs/runs/coarse_scan/task_manifest.json`
- `outputs/summaries/coarse_scan/summary.csv`
- `outputs/summaries/coarse_scan/summary.parquet` when parquet support is available
- `outputs/logs/coarse_scan/generate_coarse_scan_tasks.log`

Manifest improvement:

- each serialized config in `task_manifest.json` now includes `config_hash`

Relevant code:

- [run_coarse_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan.py)

## Primary Contract After Fix

### Shared path contract

All workflow stages now write through the same phase-based root layout:

- `outputs/runs/{phase}/...`
- `outputs/summaries/{phase}/...`
- `outputs/logs/{phase}/...`

For executed runs, the primary per-config path is:

- `outputs/runs/{phase}/{geometry_id}/{config_hash}/result.json`

For phase summaries, the primary outputs are:

- `outputs/summaries/{phase}/summary.csv`
- `outputs/summaries/{phase}/summary.parquet`

### Preserved core identifiers

The following are now preserved consistently in serialized workflow payloads:

- `seed`
- `model_variant`
- `config_hash`
- `geometry_id`
- selected input parameters carried into summary rows

## Backward-Compatibility Shims Added

- Reference-scale legacy directory shim:
  - still writes `outputs/reference/reference_scales.json`
  - still writes `outputs/reference/baseline_transition_stats.csv`
  - still writes `outputs/reference/baseline_transition_stats.parquet`
- `RunConfig.from_dict()` shim:
  - accepts payloads with serialized `config_hash`
  - ignores `config_hash` on reconstruction to preserve current call sites
- Benchmark mini-scan metadata shim:
  - still writes `outputs/summaries/benchmark_mini_scan/metadata.json`

## Validation

Diagnostics:

- no diagnostics reported for updated schema, runner, utility, or test files

Tests run:

```bash
pytest -q tests/test_adapter_schema.py tests/test_reference_scales.py tests/test_small_scan_smoke.py tests/test_legacy_regression.py
```

Result:

- `18 passed`

## Remaining Non-Physics Gaps

These were not part of the requested contract-only fix and remain for later work:

- `raw_summary_path` now points to adapter-written `raw_summary.csv`, not a legacy task-writer artifact
- workflow-specific fields such as `alignment_mean`, `alignment_lag_peak`, and `runtime_seconds` are still placeholders in summary rows
- coarse-scan generation writes manifests and summary tables, but does not execute runs, so it does not emit per-config `result.json` files
