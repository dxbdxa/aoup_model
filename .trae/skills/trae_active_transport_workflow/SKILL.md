---
name: trae_active_transport_workflow
description: perform
---

# Productive Memory in Gated Active Transport
## Executable Computation Plan and Trae IDE Workflow Controller

Version: v0.1  
Project type: theory + simulation  
Target: journal-grade large-scale parameter scan for delayed active transport in gated complex environments

---

## 1. Project objective

Build a reproducible large-scale computation pipeline for a delayed active generalized Langevin model in gated geometries, with the scientific goal of testing the following central claim:

> In complex gated environments, memory improves active transport only within a productive window where medium memory and control delay match the gate-crossing dynamics; the fastest transport regime is generally different from the most dissipation-efficient regime.

This document is the **single control file** for:
- theory simplification and nondimensionalization
- simulation parameter scans
- convergence and statistical validation
- figure generation for main Figures 1–4
- Trae IDE task orchestration and milestone tracking

---

## 2. Scientific hypotheses to test

### H1. Productive-memory window
There exists an internal ridge in parameter space, rather than a boundary optimum, such that transport efficiency is maximized when

\[
\Pi_m + \Pi_f \sim O(1), \qquad \Pi_p \gtrsim 1
\]

where \(\Pi_m\) is the memory-to-gate time ratio, \(\Pi_f\) is the feedback-delay-to-gate time ratio, and \(\Pi_p\) is the persistence-to-gate-length ratio.

### H2. Speed-efficiency separation
The parameter set that minimizes mean first-passage time (MFPT) is generically different from the one that maximizes dissipation-normalized transport efficiency.

### H3. Failure by trapping, not just slowing down
Outside the productive-memory window, transport degrades primarily because of prolonged wall trapping, revisit cycles, and stale steering, rather than a simple reduction in instantaneous speed.

### H4. Weak-flow assistance and strong-flow breakdown
A weak co-flow can enlarge the productive window, while strong flow can collapse it by over-biasing trajectories toward wall hugging or wrong-gate overshoot.

### H5. Geometry-robust collapse
The same nondimensional control law should approximately organize results across several geometry families.

---

## 3. Minimal model summary

State variables per particle:
- position: \((x,y)\)
- velocity: \((v_x,v_y)\)
- memory auxiliary variable: \((q_x,q_y)\)
- heading: \(\theta\)

Dynamics:
- active self-propulsion with speed scale \(v_0\)
- uniform background flow \(\mathbf U=(U,0)\)
- wall soft-repulsion from signed distance field
- viscoelastic memory via single-exponential kernel implemented with Markovian embedding
- delayed alignment to the local negative navigation-field gradient
- translational and rotational noise

Primary observables:
- success probability \(P_{\mathrm{succ}}\)
- MFPT and FPT quantiles
- total trap time and trap count
- wall-contact fraction
- drag-dissipation proxy \(\Sigma_{\mathrm{drag}}\)
- transport proxy \(J_{\mathrm{proxy}}\)
- dissipation-normalized efficiency \(\eta_\sigma\)
- alignment correlation and revisit statistics

---

## 4. Nondimensional control parameters

Use a reference geometry and baseline dynamics (`no_memory`, `no_feedback`, `U=0`) to define:

- gate-search length: \(\ell_g\)
- gate-crossing time: \(\tau_g\)
- persistence time: \(\tau_p = D_r^{-1}\)
- persistence length: \(\ell_p = v_0 \tau_p\)
- effective memory time: \(\tau_{\mathrm{mem}}\)

Recommended dimensionless groups:

\[
\Pi_p = \frac{\ell_p}{\ell_g} = \frac{v_0 / D_r}{\ell_g}
\]

\[
\Pi_m = \frac{\tau_{\mathrm{mem}}}{\tau_g}
\]

\[
\Pi_f = \frac{\tau_f}{\tau_g}
\]

\[
\Pi_U = \frac{U}{v_0}
\]

\[
\Pi_W = \frac{w_{\mathrm{gate}}}{L}
\]

