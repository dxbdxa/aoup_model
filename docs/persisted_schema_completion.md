# Persisted Schema Completion

## Scope

This update completes persisted workflow fields and provenance only.

Constraints preserved:

- no changes to legacy physics
- no changes to stepping, geometry, or random-number logic
- no changes to the schema-aligned output path contract
- no redesign of coarse-scan execution

Files updated:

- `src/utils/workflow_schema.py`
- `src/runners/run_reference_scales.py`
- `src/runners/run_benchmark_mini_scan.py`
- `src/runners/run_coarse_scan.py`
- `tests/test_reference_scales.py`
- `tests/test_small_scan_smoke.py`

Files created:

- `docs/persisted_schema_completion.md`
- `outputs/examples/reference_scales_example.json`
- `outputs/examples/benchmark_mini_scan_example.json`
- `outputs/examples/coarse_scan_example.json`

## What Was Added

### Shared persisted provenance fields

The shared workflow writer helper now supports explicit persisted provenance fields across phases:

- `scan_id`
- `task_id`
- `shard_id`
- `state_point_id`
- `config_hash`
- `geometry_id`
- `model_variant`
- `seed`
- `upstream_reference_scales_path`
- `status_completion`
- `status_stage`
- `status_reason`

For executed phases, these fields are now written into:

- `result.json`
- phase summary rows in `summary.csv` / `summary.parquet`
- phase `metadata.json`

For coarse-scan generation, these fields are now written into:

- `task_manifest.json`
- generated summary rows in `summary.csv` / `summary.parquet`
- phase `metadata.json`

Relevant code:

- [workflow_schema.py](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py)

### Completed aggregate state-point fields

Where the current stage can compute them now, summary rows include:

- dimensional inputs: `v0`, `Dr`, `tau_v`, `gamma0`, `gamma1`, `tau_f`, `U`, `dt`, `Tmax`
- geometry inputs: `wall_thickness`, `gate_width`, `exit_radius`, `n_shell`, `grid_n`
- additional controls: `kf`, `kBT`, `eps_psi`
- dimensionless parameters:
  - `gamma1_over_gamma0`
  - `tau_p`
  - `tau_v_over_tau_p`
  - `tau_f_over_tau_p`
  - `U_over_v0`
  - `Xi`
  - `De`
  - `tau_m`
- aggregate observables:
  - `n_traj`
  - `n_success`
  - `Psucc_mean`
  - `Psucc_ci_low`
  - `Psucc_ci_high`
  - `MFPT_mean`
  - `MFPT_median`
  - `FPT_q10`
  - `FPT_q90`
  - `trap_time_mean`
  - `trap_count_mean`
  - `wall_fraction_mean`
  - `Sigma_drag_mean`
  - `J_proxy`
  - `eta_sigma_mean`
  - `eta_sigma_ci_low`
  - `eta_sigma_ci_high`

### Explicit placeholders for not-yet-computable fields

The following workflow fields are now kept explicit instead of being silently omitted:

- `revisit_mean`
- `alignment_mean`
- `alignment_lag_peak`
- `runtime_seconds`
- `code_version`
- `status_converged`

For coarse-scan generation only, execution-dependent fields are also explicit placeholders:

- `n_success`
- `Psucc_mean`
- `MFPT_mean`
- `MFPT_median`
- `FPT_q10`
- `FPT_q90`
- `trap_time_mean`
- `trap_count_mean`
- `wall_fraction_mean`
- `Sigma_drag_mean`
- `J_proxy`
- `eta_sigma_mean`

These are persisted as `null` in JSON or empty/NA values in tabular outputs until that stage is executed.

## Phase-by-Phase Completion

### Reference scales

Added or completed:

- `task_id = reference_scale_extraction`
- explicit `state_point_id = config_hash`
- explicit per-trajectory provenance in `baseline_transition_stats.*`
- explicit `metadata.json`
- explicit `result.json` provenance block

Per-trajectory lightweight fields now persisted where currently available:

- `scan_id`
- `task_id`
- `shard_id`
- `geometry_id`
- `model_variant`
- `state_point_id`
- `seed`
- `traj_id`
- `success`
- `fpt`
- `termination_reason`
- `trap_time_total`
- `trap_count`
- `wall_fraction`
- `drag_dissipation`

And explicitly placeholdered for later work:

- `path_length`
- `revisit_count`
- `mean_progress_along_nav`
- `mean_speed`
- `mean_rel_speed_to_flow`
- `alignment_cos_mean`
- `alignment_cos_std`
- `gate_cross_count`
- `last_gate_index`

Relevant code:

- [run_reference_scales.py](file:///home/zhuguolong/aoup_model/src/runners/run_reference_scales.py)

### Benchmark mini-scan

Added or completed:

- `task_id` per state point
- explicit upstream reference-scales link field
- explicit `result.json` provenance block
- `metadata.json` with completion/provenance fields
- completed summary-row field set through the shared helper

Relevant code:

- [run_benchmark_mini_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_benchmark_mini_scan.py)

### Coarse scan

Added or completed:

- manifest-level provenance:
  - `scan_id`
  - `task_id`
  - `shard_id`
  - `status_completion`
  - `status_stage`
  - `status_reason`
  - `upstream_reference_scales_path`
- summary rows with task-level provenance:
  - `task_id`
  - `shard_id`
  - `state_point_id`
  - `config_hash`
- explicit `metadata.json`
- explicit placeholder values for execution-only observables

Relevant code:

- [run_coarse_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan.py)

## JSON Validity

The shared JSON writer now sanitizes non-finite floats such as `NaN` and `Inf` to `null` before serialization.

Result:

- `result.json`
- `metadata.json`
- `reference_scales.json`
- `task_manifest.json`

are emitted as strict machine-readable JSON.

## Machine-Readable Examples

Generated examples:

- [reference_scales_example.json](file:///home/zhuguolong/aoup_model/outputs/examples/reference_scales_example.json)
- [benchmark_mini_scan_example.json](file:///home/zhuguolong/aoup_model/outputs/examples/benchmark_mini_scan_example.json)
- [coarse_scan_example.json](file:///home/zhuguolong/aoup_model/outputs/examples/coarse_scan_example.json)

These examples were generated from small live runs or generation steps using the current code path, not handwritten mock payloads.

## Validation

Diagnostics:

- no diagnostics reported for the updated helper, runners, tests, or this report

Tests run:

```bash
pytest -q tests/test_reference_scales.py tests/test_small_scan_smoke.py tests/test_adapter_schema.py tests/test_legacy_regression.py
```

Result:

- `18 passed`

## Remaining Explicit Limits

Still intentionally unchanged in this step:

- coarse scan does not execute runs and therefore does not emit per-config `result.json`
- physics-derived fields not available from the current legacy outputs remain explicit placeholders
- `raw_summary_path` points to adapter-written normalized raw summary snapshots, not legacy task-writer artifacts
