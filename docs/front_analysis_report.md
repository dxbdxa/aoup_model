# Front Analysis Report

## Scope

This report builds the final front-analysis package for the productive-memory ridge using the confirmatory scan as the primary dataset.

Primary inputs:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [confirmatory_scan_run_report.md](file:///home/zhuguolong/aoup_model/docs/confirmatory_scan_run_report.md)
- [confirmatory_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/confirmatory_scan_first_look.md)
- [final_front_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/final_front_candidates.csv)
- [confirmatory_front_analysis.json](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/confirmatory_front_analysis.json)

Confidence policy:

- all confirmatory points are kept in the working dataset
- `8192`-trajectory points are treated as highest-confidence anchors
- publication-facing winner separation uses CI-aware comparisons on the confirmatory winners

Dataset summary:

- working state points: `140`
- `8192` anchors: `6`
- Pareto candidates: `20`
- `Pi_f` support in confirmatory ridge: `[0.018, 0.025]`

## Publication-Ready Fronts

### Maximum `Psucc_mean`

- winner: `full_final_candidate_resample_pm0p08_pf0p025_pu0p1_n8192`
- winner location: `Pi_m = 0.08`, `Pi_f = 0.025`, `Pi_U = 0.1`
- winner value: `0.97412109375`
- winner CI: `[0.970454288114538, 0.97734345041294]`
- highest-confidence anchor: `full_final_candidate_resample_pm0p08_pf0p025_pu0p1_n8192` at `n_traj = 8192`

### Maximum `eta_sigma_mean`

- winner: `full_confirmatory_ridge_grid_pm0p18_pf0p018_pu0p15_n4096`
- winner location: `Pi_m = 0.18`, `Pi_f = 0.018`, `Pi_U = 0.15`
- winner value: `6.685949490215236e-05`
- winner CI: `[6.415550898232491e-05, 6.968156530021476e-05]`
- highest-confidence anchor: `full_final_candidate_resample_pm0p2_pf0p02_pu0p2_n8192` at `n_traj = 8192`

### Minimum `MFPT_mean`

- winner: `full_final_candidate_resample_pm0p1_pf0p018_pu0p3_n8192`
- winner location: `Pi_m = 0.1`, `Pi_f = 0.018`, `Pi_U = 0.3`
- winner value: `2.816089797639123`
- winner CI: `[2.7590000028704518, 2.871498713967931]`
- highest-confidence anchor: `full_final_candidate_resample_pm0p1_pf0p018_pu0p3_n8192` at `n_traj = 8192`

## Front Geometry

- the ridge remains tightly pinned in `Pi_f`, with front winners confined to `Pi_f = 0.018` to `0.025`
- `Pi_U` orders objective preference along the ridge: low flow for success, moderate flow for efficiency, high flow for speed
- `Pi_m` tunes where each objective sits on the ridge, but does not erase the `Pi_U` ordering
- the non-dominated set spans `20` confirmatory points, not just the three winners

Projection figures:

- [front_projection_PiU.png](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_projection_PiU.png)
- [front_projection_Pim.png](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_projection_Pim.png)
- [front_projection_Pif.png](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_projection_Pif.png)

## Uncertainty-Aware Separation

Top-k overlap counts:

|                                            |   5 |   10 |   20 |
|:-------------------------------------------|----:|-----:|-----:|
| ('Psucc_mean', 'MFPT_mean')                |   0 |    0 |    0 |
| ('Psucc_mean', 'eta_sigma_mean')           |   0 |    0 |    1 |
| ('Psucc_mean', 'eta_sigma_mean|MFPT_mean') |   0 |    0 |    0 |
| ('eta_sigma_mean', 'MFPT_mean')            |   0 |    0 |    0 |

Winner-distance summary:

| winner_a       | winner_b       |   delta_Pi_m |   delta_Pi_f |   delta_Pi_U |   euclidean_distance |   normalized_distance | b_separated_from_a_by_ci   | a_separated_from_b_by_ci   |
|:---------------|:---------------|-------------:|-------------:|-------------:|---------------------:|----------------------:|:---------------------------|:---------------------------|
| Psucc_mean     | eta_sigma_mean |         0.1  |       -0.007 |         0.05 |             0.112022 |              1.25407  | True                       | True                       |
| Psucc_mean     | MFPT_mean      |         0.02 |       -0.007 |         0.2  |             0.201119 |              1.42141  | True                       | True                       |
| eta_sigma_mean | MFPT_mean      |        -0.08 |        0     |         0.15 |             0.17     |              0.942884 | True                       | True                       |

Interpretation:

- top-5 overlap is zero for every objective pair
- top-10 overlap is zero for every objective pair
- top-20 overlap stays zero except for a single success/efficiency shared point
- each winner remains separated from the other winners on its own metric under CI-aware comparison

## Does the ridge encode a Pareto-like transport front?

Yes. The confirmatory scan is best described as **Pareto-like ridge**.

Reasoning:

- the non-dominated set is extended rather than collapsing to three isolated points
- front winners remain distinct, so the ridge has separated tips instead of one universal optimum
- overlap is negligible at `k = 5` and `k = 10`, which preserves practical objective specificity
- limited overlap only appears deeper in the ranked sets, which is consistent with a shared ridge backbone
- the strongest shared coordinate is the narrow `Pi_f` band, while `Pi_U` carries the dominant ordering signal

## Practical Decision Tradeoffs

- choose the success front when maximizing hit probability is the primary constraint
- choose the efficiency front when transport per dissipation is the main figure of merit
- choose the speed front when first-passage time dominates and some success loss is acceptable
- treat the `8192` anchors as the most reliable manuscript callouts, especially for the success and speed tips
- keep the efficiency tip tied to the local ridge family rather than forcing it onto the speed branch

## Output Bundle

- [front_overlap_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_overlap_summary.csv)
- [front_distance_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_distance_summary.csv)
- [pareto_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/pareto_candidates.csv)
- [front_conclusion_box.txt](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_conclusion_box.txt)

## Manuscript Quote

```text
The confirmatory ridge resolves into a narrow productive-memory front family rather than a single optimum. The best descriptor is 'Pareto-like ridge': The productive-memory structure is best described as a Pareto-like ridge with distinct front tips: the non-dominated set is extended, Pi_f stays tightly pinned, Pi_U orders the tradeoff, and winner separation survives CI-aware checks. The winner for success sits at (Pi_m, Pi_f, Pi_U) = (0.08, 0.025, 0.1), the efficiency winner at (0.18, 0.018, 0.15), and the speed winner at (0.1, 0.018, 0.3). Top-10 overlap counts remain zero for all front pairs, so Pi_U orders practical objective preference along the ridge without collapsing the three decision points into one.
```