\[
\Pi_B = \frac{\delta_{\mathrm{wall}}}{L}
\]

Optional secondary controls:
- memory strength ratio \(\chi_m = \gamma_1 / (\gamma_0 + \gamma_1)\)
- translational noise ratio \(\Theta_t = k_B T / (\gamma_0 v_0 \ell_g)\)
- rotational noise ratio \(\Theta_r = D_r \tau_g\)

---

## 5. Parameter table

## 5.1 Baseline dimensional defaults

| Symbol | Meaning | Baseline choice | Notes |
|---|---|---:|---|
| `L` | system size | 1.0 | nondimensionalized geometry size |
| `v0` | self-propulsion speed | 1.0 | defines active advection scale |
| `Dr` | rotational diffusion | 0.2–2.0 | set via target persistence ratio |
| `gamma0` | instantaneous drag | 1.0 | baseline drag scale |
| `gamma1` | memory drag strength | 0–10 | scan separately or encode into `tau_mem` |
| `tau_v` | viscoelastic relaxation | 1e-2–1e2 | broad log scan |
| `tau_f` | feedback delay | 1e-2–1e2 | broad log scan |
| `U` | background flow speed | -1.5 to 1.5 | linear scan relative to `v0` |
| `delta_wall` | soft wall range | 0.005–0.05 | geometry dependent |
| `kf` | alignment gain | 0–10 | used for ablation and sensitivity |
| `Tmax` | max run time | 20–50 `tau_g` | adaptive by regime |
| `dt` | time step | `min(timescale)/100` initially | verify via convergence |

## 5.2 Primary scan ranges in dimensionless form

| Parameter | Symbol | Range | Grid style | Initial points | Refined points |
|---|---|---|---|---:|---:|
| Persistence ratio | `Pi_p` | 1e-1 to 1e2 | log | 16 | 30–40 local |
| Memory ratio | `Pi_m` | 1e-2 to 1e2 | log | 20 | 40–60 local |
| Feedback ratio | `Pi_f` | 1e-2 to 1e2 | log | 20 | 40–60 local |
| Flow ratio | `Pi_U` | -1.5 to 1.5 | linear | 13 | 25 local |
| Gate width ratio | `Pi_W` | 0.02 to 0.25 | linear/log hybrid | 6 | 10 |
| Wall range ratio | `Pi_B` | 0.005 to 0.05 | linear | 5 | 8 |
| Memory strength | `chi_m` | 0 to 1 | linear | 6 | 10 |

## 5.3 Scan phases

| Phase | Goal | Parameters varied | Samples per point | Method |
|---|---|---|---:|---|
| A | numerical validation | `dt`, `Tmax`, seed count | 1e3–1e4 | deterministic convergence tests |
| B | baseline ablations | `Pi_p`, `Pi_m`, `Pi_f`, `Pi_U` on sparse set | 1e3 | compare `full`, `no_memory`, `no_feedback`, `no_flow` |
| C | coarse global scan | `Pi_p`, `Pi_m`, `Pi_f`, `Pi_U` | 5e2–2e3 | Sobol / Latin hypercube |
| D | adaptive refinement | around ridges, phase boundaries, ranking reversals | up to 1e4 | local densification + bootstrap stopping |
| E | rare-event supplement | low-success regions | effective 1e5–1e6 | weighted ensemble / splitting |
| F | geometry transfer | selected geometry families | 2e3–1e4 | ridge-following slices |

---

## 6. Theory-to-simulation workflow

### Stage T1. Baseline reference extraction
Compute \(\ell_g\) and \(\tau_g\) from the reference model:
- no memory
- no delayed feedback
- no external flow
- main geometry only

Output:
- `reference_scales.json`
- `baseline_transition_stats.parquet`

Acceptance:
- stable within 5% under seed and run-length doubling

### Stage T2. Coarse-grained gate model
Fit a reduced-state description:
- bulk search
- wall sliding
- gate capture
- successful crossing / failure return

Target outputs:
- effective rates \(k_{\mathrm{search}}, k_{\mathrm{slide}}, k_{\mathrm{cross}}, k_{\mathrm{return}}\)
- phenomenological productive-memory criterion

