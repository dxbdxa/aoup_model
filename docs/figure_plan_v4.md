# Figure Plan V4

## Overall Strategy

This package upgrades the manuscript from a one-maze optimization paper to a principle-paper. The new central claim is not merely that one geometry contains a productive optimum family, but that the project now supports a geometry-tested, thermodynamically upgraded pre-commit transport principle with explicit scope limits.

Standardized notation used in all panels:

- `Pi_m = tau_mem / tau_g`
- `Pi_f = tau_f / tau_g`
- `Pi_U = U / v0`
- `tau_g = 7.337`
- `l_g = 3.669`

Source policy:

- front geometry and winner separation come from `confirmatory_scan` plus front analysis
- mechanism language comes from the refined mechanism dataset and pre-commit gate theory
- geometry-general scope comes from the first geometry-transfer validation
- thermodynamic branch reordering comes from the efficiency-metric upgrade package
- full crossing law and full thermodynamic closure remain explicitly outside scope

## Figure Logic

The revised paper should read as a principle progression rather than a search chronology.

1. define the transport problem and the pre-commit object
2. establish the Pareto-like ridge quantitatively
3. explain the ridge through the pre-commit backbone and show branch reordering under the thermodynamic upgrade
4. show that the backbone shape transfers across geometries while coefficients renormalize

The scan-localization history remains useful, but it should become supporting logic rather than the main narrative center.

## Figure 1

Title:

- Problem setup, reference scales, and the pre-commit transport object

Role:

- define the gated transport problem, reference scales, and nondimensional controls
- introduce the search-to-residence-to-commit backbone before any optimization plots appear
- make clear that the paper is about a transport principle, not only about finding one best point

Recommended panels:

- stylized geometry and navigation-field schematic
- definition of `l_g`, `tau_g`, `Pi_m`, `Pi_f`, and `Pi_U`
- compact state-graph inset for `bulk -> wall_sliding -> gate_approach -> gate_residence_precommit -> gate_commit`
- note that crossing-completion structure is deferred

Key takeaway:

- the primary transferable object is the pre-commit backbone

## Figure 2

Title:

- Quantitative discovery of the Pareto-like productive ridge

Role:

- establish the ridge from the confirmatory package, not as a single optimum and not as a purely local anecdote
- keep enough localization history to show that the final ridge claim is numerically earned
- prepare the reader for the branch structure that Figure 3 will explain

Recommended panels:

- compact localization strip from coarse to confirmatory stages
- confirmatory Pareto-like ridge in parameter space
- top-k non-overlap / CI-aware winner separation summary
- front-tip map showing success, efficiency, and speed branches

Key takeaway:

- the productive-memory structure is a narrow Pareto-like ridge with distinct front tips

## Figure 3

Figure 3 should remain the centerpiece.

Title:

- Centerpiece: pre-commit backbone principle and branch reordering on the ridge

Role:

- remain the centerpiece figure
- integrate the three most important principle-paper elements into one figure:
  - Pareto-like ridge
  - pre-commit backbone principle
  - branch reordering under thermodynamic upgrade
- explicitly convert the project from ridge discovery to principle interpretation

Required panels:

- ridge structure panel from confirmatory front analysis
- pre-commit backbone panel showing delay admissibility, productive smoothing, and flow ordering
- matched ridge-versus-stale mechanism panel emphasizing first-commit delay, wall dwell before commitment, and recycling burden
- branch-reordering panel comparing `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag`

Required takeaways:

- the ridge is created before final crossing
- the success, efficiency, and speed branches correspond to different regions of the same pre-commit backbone
- thermodynamic upgrade changes which branch looks best without destroying the ridge
- full crossing law and full thermodynamic closure remain outside scope

## Figure 4

Title:

- Geometry-tested universality: shape-level transfer and coefficient-level renormalization

Role:

- explicitly show that the paper is no longer centered on one maze
- make the distinction between shape-level universality and coefficient-level renormalization visually unavoidable
- connect geometry transfer back to the pre-commit principle rather than to raw full-success collapse

Required panels:

- geometry gallery for `GF0`, `GF1`, and `GF2`
- backbone-ordering comparison across geometries
- renormalized-scale summary showing what shifts in `tau_g`, `l_g`, and local encounter baselines
- verdict panel distinguishing transferred structure from renormalized coefficients

Key takeaway:

- backbone shape transfers across the tested family while coefficients renormalize

## Supporting Hierarchy

- Figure 3 is the centerpiece
- Figure 4 is the scope-expansion figure that moves the project beyond one geometry
- Figure 2 is the quantitative discovery figure that secures the ridge evidence
- Figure 1 defines the transport object and notation for the principle-paper framing

## What should be de-emphasized from V3

De-emphasize:

- treating the localization history as the main story
- presenting the paper as a search for one efficiency optimum
- implying that the reference geometry alone carries the full principle claim

Emphasize:

- branch structure on a common ridge
- pre-commit mechanism before crossing
- geometry-tested shape-level generality
- conservative thermodynamic upgrade

## Package Deliverables

Revised package outputs should live in `outputs/figures/main_figures_revised/` and include at minimum:

- revised package manifest
- storyboard or overview graphic for the four figures
- final figure files once the panel builders are updated

## Bottom Line

The revised main-figure package should tell one story:

- a Pareto-like ridge is discovered quantitatively
- the ridge is explained by a pre-commit backbone principle
- the backbone survives geometry transfer at the level of shape
- a thermodynamic upgrade changes branch preference without overturning the principle
