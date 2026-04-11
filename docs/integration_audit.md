# Integration Audit

## Scope

Audit target: current legacy-adapter integration after workflow injection work.

Checked only:

1. all workflow runners call the legacy adapter consistently
2. `RunConfig` and `RunResult` fields are fully propagated
3. output paths follow the workflow schema
4. metadata, seed, `config_hash`, and `model_variant` are preserved
5. missing links and silent schema mismatches

Files inspected:

- `src/configs/schema.py`
- `src/adapters/legacy_simcore_adapter.py`
- `src/adapters/catalog_bridge.py`
- `src/runners/run_reference_scales.py`
- `src/runners/run_benchmark_mini_scan.py`
- `src/runners/run_coarse_scan.py`
- `docs/trae_active_transport_workflow.md`
- `docs/migration_map.md`

Constraint applied throughout this audit: no legacy physics changes.

## Executive Verdict

Current status: **partially integrated**.

What is already correct:

- reference-scale extraction and benchmark mini-scan both execute through `LegacySimcoreAdapter`
- coarse scan task generation emits `RunConfig` / `SweepTask` objects that are adapter-compatible
- `seed`, `geometry_id`, and `model_variant` are usually preserved inside in-memory config objects
- baseline regression coverage exists for direct legacy vs adapter point execution

What is not yet complete:

- workflow output locations do not yet match the documented workflow schema
- several required workflow fields are not propagated into persisted scan outputs
- `config_hash` is not serialized into coarse-scan manifests
- `raw_summary_path` is never populated in the current workflow runners

## Findings

### Blocking

#### 1. Persisted output paths do not follow the workflow schema

Workflow spec requires structured outputs such as:

- `outputs/runs/{phase}/{geometry_id}/{config_hash}/result.json`
- `outputs/summaries/{phase}/summary.parquet`
- `outputs/logs/{phase}/{task_id}.log`

Current implementation diverges:

- `run_reference_scales.py` writes to `outputs/reference/` and emits `baseline_transition_stats.csv` plus optional parquet
- `run_benchmark_mini_scan.py` writes only `outputs/summaries/benchmark_mini_scan/summary.csv` and `metadata.json`
- `run_coarse_scan.py` writes `outputs/runs/coarse_scan/task_manifest.json`

Impact:

- downstream tooling cannot rely on the documented path contract
- workflow stages are not yet interchangeable with the schema described in `docs/migration_map.md` and `docs/trae_active_transport_workflow.md`

Relevant code:

