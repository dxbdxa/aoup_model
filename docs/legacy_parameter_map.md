# Legacy Parameter Map

## Scope

This document records the concrete legacy inputs used by `legacy/simcore` so a future adapter can call the code without rewriting the physics.

The legacy stack has two input layers:

- task-level inputs: `SimulationTask`
- point-level inputs: `SweepPoint`

The effective single-run numerical entry is:

- task-level: `SimulationTaskRunner.run(task, overwrite=False)`
- point-level: `PointSimulator.run(point, dynamics, point_seed)`

## Entry Points

| Layer | Legacy symbol | File | Role |
| --- | --- | --- | --- |
| CLI | `main()` | `legacy/simcore/cli.py` | Parses `list` / `run` commands |
| CLI wrapper | `run_task(task_id, override=None, paths=None)` | `legacy/simcore/cli.py` | Loads catalog task and invokes the runner |
| Programmatic task run | `SimulationTaskRunner.run(task, overwrite=False)` | `legacy/simcore/simulation.py` | Builds geometry/navigation once, runs all `SweepPoint`s, writes artifacts |
| Programmatic point run | `PointSimulator.run(point, dynamics, point_seed)` | `legacy/simcore/simulation.py` | Executes one parameter point over `n_traj` trajectories |

## Task-Level Containers

### `GeometryConfig`

| Legacy field | Default | Meaning | Notes |
| --- | --- | --- | --- |
| `L` | `1.0` | domain size | Used for maze extent and derived `De` |
| `w` | `0.04` | wall thickness / corridor scale | Also used in wall-contact threshold and `tau_adv` |
| `g` | `0.08` | doorway width | Gate opening width in shell walls |
| `r_exit` | `0.06` | exit half-width | Center square exit test |
| `n_shell` | `6` | number of shells | Builtin detectability task overrides to `1` |
| `grid_n` | `1024` | grid resolution | Builtin detectability task overrides to `257` |

### `DynamicsConfig`

| Legacy field | Default | Meaning | Adapter note |
| --- | --- | --- | --- |
| `gamma0` | `1.0` | instantaneous drag | Direct map |
| `gamma1_over_gamma0` | `4.0` | memory drag ratio | Legacy scans ratio, not raw `gamma1` |
| `Dr` | `1.0` | rotational diffusion | Direct map |
| `v0` | `0.5` | self-propulsion speed | Direct map |
| `kf` | `3.0` | feedback/alignment gain | Zero gives `no_feedback` behavior |
| `kBT` | `0.01` | thermal noise scale | New workflow should likely preserve as advanced field |
| `dt` | `0.0025` | integration step | Direct map |
| `Tmax` | `40.0` | max simulation time | Builtin detectability task overrides to `20.0` |
| `sigma_floor` | `1e-12` | efficiency denominator floor | Used only in post-processing |
| `sigma_m` | `0.0` | unused legacy field | Present in config but not consumed in `simulation.py` |
| `delta_t_s` | `0.0025` | unused legacy field | Present in config but not consumed in `simulation.py` |
| `eps_psi` | `1e-12` | navigation-gradient threshold | Used in delayed steering and normalization |
| `bootstrap_resamples` | `1000` | bootstrap draws | Output CI computation |
| `n_traj` | `1000` | trajectories per point | Builtin detectability task overrides to `64` |
| `seed` | `20260411` | base RNG seed | Point seed is `seed + 1000 * point_index` |

### `SweepPoint`

| Legacy field | Default | Meaning | Notes |
| --- | --- | --- | --- |
| `sweep_id` | none | point identifier | Written to all outputs |
| `figure_group` | none | downstream grouping label | E.g. `fig1_timescale_map`, `fig2_flow_competition` |
| `control_label` | none | branch label / ablation tag | Encodes coupled vs ablated branches |
| `tau_v` | none | memory relaxation time | Direct scan variable |
| `tau_f` | none | delayed feedback time | Direct scan variable |
| `U` | none | x-direction flow speed | Direct scan variable |
| `gamma1_over_gamma0` | none | point-specific memory ratio | Combined with `gamma0` to make `gamma1` |
| `kf` | none | point-specific alignment gain | Can override nominal dynamics branch-wise |

## New Schema To Legacy Map

