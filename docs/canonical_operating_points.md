# Canonical Operating Points

## Scope

This note freezes the default representative operating points for all downstream mechanism and theory work.

Source-of-truth policy:

- the selections come only from the finished `confirmatory_scan` results and the front-analysis package
- no search has been reopened
- the front tips follow the confirmed success / efficiency / speed winners
- the two additional points are chosen only to stabilize downstream comparison tasks

Primary inputs:

- [confirmatory_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/confirmatory_scan_first_look.md)
- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [pareto_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/pareto_candidates.csv)
- [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)

## Frozen Canonical Set

| Canonical label | Role | Pi_m | Pi_f | Pi_U | Source | n_traj | Rationale |
|---|---:|---:|---:|---:|---|---:|---|
| `OP_SUCCESS_TIP` | success tip | 0.08 | 0.025 | 0.10 | `resampled_8192` | 8192 | Highest-confidence success winner; canonical point when downstream work needs the most reliable gate-capture regime. |
| `OP_EFFICIENCY_TIP` | efficiency tip | 0.18 | 0.018 | 0.15 | `base_4096` | 4096 | Confirmed efficiency winner on the Pareto ridge; canonical point for dissipation-normalized transport analysis. |
| `OP_SPEED_TIP` | speed tip | 0.10 | 0.018 | 0.30 | `resampled_8192` | 8192 | Highest-confidence speed winner; canonical point for minimum-MFPT and fast-throughput analyses. |
| `OP_BALANCED_RIDGE_MID` | balanced ridge midpoint | 0.15 | 0.020 | 0.20 | `base_4096` | 4096 | Central Pareto-ridge compromise point with strong success, efficiency, and speed simultaneously; canonical neutral reference on the ridge backbone. |
| `OP_STALE_CONTROL_OFF_RIDGE` | off-ridge stale-control point | 0.15 | 0.025 | 0.20 | `base_4096` | 4096 | Delay-mismatch comparator matched in `Pi_m` and `Pi_U` to the balanced ridge midpoint, but shifted upward in `Pi_f` and pushed off the Pareto family. |

## Numerical Summary

| Canonical label | Psucc_mean | eta_sigma_mean | MFPT_mean | trap_time_mean |
|---|---:|---:|---:|---:|
| `OP_SUCCESS_TIP` | 0.97412109375 | 5.374062449901737e-05 | 6.123713972431078 | 0.5125000000000001 |
| `OP_EFFICIENCY_TIP` | 0.959228515625 | 6.685949490215236e-05 | 4.241863069483329 | 0.0 |
| `OP_SPEED_TIP` | 0.86865234375 | 4.9076887165645115e-05 | 2.816089797639123 | 0.0 |
| `OP_BALANCED_RIDGE_MID` | 0.952392578125 | 6.656774362363983e-05 | 4.045141630351192 | 0.0 |
| `OP_STALE_CONTROL_OFF_RIDGE` | 0.948486328125 | 6.323705227630503e-05 | 4.203626126126126 | 0.5112500000000001 |

## Point-By-Point Rationale

### `OP_SUCCESS_TIP`

- canonical label: `OP_SUCCESS_TIP`
- tuple: `(Pi_m, Pi_f, Pi_U) = (0.08, 0.025, 0.10)`
- role: front tip for maximum `Psucc_mean`
- rationale: use when downstream work must represent the most selective and most reliable operating point rather than the fastest or most efficient one

### `OP_EFFICIENCY_TIP`

- canonical label: `OP_EFFICIENCY_TIP`
- tuple: `(0.18, 0.018, 0.15)`
- role: front tip for maximum `eta_sigma_mean`
- rationale: use as the main dissipation-normalized transport representative and as the most direct numerical expression of the productive-memory ridge

### `OP_SPEED_TIP`

- canonical label: `OP_SPEED_TIP`
- tuple: `(0.10, 0.018, 0.30)`
- role: front tip for minimum `MFPT_mean`
- rationale: use when downstream work needs the strongest fast-transport branch, even though it is not the success or efficiency optimum

### `OP_BALANCED_RIDGE_MID`

- canonical label: `OP_BALANCED_RIDGE_MID`
- tuple: `(0.15, 0.020, 0.20)`
- role: central ridge compromise point
- rationale: use as the default "generic productive ridge" reference because it sits near the middle of the Pareto family and remains strong on all three objectives at once

### `OP_STALE_CONTROL_OFF_RIDGE`

- canonical label: `OP_STALE_CONTROL_OFF_RIDGE`
- tuple: `(0.15, 0.025, 0.20)`
- role: off-ridge stale-control / delay-mismatch comparator
- rationale: use as the standard contrast to `OP_BALANCED_RIDGE_MID` because `Pi_m` and `Pi_U` are matched while `Pi_f` is shifted upward, making the delay effect interpretable without reopening the search

## Default Use Rule

These five points are the default input set for:

- trajectory analysis
- gate theory
- geometry transfer
- thermodynamic analysis

Unless a task explicitly requires a wider scan slice, this canonical set should be used first.

## Why these points are sufficient for downstream principle-building

These five points span the smallest set that still captures the full confirmed ridge logic. The three front tips encode the irreducible objective separation. The balanced ridge midpoint represents the interior backbone of the Pareto family rather than an extremal tip. The stale-control point provides a matched off-ridge counterexample that isolates the effect of increasing delay at fixed memory and flow. Together, they are sufficient to build mechanism arguments, reduced gate theory, geometry-transfer comparisons, and thermodynamic contrasts without reopening the search or carrying the entire confirmatory grid into every downstream task.

## Operational Consequence

Use the frozen table in [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv) as the default manifest for all downstream principle-building modules.
