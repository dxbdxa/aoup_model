# Gate Theory Principle Note

## Scope

This note compresses the fitted pre-commit gate theory into a transport principle statement. It is intentionally framed as a transport principle rather than as a maze-specific optimization anecdote.

Primary inputs:

- [precommit_gate_theory_state_graph.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_state_graph.md)
- [precommit_gate_theory_fit_report.md](file:///home/zhuguolong/aoup_model/docs/precommit_gate_theory_fit_report.md)
- [theory_compression_note.md](file:///home/zhuguolong/aoup_model/docs/theory_compression_note.md)
- [physics_storyline_v1.md](file:///home/zhuguolong/aoup_model/docs/physics_storyline_v1.md)

This note does not claim a full doorway-crossing theory. It states only what is already supported by the fitted pre-commit backbone.

## Principle Statement

The productive-memory ridge is best understood as a pre-commit transport principle:

- productive transport is selected primarily by how efficiently trajectories cycle through bulk search, wall-guided search, and gate-local residence before strong commitment
- the leading competition is not yet in the final crossing step, but in the timing and recycling structure that determines whether commitment is reached quickly, reliably, or after prolonged wall recirculation
- delay, memory, and flow shape that pre-commit competition in different ways:
  - delay controls whether the approach-to-commit backbone remains admissible
  - memory controls whether pre-commit search is productively smoothed or made stale
  - flow orders which part of the admissible pre-commit family is favored

In compact form:

> Productive transport emerges when the controller keeps the pre-commit search-to-residence-to-commit backbone synchronized, avoids excessive recycling before commitment, and suppresses stale trapping strongly enough that commitment is reached on a useful timescale.

## Why the productive-memory ridge is already visible before crossing

The fitted pre-commit theory already reveals the ridge before any explicit crossing-rate fit for three reasons.

First, the robust fitted rates show that the main populated backbone is

- `bulk <-> wall_sliding`
- `wall_sliding -> gate_approach`
- `gate_approach -> gate_residence_precommit`
- `gate_residence_precommit -> gate_commit`

Second, the fitted model already captures the qualitative success and speed winners:

- speed is explained by the shortest effective time to commitment
- success is explained by the highest probability of reaching commitment before loss

Third, the matched ridge-vs-stale comparison is already encoded in pre-commit observables:

- the stale-control point has a slower fitted commitment clock than the balanced ridge point
- the stale-control point carries a weak but real trap sink before commitment
- the residence-to-commit rate itself is not the main separator, so the ridge is not primarily a story about a special final jump once the system is already poised to cross

This means the productive ridge is visible as an organization of approach, residence, recycling, and commitment timing before the final transit step is even modeled.

## How front separation emerges from pre-commit rate competition

The front tips separate because the pre-commit backbone rewards different balances of three quantities:

- commitment reach probability
- commitment timescale
- pre-commit recycling burden

Success-favored operation:

- arises when the probability of reaching `gate_commit` before loss is largest
- tolerates a longer commitment clock if that preserves reliable pre-commit organization

Speed-favored operation:

- arises when the effective commitment clock is shortest
- accepts weaker overall selectivity if trajectories are driven into commitment more rapidly

Efficiency-favored operation:

- appears to require a balance between pre-commit organization and downstream transport-cost structure
- is therefore only partially captured by the present theory

So front separation is the result of rate competition before commitment:

- one branch favors fast commitment
- another favors reliable commitment
- an intermediate branch benefits from a balance that is not purely pre-commit

## Relation to delay admissibility, productive memory, and flow ordering

### Delay admissibility

The earlier ridge compression identified `Pi_f` as a practical admissibility coordinate. The pre-commit fit now explains why:

- if delay becomes too large, the search-to-residence-to-commit backbone can no longer stay synchronized
- once that synchronization is lost, the model predicts slower effective commitment and more useless recycling before commitment
- that makes the point drop out of the competitive pre-commit family before any crossing-specific physics needs to be invoked

So the fitted pre-commit theory gives a dynamical meaning to delay admissibility: it is the requirement that the commitment backbone remain phase-coherent enough to compete.

### Productive memory band

The earlier ridge picture identified a low but non-minimal productive memory band. The pre-commit theory gives that band a mechanism:

- too little memory preserves responsiveness but gives less smoothing of the wall-to-approach-to-residence cycle
- too much memory makes the pre-commit guidance stale and lengthens the effective commitment clock
- the productive band is where memory smooths the backbone without destroying its timing

So productive memory is not a generic benefit. It is the band in which memory regularizes pre-commit search while remaining synchronized with commitment dynamics.

### Flow ordering along the ridge

The earlier ridge picture identified `Pi_U` as the ordering coordinate along the front. The pre-commit fit clarifies that ordering:

- higher flow shortens the effective time to commitment and therefore favors the speed branch
- lower flow preserves the more selective branch with the highest commitment reach probability and therefore favors success
- the efficiency branch sits between them because it benefits from pre-commit organization without being reducible to the fastest commitment clock alone

Thus flow ordering along the ridge is already visible as a way of choosing which pre-commit rate competition is favored.

## Why this theory is already more general than a single gated-maze result

This principle is already more general than one maze optimization result because it is stated in terms of a state graph and rate competition, not in terms of a particular best parameter tuple.

What is geometry-specific right now:

- the numerical values of the rates
- the exact doorway layout
- the exact threshold values used to classify gate-local states

What is more general already:

- the distinction between pre-commit search states and post-commit crossing states
- the idea that productive transport can be selected by a commitment backbone before crossing
- the decomposition of control into delay admissibility, productive memory smoothing, and flow ordering
- the identification of stale control as a weak pre-commit sink plus a slower commitment clock

That makes the current theory a transport principle candidate for gated search-and-commit systems, not just a numerical curiosity of one optimization landscape.

## What this principle explains, and what it does not yet explain

Explains already:

- why the productive-memory ridge is visible before crossing
- why success and speed already separate within the pre-commit backbone
- why stale-control degradation appears as slower commitment plus rare stale trapping
- why the productive ridge is organized by timing and recycling rather than by one exceptional final jump

Does not yet explain:

- the crossing step itself as a fitted kinetic branch
- the efficiency winner as a complete reduced-theory consequence
- thermodynamic efficiency as a first-principles cost statement
- geometry transfer beyond the current family without further testing

So the current principle is intentionally incomplete: it is a robust pre-commit transport principle, not yet a full transport completion principle.

## Compact Candidate Statement

One compact manuscript-ready formulation is:

> The productive-memory ridge is selected primarily before crossing: competitive points are those for which delay remains low enough to preserve a coherent pre-commit search-to-residence-to-commit backbone, memory remains in a productive smoothing band rather than becoming stale, and flow chooses whether that backbone favors reliable commitment or rapid commitment.

## Bottom Line

The fitted pre-commit gate theory suggests a general transport principle:

- productive gated transport is first a problem of reaching commitment on the right timescale
- the key competition is between approach, residence, recycling, and stale loss before crossing
- delay, memory, and flow shape that competition in distinct and interpretable ways
- the final crossing step matters, but it is not yet the first place where the productive ridge is created
