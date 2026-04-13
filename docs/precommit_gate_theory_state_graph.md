# Precommit Gate Theory State Graph

## Scope

This note defines the first coarse-grained gate theory around the pre-commit bottleneck only. It uses the refined mechanism dataset and stops the reduced theory at `gate_commit` rather than forcing an early doorway-crossing model.

- refined summary source: [refined_summary_by_point.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_summary_by_point.csv)
- refined event source: [event_level.parquet](file:///home/zhuguolong/aoup_model/outputs/datasets/mechanism_dataset_refined/event_level.parquet)
- state-graph figure: [precommit_state_graph.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/precommit_state_graph.png)

## Minimal Pre-Commit State Graph

Minimal robust model:

- `bulk`
- `wall_sliding`
- `gate_residence_precommit`
- `gate_commit`
- `trap_episode`

Interpretation:

- `gate_approach` is collapsed into an effective arrival layer between non-gate search and precommit residence.
- `trap_episode` is retained as an occupancy sink for stale burden, but its entry and escape transitions are too sparse to center the first theory.

## Slightly Richer Pre-Commit State Graph

Slightly richer model:

- `bulk`
- `wall_sliding`
- `gate_approach`
- `gate_residence_precommit`
- `gate_commit`
- `trap_episode`

This richer model is still pre-crossing, but it preserves the arrival funnel into the doorway mouth.

## Mapping Trustworthy Observables Onto The Graph

- `first_gate_commit_delay`: first-passage observable from pre-commit search (`bulk`, `wall_sliding`, and optionally `gate_approach`) to `gate_commit`.
- `wall_dwell_before_first_commit`: residence-time observable on the wall-guided branch before first entry into `gate_commit`.
- `trap_burden_mean`: occupancy burden of the rare stale sink `trap_episode`, not yet a reliable transition-rate object.
- `commit_given_residence`: robust transition fraction from `gate_residence_precommit` to `gate_commit`.
- `residence_given_approach`: robust transition fraction from `gate_approach` to `gate_residence_precommit` in the richer model.
- `return_to_wall_after_precommit_rate`: recycling from `gate_residence_precommit` back to wall-guided search.

## Which Transitions Can Be Estimated Robustly Now?

| src                      | dst                      |   mean_prob |   min_prob |   max_prob |   total_count |
|:-------------------------|:-------------------------|------------:|-----------:|-----------:|--------------:|
| bulk_motion              | wall_sliding             |  0.93594    | 0.918497   | 0.957357   |       7579579 |
| bulk_motion              | gate_approach            |  0.0500934  | 0.0325976  | 0.0651689  |        399854 |
| bulk_motion              | gate_residence_precommit |  0.0102352  | 0.00699975 | 0.0130638  |         81866 |
| gate_approach            | bulk_motion              |  0.504706   | 0.489771   | 0.523924   |        303386 |
| gate_approach            | wall_sliding             |  0.27049    | 0.266893   | 0.273378   |        160816 |
| gate_approach            | gate_residence_precommit |  0.222068   | 0.206493   | 0.233866   |        130390 |
| gate_approach            | gate_commit              |  0.00273635 | 0.00251834 | 0.00298489 |          1637 |
| gate_commit              | gate_residence_precommit |  0.989479   | 0.988707   | 0.990836   |        318793 |
| gate_commit              | bulk_motion              |  0.00531973 | 0.0048693  | 0.00561492 |          1677 |
| gate_commit              | wall_sliding             |  0.0051159  | 0.00423212 | 0.00572206 |          1581 |
| gate_residence_precommit | gate_commit              |  0.533757   | 0.531756   | 0.535909   |        320148 |
| gate_residence_precommit | bulk_motion              |  0.258075   | 0.254773   | 0.260486   |        154111 |
| gate_residence_precommit | wall_sliding             |  0.148806   | 0.14723    | 0.150494   |         89144 |
| gate_residence_precommit | gate_approach            |  0.0593615  | 0.0574186  | 0.061268   |         35755 |
| wall_sliding             | bulk_motion              |  0.970344   | 0.962348   | 0.979924   |       7628487 |
| wall_sliding             | gate_approach            |  0.0208173  | 0.0138738  | 0.026435   |        160616 |
| wall_sliding             | gate_residence_precommit |  0.00876774 | 0.00608245 | 0.0111731  |         68094 |

Robust now:

- `bulk <-> wall_sliding`: dominant search-cycle backbone.
- `wall_sliding -> gate_approach` and `bulk -> gate_approach`: robust approach-entry traffic in the richer model.
- `gate_approach -> gate_residence_precommit`: robust precommit residence entry.
- `gate_residence_precommit -> gate_commit`: robust commitment step.
- `gate_residence_precommit -> bulk` and `gate_residence_precommit -> wall_sliding`: robust recycling out of the mouth before commitment.
- `gate_commit -> gate_residence_precommit`: robust evidence that the present commit state is a pre-crossing preparation state rather than a crossing state.

Not robust enough yet:

- `trap_episode` entry and escape transitions as fitted rates, because total counts remain tiny.
- any transition involving `gate_crossing`, because the crossing branch remains too sparse.

## Why the first reduced theory should stop at gate commitment

The refined mechanism analysis shows that the current front structure is already explained before the final transit step. Three observations make `gate_commit` the correct stopping point for the first reduced theory:

- `crossing_given_commit` is still extremely small, so a crossing-rate theory would be numerically fragile.
- `gate_commit -> gate_residence_precommit` is overwhelmingly dominant, which means the current commit state is still a preparation/recycling state rather than a resolved crossing state.
- the main canonical ordering already appears in `first_gate_commit_delay`: speed `1.3750`, balanced `1.6677`, efficiency `1.9410`, success `2.8326`.

The first reduced theory should therefore explain commitment timing and precommit recycling, while explicitly deferring the final transit branch.

## Which parts of the productive-memory ridge are explained before crossing?

Most of the currently trustworthy ridge structure.

- `OP_SPEED_TIP` reaches commit fastest (`1.3750`) and has the shortest wall dwell before commit (`0.4006`).
- `OP_SUCCESS_TIP` reaches commit slowest (`2.8326`) and has the longest wall dwell before commit (`0.8695`).
- `OP_EFFICIENCY_TIP` stays between those extremes (`1.9410`), which fits the ridge tradeoff without invoking a crossing-rate hierarchy.
- the matched ridge-vs-stale difference is also precommit-dominated: delay `1.6677` -> `1.7356`, wall dwell `0.5026` -> `0.5250`.
- trap burden adds a small off-ridge penalty: `0.000000` on the balanced ridge point vs `0.000250` at the stale-control point.

What is not yet explained before crossing:

- final transit success conditional on strong commitment
- any post-crossing state sequence
- crossing-specific rate asymmetries

## Where ridge-vs-stale separation is encoded in the reduced graph

Mainly in observables attached to search-to-commit timing, not in currently measured commitment probabilities.

- `time to first commit`: clear matched-pair shift (`1.6677` vs `1.7356`)
- `probability of reaching commit` from precommit residence: almost unchanged (`0.5330` vs `0.5343`)
- `wall-to-residence cycling`: populated and meaningful, but only weakly different in the matched pair
- `residence-to-trap recycling`: conceptually important for stale control, but still too sparse to estimate as a central transition object

This means the first reduced theory should encode ridge-vs-stale separation primarily through a slower effective approach-to-commit clock plus a rare stale sink, not through a large change in commitment probability itself.

## Proposed Models

**Minimal model**

- states: `bulk`, `wall_sliding`, `gate_residence_precommit`, `gate_commit`, `trap_episode`
- use when the goal is a robust five-state precommit theory with maximal interpretability
- treat `gate_approach` as an unresolved fast substep folded into the effective arrival process

**Slightly richer model**

- states: `bulk`, `wall_sliding`, `gate_approach`, `gate_residence_precommit`, `gate_commit`, `trap_episode`
- use when the goal is to preserve doorway-mouth arrival explicitly while still stopping before crossing
- this is the better candidate for later rate fitting once more precommit statistics are accumulated

## Deferred Until Later Crossing-Specific Analysis

- `gate_commit -> gate_crossing`
- any transition beginning from `gate_crossing`
- any full doorway-crossing success model
- trap entry and trap escape rates as fitted kinetic parameters

## Practical Conclusion

The first robust gate theory should be a precommit bottleneck theory: trajectories separate mainly by how long they circulate between bulk, wall-guided motion, and precommit mouth residence before strong commitment. The productive-memory ridge is already largely explained by that precommit organization, while the final crossing step should be deferred to a later, crossing-specific analysis.
