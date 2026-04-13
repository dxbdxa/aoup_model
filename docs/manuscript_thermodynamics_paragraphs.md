# Manuscript Thermodynamics Paragraphs

## Scope

This note collects manuscript-ready paragraph options for discussing the thermodynamic upgrade conservatively and consistently with the current model scope.

Primary sources:

- [thermodynamic_upgrade_discussion.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_upgrade_discussion.md)
- [efficiency_metric_upgrade.md](file:///home/zhuguolong/aoup_model/docs/efficiency_metric_upgrade.md)
- [thermodynamic_bookkeeping.md](file:///home/zhuguolong/aoup_model/docs/thermodynamic_bookkeeping.md)
- [gate_theory_principle_note.md](file:///home/zhuguolong/aoup_model/docs/gate_theory_principle_note.md)
- [geometry_transfer_principle_note.md](file:///home/zhuguolong/aoup_model/docs/geometry_transfer_principle_note.md)

## Main Results Paragraph

```text
The thermodynamic upgrade leaves the productive-memory structure qualitatively intact: the confirmatory front remains a Pareto-like ridge rather than collapsing to a single optimum. What changes is the preferred efficient branch along that ridge. The original screening quantity, eta_sigma, favors a moderate-flow efficiency family, whereas the stronger directly computed upgrade eta_completion_drag shifts the preferred branch toward the high-flow fast-completion tip. This shift does not destroy the ridge geometry itself: the non-dominated set remains extended and stays tightly pinned to the same narrow Pi_f band. Thus the thermodynamic upgrade changes front ordering along the ridge more than it changes the existence of the ridge.
```

## Scope-Conservative Paragraph

```text
These upgraded efficiency quantities should be read conservatively. eta_sigma remains a useful model-internal screening metric, but it is not a full thermodynamic efficiency because it uses a transport proxy in the numerator and a drag-only dissipation proxy in the denominator. eta_completion_drag is the strongest directly computed metric currently available for manuscript-level thermodynamic discussion, because it upgrades the numerator to successful completion rate while remaining within the quantities the model actually computes. However, the present bookkeeping still omits explicit active-propulsion work, controller work, memory-bath dissipation, information-rate costs, and a full post-commit completion budget, so total entropy production is not yet available.
```

## Mechanism Paragraph

```text
The pre-commit backbone changes the interpretation of efficiency by identifying where efficiency is first created or lost. On the current evidence, a large share of the efficient-versus-wasteful distinction is already determined before final completion, through the timing and recycling structure of the search-to-residence-to-commit backbone. Stale operation wastes cost through prolonged wall dwell, recycling, and delayed commitment, whereas productive operation organizes the same pre-commit pathway more effectively. In this sense, the thermodynamic upgrade supports a mechanism-aware reading of efficiency: it is not only the last crossing event, but the quality of pre-commit organization, that determines whether drag spending is productive.
```

## Trap-Refinement Paragraph

```text
The trap-aware refinement eta_trap_drag does not qualitatively change the leading branch on the competitive ridge. Instead, it confirms that the high-performing ridge branches already carry weak trap burden, so explicit penalization of stale loss mainly sharpens the interpretation rather than shifting the optimum. This is consistent with the current mechanism picture: trapping is important for off-ridge degradation and stale-control failure, but it is not the dominant source of branch selection among the leading competitive ridge points.
```

## Geometry-Transfer Paragraph

```text
The thermodynamic reading is strengthened by the first geometry-transfer validation. The transferable object is the pre-commit backbone, not a full crossing-completion law, and that backbone survives across the tested geometry family even though the relevant coefficients renormalize. This means the upgraded efficiency discussion can be phrased as a geometry-tested statement about productive versus wasteful pre-commit organization, while still remaining conservative about post-commit completion costs and full thermodynamic closure.
```

## Short Figure-Caption Version

```text
The thermodynamic upgrade preserves the Pareto-like ridge but changes the preferred efficient branch: eta_sigma remains a useful screening metric, whereas eta_completion_drag shifts the efficient branch toward the fast-completion tip. Trap-aware refinement does not overturn this shift, consistent with a pre-commit backbone interpretation in which stale loss matters mainly off ridge.
```

## Strongest Safe Claim

```text
The strongest thermodynamic claim currently supported is not that total entropy production has been resolved, but that a compact drag-normalized efficiency upgrade changes which branch of the productive-memory ridge looks best while preserving the ridge itself, and that this shift is mechanistically consistent with a geometry-tested pre-commit transport principle.
```
