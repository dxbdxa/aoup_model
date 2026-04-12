# Ridge Control Law Candidates

## Scope

This note lists compact phenomenological control-law candidates suggested by the confirmed numerical ridge structure.

Sources:

- [precision_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/precision_scan_first_look.md)
- [confirmatory_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/confirmatory_scan_first_look.md)
- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)

These are empirical control statements intended for theory compression. They are not exact derivations.

## Candidate 1: Delay-Admissibility Law

### Statement

There exists a small admissible delay strip

`Pi_f <= Pi_f,crit`

such that productive transport is confined to that strip.

### Current empirical version

In the confirmatory ridge dataset, all front winners and the full non-dominated family are concentrated near

`0.018 <= Pi_f <= 0.025`

### Interpretation

- `Pi_f` measures how stale the steering signal is compared with the gate-crossing timescale
- the delay coordinate behaves less like a smooth optimizer and more like an eligibility filter
- once the lag is too large, the point leaves the productive front family rather than merely moving to a weaker optimum

### Status

- robust numerical finding: yes
- physical interpretation: plausible
- exact asymptotic law: not yet established

## Candidate 2: Ordered Ridge Law

### Statement

Conditional on delay admissibility, the productive front is ordered mainly by flow:

- low `Pi_U` favors success
- moderate `Pi_U` favors efficiency
- high `Pi_U` favors speed

with memory providing a secondary adjustment inside a low productive band.

### Current empirical version

The front winners occur at:

- success: `(Pi_m, Pi_f, Pi_U) = (0.08, 0.025, 0.1)`
- efficiency: `(0.18, 0.018, 0.15)`
- speed: `(0.1, 0.018, 0.3)`

### Interpretation

- `Pi_U` is the main ordering coordinate along the ridge
- `Pi_m` shifts where each front tip sits, especially between success and efficiency
- the shared small-`Pi_f` strip means the front is effectively one-dimensional to first approximation

### Status

- robust numerical finding: yes
- physical interpretation: strong
- exact reduced law: not yet established

## Candidate 3: Productive Memory Band Law

### Statement

Productive memory occupies a low but non-minimal band:

`Pi_m,prod ~ O(0.1)`

in the current nondimensionalization and geometry.

### Current empirical version

- very low memory can still support high success
- the best efficiency point shifts upward in memory
- large memory is not favored by the confirmed front package

### Interpretation

- too little memory preserves responsiveness but gives less temporal smoothing
- some memory improves regularity or phase matching
- too much memory becomes stale relative to the gate-search cycle

### Status

- robust numerical finding: partly
- physical interpretation: plausible
- mechanism-level proof: open

## Combined Working Control Law

The most useful compressed working rule is:

1. enforce very small `Pi_f`
2. keep `Pi_m` in a low productive band rather than driving it to zero or very large values
3. choose `Pi_U` according to the objective:
   - success: low positive flow
   - efficiency: moderate positive flow
   - speed: stronger positive flow

In words:

First satisfy delay admissibility, then tune memory inside the productive band, then move along the ridge with flow to choose the desired objective.

## What Is Confirmed vs Open

Confirmed:

- the front is Pareto-like, not single-point
- top-`10` overlap counts are zero for all objective pairs
- `Pi_f` is tightly pinned
- `Pi_U` orders the front tips

Interpretive but reasonable:

- delay is acting as a synchronization constraint
- memory is acting as a smoothing or phase-matching variable
- flow is trading selectivity against throughput

Open:

- the exact form of `Pi_f,crit`
- whether the ridge is best parameterized by `Pi_m + c Pi_f`
- whether the same compressed law survives geometry transfer with only weak coefficient changes

## Preferred Language For Manuscript Drafting

Recommended conservative phrasing:

- "The data suggest"
- "The confirmed ridge is consistent with"
- "A useful phenomenological description is"
- "We interpret the delay strip as"

Avoid for now:

- "We derive"
- "We prove"
- "The theory predicts exactly"
