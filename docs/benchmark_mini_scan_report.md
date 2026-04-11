# Benchmark Mini-Scan Report

## Scope

This report summarizes the production benchmark mini-scan run executed with:

- the validated workflow contract
- the production reference scales in `outputs/summaries/reference_scales/reference_scales.json`
- unchanged legacy physics and adapter behavior

The scan was used to:

- probe a compact productive-memory parameter box
- test `dt` convergence
- test `Tmax` robustness
- test `n_traj` uncertainty
- produce production recommendations before any coarse scan execution

## Upstream Normalization Reference

Normalization reference taken from:

- [reference_scales.json](file:///home/zhuguolong/aoup_model/outputs/summaries/reference_scales/reference_scales.json)

Reference values:

- `tau_g = 7.337257462686567`
- `l_g = 3.6686287313432837`
- `tau_p = 1.0`

Dimensionless reporting in this scan uses:

- `Pi_m = tau_v / tau_g`
- `Pi_f = tau_f / tau_g`
- `Pi_U = U * tau_g / l_g`

## Scan Design

### Productive-memory box

Full branch:

- `Pi_m in {0.3, 1.0, 3.0}`
- `Pi_f in {0.1, 0.3, 1.0}`
- `Pi_U in {-0.25, 0.0, 0.25}`

Dimensional values:

- `tau_v in {2.20117723880597, 7.337257462686567, 22.0117723880597}`
- `tau_f in {0.7337257462686568, 2.20117723880597, 7.337257462686567}`
- `U in {-0.125, 0.0, 0.125}`

### Sparse ablation strip

At the central memory/delay point:

- `Pi_m = 1.0`
- `Pi_f = 0.3`
- `Pi_U in {-0.25, 0.0, 0.25}`

Variants:

- `no_memory`
- `no_feedback`

### Sensitivity checks

Central candidate:

- `Pi_m = 1.0`
- `Pi_f = 0.3`
- `Pi_U = 0.25`

Sensitivity axes:

- `dt in {0.005, 0.0025, 0.00125}`
- `Tmax in {15.0, 20.0, 30.0}`
- `n_traj in {256, 512, 1024}`

## Output Artifacts

Primary output tables:

- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/benchmark_mini_scan/summary.csv)
- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/benchmark_mini_scan/summary.parquet)

Phase metadata:

- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/summaries/benchmark_mini_scan/metadata.json)

Run size:

- `n_configs = 42`

## Main Outcomes

### Best efficiency inside the productive-memory box

Best `eta_sigma_mean` occurred at:

- scan label: `full_low_low_zero`
- dimensional:
  - `tau_v = 2.20117723880597`
  - `tau_f = 0.7337257462686568`
  - `U = 0.0`
- dimensionless:
  - `Pi_m = 0.3`
  - `Pi_f = 0.1`
  - `Pi_U = 0.0`

Metrics:

- `Psucc_mean = 0.79296875`
- `MFPT_mean = 7.847524630541873`
- `eta_sigma_mean = 2.77820358551725e-05`

### Best success probability inside the productive-memory box

The same point also maximized `Psucc_mean`:

- `full_low_low_zero`
- `Pi_m = 0.3`
- `Pi_f = 0.1`
- `Pi_U = 0.0`

### Fastest mean first-passage time inside the productive-memory box

Best `MFPT_mean` occurred at:

- scan label: `full_low_low_pos_weak`
- dimensional:
  - `tau_v = 2.20117723880597`
  - `tau_f = 0.7337257462686568`
  - `U = 0.125`
- dimensionless:
  - `Pi_m = 0.3`
  - `Pi_f = 0.1`
  - `Pi_U = 0.25`

Metrics:

- `Psucc_mean = 0.66796875`
- `MFPT_mean = 3.763318713450293`
- `eta_sigma_mean = 2.6161777257945783e-05`

### Interpretation

The compact scan points to a likely productive-memory region at:

- low memory ratio
- low feedback-delay ratio
- near-zero to weakly positive flow

In this box:

- zero flow gives the best success and best efficiency
- weak positive flow gives the fastest transport among successful trajectories

## Ablation Comparison

Central-strip ablations show:

