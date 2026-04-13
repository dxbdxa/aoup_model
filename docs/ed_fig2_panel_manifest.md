# Extended Data Figure 2 Panel Manifest

## Scope

This note documents the panel logic for Extended Data Figure 2, which provides detailed support for the main-text claim that the productive region forms a Pareto-like ridge with distinct success, efficiency, and speed tips.

Primary data sources:

- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [front_overlap_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_overlap_summary.csv)
- [front_distance_summary.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/front_distance_summary.csv)
- [pareto_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/front_analysis/pareto_candidates.csv)
- [ED Figure 2 PNG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig2_front_analysis_detail.png)
- [ED Figure 2 SVG](file:///home/zhuguolong/aoup_model/outputs/figures/extended_data/ed_fig2_front_analysis_detail.svg)

## Visual Language

- blue, green, and red retain the `success`, `efficiency`, and `speed` front naming from the completed front-analysis package
- top-row panels project the top-20 front members onto `Pi_m`, `Pi_f`, and `Pi_U` while keeping all confirmatory points as a light reference rug
- diamonds mark the front winners and open black circles mark `8192` anchors that lie on the plotted front
- lower-row panels report overlap counts, parameter-space winner distances, and CI-aware confidence callouts without adding new interpretation

## Panel Logic

### Panel A

- title: `Front projection in Pi_m`
- purpose: show where the success, efficiency, and speed fronts sit along `Pi_m`
- quantitative note: the three winners sit at `Pi_m = 0.08`, `0.18`, and `0.10`

### Panel B

- title: `Front projection in Pi_f`
- purpose: show the tight `Pi_f` pinning of the front family
- quantitative note: the front remains concentrated on `Pi_f = 0.018` to `0.025`

### Panel C

- title: `Front projection in Pi_U`
- purpose: show that `Pi_U` orders objective preference along the ridge
- quantitative note: the winners sit at `Pi_U = 0.10`, `0.15`, and `0.30`

### Panel D

- title: `Top-k overlap for ranked front sets`
- purpose: report overlap counts and Jaccard indices for `k = 5`, `10`, and `20`
- quantitative note: the only nonzero pairwise overlap count is `1` at `top-20` for `success vs efficiency`

### Panel E

- title: `Winner-distance summary in parameter space`
- purpose: show the three winner locations in `(Pi_U, Pi_m)` with `Pi_f` labels and pairwise normalized distances
- quantitative note: pairwise normalized distances span `0.94` to `1.42`

### Panel F

- title: `CI-aware winner callout and anchor support`
- purpose: report the completed uncertainty-aware checks already used in the front-analysis package
- quantitative note: directional CI checks pass in `6/6` cases and the confirmatory set contains `6` anchors

## Why this supports rather than replaces Main Figure 2

- the main text keeps the cleaner claim-bearing view of ridge structure and front-tip separation
- Extended Data Figure 2 carries the denser front-analysis detail: per-axis projections, top-k overlap bookkeeping, parameter-distance bookkeeping, and confidence callouts
- this figure therefore supports the main-text claim quantitatively without becoming the primary interpretive figure

## Bottom Line

Extended Data Figure 2 is the detailed numerical support layer for the front-analysis package. It keeps the separation structure explicit, quantitative, and uncertainty-aware while staying within the already completed front-analysis outputs.