Acceptance:
- reduced model qualitatively reproduces ridge position and trapping growth

### Stage T3. Small-delay / small-memory asymptotics
Derive and verify low-order corrections to crossing rate and alignment phase lag.

Output:
- note or appendix derivation
- symbolic expressions for local expansion
- comparison plots against simulations at small \(\Pi_m, \Pi_f\)

### Stage T4. Large-delay mismatch regime
Characterize stale-control regime through revisit rate, trap-time growth, and alignment decorrelation.

Output:
- asymptotic narrative and scaling ansatz
- one summary panel for stale steering signature

---

## 7. Repository and file structure

Recommended repository layout:

```text
project_root/
├─ README.md
├─ pyproject.toml
├─ configs/
│  ├─ geometries/
│  │  ├─ maze_main.yaml
│  │  ├─ channel_single_bottleneck.yaml
│  │  ├─ pore_array.yaml
│  │  └─ random_labyrinth.yaml
│  ├─ scans/
│  │  ├─ phaseA_validation.yaml
│  │  ├─ phaseB_ablations.yaml
│  │  ├─ phaseC_global_sobol.yaml
│  │  ├─ phaseD_refinement.yaml
│  │  ├─ phaseE_rare_events.yaml
│  │  └─ phaseF_geometry_transfer.yaml
│  └─ figures/
│     ├─ fig1_productive_memory.yaml
│     ├─ fig2_speed_efficiency_separation.yaml
│     ├─ fig3_trapping_mechanism.yaml
│     └─ fig4_geometry_collapse.yaml
├─ docs/
│  ├─ theory_notes.md
│  ├─ derivations/
│  ├─ manuscript_notes/
│  └─ trae_active_transport_workflow.md
├─ src/
│  ├─ core/
│  │  ├─ geometry.py
│  │  ├─ navigation.py
│  │  ├─ dynamics.py
│  │  ├─ kernels.py
│  │  ├─ observables.py
│  │  └─ rng.py
│  ├─ scans/
│  │  ├─ generate_design.py
│  │  ├─ run_point.py
│  │  ├─ run_batch.py
│  │  ├─ adaptive_refine.py
│  │  └─ rare_event.py
│  ├─ analysis/
│  │  ├─ aggregate.py
│  │  ├─ bootstrap.py
│  │  ├─ ridge_detection.py
│  │  ├─ collapse.py
│  │  └─ diagnostics.py
│  ├─ figures/
│  │  ├─ fig1.py
│  │  ├─ fig2.py
│  │  ├─ fig3.py
│  │  └─ fig4.py
│  └─ cli/
│     ├─ scan_cli.py
│     ├─ analysis_cli.py
│     └─ figure_cli.py
├─ jobs/
│  ├─ local/
│  ├─ slurm/
│  └─ manifests/
├─ data/
│  ├─ raw/
│  ├─ interim/
│  ├─ processed/
│  └─ reference/
├─ outputs/
│  ├─ logs/
│  ├─ tables/
│  ├─ figures/
│  └─ reports/
└─ tests/
   ├─ test_geometry.py
   ├─ test_dynamics.py
   ├─ test_observables.py
   ├─ test_reproducibility.py
   └─ test_figures.py
```

---

## 8. Parallel task decomposition

### 8.1 Unit of work
The atomic unit should be:

`(geometry_id, model_variant, state_point_id, seed_chunk_id)`

where:
- `geometry_id`: one geometry file
- `model_variant`: `full`, `no_memory`, `no_feedback`, `no_flow`, optional `no_delay`
- `state_point_id`: one nondimensional parameter tuple
- `seed_chunk_id`: one shard of trajectories, e.g. 200–1000 trajectories

This design allows:
- embarrassingly parallel trajectory generation
- adaptive re-submission for under-converged points
- deterministic aggregation by state point

### 8.2 Recommended sharding

