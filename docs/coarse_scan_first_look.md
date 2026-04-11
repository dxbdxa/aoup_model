# Coarse-Scan First Look

## Scope

This note gives a first-pass interpretation of the first completed production coarse scan.

Caution:

- this is a coarse screening pass
- `eta_sigma_mean` is useful for ranking candidate regions, but not yet for final precision claims
- no adaptive refinement has been started yet

Primary tables:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/summary.parquet)
- [top_screening_points.csv](file:///home/zhuguolong/aoup_model/outputs/figures/coarse_scan_quicklook/top_screening_points.csv)

## Coverage Summary

Completed scan counts:

- total state points: `60`
- full-branch points: `56`
- dense inner-box full points: `48`
- outer-frame full points: `8`
- sparse validation controls: `4`

## Main Signals

### Best success probability

Best full-branch `Psucc_mean` occurred at:

- label: `full_dense_inner_box_pm0p3_pf0p05_pu0`
- `Pi_m = 0.3`
- `Pi_f = 0.05`
- `Pi_U = 0.0`

Metrics:

- `Psucc_mean = 0.923828125`
- `MFPT_mean = 8.32181289640592`
- `eta_sigma_mean = 3.361606473116094e-05`

Interpretation:

- the high-success region remains in the low-memory, low-delay, zero-flow neighborhood
- this is broadly consistent with the benchmark mini-scan, although the coarse scan shifts the strongest success point toward even smaller `Pi_f`

### Best efficiency screening signal

Best full-branch `eta_sigma_mean` occurred at:

- label: `full_dense_inner_box_pm0p1_pf0p05_pu0p25`
- `Pi_m = 0.1`
- `Pi_f = 0.05`
- `Pi_U = 0.25`

Metrics:

- `Psucc_mean = 0.84375`
- `MFPT_mean = 3.800931712962963`
- `eta_sigma_mean = 3.879151251044084e-05`

Interpretation:

- the strongest screening efficiency now sits at the low-memory, low-delay, weak-positive-flow corner of the dense box
- this supports the benchmark expectation that weak positive flow can accelerate transport while still keeping a productive regime

### Fastest transport

Smallest full-branch `MFPT_mean` occurred at:

- label: `full_outer_frame_pm3_pf3_pu0p5`
- `Pi_m = 3.0`
- `Pi_f = 3.0`
- `Pi_U = 0.5`

Metrics:

- `Psucc_mean = 0.34765625`
- `MFPT_mean = 3.758848314606742`
- `eta_sigma_mean = 5.359477792560652e-06`

Interpretation:

- the fastest point is not the most successful or the most efficient
- this preserves the speed-versus-efficiency separation seen earlier
- the outer-frame fast point is a poor screening optimum because success collapses and efficiency is much weaker

## Outer-Frame Check

Best outer-frame point by success and efficiency:

- label: `full_outer_frame_pm3_pf0p1_pu0`
- `Pi_m = 3.0`
- `Pi_f = 0.1`
- `Pi_U = 0.0`
- `Psucc_mean = 0.7578125`
- `MFPT_mean = 11.745805412371134`
- `eta_sigma_mean = 1.6603607994222564e-05`

Interpretation:

- the outer frame does not beat the best inner-box candidates on either success or efficiency
- the first coarse scan does not suggest that the optimum is escaping to very large memory or very large delay

## Validation Controls

Sparse controls at `Pi_m = 1.0`, `Pi_f = 0.3` show:

- `no_feedback`, `Pi_U = 0.0`
  - `Psucc_mean = 0.478515625`
  - `MFPT_mean = 12.210989795918367`
  - `eta_sigma_mean = 7.885470067525823e-06`
- `no_feedback`, `Pi_U = 0.25`
  - `Psucc_mean = 0.46875`
  - `MFPT_mean = 7.176666666666667`
  - `eta_sigma_mean = 8.384878547210873e-06`
- `no_memory`, `Pi_U = 0.0`
  - `Psucc_mean = 0.48828125`
  - `MFPT_mean = 11.29191`
  - `eta_sigma_mean = 8.150262158209175e-06`
- `no_memory`, `Pi_U = 0.25`
  - `Psucc_mean = 0.53125`
  - `MFPT_mean = 11.082564338235295`
  - `eta_sigma_mean = 9.195751078968613e-06`

Reference full-branch points at the same center:

- `full_dense_inner_box_pm1_pf0p3_pu0`
  - `Psucc_mean = 0.748046875`
  - `MFPT_mean = 11.8927284595`
  - `eta_sigma_mean = 1.62192e-05`
- `full_dense_inner_box_pm1_pf0p3_pu0p25`
  - `Psucc_mean = 0.458984375`
  - `MFPT_mean = 5.9742765957`
  - `eta_sigma_mean = 8.4465e-06`

Interpretation:

- at the central comparison point with zero flow, the full branch clearly outperforms both sparse ablations in success and efficiency screening
- under weak positive flow at the same center, the full branch remains the fastest among the compared variants, while `eta_sigma_mean` is of similar order to the sparse controls

## Practical Readout

Current coarse-scan picture:

- the strongest success region sits near low memory and very low delay with zero flow
- the strongest efficiency screening signal sits near the same low-memory/low-delay edge but shifts toward weak positive flow
- the outer frame confirms that very large memory and delay do not dominate this first production scan
- the speed optimum remains separated from the success and efficiency optima

## Next Step

Recommended next step after this first look:

- do not expand the outer frame yet
- do not start adaptive refinement in this step
- use this completed coarse scan to define the first refinement envelope around the low-memory / low-delay corner of the inner box, especially near:
  - `Pi_m in [0.1, 0.3]`
  - `Pi_f in [0.05, 0.1]`
  - `Pi_U in [0.0, 0.25]`

Open caution:

- the best efficiency screening point lies on the lower-memory and lower-delay edge of the current inner box, so the next refinement stage should test whether the productive region bends further toward smaller values rather than toward the large-memory outer frame.
