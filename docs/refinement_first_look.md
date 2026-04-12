# Refinement First Look

## Scope

This note gives a first-pass interpretation of the first completed adaptive refinement scan.

Caution:

- this is still a screening-stage interpretation
- `eta_sigma_mean` remains a ranking aid rather than a final precision metric
- no second refinement stage is started in this step

Primary outputs:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/summary.parquet)
- [top_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/refinement_quicklook/top_candidates.csv)

## Coverage Summary

Completed scan counts:

- total state points: `244`
- dense refinement-box points: `240`
- anchor points: `4`

## Best Points

### Best success probability

Best dense-box `Psucc_mean` occurred at:

- label: `full_dense_refinement_box_pm0p05_pf0p02_pu0p1`
- `Pi_m = 0.05`
- `Pi_f = 0.02`
- `Pi_U = 0.1`

Metrics:

- `Psucc_mean = 0.9794921875`
- `MFPT_mean = 6.223741276171486`
- `eta_sigma_mean = 5.444279788790285e-05`
- `trap_time_mean = 0.0`

Interpretation:

- the strongest success point moved further toward the lower-left corner than the coarse scan suggested
- the best success region now prefers very low delay and very low memory, with a small positive flow instead of strict zero flow

### Best efficiency screening signal

Best dense-box `eta_sigma_mean` occurred at:

- label: `full_dense_refinement_box_pm0p2_pf0p02_pu0p2`
- `Pi_m = 0.2`
- `Pi_f = 0.02`
- `Pi_U = 0.2`

Metrics:

- `Psucc_mean = 0.9541015625`
- `MFPT_mean = 3.921732343909929`
- `eta_sigma_mean = 6.837019856230414e-05`
- `trap_time_mean = 0.0`

Interpretation:

- the best efficiency ridge clearly pushes to the smallest tested `Pi_f`
- the ridge does not collapse all the way to the smallest tested `Pi_m`
- instead, the strongest screening band sits at low-to-moderate memory around `Pi_m = 0.15` to `0.2`, with weak-to-moderate positive flow

### Fastest transport

Smallest dense-box `MFPT_mean` occurred at:

- label: `full_dense_refinement_box_pm0p15_pf0p02_pu0p3`
- `Pi_m = 0.15`
- `Pi_f = 0.02`
- `Pi_U = 0.3`

Metrics:

- `Psucc_mean = 0.876953125`
- `MFPT_mean = 2.777263363028953`
- `eta_sigma_mean = 5.1615964791020674e-05`
- `trap_time_mean = 0.5025000000000003`

Interpretation:

- increasing `Pi_U` toward `0.3` continues to accelerate transport
- the fastest point is not the top success point and not the top screening-efficiency point

## Ridge Shape

The refinement scan answers the main question from the coarse pass:

- yes, the productive region bends further toward smaller `Pi_f`
- partially, it bends toward smaller `Pi_m`, but not monotonically to the smallest tested value

Evidence from the top `20` `eta_sigma_mean` points:

- `19 / 20` occur at `Pi_f <= 0.03`
- `12 / 20` occur at `Pi_U >= 0.2`
- only `6 / 20` occur at `Pi_m <= 0.1`

Best-by-`Pi_U` screening points:

- `Pi_U = 0.0`: `Pi_m = 0.4`, `Pi_f = 0.02`
- `Pi_U = 0.1`: `Pi_m = 0.2`, `Pi_f = 0.02`
- `Pi_U = 0.2`: `Pi_m = 0.2`, `Pi_f = 0.02`
- `Pi_U = 0.25`: `Pi_m = 0.15`, `Pi_f = 0.02`
- `Pi_U = 0.3`: `Pi_m = 0.15`, `Pi_f = 0.02`

Interpretation:

- the refined ridge strongly hugs the lowest tested delay edge
- the best memory scale is low, but not minimal
- the efficiency-favored band stabilizes near `Pi_m = 0.15` to `0.2`
- the flow-favored band stabilizes near `Pi_U = 0.2` to `0.3`

## Lower-Left Corner Check

The lower-left corner remains highly competitive:

- `Pi_m = 0.03`, `Pi_f = 0.02`, `Pi_U = 0.2`
  - `Psucc_mean = 0.9140625`
  - `MFPT_mean = 4.861287393162393`
  - `eta_sigma_mean = 4.83980160275956e-05`
- `Pi_m = 0.05`, `Pi_f = 0.02`, `Pi_U = 0.1`
  - `Psucc_mean = 0.9794921875`
  - `MFPT_mean = 6.223741276171486`
  - `eta_sigma_mean = 5.444279788790285e-05`
- `Pi_m = 0.08`, `Pi_f = 0.02`, `Pi_U = 0.2`
  - `Psucc_mean = 0.9306640625`
  - `MFPT_mean = 4.478693599160546`
  - `eta_sigma_mean = 5.516169736514651e-05`

Interpretation:

- success remains excellent even at the very smallest tested memory scales
- the absolute best screening metric shifts slightly upward in memory from that corner
- this suggests a narrow tradeoff front rather than a single sharp optimum

## Anchor Check

The retained anchors do not outperform the refined dense box.

Best anchor point:

- label: `full_anchor_points_pm0p6_pf0p2_pu0`
- `Psucc_mean = 0.822265625`
- `MFPT_mean = 10.845727434679336`
- `eta_sigma_mean = 2.067596858530092e-05`

Interpretation:

- the anchor set confirms that the productive ridge remains inside the refinement envelope
- there is no evidence in this run that the best screening region escaped back toward larger delay or larger memory

## Practical Readout

Current refined picture:

- best success sits near `Pi_m = 0.05`, `Pi_f = 0.02`, `Pi_U = 0.1`
- best screening efficiency sits near `Pi_m = 0.2`, `Pi_f = 0.02`, `Pi_U = 0.2`
- fastest transport sits near `Pi_m = 0.15`, `Pi_f = 0.02`, `Pi_U = 0.3`
- all three leading signals now share the same very-low-delay edge

This means the coarse-scan hypothesis was only partly right:

- it was correct that the ridge bends toward smaller `Pi_f`
- it was too conservative about how far success moves toward smaller `Pi_m`
- it was too aggressive if interpreted as “the best efficiency point must be at the smallest `Pi_m`”

## Next Candidate Envelope

If a second refinement stage is requested later, the data now support focusing on:

- `Pi_f` fixed very near `0.02` to `0.03`
- `Pi_m` concentrated in `0.05` to `0.25`
- `Pi_U` concentrated in `0.1` to `0.3`

Within that band, the main tradeoff to resolve is:

- maximum `Psucc_mean` near very small `Pi_m`
- maximum `eta_sigma_mean` near slightly larger low-memory values
- minimum `MFPT_mean` near the higher-flow edge
