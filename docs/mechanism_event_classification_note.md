# Mechanism Event Classification Note

## Scope

This note defines the first wrapper-side event-classification layer used to build the mechanism dataset from the frozen canonical operating points only.

- source manifest: [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- schema: [mechanism_dataset_schema.md](file:///home/zhuguolong/aoup_model/docs/mechanism_dataset_schema.md)
- output dataset directory: [mechanism_dataset](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset)
- diagnostic figure directory: [mechanism_dataset](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset)

The implementation replays only the persisted canonical `result.json` inputs and leaves `legacy/simcore` unchanged.

## Gate Definition

For the frozen `maze_v1` canonical geometry, the gate-conditioned extractor uses shell-doorway gates only.

- gate ids used in this first dataset: `0`
- gate neighborhood is measured in local gate coordinates:
  - normal coordinate: signed distance through the doorway
  - tangential coordinate: offset along the doorway mouth

This choice keeps the gate-conditioned records focused on the bottleneck that separates productive ridge behavior from stale-control recirculation.

## Thresholds

| Quantity | Rule | Value |
|---|---|---:|
| Wall contact distance | `signed_distance <= wall_contact_distance` | 0.0400 |
| Wall-sliding alignment | `|u . t_wall| >= wall_sliding_alignment_min` | 0.70 |
| Gate lane half-width | `|t_gate| <= gate_lane_half_width` | 0.0600 |
| Gate approach depth | `-gate_approach_depth <= n_gate < -gate_capture_depth` | 0.0600 |
| Gate capture depth | `|n_gate| <= gate_capture_depth` | 0.0200 |
| Gate progress minimum | `v . n_gate >= gate_progress_min` | 0.0250 |
| Gate capture alignment | `u . n_gate >= gate_capture_alignment_min` | 0.30 |
| Gate crossing margin | crossing requires normal-coordinate sign change larger than margin | 0.0100 |
| Trap progress window | rolling average window | 0.2500 |
| Trap progress threshold | `rolling_progress <= trap_progress_max` | 0.0000 |
| Trap minimum duration | confirmed trap threshold | 0.5000 |

## Rules By Event Type

### `bulk_motion`

- default state when the trajectory is outside gate-local and wall-sliding conditions
- interpreted as free search away from walls and away from gate commitment

### `wall_sliding`

- requires wall contact plus strong tangential wall alignment
- excludes gate-local approach, capture, crossing, and confirmed trap intervals

### `gate_approach`

- requires residence in the gate lane
- requires the trajectory to remain on the outer side of the doorway
- requires positive doorway-normal progress

### `gate_capture`

- requires residence inside the narrower gate-capture band
- requires positive gate-forward alignment
- remains distinct from `gate_crossing`, which is reserved for the actual sign-changing transit

### `gate_crossing`

- requires a same-gate sign change in the doorway-normal coordinate
- requires both the previous and current samples to remain in the gate lane

### `trap_episode`

- requires wall-contact plus non-positive rolling navigation progress
- becomes a confirmed event only after the dwell exceeds the minimum duration threshold
- event-table trap rows therefore represent confirmed stale residence, while trajectory-level `trap_time_total` includes the full dwell once a trap qualifies

### `trap_escape`

- recorded on the first interval immediately after a confirmed trap ends
- preserves the direction of recovery back to wall, bulk, or gate-local motion

## Which observables are most likely to separate ridge points from the stale-control point?

The matched comparison between `OP_BALANCED_RIDGE_MID` and `OP_STALE_CONTROL_OFF_RIDGE` is most strongly separated by steering mismatch and gate-conversion observables in this first dataset:

- steering lag shifts from `0.022` on-ridge to `0.010` off-ridge
- capture-given-approach drops from `0.574` to `0.584`
- return-to-wall-after-capture rises from `0.367` to `0.364`
- mean trap duration rises from `0.000` to `0.511`

These are the most plausible first discriminants for later gate-theory support.

## Sensitivity of mechanism conclusions to event-classification thresholds

The first sensitivity check is based on the fraction of extracted events that sit close to the operative thresholds.

- mean near-threshold wall-sliding share: `0.055`
- mean near-threshold gate-capture share: `0.546`
- mean near-threshold trap share: `1.000`

The main ridge-vs-stale conclusions are therefore not driven solely by marginal classification cases. The strongest separating signals arise in steering lag, gate conversion, and trap residence, where the ridge/off-ridge differences remain larger than the measured near-threshold fractions.

Supporting diagnostics:

- [canonical_mechanism_overview.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/canonical_mechanism_overview.png)
- [ridge_vs_stale_observables.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/ridge_vs_stale_observables.png)
- [threshold_sensitivity.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset/threshold_sensitivity.png)
