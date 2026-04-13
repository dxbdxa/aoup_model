# Efficiency Metric Upgrade

## Scope

This note defines a compact upgraded family of transport-efficiency quantities beyond `eta_sigma`, tests them on the confirmatory scan, and asks whether the productive-memory ridge remains Pareto-like under better-separated cost accounting.

Primary inputs:

- [thermodynamic_bookkeeping.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_bookkeeping.md)
- [eta_sigma_interpretation_note.md](file:///home/zhuguolong/aoup_model/docs/eta_sigma_interpretation_note.md)
- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [geometry_transfer_principle_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_principle_note.md)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [trajectory_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined/trajectory_level.parquet)
- [efficiency_metric_comparison.csv](file:///home/zhuguolong/aoup_model/outputs/tables/efficiency_metric_comparison.csv)
- [metric_comparison.png](file:///home/zhuguolong/aoup_model/outputs/figures/thermodynamics/metric_comparison.png)

The goal is not to produce a full thermodynamic completion law. It is to see whether a small and interpretable metric family changes the ridge picture qualitatively.

## Compact Metric Family

The recommended family is intentionally small.

### Directly computed quantities

| metric_name         | formula                                    | purpose                             | cost_channels                                       |
|:--------------------|:-------------------------------------------|:------------------------------------|:----------------------------------------------------|
| eta_sigma           | (Psucc_mean / Tmax) / Sigma_drag_mean      | screening                           | transport proxy + drag dissipation proxy            |
| eta_completion_drag | (Psucc_mean / MFPT_mean) / Sigma_drag_mean | manuscript_thermodynamic_discussion | successful completion rate + drag dissipation proxy |

Interpretation:

- `eta_sigma` remains the baseline drag-normalized screening metric
- `eta_completion_drag` upgrades the numerator from success-per-budget-window to success-per-completion-time, while keeping the same drag proxy in the denominator

### Proxy quantity

| metric_name   | formula                                           | purpose                  | cost_channels                                                               |
|:--------------|:--------------------------------------------------|:-------------------------|:----------------------------------------------------------------------------|
| eta_trap_drag | eta_completion_drag / (1 + trap_time_mean / Tmax) | mechanism_interpretation | successful completion rate + drag dissipation proxy + trap-time waste proxy |

Interpretation:

- `eta_trap_drag` adds one explicit stale-burden penalty using `trap_time_mean / Tmax`
- this is the cleanest current pre-commit waste proxy available on the full confirmatory scan

### Aspirational future quantity

| metric_name      | formula                                                                                        | purpose                              | cost_channels           |
|:-----------------|:-----------------------------------------------------------------------------------------------|:-------------------------------------|:------------------------|
| eta_total_future | productive output / (drag + propulsion + controller + memory + information + completion costs) | future_full_thermodynamic_discussion | future full bookkeeping |

Interpretation:

- `eta_total_future` is the placeholder for a later full bookkeeping quantity
- it is intentionally not computed now because active propulsion work, controller work, information/update costs, and post-commit completion costs are not yet separated

## Why trap burden is the preferred proxy upgrade

The refined mechanism dataset suggests that raw wall contact should not be penalized as if it were always waste.

Canonical mechanism means:

| canonical_label            |   trap_time_total |   boundary_contact_fraction_i |   wall_dwell_before_first_commit |   first_gate_commit_delay |   Sigma_drag_i |
|:---------------------------|------------------:|------------------------------:|---------------------------------:|--------------------------:|---------------:|
| OP_BALANCED_RIDGE_MID      |       0           |                      0.423615 |                         0.502555 |                   1.66767 |        476.904 |
| OP_EFFICIENCY_TIP          |       0           |                      0.427607 |                         0.602276 |                   1.94096 |        478.231 |
| OP_SPEED_TIP               |       0           |                      0.441886 |                         0.40057  |                   1.375   |        589.994 |
| OP_STALE_CONTROL_OFF_RIDGE |       0.000249634 |                      0.42951  |                         0.525013 |                   1.73561 |        499.963 |
| OP_SUCCESS_TIP             |       6.2561e-05  |                      0.42262  |                         0.869471 |                   2.83263 |        604.211 |

This matters because:

- the speed tip has higher wall-contact fraction than the efficiency tip (`0.442` vs `0.428`), yet both remain essentially trap-free
- wall-guided motion can therefore be productive, not merely dissipative waste
- trap burden is the cleaner current full-scan penalty because it tracks stale loss more directly than generic wall contact does

## What changes under the upgraded metrics?

Baseline `eta_sigma`:

- winner stays on the moderate-flow efficiency ridge family, with raw maximum at `(Pi_m, Pi_f, Pi_U) = (0.200, 0.020, 0.200)`
- top-10 overlap remains zero with both success and speed fronts

Completion-aware `eta_completion_drag`:

- winner moves to `(Pi_m, Pi_f, Pi_U) = (0.100, 0.018, 0.300)`
- this coincides with the speed tip at `(Pi_m, Pi_f, Pi_U) = (0.100, 0.018, 0.300)`
- the completion-aware upgrade therefore shifts the efficiency emphasis toward the high-flow fast-completion branch

Trap-aware `eta_trap_drag`:

- winner remains at the same high-flow point as `eta_completion_drag`
- the trap penalty is weak on the competitive ridge, so this proxy mainly refines interpretation rather than moving the optimum
- the near-identity of the two upgraded metrics is consistent with the current ridge carrying low trap burden over its leading branches

Spearman rank comparison:

- `eta_completion_drag` vs `eta_sigma`: `-0.077`
- `eta_trap_drag` vs `eta_sigma`: `-0.092`

So the thermodynamic upgrade is not trivial. It meaningfully changes which branch looks best, even though it does not destroy the ridge itself.

## Does the Pareto-like ridge survive the thermodynamic upgrade?

Yes. The ridge remains Pareto-like under the upgraded metrics.

Evidence:

- `eta_sigma` gives a non-dominated set of `18` points
- `eta_completion_drag` gives a non-dominated set of `18` points
- `eta_trap_drag` gives a non-dominated set of `20` points
- in every computed case, the non-dominated set stays pinned to `Pi_f` in `[0.018, 0.025]`
- the success front and upgraded-efficiency fronts remain largely distinct at top-10 depth

What changes is not the existence of the ridge, but the preferred branch along it:

- baseline `eta_sigma` favors a moderate-flow efficiency family
- completion-aware drag efficiency favors the high-flow fast-completion branch
- trap-aware drag efficiency leaves that branch choice essentially unchanged

So the thermodynamic upgrade changes the front ordering along the ridge more than it changes the ridge geometry itself.

## Which metric should be used in the manuscript, and for what purpose?

Recommended usage:

- use `eta_sigma` for screening, continuity with earlier figures, and broad ridge localization
- use `eta_completion_drag` for manuscript-level thermodynamic discussion, because it cleanly upgrades the numerator while staying inside directly computed quantities
- use `eta_trap_drag` for mechanism interpretation, because it asks whether pre-commit stale burden changes the thermodynamic ranking
- reserve `eta_total_future` for later thermodynamic closure once missing channels are explicitly computed

Practical reading:

- `eta_sigma` answers: which points are good transport-per-drag screeners?
- `eta_completion_drag` answers: which points convert drag spending into successful completed transport most efficiently?
- `eta_trap_drag` answers: does the answer change once stale pre-commit loss is penalized?

Current manuscript recommendation:

- main screening metric: `eta_sigma`
- main upgraded thermodynamic metric: `eta_completion_drag`
- supporting mechanism metric: `eta_trap_drag`

## Bottom Line

The upgraded metric family remains compact and interpretable:

- one directly computed baseline metric
- one directly computed completion-aware upgrade
- one proxy trap-aware refinement
- one aspirational future full-efficiency placeholder

The Pareto-like ridge survives the thermodynamic upgrade, but the preferred efficient branch shifts toward the high-flow speed tip once completion rate is separated more cleanly from the old `eta_sigma` numerator.
