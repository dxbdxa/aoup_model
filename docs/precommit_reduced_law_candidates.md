# Precommit Reduced Law Candidates

## Scope

This note converts the current pre-commit gate theory into an explicit falsifiable law package. The law is intentionally strict: it stops at `gate_commit` and does not claim post-commit completion or final crossing kinetics.

- intervention dataset: [point_summary.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/point_summary.csv)
- intervention ordering: [metric_ordering.csv](file:///home/zhuguolong/aoup_model/outputs/datasets/intervention_dataset/metric_ordering.csv)
- precommit fit report: [precommit_gate_theory_fit_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_fit_report.md)
- gate-theory principle: [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- general principle note: [general_principle_candidates.md](file:///home/zhuguolong/aoup_model/docs/general_principle_candidates.md)
- validation figure: [prediction_vs_validation.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/prediction_vs_validation.png)
- scope-map figure: [reduced_law_scope_map.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/reduced_law_scope_map.png)

## Reduced Pre-Commit Variables

The reduced law uses only the currently supported pre-commit observables:

- `T_commit = first_gate_commit_delay`
- `T_wall = wall_dwell_before_first_commit`
- `A_pre = residence_given_approach`
- `C_pre = commit_given_residence`
- `S_pre = trap_burden_mean`

Mechanism reading from the existing fitted rate model:

- `wall_sliding -> gate_approach` and `gate_approach -> gate_residence_precommit` encode arrival organization.
- `gate_residence_precommit -> gate_commit` is comparatively stable and should not be treated as the leading control-sensitive knob.
- trap entry remains too sparse for a smooth kinetic law and should be retained only as a stale-flag variable.

| canonical_label            | src                      | dst                      |   rate_estimate |
|:---------------------------|:-------------------------|:-------------------------|----------------:|
| OP_SUCCESS_TIP             | wall_sliding             | gate_approach            |         4.12772 |
| OP_SUCCESS_TIP             | gate_approach            | gate_residence_precommit |        40.467   |
| OP_SUCCESS_TIP             | gate_residence_precommit | gate_commit              |        29.7258  |
| OP_EFFICIENCY_TIP          | wall_sliding             | gate_approach            |         3.85266 |
| OP_EFFICIENCY_TIP          | gate_approach            | gate_residence_precommit |        45.2592  |
| OP_EFFICIENCY_TIP          | gate_residence_precommit | gate_commit              |        33.891   |
| OP_SPEED_TIP               | wall_sliding             | gate_approach            |         5.3105  |
| OP_SPEED_TIP               | gate_approach            | gate_residence_precommit |        49.2453  |
| OP_SPEED_TIP               | gate_residence_precommit | gate_commit              |        33.263   |
| OP_BALANCED_RIDGE_MID      | wall_sliding             | gate_approach            |         4.68973 |
| OP_BALANCED_RIDGE_MID      | gate_approach            | gate_residence_precommit |        47.279   |
| OP_BALANCED_RIDGE_MID      | gate_residence_precommit | gate_commit              |        33.1264  |
| OP_STALE_CONTROL_OFF_RIDGE | wall_sliding             | gate_approach            |         4.20972 |
| OP_STALE_CONTROL_OFF_RIDGE | gate_approach            | gate_residence_precommit |        46.9884  |
| OP_STALE_CONTROL_OFF_RIDGE | gate_residence_precommit | gate_commit              |        33.5421  |

## Explicit Reduced-Law Predictions

### P1: Delay Acts First On Timing

Law statement: Around the productive ridge midpoint, delay enters first through the pre-commit timing budget: off-center delay perturbations should lengthen `first_gate_commit_delay` and `wall_dwell_before_first_commit` before they materially change `commit_given_residence`.

Operational prediction: On the delay slice, the balanced ridge midpoint should minimize the timing observables, `commit_given_residence` should stay subleading, and trap burden should appear only at the stale edge.

Current validation status: `supported` with score `1.00`.

### P2: Flow Orders The Timing Budget

Law statement: Increasing flow should monotonically compress the pre-commit timing budget and modestly improve approach-to-residence organization, while leaving `commit_given_residence` approximately invariant.

Operational prediction: On the flow slice, both timing observables should decrease monotonically, `residence_given_approach` should increase, and `commit_given_residence` should remain flat.

Current validation status: `supported` with score `1.00`.

### P3: Memory Acts First On Arrival Organization

Law statement: Within the productive memory band, memory should act more cleanly on the `gate_approach -> gate_residence_precommit` part of the backbone than on timing or final pre-commit conversion.

Operational prediction: On the memory slice, `residence_given_approach` should vary more coherently than either timing metric or `commit_given_residence`, even if the full slice is not perfectly monotone.

Current validation status: `supported` with score `1.00`.

### P4: Commit Conversion Is A Late Correlate

Law statement: `commit_given_residence` is not the leading control knob of the local ridge. Its control sensitivity should remain subleading compared with timing and approach organization.

Operational prediction: Across all intervention slices, `commit_given_residence` should never rank as a leading early-indicator variable.

Current validation status: `supported` with score `1.00`.

### P5: Trap Burden Is A Punctate Stale Flag

Law statement: `trap_burden_mean` should be treated as a weak or punctate stale flag, not as a smooth reduced-law coordinate. It should remain near zero on productive local ridge points and turn on only at stale edge points or intermittently.

Operational prediction: Trap burden should be absent on most productive delay and flow points, appear at the high-delay stale point, and remain mixed rather than monotone on the memory slice.

Current validation status: `supported` with score `1.00`.

## Which control parameter acts on which part of the backbone first?

| control_parameter   | timing_budget     | approach_to_residence   | residence_to_commit   | trap_burden         |
|:--------------------|:------------------|:------------------------|:----------------------|:--------------------|
| Pi_f                | first / strong    | secondary               | late / flat           | punctate stale edge |
| Pi_m                | weak / mixed      | first / cleanest        | late / flat           | intermittent flag   |
| Pi_U                | first / strongest | secondary increasing    | late / flat           | weak / punctate     |

Interpretation:

- `Pi_f` and `Pi_U` act first on the timing budget.
- `Pi_m` acts first on approach-to-residence organization.
- `commit_given_residence` is a late correlate rather than the main control-sensitive branch.
- `trap_burden_mean` is a stale-edge flag, not a smooth backbone coordinate.

## Observable Roles

| metric_name                    | classification              |   mean_early_indicator_score |   mean_monotonicity_score | reason                                                                      |
|:-------------------------------|:----------------------------|-----------------------------:|--------------------------:|:----------------------------------------------------------------------------|
| wall_dwell_before_first_commit | early_indicator             |                   0.0668827  |                  0.554365 | Dominant pre-commit timing discriminator.                                   |
| first_gate_commit_delay        | early_indicator             |                   0.0601099  |                  0.554365 | Dominant pre-commit timing discriminator.                                   |
| residence_given_approach       | early_indicator             |                   0.0129009  |                  0.73254  | Cleaner secondary early signal, especially on memory and flow slices.       |
| commit_given_residence         | late_correlate              |                   0.00139989 |                  0.269841 | Cross-slice response stays small and comparatively flat.                    |
| trap_burden_mean               | weak_or_punctate_stale_flag |                   0.0646863  |                  0.431265 | Appears mainly at stale edges or intermittently, with mixed directionality. |

## Minimal Reduced-Law Statement For Results

A manuscript-strength reduced-law statement supported now is:

> Locally around the productive ridge, delay and flow act first on the pre-commit timing budget, memory acts first on approach-to-residence organization, residence-to-commit conversion is approximately invariant to first order, and trap burden is only a punctate stale flag. The productive ridge is therefore selected before crossing by a timing-and-arrival backbone rather than by post-commit completion physics.

## What would falsify the pre-commit law?

- If `commit_given_residence` became the strongest early responder on any local control slice.
- If changing `Pi_f` or `Pi_U` did not move the timing budget before other mechanism observables.
- If memory acted first on `commit_given_residence` rather than on `residence_given_approach`.
- If trap burden became a smooth dominant ridge coordinate rather than a punctate stale flag.
- If explaining the local ridge slices required post-commit completion physics before the pre-commit observables separated.

## Scope Limits

- The law stops at `gate_commit`.
- It does not claim a crossing-completion law.
- It does not claim a smooth kinetic trap law.
- It should not be used as a full efficiency law, because efficiency still mixes in downstream transport costs.
