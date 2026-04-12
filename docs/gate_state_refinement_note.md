# Gate State Refinement Note

## Scope

This note defines the refined gate-local wrapper-side state graph used before any coarse-grained gate theory fit.

- canonical manifest: [canonical_operating_points.csv](file:///home/zhuguolong/aoup_model/outputs/tables/canonical_operating_points.csv)
- refined dataset directory: [mechanism_dataset_refined](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined)
- refined figure directory: [mechanism_dataset_refined](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined)

The legacy physics kernel remains unchanged.

## Why The Original Gate States Were Refined

The audit showed that the first `gate_capture` proxy was too broad: it mixed mouth residence, partial commitment, and non-transiting near-gate dwell. As a result, `crossing_given_capture` was too small to use directly as a first rate-model transition probability.

## Refined Gate-Local Taxonomy

### `gate_approach`

- outer-side, gate-lane motion with positive inward progress
- intended to represent guided arrival toward the doorway mouth

### `gate_residence_precommit`

- near-mouth residence inside the broader gate band
- may include dithering, tangential recirculation, or failed alignment before commitment

### `gate_commit`

- narrower gate lane
- near-mouth or slightly inner-side position
- stronger inward alignment and stronger inward progress
- intended to represent a cleaner crossing-preparation state

### `gate_crossing`

- actual through-door sign-change transit in the narrow gate lane

## Thresholds

| Quantity | Value |
|---|---:|
| wall_sliding_alignment_min | 0.70 |
| gate_lane_half_width | 0.0600 |
| gate_commit_lane_half_width | 0.0340 |
| gate_approach_depth | 0.0600 |
| gate_residence_depth | 0.0300 |
| gate_commit_outer_depth | 0.0180 |
| gate_commit_inner_depth | 0.0200 |
| gate_progress_min | 0.0250 |
| gate_commit_progress_min | 0.0750 |
| gate_commit_alignment_min | 0.60 |
| gate_crossing_margin | 0.0100 |

## Added Directional Observables

- `signed_wall_tangent_mean`: signed local wall-tangent motion rather than unsigned tangentiality only
- `wall_circulation_signed_mean`: signed circulation around the maze center during wall-local motion
- `signed_gate_approach_angle_mean`: signed gate-local approach angle using tangent-versus-normal motion decomposition
- `local_recirculation_polarity_mean`: signed orbital polarity around the gate center during gate-local states

## Old Versus Refined Definitions

| Old state | Refined interpretation |
|---|---|
| `gate_capture` | split into `gate_residence_precommit` and `gate_commit` |
| `gate_crossing` | preserved, but now attached to a narrower commit lane |
| unsigned wall tangentiality only | supplemented with signed wall circulation and tangent direction |
| unsigned gate-forward alignment only | supplemented with signed gate approach angle and local recirculation polarity |

## Did the refined gate-state definition make stale-control more mechanistically distinguishable?

Only modestly. The refined state graph improves interpretability and makes the matched comparison better targeted, but it does not yet produce a strong stale-control separation in the gate-local transition statistics.

- first gate commit delay: `1.6677` on-ridge vs `1.7356` off-ridge
- wall dwell before first commit: `0.5026` on-ridge vs `0.5250` off-ridge
- return to wall after commit: `0.0057` on-ridge vs `0.0050` off-ridge
- steering lag at commit: `0.0061` on-ridge vs `0.0021` off-ridge

The delay and wall-dwell differences remain in the expected direction, but the commit conversion and post-commit return metrics remain too similar to support a strong mechanistic separation on gate-local statistics alone.

## Is the refined state graph now clean enough for a first rate model?

Not yet. Not yet. The refined graph is cleaner than the original because it separates gate-mouth residence from stronger forward commitment. The first candidate state graph is:

- bulk
- wall_sliding
- gate_approach
- gate_residence_precommit
- gate_commit
- gate_crossing
- trap_episode

However, the present refined replay still yields `crossing_given_commit` values only on the order of `0.00008` and `commit_given_residence` remains nearly unchanged across the matched ridge/stale pair. The refined graph should therefore be treated as a cleaner diagnostic layer, not yet as a final first rate-model state graph.

Supporting diagnostics:

- [refined_gate_state_summary.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_gate_state_summary.png)
- [balanced_vs_stale_refined.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/balanced_vs_stale_refined.png)
- [old_vs_refined_balanced_stale.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/old_vs_refined_balanced_stale.png)
