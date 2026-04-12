# Precision Scan First Look

## Scope

This note gives a first-pass interpretation of the targeted precision scan along the refined productive ridge.

Caution:

- this is a precision screening pass, not yet a final model-selection theorem
- the key goal here is to resolve the tradeoff front geometry, not to reopen the global search

Primary outputs:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/precision_scan/summary.parquet)
- [top_points_by_objective.csv](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/top_points_by_objective.csv)
- [precision_front_analysis.json](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/precision_front_analysis.json)

## Best Objective Points

### Maximum `Psucc_mean`

Best base-grid success point:

- label: `full_precision_ridge_grid_pm0p1_pf0p02_pu0p1_n2048`
- `Pi_m = 0.1`
- `Pi_f = 0.02`
- `Pi_U = 0.1`

Metrics:

- `Psucc_mean = 0.97900390625`
- `MFPT_mean = 5.795831670822943`
- `eta_sigma_mean = 5.778780986555034e-05`
- `trap_time_mean = 0.5100000000000001`

Reading:

- the highest-success front prefers the smallest tested delay, low memory, and the lowest tested flow within this precision window

### Maximum `eta_sigma_mean`

Best base-grid efficiency-screening point:

- label: `full_precision_ridge_grid_pm0p2_pf0p02_pu0p2_n2048`
- `Pi_m = 0.2`
- `Pi_f = 0.02`
- `Pi_U = 0.2`

Metrics:

- `Psucc_mean = 0.951171875`
- `MFPT_mean = 3.9202284394250513`
- `eta_sigma_mean = 6.716089379588434e-05`
- `trap_time_mean = 0.5175`

Reading:

- the efficiency ridge stays pinned to the minimum tested delay
- compared with the success optimum, it shifts to moderately larger memory and moderately larger flow

### Minimum `MFPT_mean`

Fastest base-grid point:

- label: `full_precision_ridge_grid_pm0p1_pf0p02_pu0p3_n2048`
- `Pi_m = 0.1`
- `Pi_f = 0.02`
- `Pi_U = 0.3`

Metrics:

- `Psucc_mean = 0.87939453125`
- `MFPT_mean = 2.7478428650749582`
- `eta_sigma_mean = 5.257869623062748e-05`
- `trap_time_mean = 0.0`

Reading:

- the fastest front sits on the same lowest-delay edge, but at the highest tested flow
- this preserves the separation between transport speed and the other two objectives

## Are The Fronts Distinct?

Top-`10` overlap counts from [precision_front_analysis.json](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/precision_front_analysis.json):

- `Psucc_mean` vs `eta_sigma_mean`: `0`
- `Psucc_mean` vs `MFPT_mean`: `0`
- `eta_sigma_mean` vs `MFPT_mean`: `0`
- all three top-`10` sets: `0`

Interpretation:

- the three fronts are not merely shifted versions of one another
- they occupy neighboring but distinct parts of the same narrow window
- the remaining uncertainty is now about tradeoff preference, not broad localization

## Ridge Geometry

What stays fixed across all three objectives:

- `Pi_f = 0.02` dominates the best points
- `Pi_m` remains low, never leaving the `0.1` to `0.2` band for the three primary optima
- `Pi_U` orders the front:
  - low flow favors success
  - moderate flow favors `eta_sigma_mean`
  - high flow favors minimum `MFPT`

This means the precision scan resolves the ridge as mainly:

- very narrow in `Pi_f`
- modestly extended in `Pi_m`
- clearly ordered along `Pi_U`

## Resample Check

The optional `4096`-trajectory resample covered the top `10` candidates.

Key readout from [resample_comparison.csv](file:///home/zhuguolong/aoup_model/outputs/figures/precision_scan/resample_comparison.csv):

- `Pi_m = 0.1`, `Pi_f = 0.02`, `Pi_U = 0.15`
  - `eta_sigma_mean` changed from `6.093943967610685e-05` to `6.157407725710657e-05`
- `Pi_m = 0.15`, `Pi_f = 0.02`, `Pi_U = 0.2`
  - `eta_sigma_mean` changed from `6.291636033608778e-05` to `6.343984068567377e-05`
- `Pi_m = 0.18`, `Pi_f = 0.02`, `Pi_U = 0.15`
  - `eta_sigma_mean` changed from `6.65327872704118e-05` to `6.491037861945741e-05`

Interpretation:

- the resample confirms the same narrow candidate strip
- the ordering among neighboring ridge points moves slightly, but not enough to change the global picture
- the best-efficiency neighborhood remains around `Pi_f = 0.02` and `Pi_m = 0.15` to `0.2`

## Is the productive-memory window better described as a ridge or a compact basin?

It is better described as a `ridge`.

Reasoning:

- the dominant points lie on a thin delay edge rather than filling a broad 2D pocket
- the best front positions translate systematically with `Pi_U`
- the three objective fronts are distinct, with zero overlap in their top-`10` sets
- nearby ridge points remain competitive under `4096`-trajectory resampling

Why not a compact basin:

- a compact basin would show stronger overlap among the top success, efficiency, and speed sets
- it would also show weaker directional ordering in `Pi_U`
- neither pattern is present here

## Practical Decision View

If the decision goal is highest success:

- stay near `Pi_m = 0.1`, `Pi_f = 0.02`, `Pi_U = 0.1`

If the decision goal is best screening efficiency:

- stay near `Pi_m = 0.18` to `0.2`, `Pi_f = 0.02`, `Pi_U = 0.15` to `0.2`

If the decision goal is minimum transport time:

- stay near `Pi_m = 0.1`, `Pi_f = 0.02`, `Pi_U = 0.3`

## Bottom Line

The productive-memory window is now localized precisely enough that the main unresolved question is not “where is the good region?” but “which objective should define the final operating point along the ridge?”
