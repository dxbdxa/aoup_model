# Principle Evidence Matrix

## Scope

This note maps the current project claims to their direct supporting evidence and classifies each claim conservatively using only completed project documents and results.

Primary sources:

- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)
- [theory_compression_note.md](file:///home/zhuguolong/aoup_model/docs/theory_compression_note.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [general_principle_candidates.md](file:///home/zhuguolong/aoup_model/docs/general_principle_candidates.md)
- [geometry_transfer_plan.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_plan.md)
- [geometry_family_spec.md](file:///home/zhuguolong/aoup_model/docs/geometry_family_spec.md)
- [thermodynamic_bookkeeping.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_bookkeeping.md)
- [efficiency_metric_upgrade.md](file:///home/zhuguolong/aoup_model/docs/efficiency_metric_upgrade.md)
- [thermodynamic_upgrade_discussion.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_upgrade_discussion.md)
- [principle_integration_note.md](file:///home/zhuguolong/aoup_model/docs/principle_integration_note.md)
- [claim_hierarchy_v1.md](file:///home/zhuguolong/aoup_model/docs/claim_hierarchy_v1.md)

Classification key:

- `confirmed`: directly demonstrated by completed analysis in the current project scope
- `supported but scoped`: strongly supported in the tested scope, but not yet broad enough for an unrestricted general claim
- `still conjectural`: motivated by current results, but still lacking a decisive supporting result

## Evidence Matrix

| Claim | Evidence source | Confidence level | Current limitation | What would falsify it? |
|---|---|---|---|---|
| The productive-memory structure is a Pareto-like ridge rather than a single optimum. | `front_analysis_report.md`; `principle_integration_note.md` | confirmed | Established on the current scan family and current objective set only. | A denser confirmatory analysis showing collapse to one dominant optimum or disappearance of the extended non-dominated set. |
| Success, efficiency, and speed occupy distinct front tips rather than one shared winner. | `front_analysis_report.md`; `theory_compression_note.md` | confirmed | Distinctness is established for the present metrics and current confirmatory scan. | A corrected or better-resolved front analysis showing large top-rank overlap or one point dominating all three criteria. |
| The ridge is narrow in delay and ordered mainly by flow along its branches. | `front_analysis_report.md`; `theory_compression_note.md` | confirmed | This ordering is empirical, not yet a closed-form law. | A re-analysis showing broad `Pi_f` support or no stable branch ordering by `Pi_U`. |
| The decisive competitive structure is already visible before final crossing. | `gate_theory_principle_note.md`; `principle_integration_note.md` | supported but scoped | Supported through refined mechanism analysis and pre-commit theory, but not yet through a full completion-layer decomposition. | A completion-aware analysis showing that pre-commit observables fail to separate branches and that the branch structure is created mainly after commitment. |
| The most robust current mechanism is a delay-admissible, memory-smoothed, flow-ordered pre-commit backbone. | `gate_theory_principle_note.md`; `general_principle_candidates.md`; `claim_hierarchy_v1.md` | supported but scoped | Mechanism is reduced and qualitative; efficiency and crossing layers remain incomplete. | A better-resolved reduced theory showing that delay, memory, and flow do not play the claimed organizing roles or that another state structure explains the ridge more directly. |
| The first transferable object is backbone shape rather than full crossing success. | `geometry_transfer_plan.md`; `geometry_family_spec.md`; `principle_integration_note.md` | supported but scoped | Based on the completed first transfer stage only; stress-test geometry remains deferred. | A transfer validation showing that the pre-commit backbone ordering itself collapses even when crossing-specific outcomes are ignored. |
| Shape-level universality survives across `GF0`, `GF1`, and `GF2`, while coefficients renormalize. | `principle_integration_note.md`; `claim_hierarchy_v1.md`; `thermodynamic_upgrade_discussion.md` | supported but scoped | Tested-family result only; not yet coefficient-exact and not yet stress-tested on irregular labyrinths. | A completed transfer on the current tested family showing incompatible backbone ordering, or a broader geometry test showing no stable shape-level transfer. |
| The project has moved beyond one gated maze at the level of principle shape. | `principle_integration_note.md`; `claim_hierarchy_v1.md` | supported but scoped | True only at the level of tested-family backbone shape, not full completion law. | Evidence that the current transfer result was an artifact of coarse renormalization and does not hold once transfer observables are sharpened. |
| `eta_sigma` is useful for screening but is not the full thermodynamic answer. | `thermodynamic_bookkeeping.md`; `thermodynamic_upgrade_discussion.md` | confirmed | Still a drag-normalized proxy, not a full efficiency. | Discovery that the implemented bookkeeping already contains the missing propulsion, controller, information, and completion terms, or that `eta_sigma` fails even as a stable screening metric. |
| `eta_completion_drag` is the strongest directly computed metric for manuscript-level thermodynamic discussion. | `efficiency_metric_upgrade.md`; `thermodynamic_upgrade_discussion.md`; `claim_hierarchy_v1.md` | confirmed | Strongest among currently computed metrics only; denominator remains drag-only. | A computed metric already present in the project outperforming it in physical interpretability while staying equally direct and within current bookkeeping. |
| The ridge survives the thermodynamic upgrade, even though the preferred efficient branch changes. | `efficiency_metric_upgrade.md`; `thermodynamic_upgrade_discussion.md`; `principle_integration_note.md` | confirmed | Established for the compact current metric family, not for arbitrary future cost definitions. | An upgraded metric built from currently available quantities that collapses the ridge or merges the efficient branch with a single universal optimum. |
| Trap-aware refinement does not qualitatively change the leading branch on the competitive ridge. | `efficiency_metric_upgrade.md`; `thermodynamic_upgrade_discussion.md` | confirmed | This result uses current trap-aware proxy construction and current scan observables only. | A corrected trap-aware metric built from the same completed data showing a different leading branch among the competitive ridge points. |
| The whole-project storyline supports a geometry-tested, thermodynamically upgraded pre-commit transport principle. | `principle_integration_note.md`; `claim_hierarchy_v1.md` | supported but scoped | This is an integrated project-level claim with explicit exclusions for full crossing law and full thermodynamic closure. | Failure of any one of the four completed packages to remain internally consistent with the others, especially geometry transfer or metric-upgrade survival. |
| The same principle may extend to a fuller completion-layer transport law. | `principle_integration_note.md`; `claim_hierarchy_v1.md` | still conjectural | This is explicitly identified as the main next extension, not a completed result. | A completion-layer study showing that post-commit organization obeys a different principle incompatible with the current pre-commit backbone claim. |
| A broader stress-test geometry family will preserve the same shape-level principle. | `claim_hierarchy_v1.md`; `geometry_transfer_plan.md` | still conjectural | `GF3_RANDOM_LABYRINTH_STRESS_TEST` remains deferred. | A completed stress-test geometry run showing breakdown of the backbone ordering despite reasonable renormalization. |
| A full thermodynamic closure will preserve the same qualitative ridge logic. | `thermodynamic_bookkeeping.md`; `thermodynamic_upgrade_discussion.md`; `claim_hierarchy_v1.md` | still conjectural | Full entropy production and completion-layer costs are not yet computed. | A fuller bookkeeping showing that once missing cost channels are added, the ridge or branch logic changes qualitatively. |

## How to read the matrix

The strongest claims currently separate into three layers.

- empirical structure claims: ridge existence, front-tip separation, and thermodynamic-upgrade survival
- mechanism and transfer claims: pre-commit backbone principle and tested-family shape-level universality
- extension claims: completion-law closure, stress-test geometry generality, and full thermodynamic closure

The first layer is mostly `confirmed`. The second layer is mostly `supported but scoped`. The third layer remains `still conjectural` by design.

## Which claims are already strong enough for a Nature-level narrative?

Strong enough for a high-level narrative, if phrased conservatively:

- productive transport forms a Pareto-like ridge rather than a single optimum
- the ridge is organized by a pre-commit backbone before final crossing
- the backbone shape survives a first geometry-transfer test while coefficients renormalize
- the ridge survives a conservative thermodynamic upgrade even though branch preference changes

These are strong enough because they combine:

- a nontrivial structural discovery
- a reduced mechanism
- a first transfer test beyond one geometry
- a metric-upgrade robustness test beyond one efficiency definition

But the Nature-level version must still remain scoped.

Allowed narrative style:

- geometry-tested pre-commit transport principle
- shape-level universality with coefficient-level renormalization
- thermodynamic-upgrade survival of the ridge

Not yet strong enough for that narrative:

- universal crossing-completion law
- total entropy production or full thermodynamic closure
- unrestricted universality across disordered stress-test geometries

## Practical Summary

For current manuscript use:

- `confirmed` claims can anchor Results and selected title or abstract phrasing if kept close to the data
- `supported but scoped` claims are appropriate for title, abstract, and Results only when the scope qualifier remains explicit
- `still conjectural` claims belong in Discussion or Outlook only