| Layer | Unit | Typical size |
|---|---|---:|
| Design | state point | 1 parameter tuple |
| Compute shard | seed chunk | 200–1000 trajectories |
| Batch | scheduler job | 20–200 shards |
| Merge | aggregation unit | all shards for one state point |

### 8.3 Scheduler strategy

#### Local workstation mode
Use multiprocessing across state points and seed chunks.
Best for:
- phase A validation
- debugging
- figure reproduction on small subsets

#### Cluster mode
Use array jobs over shards.
Best for:
- phase C and D scans
- phase E rare events

Suggested SLURM logic:
1. generate design manifest
2. split into state-point shards
3. launch array jobs
4. write shard outputs to `data/raw/{scan_id}/`
5. aggregate to `data/processed/{scan_id}/`
6. trigger post-analysis only for converged points

### 8.4 Adaptive resubmission rule
For each state point, continue submitting seed chunks until all selected stopping criteria are satisfied:
- `CI_width(Psucc) < 0.02`
- `relative_error(logMFPT) < 0.05`
- `relative_error(eta_sigma) < 0.10`
- or hard cap reached

### 8.5 Rare-event branch
For points with
- `Psucc < 0.05`, or
- severe right-tailed FPT, or
- unstable naive estimates under doubling,

switch from brute-force to:
- weighted ensemble
- trajectory splitting at gate milestones
- optional flux-interface approach

---

## 9. Output schema and fields

All outputs should be machine-readable and versioned. Prefer Parquet for tabular data and JSON for metadata.

## 9.1 Per-trajectory lightweight record

File: `data/raw/<scan_id>/trajlite/<state_point_id>/<seed_chunk_id>.parquet`

Required fields:
- `scan_id`
- `geometry_id`
- `model_variant`
- `state_point_id`
- `seed`
- `traj_id`
- `success` (bool)
- `fpt`
- `termination_reason`
- `trap_time_total`
- `trap_count`
- `wall_fraction`
- `drag_dissipation`
- `path_length`
- `revisit_count`
- `mean_progress_along_nav`
- `mean_speed`
- `mean_rel_speed_to_flow`
- `alignment_cos_mean`
- `alignment_cos_std`
- `gate_cross_count`
- `last_gate_index`

Optional fields:
- `max_wall_depth`
- `largest_stuck_episode`
- `orbitality_score`
- `turning_number`

## 9.2 State-point aggregated record

File: `data/processed/<scan_id>/state_points.parquet`

Required fields:
- `scan_id`
- `geometry_id`
- `model_variant`
- all dimensionless parameters
- all dimensional back-mapped parameters
- `n_traj`
- `n_success`
- `Psucc_mean`
- `Psucc_ci_low`
- `Psucc_ci_high`
- `MFPT_mean`
- `MFPT_median`
- `FPT_q10`
- `FPT_q90`
- `trap_time_mean`
- `trap_count_mean`
- `wall_fraction_mean`
- `Sigma_drag_mean`
- `J_proxy`
- `eta_sigma_mean`
- `eta_sigma_ci_low`
- `eta_sigma_ci_high`
- `revisit_mean`
- `alignment_mean`
- `alignment_lag_peak`
- `status_converged`
- `status_rare_event_used`
- `runtime_seconds`
- `code_version`

## 9.3 Metadata and provenance

File: `data/processed/<scan_id>/metadata.json`

Include:
- git commit hash
- environment snapshot
- geometry checksum
- config file path
- random seed policy
- date/time
- scan description
- upstream reference scales file

---

## 10. Quality assurance and acceptance tests

### QA1. Time-step convergence
For a representative subset of points, verify all key observables are stable under
- `dt`
- `dt/2`
- `dt/4`

Acceptance:
- no qualitative regime change
- quantitative changes < 5% for primary observables

### QA2. Run-length truncation check
For slow and trapping-prone points, verify sensitivity to `Tmax`.

Acceptance:
- ranking of regimes unchanged
- right-tail diagnostics reported when unresolved

### QA3. Seed reproducibility
Repeat selected points with independent seed families.

Acceptance:
- confidence intervals overlap for primary observables

