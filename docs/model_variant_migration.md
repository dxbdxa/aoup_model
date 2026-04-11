# Model Variant Migration

## Scope

This document separates ablation-branch identity from flow-condition semantics while preserving backward compatibility.

Constraints preserved:

- no changes to legacy physics
- no changes to stepping, geometry, or random-number logic
- no changes to schema-aligned output paths
- no changes to artifact provenance policy

## Old Semantics

Historically, `model_variant` mixed two different concerns:

- ablation branch identity:
  - `full`
  - `no_memory`
  - `no_feedback`
- flow-control semantics:
  - `no_flow`

This created an ambiguity:

- `model_variant = "full"` with `U = 0` could mean a zero-flow state point inside the full branch
- `model_variant = "no_flow"` could mean an explicit no-flow control branch

Those are not the same semantic statement.

## New Semantics

### `model_variant`

`model_variant` now means **ablation branch identity only**.

Supported normalized values:

- `full`
- `no_memory`
- `no_feedback`

### `flow_condition`

`flow_condition` now carries the flow semantics explicitly.

Supported values:

- `with_flow`
- `zero_flow`
- `explicit_no_flow_control`

Meaning:

- `with_flow`: nonzero `U`
- `zero_flow`: numerically `U = 0`, but not an explicit no-flow branch
- `explicit_no_flow_control`: compatibility-preserved semantic for older payloads that encoded `model_variant = "no_flow"`

### `legacy_model_variant`

`legacy_model_variant` is optional compatibility metadata.

Current usage:

- `legacy_model_variant = "no_flow"` when an old payload or old control branch is normalized into:
  - `model_variant = "full"`
  - `flow_condition = "explicit_no_flow_control"`

## Canonical Interpretation

### Full branch with zero flow

```json
{
  "model_variant": "full",
  "flow_condition": "zero_flow",
  "U": 0.0
}
```

Interpretation:

- full ablation branch
- zero flow as the numerical state condition

### Explicit no-flow control branch

```json
{
  "model_variant": "full",
  "flow_condition": "explicit_no_flow_control",
  "legacy_model_variant": "no_flow",
  "U": 0.0
}
```

Interpretation:

- full ablation branch
- explicit no-flow control semantics preserved from old payloads

## Compatibility Rules

### Reading old payloads

Old payload:

```json
{
  "model_variant": "no_flow",
  "U": 0.0
}
```

Normalized read result:

```json
{
  "model_variant": "full",
  "flow_condition": "explicit_no_flow_control",
  "legacy_model_variant": "no_flow",
  "U": 0.0
}
```

### Reading new payloads

If `flow_condition` is already present, it is preserved.

### Writing new payloads

New outputs should always write:

- normalized `model_variant`
- explicit `flow_condition`
- optional `legacy_model_variant` only when needed for compatibility provenance

## Affected Surfaces

Updated:

- `RunConfig` serialization and deserialization
- `RunResult` compatibility deserialization
- adapter translation from legacy tasks
- summary-row writers
- coarse-scan manifest payloads
- per-config normalized `result.json`

Relevant code:

- [schema.py](file:///home/zhuguolong/aoup_model/src/configs/schema.py)
- [legacy_simcore_adapter.py](file:///home/zhuguolong/aoup_model/src/adapters/legacy_simcore_adapter.py)
- [workflow_schema.py](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py)
- [run_reference_scales.py](file:///home/zhuguolong/aoup_model/src/runners/run_reference_scales.py)
- [run_benchmark_mini_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_benchmark_mini_scan.py)
- [run_coarse_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan.py)

## Guidance For Downstream Scripts

### Aggregation

Use:

- `model_variant` for ablation grouping
- `flow_condition` for flow semantics grouping
- `U` for the numerical control value

Do not infer branch identity from `U == 0`.

### Plotting

Recommended:

- color or facet by `model_variant`
- annotate or subset by `flow_condition`

Examples:

- compare `full` vs `no_memory` vs `no_feedback`
- separately compare `zero_flow` vs `explicit_no_flow_control` inside the `full` branch

### Legacy compatibility

If a script reads older persisted payloads, normalize first using the compatibility layer in:

- [normalize_model_variant_payload](file:///home/zhuguolong/aoup_model/src/configs/schema.py)
- [normalize_persisted_artifact_payload](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py)

## Validation

Compatibility coverage includes:

- old payload with `model_variant = "no_flow"`
- new payload with explicit `flow_condition`
- normalized persisted-row compatibility helper

Relevant test:

- [test_model_variant_compatibility_reads_old_and_new_payloads](file:///home/zhuguolong/aoup_model/tests/test_adapter_schema.py)
