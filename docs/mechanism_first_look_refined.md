# Mechanism First Look Refined

## Scope

This note gives the first robust mechanism reading from the refined canonical-only mechanism dataset, using only observables that are already trustworthy enough for interpretation.

- refined summary source: [refined_summary_by_point.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_summary_by_point.csv)
- refined comparison source: [old_vs_refined_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/old_vs_refined_summary.csv)
- discriminator figure: [mechanism_discriminator_summary.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/mechanism_discriminator_summary.png)

Excluded from the central mechanism argument:

- `crossing_given_commit` as a primary explanatory rate, because the refined gate-crossing counts remain too sparse for a committed crossing-rate theory.

## Canonical Mechanism Comparison

The five canonical points already separate cleanly in pre-commit timing, while post-commit crossing remains too sparse to explain the front structure directly.

- `OP_SPEED_TIP` is the earliest committing branch: first commit delay `1.3750`, wall dwell before first commit `0.4006`.
- `OP_SUCCESS_TIP` is the latest and most deliberate branch: first commit delay `2.8326`, wall dwell before first commit `0.8695`.
- `OP_EFFICIENCY_TIP` sits between success and balanced in commitment timing: first commit delay `1.9410`.
- `OP_BALANCED_RIDGE_MID` is the ridge reference: first commit delay `1.6677`, wall dwell `0.5026`, zero trap burden.
- `OP_STALE_CONTROL_OFF_RIDGE` differs from the matched ridge point mainly through slower pre-commit timing and nonzero trap burden: first commit delay `1.7356`, wall dwell `0.5250`, trap burden `0.000250`.

## Which Observables Best Separate The Canonical Points?

Most useful now:

- `first_gate_commit_delay`: spans from `1.3750` at `OP_SPEED_TIP` to `2.8326` at `OP_SUCCESS_TIP`, and also separates the balanced ridge point from the stale-control point.
- `wall_dwell_before_first_commit`: follows the same ordering, from `0.4006` to `0.8695`.
- `trap_burden_mean`: remains zero on the productive ridge points and rises only on the stale-control point (`0.000250`) and, weakly, on the success tip (`0.000063`).

Secondary but not central:

- `steering_lag_at_commit_mean`: small but nonzero across the set, with matched-pair values `0.0061` and `0.0021`; useful as a cautionary secondary diagnostic, not as the main separator.
- signed directional observables: their matched-pair signs change in some cases, but their point-level means remain small enough that they are not yet as robust as the timing and trap signals.

## Is the productive-memory ridge mainly a pre-commit phenomenon?

Yes, in the first robust reading.

The strongest trustworthy ordering across the success, efficiency, speed, ridge-mid, and stale-control points appears before strong gate commitment:

- speed corresponds to the shortest first-commit delay (`1.3750`) and shortest pre-commit wall dwell (`0.4006`)
- success corresponds to the longest first-commit delay (`2.8326`) and longest pre-commit wall dwell (`0.8695`)
- the balanced ridge and stale-control comparison is also dominated by a pre-commit shift: delay `1.6677` -> `1.7356`, wall dwell `0.5026` -> `0.5250`

By contrast, the refined crossing probability from the commit state remains far too sparse to support a post-commit crossing-control explanation. The current front structure is therefore most plausibly read as a difference in how trajectories arrive at and prepare for commitment, not in how they traverse the doorway after commitment.

## Matched Comparison: Balanced Ridge Vs Stale Control

- first gate commit delay: `1.6677` vs `1.7356`
- wall dwell before first commit: `0.5026` vs `0.5250`
- trap burden mean: `0.000000` vs `0.000250`
- steering lag at commit mean: `0.0061` vs `0.0021`

This matched pair already supports a cautious mechanism statement: increasing `Pi_f` at fixed `Pi_m` and `Pi_U` primarily delays or prolongs pre-commit search and adds rare but real stale trapping, rather than cleanly changing a post-commit crossing rate.

## Which mechanism signals are already robust enough for principle-building?

- Robust now: `first_gate_commit_delay`, `wall_dwell_before_first_commit`, and source-aligned `trap_burden_mean`.
- Useful but secondary: `steering_lag_at_commit_mean` when interpreted as a weak supporting diagnostic rather than a headline separator.
- Not yet robust enough for central principle-building: the signed directional observables as leading signals, and any crossing-rate quantity derived from `gate_crossing`.

## Practical Summary

The current refined mechanism picture is that the productive-memory ridge is distinguished mainly by how trajectories organize wall-guided search before commitment. The success, efficiency, and speed tips differ primarily in the timing budget they spend before strong commitment, while the stale-control point differs from the balanced ridge point by slightly slower pre-commit timing and a small but source-aligned trap burden.
