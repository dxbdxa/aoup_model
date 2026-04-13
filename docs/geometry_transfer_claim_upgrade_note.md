# Geometry Transfer Claim Upgrade Note

## Scope

This note identifies exactly which claims are upgraded by the completed GF0/GF1/GF2 transfer package and which remain candidate-level.

- principle scope statement: [principle_scope_statement_v2.md](file:///home/zhuguolong/aoup_model/docs/principle_scope_statement_v2.md)
- geometry transfer principle note: [geometry_transfer_principle_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_principle_note.md)
- invariant table: [geometry_transfer_invariant_table.csv](file:///home/zhuguolong/aoup_model/outputs/tables/geometry_transfer_invariant_table.csv)
- transfer stress figure: [transfer_stress_figure.png](file:///home/zhuguolong/aoup_model/outputs/figures/geometry_transfer/transfer_stress_figure.png)

## Strengthened By Transfer

| invariant_name                          | classification   | interpretation                                                                                                   |
|:----------------------------------------|:-----------------|:-----------------------------------------------------------------------------------------------------------------|
| Timing-order backbone shape             | survives         | The pre-commit timing backbone keeps the same canonical ordering across GF0/GF1/GF2.                             |
| Arrival-order backbone shape            | survives         | The arrival-organization branch remains discriminative in the same direction across the tested family.           |
| Stale-vs-balanced timing penalty        | survives         | The stale comparator still reads as a slower pre-commit backbone rather than a different post-commit law.        |
| Reference scales and local coefficients | renormalizes     | Transfer is shape-level, while the absolute search scales and local encounter coefficients renormalize strongly. |

These rows justify upgrading the project language from a one-geometry mechanism note to a tested-family pre-commit principle:

- the timing backbone keeps the same canonical order across GF0/GF1/GF2
- the stale comparator still reads as a slower pre-commit branch rather than a different completion law
- the correct geometry-transfer reading is shape survival with coefficient renormalization

## Remain Only Candidate-Level

| invariant_name                           | classification   | interpretation                                                                                                          |
|:-----------------------------------------|:-----------------|:------------------------------------------------------------------------------------------------------------------------|
| Unique success selectivity scalar        | weakens          | The success branch stays on the selective edge, but one single scalar does not isolate it uniformly across GF1 and GF2. |
| Trap burden as a matched transfer signal | weakens          | Trap burden stays too geometry- and support-sensitive to upgrade into a robust transfer invariant.                      |

| claim_name                                  | note                                                                                |
|:--------------------------------------------|:------------------------------------------------------------------------------------|
| Single universal success selectivity scalar | Success stays selective, but no single scalar isolates it uniformly across GF1/GF2. |
| Trap burden as a transferable invariant     | Trap burden remains sparse and geometry-sensitive.                                  |
| Irregular GF3 geometry universality         | GF3 remains deferred, so broader universality is not upgraded yet.                  |

These claims should stay in Discussion or future-work language rather than being upgraded into the strongest Results statement.

## Explicitly Ruled Out Or Not Upgraded

| invariant_name             | classification   | interpretation                                                                                           |
|:---------------------------|:-----------------|:---------------------------------------------------------------------------------------------------------|
| Coefficient-exact identity | fails            | The tested family directly rules out coefficient-exact transfer as the current reading of the principle. |

| claim_name                      | note                                                          |
|:--------------------------------|:--------------------------------------------------------------|
| Post-commit completion transfer | The current transfer object stops at the pre-commit backbone. |

Interpretation:

- coefficient-exact universality is not the right reading of the tested-family transfer data
- post-commit completion transfer is not contradicted here, but it is not upgraded because it remains outside the transfer object

## Strongest Upgraded Claim

The strongest claim upgraded by transfer is:

> Across GF0, GF1, and GF2, the pre-commit backbone transfers at the level of shape: the canonical timing order, the stale-vs-balanced timing penalty, and the arrival-organization discriminator all survive, while the absolute reference scales and local coefficients renormalize rather than collapsing exactly.

## Still Candidate-Level

The following should remain candidate-level after the present transfer stage:

- any claim that one unique selectivity scalar always isolates the success branch
- any claim that trap burden is a robust geometry-invariant stale discriminator
- any claim beyond the clean GF0/GF1/GF2 family, especially the deferred GF3 stress geometry
- any post-commit completion transfer claim
