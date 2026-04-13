# Geometry Transfer Evidence Table

## Scope

This note compresses the GF0/GF1/GF2 transfer evidence into a compact invariant table for principle validation.

- canonical transfer summary: [canonical_transfer_summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/geometry_transfer/canonical_transfer_summary.csv)
- reference extraction summary: [reference_extraction_summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/geometry_transfer/reference_extraction_summary.csv)
- invariant table: [geometry_transfer_invariant_table.csv](file:///home/zhuguolong/aoup_model/outputs/tables/geometry_transfer_invariant_table.csv)
- stress figure: [transfer_stress_figure.png](file:///home/zhuguolong/aoup_model/outputs/figures/geometry_transfer/transfer_stress_figure.png)
- geometry transfer run report: [geometry_transfer_run_report.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_run_report.md)

## Verdict Classes

- `survives`: the same shape-level invariant is preserved across GF0/GF1/GF2.
- `renormalizes`: the invariant persists only after accepting geometry-dependent coefficient shifts.
- `weakens`: the signal is still visible but no longer strong enough to upgrade into a clean tested-family claim.
- `fails`: the tested family directly contradicts the stronger invariant claim.

## Compact Invariant Table

| invariant_id   | invariant_name                           | invariant_group   | gf0_reference                                                                                                               | gf1_result                                                                                                      | gf2_result                                                                                                      | classification   | claim_effect   | interpretation                                                                                                          |
|:---------------|:-----------------------------------------|:------------------|:----------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------|:-----------------|:---------------|:------------------------------------------------------------------------------------------------------------------------|
| INV1           | Timing-order backbone shape              | shape             | delay order `speed < balanced < stale < efficiency < success`; wall order `speed < balanced < stale < efficiency < success` | delay `speed < balanced < stale < efficiency < success`; wall `speed < balanced < stale < efficiency < success` | delay `speed < balanced < stale < efficiency < success`; wall `speed < balanced < stale < efficiency < success` | survives         | strengthens    | The pre-commit timing backbone keeps the same canonical ordering across GF0/GF1/GF2.                                    |
| INV2           | Arrival-order backbone shape             | shape             | `residence_given_approach` order `speed > stale > balanced > efficiency > success`                                          | `speed > stale > balanced > efficiency > success`                                                               | `speed > stale > balanced > efficiency > success`                                                               | survives         | strengthens    | The arrival-organization branch remains discriminative in the same direction across the tested family.                  |
| INV3           | Stale-vs-balanced timing penalty         | shape             | delay `1.6677` -> `1.7356`, wall `0.5026` -> `0.5250`                                                                       | delay `2.8584` -> `2.9964`, wall `0.7422` -> `0.7733`                                                           | delay `2.6434` -> `2.7049`, wall `0.9112` -> `0.9347`                                                           | survives         | strengthens    | The stale comparator still reads as a slower pre-commit backbone rather than a different post-commit law.               |
| INV4           | Unique success selectivity scalar        | selectivity       | top `p_reach_commit` = `OP_SUCCESS_TIP`; top `commit_given_residence` = `OP_SUCCESS_TIP`                                    | top `p_reach_commit` = `None`; top `commit_given_residence` = `OP_STALE_CONTROL_OFF_RIDGE`                      | top `p_reach_commit` = `None`; top `commit_given_residence` = `OP_SUCCESS_TIP`                                  | weakens          | candidate_only | The success branch stays on the selective edge, but one single scalar does not isolate it uniformly across GF1 and GF2. |
| INV5           | Reference scales and local coefficients  | coefficient       | Reference family fixes the baseline coefficients.                                                                           | `tau_g/GF0 = 2.73`, `ell_g/GF0 = 2.73`, `wall_frac/GF0 = 1.54`, `commit_events/GF0 = 0.43`                      | `tau_g/GF0 = 2.73`, `ell_g/GF0 = 2.73`, `wall_frac/GF0 = 1.78`, `commit_events/GF0 = 0.90`                      | renormalizes     | strengthens    | Transfer is shape-level, while the absolute search scales and local encounter coefficients renormalize strongly.        |
| INV6           | Coefficient-exact identity               | coefficient       | Exact identity would require all geometry-renormalized coefficients to stay near `1` relative to GF0.                       | tau_g ratio `2.73`, ell_g ratio `2.73`, wall_fraction ratio `1.54`                                              | tau_g ratio `2.73`, ell_g ratio `2.73`, wall_fraction ratio `1.78`                                              | fails            | ruled_out      | The tested family directly rules out coefficient-exact transfer as the current reading of the principle.                |
| INV7           | Trap burden as a matched transfer signal | weak_signal       | balanced `0.000000`, stale `0.000250`                                                                                       | balanced `0.000000`, stale `0.000000`                                                                           | balanced `0.002153`, stale `0.000000`                                                                           | weakens          | candidate_only | Trap burden stays too geometry- and support-sensitive to upgrade into a robust transfer invariant.                      |

## Evidence Summary

- survives: `3`
- renormalizes: `1`
- weakens: `2`
- fails: `1`

## Practical Readout

- the backbone shape transfers most cleanly in the timing order and the stale-vs-balanced timing penalty
- arrival organization also transfers in the same canonical order
- the scale variables do not transfer identically; they renormalize strongly
- trap burden and any single selectivity scalar remain weaker than the shape-level timing evidence
