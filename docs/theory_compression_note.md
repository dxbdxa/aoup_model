# Theory Compression Note

## Scope

This note compresses the current numerical picture of the productive-memory structure into a compact physical interpretation.

Primary inputs:

- [reference_scales_run_report.md](file:///home/zhuguolong/aoup_model/docs/reference_scales_run_report.md)
- [coarse_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/coarse_scan_first_look.md)
- [refinement_first_look.md](file:///home/zhuguolong/aoup_model/docs/refinement_first_look.md)
- [precision_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/precision_scan_first_look.md)
- [confirmatory_scan_first_look.md](file:///home/zhuguolong/aoup_model/docs/confirmatory_scan_first_look.md)
- [front_analysis_report.md](file:///home/zhuguolong/aoup_model/docs/front_analysis_report.md)

Definitions used here:

- `Pi_m = tau_mem / tau_g`
- `Pi_f = tau_f / tau_g`
- `Pi_U = U / v0`

This note does not claim an exact reduced theory. It distinguishes carefully between confirmed numerical structure, physical interpretation, and open conjecture.

## Compact Physical Picture

The productive-memory window is now best read as a narrow, flow-ordered ridge rather than as a single best point. The delay ratio `Pi_f` behaves almost like an admissibility coordinate: once the system leaves the very small-delay strip, the best fronts disappear rapidly. Inside that admissible strip, performance is organized mainly by a tradeoff between memory and flow. Low positive flow favors maximum success, moderate positive flow favors the best dissipation-normalized transport, and stronger positive flow favors the fastest passage. Memory remains productive only in a low-to-moderate band, not at the smallest possible value and not at large values.

## Robust Confirmed Numerical Findings

- The confirmatory front winners remain distinct under uncertainty reduction.
- Top-`10` overlap counts are zero for all objective pairs.
- The only detected overlap deeper in the ranked sets is one success/efficiency shared point at top-`20`.
- The front winners are CI-separated on each objective's own metric.
- The front is tightly pinned in delay: all front winners lie in `Pi_f = 0.018` to `0.025`.
- The non-dominated confirmatory set contains `20` points, so the structure is extended rather than point-like.
- The front ordering along the ridge is primarily in `Pi_U`:
  - success winner near `(Pi_m, Pi_f, Pi_U) = (0.08, 0.025, 0.1)`
  - efficiency winner near `(0.18, 0.018, 0.15)`
  - speed winner near `(0.1, 0.018, 0.3)`
- `Pi_m` shifts the front tips within a low-to-moderate productive band, while `Pi_f` stays narrow.

## Why the productive-memory window is a Pareto-like ridge

The structure is Pareto-like because the best numerical points do not collapse onto one universal optimum, yet they also do not fragment into unrelated isolated islands.

Why it is not a single optimum:

- the success, efficiency, and speed winners occur at different locations
- the winner distances in parameter space are substantial
- each winner remains CI-separated from the others on its own metric

Why it is not just three isolated optima:

- the confirmatory non-dominated set contains `20` points
- the best points occupy the same narrow delay strip
- nearby points remain competitive while translating systematically in `Pi_U`
- the best fronts can be followed continuously along the ridge backbone

The most compact description is therefore:

- `Pi_f` defines a narrow admissible strip
- `Pi_m` selects a low-to-moderate productive band within that strip
- `Pi_U` orders which objective is favored along the ridge

## Why speed, efficiency, and success separate

The three objectives separate because they reward different failure modes and different uses of the same flow-assisted transport channel.

Success:

- prefers lower positive flow because the system benefits from reliable gate targeting and fewer over-biased passages
- tolerates somewhat slower transport if that preserves gate-finding probability

Efficiency:

- prefers intermediate flow because modest flow assistance shortens search time without paying the full success penalty seen on the fastest branch
- also prefers slightly larger memory than the success tip, consistent with a modest smoothing or persistence benefit

Speed:

- prefers the highest tested positive flow because that most strongly accelerates downstream progress
- accepts reduced success and weaker dissipation-normalized performance

In short, speed rewards raw advection-assisted throughput, success rewards robust gate capture, and efficiency rewards an intermediate balance between the two.

## Why very low delay behaves like a hard admissibility condition

Confirmed numerical statement:

- all leading fronts are confined to `Pi_f = 0.018` to `0.025`
- the best efficiency and speed points sit at the lowest tested delay edge
- refinement and precision already showed the same collapse toward the smallest tested delay

Physical interpretation:

- delayed steering only helps if the control field is still synchronized with the local gate-crossing geometry
- once the feedback lag exceeds that narrow tolerance band, steering becomes stale rather than corrective
- this does not merely reduce the optimum value; it appears to remove the point from the competitive front family altogether

Why this is described as an admissibility condition rather than a fitted law:

- the data show a sharp empirical selection effect
- they do not yet identify the exact asymptotic function that sets the admissible delay width

## Why productive memory occupies a low but non-minimal band

Confirmed numerical statement:

- the productive band in `Pi_m` is low, but the efficiency tip does not occur at the smallest tested memory
- success can remain excellent at very low memory, but the best efficiency point shifts upward to `Pi_m` near `0.18`
- the speed winner also stays in the low-memory regime rather than moving to large memory

Physical interpretation:

- too little memory likely behaves almost like a nearly memoryless controller, which preserves responsiveness but leaves less temporal smoothing
- some memory can stabilize the guidance history enough to improve dissipation-normalized transport and reduce useless reorientation
- too much memory eventually becomes stale relative to the gate-crossing cycle and stops being productive

This suggests that memory is helpful only when it is long enough to regularize the navigation response, but short enough to remain phase-matched to the gate-search dynamics.

## Why increasing positive flow shifts the operating point from success to efficiency to speed

Confirmed numerical statement:

- the best success point occurs at lower positive flow
- the best efficiency point occurs at moderate positive flow
- the best speed point occurs at the high-flow edge

Physical interpretation:

- weak positive flow provides useful downstream bias without strongly degrading target selection
- moderate flow gives the best balance between reduced search time and retained control quality
- stronger flow continues to shorten passage time, but pushes the system toward a speed-dominated branch where success and efficiency no longer peak

Compact reading:

- flow first helps
- then balances
- then over-prioritizes throughput

## Phenomenological Control Statements

These are compact empirical statements, not exact theory.

### Candidate statement A: delay admissibility

Competitive productive transport requires

`Pi_f <= Pi_f,crit`

with `Pi_f,crit` empirically very small and close to the observed ridge strip. In the current confirmatory dataset, the productive front is concentrated in

`0.018 <= Pi_f <= 0.025`

Interpretation:

- delay acts like a gate-synchronization tolerance
- outside this tolerance, the point drops out of the productive front family

### Candidate statement B: ridge ordering law

Within the admissible delay strip, the objective preference is ordered primarily by `Pi_U`, while `Pi_m` provides a secondary tuning coordinate:

- low `Pi_U` favors success
- moderate `Pi_U` favors efficiency
- high `Pi_U` favors speed

with the productive memory band remaining low but non-minimal:

`Pi_m = O(0.1)`

in the current nondimensionalization.

## Open Theoretical Conjectures

These statements are plausible but not yet proven by the current data alone.

- The narrow delay strip may correspond to a synchronization condition of the form `tau_f / tau_g <= O(10^-2 to 10^-1)` for this geometry family.
- The productive memory band may be controlled by a phase-matching or smoothing condition rather than by a simple monotone memory benefit.
- The ridge may be parameterized more naturally by a combined control variable such as `Pi_m + c Pi_f`, with `Pi_U` selecting direction along the front.
- The speed branch may represent a flow-assisted transport regime that is mechanically faster but less selective, while the success branch remains more gate-selective.

These are good targets for later reduced modeling, but they should remain labeled as conjectures until a dedicated theoretical reduction or geometry-transfer test supports them.

## Manuscript-Ready Results Paragraph

The confirmatory scan shows that the productive-memory region is not a single optimum but a narrow Pareto-like ridge. The leading points are confined to a very small delay band, `Pi_f = 0.018` to `0.025`, while the preferred objective shifts systematically with positive flow: low flow maximizes success, moderate flow maximizes dissipation-normalized efficiency, and high flow minimizes first-passage time. Memory remains productive only in a low-to-moderate band, which indicates that useful memory is neither absent nor arbitrarily large, but instead must stay phase-matched to the gate-crossing dynamics.

## Bottom Line

The most compressed physical reading is:

- very low delay is a practical admissibility condition
- low but non-minimal memory is the productive band
- positive flow orders the tradeoff from success to efficiency to speed
- the productive-memory structure is therefore a Pareto-like ridge, not a single optimum
