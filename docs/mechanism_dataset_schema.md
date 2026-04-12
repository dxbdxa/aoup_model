# Mechanism Dataset Schema

## Scope

This note defines the schema for a gate-conditioned mechanism dataset built on top of the frozen canonical operating points.

Purpose:

- discriminate mechanisms across the canonical ridge and off-ridge points
- support later coarse-grained gate theory
- remain portable to geometry-transfer and thermodynamic analysis

This document does **not** implement the extraction pipeline. It only defines the event vocabulary, table structure, measurement rules, and compatibility constraints.

Primary inputs:

- [canonical_operating_points.md](file:///home/zhuguolong/aoup_model/docs/canonical_operating_points.md)
- [theory_compression_note.md](file:///home/zhuguolong/aoup_model/docs/theory_compression_note.md)
- [physics_storyline_v1.md](file:///home/zhuguolong/aoup_model/docs/physics_storyline_v1.md)
- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [workflow_schema.py](file:///home/zhuguolong/aoup_model/src/utils/workflow_schema.py)
- [mechanism_dataset_spec.py](file:///home/zhuguolong/aoup_model/src/analysis/mechanism_dataset_spec.py)

## Design Principles

- use the frozen canonical operating points as the default mechanism-analysis set
- preserve compatibility with existing workflow outputs and per-state `result.json` bundles
- keep the schema minimal enough to extract robustly from the current simulator wrapper
- prioritize observables that can later support transition-rate or coarse-grained gate models
- separate required fields from optional nice-to-have fields

## Canonical Scope

The default mechanism-analysis set is:

- `OP_SUCCESS_TIP`
- `OP_EFFICIENCY_TIP`
- `OP_SPEED_TIP`
- `OP_BALANCED_RIDGE_MID`
- `OP_STALE_CONTROL_OFF_RIDGE`

Each record in the mechanism dataset must carry:

- `canonical_label`
- `state_point_id`
- `scan_id`
- `geometry_id`
- `model_variant`
- `analysis_source`
- `analysis_n_traj`
- `Pi_m`, `Pi_f`, `Pi_U`
- `tau_g`, `l_g`
- `result_json`

This makes the mechanism tables directly joinable to the existing workflow summaries and to the frozen canonical table.

## Event Vocabulary

The mechanism dataset uses the following event classes.

### `bulk_motion`

- motion away from walls and outside any gate-neighborhood
- interpret as the coarse-grained search state

### `wall_sliding`

- boundary-contact motion with strong tangential wall alignment
- interpret as the wall-guided search state prior to gate commitment

### `gate_approach`

- entry into a gate-local neighborhood with positive gate-oriented progress
- interpret as the pre-capture gate-search state

### `gate_capture`

- residence inside a gate-local capture basin before the trajectory either crosses or returns
- interpret as the gate-commitment state

### `gate_crossing`

- successful transit across the gate threshold
- interpret as the absorbing success event for gate-level rate models

### `trap_episode`

- extended low-progress residence with repeated ineffective motion
- may occur near a wall, at a gate mouth, or in a locally stale-control state
- interpret as the mechanism-level failure or delay state

### `trap_escape`

- explicit transition out of a trap episode back into bulk motion, wall sliding, or gate approach
- interpret as the recovery event needed for loop-like coarse-grained models

## Table Structure

The mechanism dataset is minimal but split into three linked tables.

### 1. Trajectory-level records

One row per trajectory within a canonical operating point.

Role:

- preserve the top-level success/failure outcome
- accumulate time budgets over coarse mechanism states
- provide trajectory totals needed for survival analysis and thermodynamic comparisons

Primary key:

- `canonical_label`
- `state_point_id`
- `traj_id`

### 2. Event-level records

One row per classified event episode.

Role:

- support transition counting
- support episode-duration statistics
- expose the event-level structure required for fitting coarse-grained gate models

Primary key:

- `canonical_label`
- `state_point_id`
- `traj_id`
- `event_index`

### 3. Gate-conditioned records

One row per canonical operating point and gate.

Role:

- summarize gate-local approach, capture, crossing, and return statistics
- support gate-conditioned rate-model building without replaying the full event table every time

Primary key:

- `canonical_label`
- `state_point_id`
- `gate_id`

## Minimum Required Observables

### Trajectory-level required fields

The minimum required fields are:

- identity and provenance:
  - `canonical_label`
  - `state_point_id`
  - `traj_id`
  - `scan_id`
  - `geometry_id`
  - `result_json`
- top-level outcome:
  - `success_flag`
  - `t_stop`
  - `t_exit_or_nan`
- existing wrapper-compatible wall metric:
  - `boundary_contact_fraction_i`
- mechanism time budgets:
  - `bulk_time_total`
  - `wall_sliding_time_total`
  - `trap_time_total`
- event counts:
  - `n_gate_approach_events`
  - `n_gate_capture_events`
  - `n_gate_crossing_events`
  - `n_trap_events`
- alignment and lag summaries:
  - `phase_lag_navigation_mean`
  - `phase_lag_steering_mean`
  - `alignment_gate_mean`
  - `alignment_wall_mean`
- progress summary:
  - `progress_along_navigation_total`
  - `progress_along_navigation_rate`

### Event-level required fields

The minimum required event fields are:

- event identity:
  - `event_id`
  - `traj_id`
  - `event_index`
  - `event_type`
- event timing:
  - `t_start`
  - `t_end`
  - `duration`
- event context:
  - `gate_id`
  - `entered_from_event_type`
  - `exited_to_event_type`
- event observables:
  - `progress_along_navigation`
  - `progress_along_navigation_rate`
  - `phase_lag_navigation_mean`
  - `phase_lag_steering_mean`
  - `alignment_gate_mean`
  - `alignment_wall_mean`
  - `capture_success_flag`

### Gate-conditioned required fields

The minimum required gate-conditioned fields are:

- gate identity:
  - `gate_id`
- event counts:
  - `n_gate_approach`
  - `n_gate_capture`
  - `n_gate_crossing`
- empirical transition probabilities:
  - `capture_given_approach`
  - `crossing_given_capture`
  - `return_to_wall_after_capture_rate`
- gate-local timing:
  - `mean_approach_duration`
  - `mean_capture_duration`
  - `mean_crossing_duration`
- gate-local mechanism summaries:
  - `alignment_at_gate_mean`
  - `phase_lag_navigation_at_gate_mean`
  - `phase_lag_steering_at_gate_mean`
  - `progress_rate_at_gate_mean`

## Which observables are essential, and which are optional?

Essential observables are the ones needed for later coarse-grained gate theory, operating-point discrimination, or portable principle-building.

Essential:

- event counts and event durations
- gate-local approach, capture, and crossing probabilities
- trap time and trap count
- progress along the navigation field
- phase lag relative to the navigation field
- phase lag relative to the steering direction
- alignment at gate
- alignment on wall
- event transition context:
  - entered-from state
  - exited-to state

Optional nice-to-have fields are useful for debugging, visualization, or richer later stories, but are not required to fit a first rate model.

Optional:

- event start/end coordinates
- mean wall distance
- mean gate distance
- mean speed within an event
- gate center coordinates
- gate-approach angle
- capture depth
- serialized gate-visit sequence
- largest trap duration

Rule of thumb:

- if a field is needed to infer rates, occupancies, transition probabilities, or lags, it is essential
- if a field is mainly useful for plotting or diagnosis, it is optional

## How the key measurements are defined

### Phase lag relative to the navigation field

Define the local navigation direction by

- `d_nav = -grad(psi) / ||grad(psi)||`

where `psi` is the navigation potential or navigation field used by the simulator.

The instantaneous navigation lag is the signed angular difference between:

- the motion heading or velocity direction
- `d_nav`

Stored observables:

- event-level circular mean lag
- trajectory-level circular mean lag
- gate-conditioned mean lag during gate-local events

### Phase lag relative to the control / steering direction

Define the steering reference as the actual control direction supplied to the delayed feedback law at that instant.

This is intentionally **not** always the same as the instantaneous navigation direction.

The instantaneous steering lag is the signed angular difference between:

- the motion heading or velocity direction
- the controller steering direction

This quantity is essential because the stale-control point is expected to separate from ridge points primarily through this mismatch.

### Alignment at gate

Alignment at gate is the cosine alignment between the motion heading and the gate-forward direction, evaluated only during:

- `gate_approach`
- `gate_capture`
- `gate_crossing`

This is required because coarse-grained gate theory needs a gate-local commitment variable, not just a global alignment metric.

### Alignment on wall

Alignment on wall is the cosine alignment between the motion heading and the local wall tangent, evaluated only during:

- `wall_sliding`
- `trap_episode`

This is required because wall-guided search and stale trapping need to be distinguished from free bulk search.

### Progress along the navigation field

Define instantaneous progress by

- `v . d_nav`

where `v` is the instantaneous velocity and `d_nav` is the local navigation direction.

Stored observables:

- event integral of progress
- event progress rate
- trajectory total progress
- trajectory mean progress rate
- gate-conditioned mean progress rate

This quantity is essential because it allows the schema to distinguish:

- productive wall or gate motion
- low-progress trapping
- fast but poorly aligned transport

## Which observables are essential for later coarse-grained gate theory?

The minimum gate-theory-ready observable set is:

- `n_gate_approach`
- `n_gate_capture`
- `n_gate_crossing`
- `capture_given_approach`
- `crossing_given_capture`
- `mean_approach_duration`
- `mean_capture_duration`
- `mean_crossing_duration`
- `return_to_wall_after_capture_rate`
- `phase_lag_navigation_at_gate_mean`
- `phase_lag_steering_at_gate_mean`
- `alignment_at_gate_mean`
- `progress_rate_at_gate_mean`
- `wall_sliding_time_total`
- `trap_time_total`

Why this set is sufficient:

- it provides occupancy times
- it provides transition counts and empirical transition probabilities
- it provides gate-local timing
- it provides the minimal lag and alignment quantities needed to interpret stale steering

This is enough to fit a first reduced-state model with states such as:

- bulk
- wall sliding
- gate approach
- gate capture
- crossing
- trap

## How the schema distinguishes ridge points from the stale-control point

The schema is designed so that `OP_BALANCED_RIDGE_MID` and `OP_STALE_CONTROL_OFF_RIDGE` can be compared as a matched pair:

- same `Pi_m`
- same `Pi_U`
- different `Pi_f`

The key separating observables are therefore expected to be:

- `phase_lag_steering_mean`
- `phase_lag_steering_at_gate_mean`
- `return_to_wall_after_capture_rate`
- `capture_given_approach`
- `progress_rate_at_gate_mean`
- `trap_time_total`
- `alignment_wall_mean`

This matters because the stale-control point should not merely look "slower." It should look more misaligned, more trap-prone, and less likely to convert gate approach into successful capture and crossing.

## Compatibility With Existing Workflow Outputs

The schema is explicitly designed to remain compatible with the current workflow.

Already available or directly joinable:

- `state_point_id`
- `scan_id`
- `geometry_id`
- `model_variant`
- `flow_condition`
- `Pi_m`, `Pi_f`, `Pi_U`
- `analysis_source`
- `analysis_n_traj`
- `result_json`
- per-trajectory:
  - `success_flag`
  - `t_stop`
  - `t_exit_or_nan`
  - `Sigma_drag_i`
  - `boundary_contact_fraction_i`
- trap durations from the existing trap dataframe

Not yet persisted and therefore to be extracted later:

- event segmentation
- gate-local event counts
- navigation and steering phase lags
- gate and wall alignment observables
- navigation-progress integrals by event context

## Why the schema is minimal but sufficient

It is minimal because it avoids:

- full time-series storage as a required output
- dense raw position snapshots as mandatory fields
- geometry-specific fields that do not transfer across tasks

It is sufficient because it preserves exactly what the later rate-model and mechanism tasks need:

- state occupancy
- transition counts
- event durations
- gate-local conversion statistics
- lag and alignment observables that diagnose stale control

## Implementation Boundary

This document and [mechanism_dataset_spec.py](file:///home/zhuguolong/aoup_model/src/analysis/mechanism_dataset_spec.py) define the schema only.

They do not:

- modify the legacy physics kernel
- define extraction thresholds as immutable constants yet
- implement the event-classification pipeline
- write any new trajectory-processing code

Those steps should come later as a wrapper-side extraction layer on top of the already frozen canonical operating points.