### QA4. Geometry-field consistency
Validate signed-distance field, wall normals, and navigation gradients.

Acceptance:
- no inward/outward sign ambiguity
- no discontinuities at gate edges larger than numerical tolerance

### QA5. Ablation sanity
`full` model must differ from at least one ablation on a preselected benchmark set.

Acceptance:
- effect sizes larger than estimated statistical noise

---

## 11. Main Figures 1–4: exact generation workflow

## Figure 1. Productive-memory phase diagram

### Scientific claim
There exists an internal productive-memory ridge in the \((\Pi_m, \Pi_f)\) plane.

### Inputs
- main geometry only
- `full` model
- fixed moderate `Pi_p` values (at least 3 slices)
- fixed weak/moderate `Pi_U` values
- aggregated state-point table from phases C and D

### Panels
- **Fig 1a:** schematic of gate sequence and time scales \(\tau_p, \tau_m, \tau_f, \tau_g\)
- **Fig 1b:** heat map of `eta_sigma_mean` in \((Pi_m, Pi_f)\)
- **Fig 1c:** heat map of `Psucc_mean` in \((Pi_m, Pi_f)\)
- **Fig 1d:** overlay of efficiency ridge and success ridge
- **Fig 1e:** representative trajectories from under-memory, productive-memory, stale-memory regimes

### Processing steps
1. subset processed table for chosen `Pi_p`, `Pi_U`
2. interpolate on log-log grid only for visualization, not inference
3. detect ridge using local maxima of `eta_sigma`
4. annotate productive region
5. select three representative state points with matched sample count and clear trajectories

### Deliverables
- `outputs/figures/fig1_main.pdf`
- `outputs/tables/fig1_ridge_points.parquet`
- `outputs/reports/fig1_methods_note.md`

---

## Figure 2. Fastest is not most efficient

### Scientific claim
The MFPT optimum and efficiency optimum are generically separated.

### Inputs
- main geometry
- `full`, `no_memory`, `no_feedback`
- scan over `Pi_U` and/or `Pi_m + Pi_f` along ridge-crossing cuts

### Panels
- **Fig 2a:** `MFPT_mean` vs `Pi_U`
- **Fig 2b:** `eta_sigma_mean` vs `Pi_U`
- **Fig 2c:** highlight distinct optima `Pi_U^fast` and `Pi_U^eff`
- **Fig 2d:** Pareto-like scatter of speed vs efficiency colored by trap fraction
- **Fig 2e:** ablation comparison showing how separation changes without memory or feedback

### Processing steps
1. choose cuts crossing productive ridge and failure regions
2. bootstrap optimum locations with uncertainty
3. compute ranking reversal statistic
4. plot confidence bands
5. identify alternative winners by criterion: fastest, highest success, highest efficiency, lowest dissipation

### Deliverables
- `outputs/figures/fig2_main.pdf`
- `outputs/tables/fig2_optima_summary.parquet`
- `outputs/reports/fig2_reversal_test.md`

---

## Figure 3. Mechanism: trapping, stale steering, and revisit cycles

### Scientific claim
Failure outside the productive window is driven by wall trapping and stale control rather than simple slowing.

### Inputs
- representative points from three regimes:
  - low memory / low delay
  - productive-memory ridge
  - stale-memory regime
- full trajectory records for selected points

### Panels
- **Fig 3a:** trajectory overlays near walls and gates
- **Fig 3b:** distribution of trap episode durations
- **Fig 3c:** revisit count / revisit probability
- **Fig 3d:** alignment correlation peak lag or phase mismatch metric
- **Fig 3e:** decomposition of performance drop into trap increase vs speed reduction

### Processing steps
1. store full trajectories for only representative points
2. segment into free, wall-sliding, gate-near, trapped states
3. estimate trap episode statistics and revisit structure
4. compute alignment-delay diagnostics
5. quantify contribution analysis by regression / decomposition on observables

### Deliverables
- `outputs/figures/fig3_main.pdf`
- `outputs/tables/fig3_episode_stats.parquet`
- `outputs/reports/fig3_mechanism_note.md`