| New field | Legacy source | Default / source | Notes |
| --- | --- | --- | --- |
| `geometry_id` | none; derive from `GeometryConfig` | adapter-defined | Legacy code stores raw geometry params, not a geometry id |
| `model_variant` | derive from `control_label`, `gamma1_over_gamma0`, `kf`, `U` | adapter-defined | No dedicated enum in legacy |
| `v0` | `DynamicsConfig.v0` | `0.5` | Direct |
| `Dr` | `DynamicsConfig.Dr` | `1.0` | Direct |
| `tau_v` | `SweepPoint.tau_v` | task point | Direct |
| `gamma0` | `DynamicsConfig.gamma0` | `1.0` | Direct |
| `gamma1` | `SweepPoint.gamma1_over_gamma0 * DynamicsConfig.gamma0` | derived | Must be computed in adapter |
| `gamma1_over_gamma0` | `SweepPoint.gamma1_over_gamma0` or `DynamicsConfig.gamma1_over_gamma0` | `4.0` | Prefer keeping this explicit in metadata |
| `tau_f` | `SweepPoint.tau_f` | task point | Direct |
| `U` | `SweepPoint.U` | task point | Direct |
| `wall_thickness` | `GeometryConfig.w` | `0.04` | Direct geometry parameter |
| `gate_width` | `GeometryConfig.g` | `0.08` | Direct geometry parameter |
| `exit_radius` | `GeometryConfig.r_exit` | `0.06` | Not in draft `RunConfig`, but needed for faithful geometry reproduction |
| `n_shell` | `GeometryConfig.n_shell` | `6` | Needed to reconstruct maze family |
| `grid_n` | `GeometryConfig.grid_n` | `1024` | Numerical geometry resolution |
| `dt` | `DynamicsConfig.dt` | `0.0025` | Direct |
| `Tmax` | `DynamicsConfig.Tmax` | `40.0` | Direct |
| `n_traj` | `DynamicsConfig.n_traj` | `1000` | Direct |
| `seed` | `DynamicsConfig.seed` | `20260411` | Base seed only |
| `bootstrap_resamples` | `DynamicsConfig.bootstrap_resamples` | `1000` | Preserve for CI parity |
| `kf` | point-specific `SweepPoint.kf` | task point | Important for `no_feedback` ablation |
| `kBT` | `DynamicsConfig.kBT` | `0.01` | Preserve as advanced field |
| `eps_psi` | `DynamicsConfig.eps_psi` | `1e-12` | Preserve as advanced field |

## Derived Legacy Quantities

These are not user-facing inputs, but the adapter should know they are reconstructed internally by the legacy solver.

| Derived quantity | Legacy definition | Purpose |
| --- | --- | --- |
| `tau_p` | `1 / Dr` | persistence time |
| `gamma1` | `gamma1_over_gamma0 * gamma0` | raw memory drag |
| `f0` | `gamma0 * v0` | active force scale |
| `tau_adv` | `w / max(v0, U, 1e-12)` | advection timescale |
| `tau_m` | `1e-2 * min(tau_v, tau_p, tau_adv, tau_f)` with fallback | Markovian embedding timescale |
| `De` | `tau_v * U / L` when `U != 0` else `0` | flow-memory diagnostic |
| `tau_mem` | `0` if `gamma1 == 0` else `(gamma1 / (gamma0 + gamma1)) * tau_v` | effective memory time |
| `Xi` | `(tau_f + tau_mem) / tau_p` | timescale-combination diagnostic |

## Legacy Ablation Encoding

The legacy code does not use a dedicated `model_variant` enum. The branch identity is encoded by parameter combinations:

| Intended branch | Legacy encoding |
| --- | --- |
| `full` | `gamma1_over_gamma0 > 0` and `kf > 0` |
| `no_memory` | `gamma1_over_gamma0 = 0` |
| `no_feedback` | `kf = 0` |
| `no_flow` | `U = 0` |

`control_label` stores a human-readable tag such as `coupled_mid_memory`, `coupled_baseline`, `no_memory`, or `no_feedback`, but the numerical behavior ultimately comes from the parameter values above.

## Catalog Defaults And Overrides

- `TaskCatalog._register_builtin_tasks()` creates a small builtin task with `n_shell=1`, `grid_n=257`, `n_traj=64`, and `Tmax=20.0`.
- `TaskCatalog._register_startup_matrix_tasks()` expects a CSV at `Experiment/designs/startup_parameter_sweep_matrix_2026-04-11.csv`.
- In the current checkout, the `Experiment/` tree is absent, so startup-matrix tasks cannot be materialized without restoring that external design file.
- `TaskOverride` can override `run_id`, `point_limit`, `n_traj`, `Tmax`, `n_shell`, `grid_n`, `seed`, and `bootstrap_resamples`.

## Migration Notes

- Preserve `gamma1_over_gamma0` in the new schema or metadata even if the adapter exposes `gamma1`, because the legacy catalog is authored in ratio form.
- Add geometry parameters to the new config schema; `geometry_id` alone is not enough to reproduce current legacy runs.
- Keep `sigma_m` and `delta_t_s` as deprecated or ignored fields if strict manifest parity is required, because they exist in legacy configs but are currently unused.
