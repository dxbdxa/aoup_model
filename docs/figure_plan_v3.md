# Figure Plan V3

## Overall Strategy

This package builds the manuscript main-figure set around one central claim: the productive-memory structure is best described as a Pareto-like ridge rather than a single optimum.

Standardized notation used in all panels:

- `Pi_m = tau_mem / tau_g`
- `Pi_f = tau_f / tau_g`
- `Pi_U = U / v0`
- `tau_g = 7.337`
- `l_g = 3.669`

Source policy:

- final quantitative claims use `confirmatory_scan`
- coarse / refinement / precision scans are used only as localization history
- front separation and ridge-vs-basin inference use the confirmatory front-analysis package

## Figure 1

Title:

- Model, geometry, reference scales, and dimensionless controls

Role:

- define the geometry-level transport problem
- fix the notation before the scan history begins
- show how `tau_g` and `l_g` anchor `Pi_m`, `Pi_f`, and `Pi_U`

## Figure 2

Title:

- Localization from coarse scan to confirmed productive-memory ridge

Role:

- show how the search contracts from a broad parameter region to a narrow low-delay ridge
- make it visually clear that the final claim does not come from the coarse scan alone
- connect coarse, refinement, precision, and confirmatory stages in one localization sequence

## Figure 3

Title:

- Pareto-like ridge with distinct success / efficiency / speed front tips

Role:

- centerpiece figure
- use `confirmatory_scan` as the main quantitative source
- make the ridge-vs-basin conclusion explicit
- show distinct front tips, top-k separation, and parameter-space separation

Required takeaways:

- the front is extended, not point-like
- the top-10 objective sets do not overlap
- `Pi_f` remains tightly pinned
- `Pi_U` orders the front tips

## Figure 4

Title:

- Physical mechanism and transport-task tradeoff interpretation

Role:

- convert the confirmed ridge into a compact physical reading
- present delay admissibility, productive memory band, and flow ordering as the organizing interpretation
- keep the distinction clear between confirmed numerical structure and mechanistic interpretation

## Visual Hierarchy

- Figure 3 is the quantitative centerpiece
- Figure 2 provides localization history
- Figure 4 provides the physical reading
- Figure 1 standardizes notation and reference scales