- `full` substantially outperforms `no_memory` in efficiency near this region
- `no_feedback` can recover success under weak positive flow, but remains less efficient than the best full-branch point

This is enough to justify using the full branch as the main coarse-scan target while keeping ablations as validation controls.

## Stability Analysis

### `dt` convergence

Central candidate comparison:

- production `dt = 0.0025` vs fine `dt = 0.00125`
  - `Psucc_mean` relative change: `3.37%`
  - `MFPT_mean` relative change: `12.26%`
  - `eta_sigma_mean` relative change: `1.01%`
  - `wall_fraction_mean` relative change: `15.14%`
- coarse `dt = 0.005` vs fine `dt = 0.00125`
  - `Psucc_mean` relative change: `4.81%`
  - `MFPT_mean` relative change: `21.06%`
  - `eta_sigma_mean` relative change: `2.31%`

Interpretation:

- `dt = 0.0025` is adequate for `Psucc_mean` and `eta_sigma_mean`
- `MFPT_mean` still moves noticeably with `dt`, but `0.0025` is materially better than `0.005`
- `0.00125` is not necessary as the production default for this stage

### `Tmax` robustness

Central candidate comparison:

- production `Tmax = 20.0` vs long `Tmax = 30.0`
  - `Psucc_mean` relative change: `8.20%`
  - `MFPT_mean` relative change: `18.35%`
  - `eta_sigma_mean` relative change: `27.98%`
- short `Tmax = 15.0` vs long `Tmax = 30.0`
  - `Psucc_mean` relative change: `15.57%`
  - `MFPT_mean` relative change: `24.57%`
  - `eta_sigma_mean` relative change: `46.80%`

Interpretation:

- `Tmax = 15.0` is too short
- `Tmax = 20.0` is improved but still censors the central candidate enough to move efficiency
- `Tmax = 30.0` is the safer production choice for coarse screening

### `n_traj` uncertainty

Central candidate comparison:

- production `n_traj = 512` vs high `n_traj = 1024`
  - `Psucc_mean` relative change: `8.82%`
  - `MFPT_mean` relative change: `2.80%`
  - `eta_sigma_mean` relative change: `13.05%`

Observed behavior:

- `MFPT_mean` is reasonably stable by `512`
- `Psucc_mean` is usable at `512` for trend finding, but still noisy
- `eta_sigma_mean` is more sensitive to Monte Carlo noise and should not be overinterpreted at coarse-scan resolution

## Recommendations

### Production `dt`

Recommended:

- `dt = 0.0025`

Reason:

- stable enough for `Psucc_mean` and `eta_sigma_mean`
- meaningfully better than `0.005` on `MFPT_mean`
- avoids doubling the cost to `0.00125`

### Production `Tmax`

Recommended:

- `Tmax = 30.0`

Reason:

- `20.0` still shows nontrivial censoring sensitivity at the central candidate
- `30.0` is the first tested horizon that behaves robustly enough for production coarse screening

### Coarse-scan default `n_traj`

Recommended:

- `n_traj = 512`

Reason:

- acceptable compromise between Monte Carlo stability and scan budget
- `MFPT_mean` is already close to the `1024` estimate
- use `1024+` only in later refinement or reference-quality checks

## Which Observables Are Stable Enough For Coarse Scan?

Recommended primary coarse-scan observables:

- `Psucc_mean`
- `MFPT_mean`
- coarse ordering and location of the high-efficiency region using `eta_sigma_mean` as a screening signal only

Recommended secondary observables until refinement:

- `eta_sigma_mean` for precise ranking
- `Sigma_drag_mean`
- `wall_fraction_mean`
- `trap_time_mean`
- `trap_count_mean`
- `FPT_q90`

Reason:

- these observables show stronger sensitivity to `Tmax`, `n_traj`, or both
- they are still useful diagnostically, but should not anchor final scientific claims at coarse resolution

## Bottom Line

The production benchmark mini-scan supports the following pre-coarse-scan defaults:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 512`

It also identifies a likely productive-memory region near:

- `Pi_m ~ 0.3`
- `Pi_f ~ 0.1`
- `Pi_U in [0.0, 0.25]`
