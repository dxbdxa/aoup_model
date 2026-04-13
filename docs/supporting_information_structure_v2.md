# Supporting Information Structure V2

## Purpose

This document separates the broad-reader main story from the technical record that must remain available to defend the claims.

Primary framing source:

- [storyline_reset_master.md](/home/zhuguolong/aoup_model/docs/storyline_reset_master.md)

Supporting sources:

- [principle_evidence_matrix.md](/home/zhuguolong/aoup_model/docs/principle_evidence_matrix.md)
- [claim_status_table.md](/home/zhuguolong/aoup_model/docs/claim_status_table.md)
- [out_of_scope_statement.md](/home/zhuguolong/aoup_model/docs/out_of_scope_statement.md)

## SI Philosophy

The Supporting Information should do three things:

- document how the main claims were built
- show the technical robustness of those claims
- keep the scope limits explicit

It should not function as an alternate main text. The main text carries the question and the discoveries. The SI carries the workflow, validation, and technical boundaries.

## Recommended SI Structure

## SI Section 1: Model, geometry, and nondimensionalization

Include:

- model equations
- control definitions
- geometry definitions for `GF0`, `GF1`, and `GF2`
- reference scales and nondimensionalization details

Why this is SI:

- necessary for reproduction
- too detailed for the narrative opening

Main-text dependency:

- supports the system schematic and control definitions in Figure 1

## SI Section 2: Search protocol and scan construction

Include:

- coarse, refinement, precision, and confirmatory scan workflow
- sampling budgets
- search bounds
- point-selection logic

Why this is SI:

- important for transparency
- not part of the Nature/Science-style narrative spine

Main-text dependency:

- supports the ridge discovery without forcing the Results to read like a pipeline report

## SI Section 3: Front construction, uncertainty, and robustness

Include:

- Pareto-candidate generation
- overlap tables
- CI-aware winner separation
- alternative front projections
- candidate inventories and anchor-point details

Why this is SI:

- technical proof of the ridge
- too detailed for the main figure sequence

Main-text dependency:

- supports the claim that the ridge is extended and the tips are distinct

## SI Section 4: Canonical operating points and mechanism observables

Include:

- frozen canonical-point definitions
- refined observable definitions
- matched balanced-ridge versus stale-control comparison tables
- additional mechanism discriminator summaries

Why this is SI:

- the main text needs only the most legible mechanistic contrasts
- the full observable inventory is supporting evidence

Main-text dependency:

- supports the claim that pre-commit timing and trap burden separate ridge from off-ridge behavior

## SI Section 5: Pre-commit state graph, fitting logic, and deferred crossing branch

Include:

- full state definitions
- transition tables
- fit methodology
- alternative coarse-graining options
- reasons for stopping the first reduced theory at `gate_commit`
- explicit note on the sparse crossing branch

Why this is SI:

- this is critical technical support
- too dense for the broad-reader main text

Main-text dependency:

- supports the central claim that selection is visible before final crossing

## SI Section 6: Geometry transfer protocol and renormalization detail

Include:

- full geometry-transfer protocol
- canonical replay details
- renormalization calculations
- any local slice checks used to distinguish survival from breakdown
- deferred stress-test geometry plan

Why this is SI:

- the main text should show only the high-level logic of shape survival and coefficient renormalization
- the protocol detail belongs in the technical record

Main-text dependency:

- supports the tested-family transfer claim while keeping the scope narrow

## SI Section 7: Thermodynamic bookkeeping and metric definitions

Include:

- drag-dissipation proxy definitions
- `eta_sigma`, `eta_completion_drag`, and `eta_trap_drag` definitions
- numerator and denominator logic
- bookkeeping caveats
- additional ranking and sensitivity tables

Why this is SI:

- the main text should emphasize what changes physically, not every bookkeeping detail

Main-text dependency:

- supports the claim that the ridge survives current metric upgrade

## SI Section 8: Claim hierarchy, scope boundaries, and non-claims

Include:

- principle evidence matrix
- claim status table
- out-of-scope statement
- explicit list of supported, scoped, and conjectural claims

Why this is SI:

- this is the manuscript's safety rail
- it prevents Supporting Information detail from being misread as support for stronger claims than the paper actually makes

Main-text dependency:

- supports conservative phrasing in the abstract, Discussion, and figure captions

## SI Section 9: Supplementary figures, tables, and data manifests

Include:

- file manifests
- additional plots
- auxiliary tables
- data-source paths for reproduced figures

Why this is SI:

- archive value and reproducibility

## What Must Leave The Main Text

Move these items out of the main paper unless a journal format absolutely requires them:

- scan-stage chronology
- full parameter-grid inventories
- complete transition tables
- fitting diagnostics
- geometry calibration tables
- metric derivations in full
- long lists of caveats that interrupt the central story

The main text should cite these items, not narrate them.

## What Must Stay Visible Even In SI

The SI should preserve the same explicit exclusions as the main paper:

- not a full crossing-completion law
- not unrestricted universality
- not coefficient-exact geometry collapse
- not full thermodynamic closure

These exclusions should appear near the front of the SI claim-hierarchy section, not only at the end.

## Main Text To SI Mapping

Use this simple mapping rule:

1. If a detail is required for a broad reader to understand the paper's answer to the selection-timing question, keep it in the main text.
2. If a detail mainly validates how that answer was extracted, move it to SI.
3. If a detail concerns workflow, calibration, or alternative constructions, default to SI.

## Bottom Line

The Supporting Information should make the paper stronger by carrying the technical load, while letting the main text stay focused on one message: across the tested family and within current bookkeeping, transport performance is selected before final crossing by a pre-commit backbone that generates a Pareto-like ridge.