---

## Figure 4. Geometry transfer and collapse

### Scientific claim
The productive-memory criterion is approximately geometry-robust when expressed in nondimensional form.

### Inputs
- main maze
- single bottleneck channel
- pore array
- random labyrinth
- scans along ridge and transverse cuts

### Panels
- **Fig 4a:** geometry gallery and definition of `ell_g`, `tau_g`, `Pi_W`
- **Fig 4b:** raw curves by geometry before collapse
- **Fig 4c:** collapsed efficiency curves vs combined control variable
- **Fig 4d:** phase-boundary comparison across geometries
- **Fig 4e:** summary schematic of temporal gating principle

### Processing steps
1. compute geometry-specific `ell_g`, `tau_g`
2. map all results to common nondimensional variables
3. test candidate collapse coordinates, e.g. `Pi_m + Pi_f`, `Pi_p`, `Pi_U`
4. quantify collapse quality using residual spread metric
5. choose the simplest successful scaling form

### Deliverables
- `outputs/figures/fig4_main.pdf`
- `outputs/tables/fig4_collapse_metrics.parquet`
- `outputs/reports/fig4_scaling_note.md`

---

## 12. Suggested command-line workflow

### 12.1 Generate design manifests
```bash
python -m src.cli.scan_cli design --config configs/scans/phaseC_global_sobol.yaml
```

### 12.2 Run local benchmark subset
```bash
python -m src.cli.scan_cli run --manifest jobs/manifests/phaseC_subset.json --mode local
```

### 12.3 Launch cluster batch
```bash
sbatch jobs/slurm/run_phaseC_array.slurm
```

### 12.4 Aggregate shard outputs
```bash
python -m src.cli.analysis_cli aggregate --scan-id phaseC_global_sobol
```

### 12.5 Check convergence and generate resubmission list
```bash
python -m src.cli.analysis_cli convergence --scan-id phaseC_global_sobol
```

### 12.6 Run adaptive refinement
```bash
python -m src.cli.scan_cli refine --config configs/scans/phaseD_refinement.yaml
```

### 12.7 Build figures
```bash
python -m src.cli.figure_cli build --figure fig1
python -m src.cli.figure_cli build --figure fig2
python -m src.cli.figure_cli build --figure fig3
python -m src.cli.figure_cli build --figure fig4
```

---

## 13. Milestones and completion criteria

| Milestone | Description | Exit criteria |
|---|---|---|
| M0 | repository bootstrapped | tests run, config loader works, geometry cache works |
| M1 | reference scales established | `ell_g`, `tau_g` stable within 5% |
| M2 | baseline ablations complete | full vs ablations show robust differences |
| M3 | global scan complete | coarse map covers all primary controls |
| M4 | ridge and reversal identified | internal ridge and distinct optima verified |
| M5 | mechanism established | trap/revisit/alignment explanation validated |
| M6 | geometry transfer complete | at least partial nondimensional collapse achieved |
| M7 | figures frozen | Figures 1–4 reproducible from clean run |

---

## 14. Trae IDE workflow controller

Trae provides project-level Rules and reusable Skills in its IDE settings, which makes it suitable for using one Markdown file as a persistent execution controller for an AI-assisted coding workflow. citeturn862190search1turn862190search5turn862190search6turn862190search8

Use this file as the canonical planning document inside the project. Keep it under `docs/trae_active_transport_workflow.md` and update checkboxes and status notes in place.

### 14.1 Project rules for Trae
Paste the following into project-level rules:

```text
You are working on a theory + simulation project for delayed active transport in gated geometries.
Always preserve reproducibility, deterministic config handling, and explicit provenance.
Never hardcode scan parameters into figure scripts.
Any new observable must be added to both trajectory-level and state-point-level schemas.
Any new geometry must expose signed distance, wall normals, and navigation field caches.
Before modifying scan logic, update docs/trae_active_transport_workflow.md.
Before claiming a physics conclusion, check convergence, confidence intervals, and at least one ablation.
Prefer small pure functions, typed configs, and testable CLI entry points.
```

