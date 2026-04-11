# Legacy Output Map

## Scope

This document records what the legacy `simcore` code returns and writes so a future adapter can normalize outputs without changing the underlying physics.

There are three output layers:

- point-level in-memory return values from `PointSimulator.run()`
- task-level in-memory return value from `SimulationTaskRunner.run()`
- persisted artifacts written by `ArtifactWriter.write()`

## Single-Point Return Contract

`PointSimulator.run(point, dynamics, point_seed)` returns:

```python
(summary: dict[str, float], traj_df: pd.DataFrame, trap_df: pd.DataFrame)
```

### `summary` fields

| Field | Meaning | Source type |
| --- | --- | --- |
| `sweep_id` | point identifier | metadata |
| `figure_group` | downstream figure grouping | metadata |
| `control_label` | branch label | metadata |
| `tau_v` | memory relaxation time | input echo |
| `tau_v_over_tau_p` | `tau_v / tau_p` | derived diagnostic |
| `tau_f` | feedback delay | input echo |
| `tau_f_over_tau_p` | `tau_f / tau_p` | derived diagnostic |
| `U` | background flow speed | input echo |
| `U_over_v0` | `U / v0` | derived diagnostic |
| `gamma1_over_gamma0` | memory ratio | input echo |
| `kf` | alignment gain | input echo |
| `v0` | propulsion speed | input echo |
| `Dr` | rotational diffusion | input echo |
| `Xi` | combined memory-delay ratio | derived diagnostic |
| `De` | flow-memory diagnostic | derived diagnostic |
| `n_traj` | trajectories simulated | count |
| `n_success` | successful trajectories | count |
| `Psucc` | success probability | primary observable |
| `Psucc_ci_low` | Wilson lower bound | uncertainty |
| `Psucc_ci_high` | Wilson upper bound | uncertainty |
| `MFPT_success_only` | mean FPT over successes only | primary observable |
| `J_proxy` | `Psucc / Tmax` | derived transport metric |
| `sigma_drag` | mean drag dissipation proxy | primary observable |
| `eta_sigma` | `J_proxy / max(sigma_drag, sigma_floor)` | primary efficiency metric |
| `mean_trap_residence` | mean trap episode duration | trap statistic |
| `q90_trap_residence` | 90th percentile trap duration | trap statistic |
| `boundary_contact_fraction` | total boundary-contact fraction | wall statistic |
| `dt` | integration time step | input echo |
| `Tmax` | maximum horizon | input echo |
| `tau_m` | internal embedding timescale | internal diagnostic |
| `grid_n` | geometry grid resolution | geometry echo |
| `n_shell` | number of shells | geometry echo |
| `MFPT_ci_low` | bootstrap MFPT lower bound | uncertainty |
| `MFPT_ci_high` | bootstrap MFPT upper bound | uncertainty |
| `J_proxy_ci_low` | bootstrap `J_proxy` lower bound | uncertainty |
| `J_proxy_ci_high` | bootstrap `J_proxy` upper bound | uncertainty |
| `sigma_drag_ci_low` | bootstrap `sigma_drag` lower bound | uncertainty |
| `sigma_drag_ci_high` | bootstrap `sigma_drag` upper bound | uncertainty |
| `eta_sigma_ci_low` | bootstrap `eta_sigma` lower bound | uncertainty |
| `eta_sigma_ci_high` | bootstrap `eta_sigma` upper bound | uncertainty |

### `traj_df` columns

One row per trajectory:

| Column | Meaning |
| --- | --- |
| `sweep_id` | parent point id |
| `traj_id` | trajectory index |
| `success_flag` | `1` for exit success, `0` otherwise |
| `t_stop` | stop time, equal to `t_exit` or `Tmax` |
| `t_exit_or_nan` | exit time for successes, `NaN` otherwise |
| `Sigma_drag_i` | per-trajectory drag dissipation rate proxy |
| `live_steps` | number of active integration steps |
| `boundary_steps` | steps counted near boundary |
| `boundary_contact_fraction_i` | `boundary_steps / live_steps` |

### `trap_df` columns

One row per trap episode that lasted at least `0.5 * tau_p`:

| Column | Meaning |
| --- | --- |
| `sweep_id` | parent point id |
| `traj_id` | trajectory index |
| `trap_duration` | duration of the recorded trap episode |

## Task-Level Return Contract

`SimulationTaskRunner.run(task, overwrite=False)` returns `TaskRunResult` with:

| Field | Meaning |
| --- | --- |
| `task` | original `SimulationTask` |
| `summary_df` | concatenated point summaries |
| `trajectory_df` | concatenated per-trajectory table |
| `trap_df` | concatenated trap episodes |
| `detectability` | optional fig1/fig2 detectability summary |
| `manifest` | run manifest dict |
| `artifact_paths` | display paths for written artifacts |

