# Metric Robustness Report

## Scope

This note tests whether the productive ridge survives the current thermodynamic metric family, or whether it only appears under one screening definition.

- confirmatory summary: [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- canonical operating points: [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- existing metric upgrade note: [efficiency_metric_upgrade.md](file:///home/zhuguolong/aoup_model/docs/efficiency_metric_upgrade.md)
- bookkeeping note: [thermodynamic_bookkeeping.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_bookkeeping.md)
- geometry-transfer evidence: [geometry_transfer_evidence_table.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_evidence_table.md)
- robustness table: [metric_robustness_table.csv](file:///home/zhuguolong/aoup_model/outputs/tables/metric_robustness_table.csv)
- robustness figure: [metric_robustness_map.png](file:///home/zhuguolong/aoup_model/outputs/figures/thermodynamics/metric_robustness_map.png)

The tested metric family remains strictly inside current bookkeeping: `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag`.

## Compact Readout

- `eta_sigma` winner: moderate-flow ridge at `(0.200, 0.020, 0.200)`
- `eta_completion_drag` winner: high-flow speed at `(0.100, 0.018, 0.300)`
- `eta_trap_drag` winner: high-flow speed at `(0.100, 0.018, 0.300)`
- non-dominated counts: `eta_sigma = 18`, `eta_completion_drag = 18`, `eta_trap_drag = 20`
- Spearman vs `eta_sigma`: `eta_completion_drag = -0.077`, `eta_trap_drag = -0.092`
- branch-family rule: Branch labels use the same operating-family split already implicit in the current upgrade note: `Pi_U <= 0.12` for the low-flow success branch, `0.12 < Pi_U < 0.25` for the moderate-flow ridge branch, and `Pi_U >= 0.25` for the high-flow speed/completion branch.

## Ridge Survival Versus Branch-Preference Change

These two questions separate cleanly in the data.

Ridge survival:

- every computed metric retains a non-dominated ridge rather than collapsing to a single isolated optimum
- every non-dominated set stays pinned to the same narrow `Pi_f` strip `[0.018, 0.025]`
- the non-dominated branch mix remains three-way rather than degenerating to only one branch family

Branch-preference change:

- `eta_sigma` concentrates its top-10 entirely on the moderate-flow ridge branch
- `eta_completion_drag` shifts top-10 concentration to the high-flow speed/completion branch
- `eta_trap_drag` leaves that high-flow preference in place rather than restoring the old moderate-flow winner

So the ridge is robust to metric choice, but the preferred branch along the ridge is not metric-invariant.

## Which conclusions survive metric upgrade, and which only survive within one metric family?

### Invariant across the current metric family

| conclusion_name                                                            | eta_sigma_result                                                                                                    | eta_completion_drag_result                                                                                          | eta_trap_drag_result                                                                                                | interpretation                                                                                                 |
|:---------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------|
| Pareto-like ridge survives the metric upgrade                              | `18` points; `Pi_f in [0.018, 0.025]`; branches: low-flow success `3`, moderate-flow ridge `8`, high-flow speed `7` | `18` points; `Pi_f in [0.018, 0.025]`; branches: low-flow success `3`, moderate-flow ridge `8`, high-flow speed `7` | `20` points; `Pi_f in [0.018, 0.025]`; branches: low-flow success `3`, moderate-flow ridge `9`, high-flow speed `8` | The productive ridge persists under every computed metric rather than collapsing to one fragile proxy optimum. |
| Competitive ridge stays on the same narrow Pi_f strip                      | winner strip `Pi_U in [0.15, 0.20]`; `Pi_f` values `[0.018, 0.02, 0.022, 0.025]`                                    | winner strip `Pi_U in [0.20, 0.30]`; `Pi_f` values `[0.018, 0.02, 0.022, 0.025]`                                    | winner strip `Pi_U in [0.20, 0.30]`; `Pi_f` values `[0.018, 0.02, 0.022, 0.025]`                                    | Metric choice does not move the competitive set off the established productive-memory strip.                   |
| Success front stays distinct from thermodynamic winners                    | top-10 overlap with success `0`; with speed `0`                                                                     | top-10 overlap with success `0`; with speed `4`                                                                     | top-10 overlap with success `0`; with speed `5`                                                                     | The metric family does not convert the low-flow success tip into the thermodynamic winner.                     |
| Trap-aware refinement does not overturn the completion-aware branch choice | baseline screening branch differs from upgraded metrics                                                             | same winner `True`; top-20 overlap `18` of `20`                                                                     | same winner `True`; top-20 overlap `18` of `20`                                                                     | Adding the current stale-loss proxy sharpens interpretation but does not create a new leading branch.          |

### Shifted but still principle-consistent

| conclusion_name                                      | eta_sigma_result                                                    | eta_completion_drag_result                                         | eta_trap_drag_result                                               | interpretation                                                                                                                    |
|:-----------------------------------------------------|:--------------------------------------------------------------------|:-------------------------------------------------------------------|:-------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------|
| Winning branch changes under the upgraded numerator  | moderate-flow ridge at `(0.200, 0.020, 0.200)`                      | high-flow speed at `(0.100, 0.018, 0.300)`                         | high-flow speed at `(0.100, 0.018, 0.300)`                         | Metric upgrade reorders which branch is favored along the ridge without destroying the ridge itself.                              |
| Top-tier branch concentration changes across metrics | low-flow success `0`, moderate-flow ridge `10`, high-flow speed `0` | low-flow success `0`, moderate-flow ridge `2`, high-flow speed `8` | low-flow success `0`, moderate-flow ridge `2`, high-flow speed `8` | The top-ranked competitive set shifts from moderate-flow concentration to high-flow concentration under completion-aware metrics. |

Interpretation:

- what survives metric upgrade is the existence and location of the productive ridge
- what only survives within one metric family is the exact branch ordering along that ridge
- the upgraded metric family therefore strengthens the ridge claim, but it only refines branch choice rather than making it universal

## What still cannot be claimed as full thermodynamic closure?

| conclusion_name                                                                            | eta_sigma_result                                                        | eta_completion_drag_result                                              | eta_trap_drag_result                                                    | interpretation                                                                                                                                     |
|:-------------------------------------------------------------------------------------------|:------------------------------------------------------------------------|:------------------------------------------------------------------------|:------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------|
| Current metrics still use drag-centered bookkeeping rather than full thermodynamic closure | drag-normalized screening metric only                                   | completion-aware numerator, but drag-only denominator                   | adds stale-loss proxy, but still not total entropy production           | The present metric family upgrades discussion credibility, but it still does not close the missing energetic and informational channels.           |
| Full branch ordering under missing cost channels remains unresolved                        | cannot test missing propulsion/controller/information/post-commit costs | cannot test missing propulsion/controller/information/post-commit costs | cannot test missing propulsion/controller/information/post-commit costs | No current metric tests whether adding propulsion, controller, memory, information, or post-commit completion costs would reorder the ridge again. |

Missing closure channels that remain explicit:

- active-propulsion work is not separately booked
- controller or steering actuation work is not separately booked
- memory-bath dissipation is not separately booked
- information-rate or update-cost terms are not booked
- pre-commit and post-commit spending are not separated into a full energetic budget
- total entropy production is therefore not available

## Current Manuscript-Level Upgrade

The safest strengthened statement is:

> Within current bookkeeping, the productive ridge is robust to the tested metric family: `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag` all preserve the same narrow competitive ridge, even though the preferred branch shifts from the moderate-flow ridge family to the high-flow fast-completion branch under the stronger completion-aware metrics.

This strengthens the thermodynamic qualifier because the ridge is no longer tied to one screening proxy. At the same time, it keeps the scope limit visible: branch preference is metric-sensitive, and full thermodynamic closure is still not available.

## Evidence Summary

- invariant conclusions: `4`
- shifted but principle-consistent conclusions: `2`
- outside current bookkeeping: `2`

Canonical-rank check:

| canonical_label   |   eta_sigma_rank |   eta_completion_drag_rank |   eta_trap_drag_rank |
|:------------------|-----------------:|---------------------------:|---------------------:|
| success           |              102 |                        144 |                  144 |
| efficiency        |                3 |                         33 |                   30 |
| speed             |              123 |                          2 |                    2 |
| balanced          |                4 |                         19 |                   14 |
| stale             |               22 |                         54 |                   57 |