### 14.2 Suggested Trae task board

```markdown
- [ ] M0 bootstrap repository and config system
- [ ] M1 compute reference scales (`ell_g`, `tau_g`)
- [ ] M2 implement observables and lightweight trajectory records
- [ ] M3 run validation suite (`dt`, `Tmax`, seeds)
- [ ] M4 run baseline ablations
- [ ] M5 generate coarse global design and launch phase C
- [ ] M6 aggregate and detect ridges / reversals
- [ ] M7 launch adaptive refinement and rare-event branch
- [ ] M8 build mechanism dataset with full trajectories
- [ ] M9 run geometry transfer scans
- [ ] M10 freeze Figures 1–4 and manuscript tables
```

### 14.3 Suggested Trae prompts by stage

#### Prompt A: repository bootstrap
```text
Create the project structure described in docs/trae_active_transport_workflow.md.
Implement typed config loading, geometry caching, and a minimal CLI skeleton.
Do not implement physics yet; focus on file structure, IO contracts, and test scaffolding.
```

#### Prompt B: dynamics kernel
```text
Implement the delayed active generalized Langevin stepping kernel with clear separation between geometry fields, stochastic dynamics, and observable accumulation.
Use testable pure functions where possible.
Expose a batch stepping interface suitable for future acceleration.
```

#### Prompt C: scan execution
```text
Implement manifest generation and shard-based execution for state-point scans.
Atomic work unit must be (geometry_id, model_variant, state_point_id, seed_chunk_id).
Outputs must conform exactly to the schema in docs/trae_active_transport_workflow.md.
```

#### Prompt D: adaptive refinement
```text
Implement convergence checks and local refinement around ridges, steep gradients, and ranking reversals.
Generate a resubmission manifest for only under-converged or high-value regions.
```

#### Prompt E: figure pipeline
```text
Implement Figure X from docs/trae_active_transport_workflow.md.
Read only processed tables, never raw trajectories unless the figure explicitly requires them.
Make the script reproducible from config and save both the figure and intermediate tables.
```

### 14.4 Daily operating loop inside Trae

```markdown
1. Open `docs/trae_active_transport_workflow.md`.
2. Pick the current milestone and one concrete deliverable.
3. Ask Trae for the smallest implementation step that advances that deliverable.
4. Run tests or a local subset immediately after code generation.
5. Record any schema or logic changes back into this document.
6. Commit only after code, config, and docs are synchronized.
```

### 14.5 Definition of done for any task
A task is done only if:
- code passes tests
- config is externalized
- outputs land in the documented location
- provenance is recorded
- this Markdown file remains consistent with the codebase

---

## 15. Immediate next actions

### Priority 1
Implement repository skeleton, typed configs, geometry cache, and output schemas.

### Priority 2
Run reference-scale extraction and produce `reference_scales.json`.

### Priority 3
Implement state-point runner and lightweight per-trajectory logging.

### Priority 4
Run the smallest benchmark set:
- one geometry
- three `Pi_p`
- three `Pi_m`
- three `Pi_f`
- three `Pi_U`
- full + two ablations

This first mini-scan should exist only to validate the pipeline, not to support claims.

---

## 16. Minimal reporting template for each scan

Use this template in `outputs/reports/<scan_id>_summary.md`:

```markdown
# Scan summary: <scan_id>

## Purpose
<what scientific question this scan addresses>

## Config
- geometry:
- model variants:
- parameter ranges:
- trajectory budget:

## Numerical status
- convergence passed / failed:
- known unstable regions:
- rare-event branch used:

## Main outcomes
- internal ridge found:
- ranking reversal found:
- strongest effect size:
- main caveat:

## Next action
<refinement, ablation, figure generation, or theory update>
```

---

## 17. Final note

This project should be developed as a **control-law discovery pipeline**, not as a generic parameter sweep. Every stage should push toward one of three outputs:
1. a productive-memory ridge,
2. a fastest-vs-efficient separation,
3. a geometry-robust temporal-gating law.

Any computation that does not sharpen at least one of these claims should be deprioritized.