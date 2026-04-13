# Extended Data Figure 6 Panel Manifest

## Scope

This note documents the panel logic for Extended Data Figure 6, which gives the detailed metric-family comparison and bookkeeping boundaries behind the main-text thermodynamic qualifier.

Primary data sources:

- [extended_data_plan.md](file:///home/zhuguolong/aoup_model/docs/extended_data_plan.md)
- [thermodynamic_bookkeeping.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_bookkeeping.md)
- [efficiency_metric_upgrade.md](file:///home/zhuguolong/aoup_model/docs/efficiency_metric_upgrade.md)
- [metric_robustness_report.md](file:///home/zhuguolong/aoup_model/docs/metric_robustness_report.md)
- [thermodynamic_results_summary_v2.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_results_summary_v2.md)
- [efficiency_metric_comparison.csv](file:///home/zhuguolong/aoup_model/outputs/tables/efficiency_metric_comparison.csv)
- [metric_robustness_table.csv](file:///home/zhuguolong/aoup_model/outputs/tables/metric_robustness_table.csv)
- [metric_robustness_map.png](file:///home/zhuguolong/aoup_model/outputs/figures/thermodynamics/metric_robustness_map.png)
- [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- [ED Figure 6 PNG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig6_thermodynamic_upgrade_detail.png)
- [ED Figure 6 SVG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig6_thermodynamic_upgrade_detail.svg)

## Figure-Level Message

- this figure exists to support the main-text thermodynamic qualifier with the full current metric family rather than a single screening metric
- the central message is ridge survival plus branch-preference shift under the stronger completion-aware metrics
- the bookkeeping remains drag-centered, so the figure strengthens robustness without implying full thermodynamic closure
- bookkeeping limits remain visible and compact rather than hidden in footnotes

## Panel Logic

### Panel A

- title: `Metric-family ridge comparison: eta_sigma, eta_completion_drag, eta_trap_drag`
- purpose: overlay the three non-dominated ridge sets and their winners to show ridge survival under metric choice
- quantitative note: non-dominated counts are `18`, `18`, and `20` for `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag`

### Panel B

- title: `Branch-preference reordering across metrics`
- purpose: show the top-tier concentration shift from the moderate-flow ridge branch to the high-flow branch
- quantitative note: top-10 counts move from `10` moderate-flow points under `eta_sigma` to `8` high-flow points under `eta_completion_drag`

### Panel C

- title: `Canonical-point rank comparison across metrics`
- purpose: show which canonical representatives move up or down when the metric numerator is upgraded
- quantitative note: the efficiency tip is rank `3` under `eta_sigma`, while the speed tip is rank `2` under `eta_completion_drag`

### Panel D

- title: `Non-dominated-set comparison across the metric family`
- purpose: compare set size and pairwise overlap for the current competitive ridge family
- quantitative note: the completion-aware and trap-aware sets share Jaccard `0.90` with overlap count `18`

### Panel E

- title: `Compact bookkeeping diagram showing what is included versus missing`
- purpose: show the current bookkeeping boundary at a glance
- quantitative note: explicit current bookkeeping contains one drag-centered cost channel plus the trap proxy refinement, while the remaining active, controller, memory, information, and completion channels stay outside the denominator

### Panel F

- title: `Explicit closure-limit panel summarizing which energetic or informational channels remain outside current bookkeeping`
- purpose: state clearly why the metric upgrade improves robustness but does not produce full closure
- quantitative note: robustness-table counts are invariant `4`, shifted-but-principle-consistent `2`, and outside-current-bookkeeping `2`

## Supported Now

- ridge survival is robust across the current metric family
- branch preference shifts from the moderate-flow ridge family to the high-flow fast-completion family under the stronger completion-aware metrics
- the trap-aware proxy keeps the same winner as `eta_completion_drag` and preserves strong top-20 agreement (`11` and `10` speed-front overlaps remain secondary to the same branch winner)

## Not Supported Now

- total entropy production
- full energetic efficiency
- a branch winner guaranteed to remain stable after missing cost channels are added
- full closure of active, controller, memory, information, and post-commit completion costs

## Bottom Line

Extended Data Figure 6 is the detailed support layer behind the thermodynamic qualifier: the productive ridge survives the tested metric family, the preferred branch along that ridge shifts under the stronger completion-aware metrics, and the current bookkeeping remains explicitly incomplete rather than thermodynamically closed.
