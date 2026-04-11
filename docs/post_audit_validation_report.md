# Post-Audit Validation Report

## Scope

This report validates workflow contract completeness after:

- schema-aligned path fixes
- persisted provenance completion
- artifact provenance policy definition
- `model_variant` / `flow_condition` semantic separation

Validation constraints:

- no legacy physics changes
- no full coarse scan
- coarse scan remains generation-only

## Validation Inputs

Reviewed docs:

- `docs/integration_audit.md`
- `docs/schema_alignment_report.md`
- `docs/persisted_schema_completion.md`
- `docs/artifact_provenance_policy.md`
- `docs/model_variant_migration.md`

Reviewed code:

- `src/configs/schema.py`
- `src/utils/workflow_schema.py`
- `src/runners/run_reference_scales.py`
- `src/runners/run_benchmark_mini_scan.py`
- `src/runners/run_coarse_scan.py`

Live validation artifacts created under:

- `outputs/examples/post_audit_examples/`

## End-to-End Validation Runs

Executed small workflow validations:

- very small reference-scale extraction
- very small benchmark mini-scan with upstream reference-scales link
- coarse-scan generation-only manifest and summary generation

Compatibility validation performed:

- old payload with `model_variant = "no_flow"`
- new payload with explicit `flow_condition`
- persisted artifact payload normalization

Tests rerun:

```bash
pytest -q tests/test_adapter_schema.py tests/test_legacy_regression.py tests/test_reference_scales.py tests/test_small_scan_smoke.py
```

Result:

- `19 passed`

## Example Artifacts

Generated examples:

- [reference_scales_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/reference_scales_validation.json)
- [benchmark_mini_scan_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/benchmark_mini_scan_validation.json)
- [coarse_scan_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/coarse_scan_validation.json)
- [compatibility_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/compatibility_validation.json)

## Validation Results

### 1. Persisted outputs contain required provenance fields

Status: `PASS`

Confirmed in executed and generation-only summary rows:

- `scan_id`
- `task_id`
- `state_point_id`
- `geometry_id`
- `model_variant`
- `flow_condition`
- `seed`
- `config_hash`
- `status_completion`
- `status_stage`

Evidence:

- [reference_scales_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/reference_scales_validation.json)
- [benchmark_mini_scan_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/benchmark_mini_scan_validation.json)
- [coarse_scan_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/coarse_scan_validation.json)

### 2. `raw_summary_path` behavior is explicit and correct

Status: `PASS`

Confirmed:

- executed phases use:
  - `raw_summary_kind = "adapter_raw_summary_csv"`
  - `raw_summary_status = "available"`
- coarse-scan generation uses:
  - `raw_summary_kind = "not_applicable_generation_only"`
  - `raw_summary_status = "not_applicable"`

This removes the earlier ambiguous bare-`None` behavior.

### 3. `model_variant` semantics are no longer overloaded

Status: `PASS`

Confirmed:

- `model_variant` now carries branch identity only
- `flow_condition` now carries flow semantics separately
- old `model_variant = "no_flow"` payloads normalize to:
  - `model_variant = "full"`
  - `flow_condition = "explicit_no_flow_control"`
  - `legacy_model_variant = "no_flow"`

Evidence:

- [compatibility_validation.json](file:///home/zhuguolong/aoup_model/outputs/examples/post_audit_examples/compatibility_validation.json)

### 4. Summary rows can be traced back to per-config artifacts

Status: `PASS`

Confirmed for executed phases:

- summary row includes `normalized_result_path`
- summary row includes `raw_summary_path`
- summary row includes `metadata_sidecar_path`
- summary row includes `upstream_reference_scales_path`
- live checks confirm `config_hash` agreement between summary row and `result.json`

### 5. Coarse-scan generation-only outputs are correctly represented

Status: `PASS`

Confirmed:

- coarse scan emits manifest and phase summary outputs only
- coarse summary rows explicitly mark:
  - `normalized_result_kind = "not_applicable_generation_only"`
  - `raw_summary_kind = "not_applicable_generation_only"`
- generation-only outputs are not misrepresented as executed runs

### 6. Very small reference-scale and mini-scan runs are stable end-to-end

Status: `PASS`

Confirmed:

- reference-scale extraction completed and produced schema-aligned outputs
- benchmark mini-scan completed and linked to upstream reference scales
- no path-contract or provenance regressions observed in the small live runs

### 7. Old payload compatibility still works after the `model_variant` migration

Status: `PASS`

Confirmed through:

- compatibility normalization example payloads
- compatibility deserialization logic
- compatibility test coverage in `tests/test_adapter_schema.py`

## PASS / FAIL Checklist For Remaining Non-Physics Blockers

- `PASS` Provenance fields are present in persisted outputs for executed and generation-only phases.
- `PASS` `raw_summary_path` semantics are explicit and phase-correct.
- `PASS` Branch identity and flow semantics are separated.
- `PASS` Executed summary rows trace back to normalized and raw per-config artifacts.
- `PASS` Coarse-scan generation-only outputs are not mislabeled as executed runs.
- `PASS` Old payload compatibility remains readable after migration.
- `FAIL` Full coarse-scan execution remains unvalidated in this report because this step intentionally excludes running a coarse scan.
- `FAIL` Some downstream analysis-only fields remain explicit placeholders rather than computed values, such as `alignment_mean`, `alignment_lag_peak`, and `runtime_seconds`.

## Remaining Non-Physics Blockers

There are no contract-breaking blockers for:

- reference scales
- benchmark mini-scan
- coarse-scan generation

Open non-physics limitations still outside this validation step:

- coarse-scan execution behavior is not validated here
- some downstream-analysis fields remain placeholder/null by design at the current stage

## Ready for reference scales / mini-scan / coarse scan?

- `Reference scales`: `YES`
  - schema-aligned outputs exist
  - provenance is explicit
  - summary rows trace to per-config artifacts
- `Benchmark mini-scan`: `YES`
  - end-to-end small run is stable
  - upstream reference linkage is explicit
  - branch and flow semantics are separated
- `Coarse scan`: `YES` for generation-only, `NO` for executed-run readiness in this specific validation
  - generation-only manifests and summaries are contract-correct
  - executed coarse-scan behavior was intentionally not run or validated in this report

## Conclusion

Post-audit contract validation passes for the currently implemented workflow scope:

- reference-scale extraction
- benchmark mini-scan
- coarse-scan generation-only

The remaining unresolved items are non-physics and out of scope for this validation step, not regressions in the current workflow contract implementation.