- [run_reference_scales.py](file:///home/zhuguolong/aoup_model/src/runners/run_reference_scales.py#L75-L126)
- [run_benchmark_mini_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_benchmark_mini_scan.py#L83-L123)
- [run_coarse_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan.py#L130-L144)
- [migration_map.md](file:///home/zhuguolong/aoup_model/docs/migration_map.md#L403-L429)
- [trae_active_transport_workflow.md](file:///home/zhuguolong/aoup_model/docs/trae_active_transport_workflow.md#L404-L491)

#### 2. Workflow outputs do not fully propagate required schema fields

The workflow doc requires trajectory-level and state-point-level records to contain fields such as:

- per-trajectory: `state_point_id`, `seed`, `termination_reason`, `trap_count`, `scan_id`, and other observables
- state-point aggregate: dimensional back-mapped parameters, `Psucc_mean`, `MFPT_median`, `FPT_q90`, `J_proxy`, `eta_sigma_mean`, status fields, provenance fields

Current integration only propagates a subset:

- reference-scale transition output adds `success`, `fpt`, `wall_fraction`, `drag_dissipation`, `scan_id`, `geometry_id`, `model_variant`
- benchmark mini-scan summary adds only a few config echoes (`seed`, `tau_v`, `tau_f`, `U`, `Dr`, `v0`) on top of `RunResult`
- coarse scan manifest stores raw `RunConfig.to_dict()` objects but does not define workflow `state_point_id` or shard identifiers

Impact:

- current runner outputs are not yet schema-complete enough for the later aggregation / analysis stages described in the workflow document

Relevant code:

- [run_reference_scales.py](file:///home/zhuguolong/aoup_model/src/runners/run_reference_scales.py#L89-L122)
- [run_benchmark_mini_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_benchmark_mini_scan.py#L96-L123)
- [run_coarse_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan.py#L99-L144)
- [trae_active_transport_workflow.md](file:///home/zhuguolong/aoup_model/docs/trae_active_transport_workflow.md#L406-L491)

#### 3. `config_hash` is not preserved into coarse-scan task manifests

`RunConfig` exposes a computed `config_hash`, but `RunConfig.to_dict()` does not include it. `SweepTask.to_dict()` serializes `config_list` via `RunConfig.to_dict()`, so `write_coarse_scan_manifest()` emits configs without serialized hashes.

Impact:

- downstream run directories cannot be deterministically mapped to the documented `{config_hash}` path scheme
- task manifests lose a stable identifier that the workflow contract expects

Relevant code:

- [schema.py](file:///home/zhuguolong/aoup_model/src/configs/schema.py#L13-L49)
- [schema.py](file:///home/zhuguolong/aoup_model/src/configs/schema.py#L78-L93)
- [run_coarse_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_coarse_scan.py#L130-L144)

#### 4. `raw_summary_path` is never populated by the workflow runners

`RunResult` includes `raw_summary_path`, but current workflow runners use `adapter.run_point()` or `adapter.run_config()`, both of which avoid the task-level artifact writer path. As a result, `raw_summary_path` stays `None` in all runner-produced results.

Impact:

- one of the documented `RunResult` provenance fields is silently absent in practice
- later tooling cannot trace a normalized result back to a persisted raw summary artifact

Relevant code:

- [legacy_simcore_adapter.py](file:///home/zhuguolong/aoup_model/src/adapters/legacy_simcore_adapter.py#L150-L212)
- [schema.py](file:///home/zhuguolong/aoup_model/src/configs/schema.py#L52-L75)

### Important But Not Blocking

#### 5. Workflow runners use the adapter consistently for execution, but not consistently for artifact generation

- `run_reference_scales.py` and `run_benchmark_mini_scan.py` both call `LegacySimcoreAdapter`
- `run_coarse_scan.py` is generation-only, so it does not execute the adapter
- none of the workflow runners use `LegacySimcoreAdapter.run_task()`, so none of them inherit task-level manifest or artifact writing from legacy

This is internally consistent for execution, but inconsistent for persistence and provenance.

Relevant code:

- [legacy_simcore_adapter.py](file:///home/zhuguolong/aoup_model/src/adapters/legacy_simcore_adapter.py#L142-L212)
- [run_reference_scales.py](file:///home/zhuguolong/aoup_model/src/runners/run_reference_scales.py#L84-L87)
- [run_benchmark_mini_scan.py](file:///home/zhuguolong/aoup_model/src/runners/run_benchmark_mini_scan.py#L96-L107)

#### 6. `model_variant` semantics are overloaded and can hide intended branch identity

Current logic encodes both ablation identity and the `U == 0` condition into `model_variant`. That makes `no_flow` both a model label and a state condition. This works for current cases but is semantically narrower than the workflow doc, where `model_variant` is primarily an ablation branch and flow is a separate control parameter.

Impact:

- branch identity can become ambiguous in manifests and summaries
- future scans may silently conflate `full` at `U = 0` with an explicit `no_flow` branch

Relevant code:

- [legacy_simcore_adapter.py](file:///home/zhuguolong/aoup_model/src/adapters/legacy_simcore_adapter.py#L21-L41)
- [migration_map.md](file:///home/zhuguolong/aoup_model/docs/migration_map.md#L217-L267)

### Good

#### 7. Core numerical delegation is preserved

- geometry construction still comes from legacy `MazeBuilder`
- navigation still comes from legacy `NavigationSolver`
- point stepping still comes from legacy `PointSimulator`
- regression tests already confirm direct legacy and adapter point execution agree on baseline cases

Relevant code:

- [legacy_simcore_adapter.py](file:///home/zhuguolong/aoup_model/src/adapters/legacy_simcore_adapter.py#L77-L148)
- [test_legacy_regression.py](file:///home/zhuguolong/aoup_model/tests/test_legacy_regression.py#L170-L216)

## Checklist Answers

### 1. Do all workflow runners call the legacy adapter consistently?

Partially yes.

- `run_reference_scales.py`: yes, through `LegacySimcoreAdapter.run_point()`
- `run_benchmark_mini_scan.py`: yes, through `LegacySimcoreAdapter.run_config()`
- `run_coarse_scan.py`: not applicable for execution; it only generates tasks

Consistency gap:

- runners do not consistently use the same adapter surface for persistence and provenance

### 2. Are `RunConfig` and `RunResult` fields fully propagated?

No.

Preserved in-memory:

- `RunConfig`: mostly preserved inside runner-built config objects
- `RunResult`: primary summary metrics, `seed`, `config_hash`, and `model_variant` are available in memory

Not fully propagated to persisted workflow artifacts:

- `config_hash` missing from coarse-scan manifest payload
- `raw_summary_path` never filled
- many workflow-required per-trajectory and aggregate fields are absent from current persisted outputs

### 3. Do output paths follow the workflow schema?

No.

Current outputs are functional but do not yet match the documented schema directories or filenames.

### 4. Are metadata, seed, `config_hash`, and `model_variant` preserved?

Partially.

- `seed`: preserved in `RunConfig`; explicitly copied into benchmark mini-scan summary rows
- `model_variant`: preserved in configs and results
- `config_hash`: present in `RunResult`, absent from serialized coarse task configs
- metadata: partially preserved, but workflow provenance fields such as upstream reference-scales link, random seed policy, and config path are not yet carried through consistently

### 5. Missing links or silent schema mismatches

Missing links:

- no link from benchmark/coarse outputs back to `reference_scales.json`
- no log path generation matching workflow docs
- no shard/state-point identifiers matching the decomposition described in the workflow doc

Silent mismatches:

- `raw_summary_path` exists in schema but is never populated
- `RunConfig` computes `config_hash`, but serialized task payloads omit it
- current outputs use ad hoc directories rather than the documented schema
- `model_variant` mixes ablation label and flow condition semantics

## Blocking Todo List

- Align runner output directories and filenames with the documented workflow schema.
- Serialize `config_hash` into coarse-scan manifests and any persisted config payload.
- Populate `raw_summary_path` or remove the silent assumption that it exists.
- Add the missing required workflow fields and provenance links to persisted reference/mini/coarse outputs.