### `detectability` fields

Only present when `task.detectability_analysis` is true.

| Field | Meaning |
| --- | --- |
| `ridge_detected` | whether an interior efficiency ridge was detected |
| `ridge_best_point` | dict with `tau_v`, `tau_f`, `Xi`, `eta_sigma`, `MFPT_success_only` |
| `ranking_reversal_detected` | whether MFPT-optimal `U` differs from efficiency-optimal `U` |
| `ranking_reversal_details` | dict with `coupled_branch_mfpt_best_U` and `coupled_branch_eta_sigma_best_U` |
| `reason` | present only in the insufficient-data fallback path |

## Persisted Artifacts

`ArtifactWriter.write()` creates one run directory under:

```text
Experiment/runs/{run_id}/
```

### Primary files

| File | Contents |
| --- | --- |
| `pilot_point_summary.csv` | point-level `summary_df` |
| `pilot_trajectory_summary.csv` | concatenated `trajectory_df` |
| `pilot_trap_episodes.csv` | concatenated `trap_df` |
| `run_manifest.json` | run metadata, config echo, artifact list |
| `maze_mask.npy` | wall mask |
| `signed_distance.npy` | signed-distance field |
| `exit_mask.npy` | exit mask |
| `inlet_mask.npy` | inlet mask |
| `psi.npy` | navigation scalar field |
| `grad_psi_x.npy` | x-gradient of navigation field |
| `grad_psi_y.npy` | y-gradient of navigation field |

### Figure-support exports

| Location | Contents |
| --- | --- |
| `Experiment/analysis/figures/{figure_group}_source_{run_id}.csv` | subset of `summary_df` for one figure group |
| `Experiment/analysis/tables/fig2_u_star_summary_{run_id}.csv` | best-`U` summary for each `control_label` in fig2 data |

### `fig2_u_star_summary` columns

| Column | Meaning |
| --- | --- |
| `control_label` | branch name |
| `tau_v` | winning point memory time |
| `tau_f` | winning point delay |
| `gamma1_over_gamma0` | winning point memory ratio |
| `kf` | winning point alignment gain |
| `U_star` | `U` at max `eta_sigma` |
| `U_star_over_v0` | normalized best flow |
| `eta_sigma_max` | max efficiency value |
| `MFPT_at_U_star` | MFPT at best `U` |
| `Psucc_at_U_star` | success probability at best `U` |

## `run_manifest.json` Structure

The manifest contains:

| Key | Meaning |
| --- | --- |
| `run_id` | run identifier |
| `mode` | task mode |
| `task_id` | catalog task id |
| `description` | task description |
| `geometry` | serialized `GeometryConfig` |
| `dynamics` | serialized `DynamicsConfig` |
| `n_points` | number of points |
| `point_ids` | list of `sweep_id` values |
| `paths` | runtime path roots |
| `artifacts` | relative artifact paths |
| `notes` | task notes |
| `detectability` | optional detectability block |

## Mapping To Proposed `RunResult`

The current legacy outputs are closer to a state-point summary table than to the draft `RunResult` dataclass.

| Proposed field | Legacy source | Mapping note |
| --- | --- | --- |
| `p_succ` | `Psucc` | direct rename |
| `mfpt_mean` | `MFPT_success_only` | success-conditioned mean only |
| `mfpt_median` | none | not available; compute later if needed from `traj_df` |
| `mfpt_q90` | none | not available; compute later if needed from `traj_df` |
| `sigma_drag_mean` | `sigma_drag` | direct rename |
| `eta_sigma` | `eta_sigma` | direct |
| `trap_time_mean` | `mean_trap_residence` | semantic rename |
| `trap_count_mean` | none | not currently emitted |
| `wall_fraction_mean` | `boundary_contact_fraction` | semantic rename |
| `revisit_rate_mean` | none | not currently emitted |
| `n_traj` | `n_traj` | direct |
| `n_success` | `n_success` | direct |
| `ci` | bootstrap + Wilson fields | adapter should nest these into one dict |
| `raw_summary_path` | `pilot_point_summary.csv` | task artifact, not per-point path |
| `metadata` | manifest + echoed inputs | adapter should restructure |

## Gaps Relative To Workflow Doc

- Legacy code does not emit MFPT median, MFPT q90, revisit metrics, alignment statistics, or mean trap count.
- Legacy code does emit useful diagnostics not present in the draft schema: `Xi`, `De`, `tau_m`, and bootstrap intervals for `J_proxy` and `sigma_drag`.
- The adapter should preserve raw legacy fields in metadata even if the normalized schema uses different names.
