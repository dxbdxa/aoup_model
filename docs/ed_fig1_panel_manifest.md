# Extended Data Figure 1 Panel Manifest

## Scope

This note documents the panel logic for Extended Data Figure 1, which is about scan localization chronology and numerical search history rather than about the final principle claim.

Primary data sources:

- [coarse summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/coarse_scan/summary.parquet)
- [refinement summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/refinement_scan/summary.parquet)
- [precision summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/precision_scan/summary.parquet)
- [confirmatory summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [ED Figure 1 PNG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig1_scan_localization_history.png)
- [ED Figure 1 SVG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig1_scan_localization_history.svg)

## Visual Language

- every panel uses log-scaled `Pi_m` on the x-axis and log-scaled `Pi_f` on the y-axis
- point color encodes a stage-local composite screening score built from normalized `Psucc_mean`, `eta_sigma_mean`, and inverse `MFPT_mean`
- open black circles mark the top stage-local screening candidates
- blue, green, and red diamonds mark the stage-local success, efficiency, and speed winners
- dashed chronology boxes show the next-stage search windows
- locator insets show each panel's zoom level within the full search frame
- stars in the confirmatory panel mark `8192`-trajectory re-evaluations
- per-panel note boxes report the number of state points and the trajectory count used at that stage

## Panel Logic

### Panel A

- title: `Coarse scan overview and outer search frame`
- purpose: show the broad initial productive region with outer-frame context
- chronology overlays: refinement, precision, and confirmatory search windows
- emphasis: broad search coverage rather than final ridge interpretation

### Panel B

- title: `Refinement scan within the low-Pi_f target window`
- purpose: show contraction toward the low-`Pi_f` productive family
- chronology overlays: precision and confirmatory search windows
- emphasis: narrowing of the active search region rather than final front geometry

### Panel C

- title: `Precision scan around the local ridge family`
- purpose: show local resolution of success, efficiency, and speed tips on the narrowed ridge family
- chronology overlays: confirmatory search window
- emphasis: local objective-tip separation before uncertainty-reduced confirmation

### Panel D

- title: `Confirmatory scan with uncertainty-reduced local structure`
- purpose: show the uncertainty-reduced final local search structure
- chronology overlays: none
- emphasis: re-evaluated anchor points and final local refinement, not the full principle claim

## Why this does not duplicate Main Figure 2

- this extended-data figure uses `Pi_m`-`Pi_f` search maps with stage-local screening scores and chronology boxes
- main Figure 2 uses the confirmatory ridge itself, front-tip overlap, and objective-space separation to make the core structural claim
- Extended Data Figure 1 is therefore about how the search converged, not about the final ceiling claim

## Dataset Sizes

- `coarse_scan`: `60` state points, `Pi_m` in `[0.100, 10.000]`, `Pi_f` in `[0.050, 3.000]`
- `refinement_scan`: `244` state points, `Pi_m` in `[0.030, 3.000]`, `Pi_f` in `[0.020, 0.300]`
- `precision_scan`: `130` state points, `Pi_m` in `[0.050, 0.250]`, `Pi_f` in `[0.020, 0.030]`
- `confirmatory_scan`: `146` state points, `Pi_m` in `[0.080, 0.220]`, `Pi_f` in `[0.018, 0.025]`

## Bottom Line

Extended Data Figure 1 exists to show the narrowing of the numerical search process from a broad coarse scan to a resolved local confirmatory structure. It supports confidence in the convergence history without competing with the main-text ridge and principle figures.
