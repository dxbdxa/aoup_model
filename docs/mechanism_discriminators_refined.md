# Mechanism Discriminators Refined

## Scope

This note ranks the current refined mechanism observables by how useful they are for trustworthy interpretation, with the balanced-ridge versus stale-control comparison as the main test.

- refined summary source: [refined_summary_by_point.csv](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/refined_summary_by_point.csv)
- figure: [mechanism_discriminator_summary.png](file:///home/zhuguolong/aoup_model/outputs/figures/mechanism_dataset_refined/mechanism_discriminator_summary.png)

## Trusted Discriminator Ranking

| label                    |   balanced_value |   stale_value |   delta_stale_minus_balanced |   matched_pair_range_fraction |
|:-------------------------|-----------------:|--------------:|-----------------------------:|------------------------------:|
| Trap Burden              |         0        |   0.000249634 |                  0.000249634 |                     1         |
| Wall Dwell Before Commit |         0.502555 |   0.525013    |                  0.022458    |                     0.047895  |
| First Commit Delay       |         1.66767  |   1.73561     |                  0.0679331   |                     0.0466051 |

Interpretation:

- `Trap Burden` is the sharpest matched-pair discriminator because it stays at `0.000000` on the balanced ridge point and rises to `0.000250` off ridge.
- `First Commit Delay` and `Wall Dwell Before First Commit` are the strongest smooth pre-commit discriminators and also explain the success-speed-efficiency ordering across the canonical front tips.
- `Steering Lag At Commit` is measurable but weaker and should remain a supporting signal rather than a primary mechanism axis.

## Directional Observables

| label                       |   balanced_value |   stale_value |   delta_stale_minus_balanced |   matched_pair_range_fraction |
|:----------------------------|-----------------:|--------------:|-----------------------------:|------------------------------:|
| Gate Recirculation Polarity |     -0.00169858  |   0.000879143 |                  0.00257772  |                      1        |
| Wall Circulation Signed     |     -0.000359866 |   0.000471636 |                  0.000831502 |                      0.641059 |
| Steering Lag At Commit      |      0.00605502  |   0.00210349  |                 -0.00395153  |                      0.557628 |
| Signed Gate Approach Angle  |     -0.0019973   |  -0.0024083   |                 -0.000411002 |                      0.159204 |
| Signed Wall Tangent         |      0.000631799 |   0.000797086 |                  0.000165287 |                      0.141105 |

Interpretation:

- The signed directional observables are useful because they now preserve polarity, but their point-level means remain small enough that they should be treated as exploratory diagnostics rather than firm mechanism discriminators.

## Front-Tip Mechanism Ordering

- `OP_SPEED_TIP`: shortest pre-commit timing budget; fastest branch, but lowest success.
- `OP_EFFICIENCY_TIP`: intermediate-to-long pre-commit timing without visible trap burden; efficient but not as selective as the success tip.
- `OP_SUCCESS_TIP`: longest pre-commit timing and largest wall dwell; slowest to commit, but highest success.
- `OP_BALANCED_RIDGE_MID`: central ridge compromise with moderate pre-commit timing and no trap burden.
- `OP_STALE_CONTROL_OFF_RIDGE`: close to the balanced ridge point in most gate-local means, but shifted toward slower pre-commit timing and rare stale trapping.

## Mechanism Summary

The first robust discriminator set supports a compact reduced-theory direction: use pre-commit timing plus trap burden as the main mechanism coordinates, and treat steering-lag and directional observables as secondary annotations rather than first-fit state rates.
