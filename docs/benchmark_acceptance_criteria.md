# Benchmark Acceptance Criteria

## Purpose

This note turns the production benchmark mini-scan into explicit acceptance gates for the next workflow stage.

Scope:

- benchmark phase: completed production mini-scan
- next phase: coarse scan planning and execution defaults
- constraints: unchanged workflow contract and unchanged legacy physics behavior

Primary benchmark artifacts:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/benchmark_mini_scan/summary.parquet)
- [summary.csv](file:///home/zhuguolong/aoup_model/outputs/summaries/benchmark_mini_scan/summary.csv)
- [metadata.json](file:///home/zhuguolong/aoup_model/outputs/summaries/benchmark_mini_scan/metadata.json)
- [benchmark_mini_scan_report.md](file:///home/zhuguolong/aoup_model/docs/benchmark_mini_scan_report.md)

## Acceptance Gates

### Gate 1: Workflow Artifact Completeness

Requirement:

- benchmark summary tables exist in both CSV and parquet form
- metadata sidecar exists
- per-config result and raw-summary paths are traceable from summary rows
- upstream reference scales path is persisted

Observed:

- `summary.csv` present
- `summary.parquet` present
- `metadata.json` present
- `n_configs = 42`
- summary rows persist `result_json`, `raw_summary_path`, `config_hash`, `state_point_id`, and `upstream_reference_scales_path`

Decision:

- `PASS`

### Gate 2: Parameter-Box Signal Exists

Requirement:

- the compact productive-memory box must show a non-degenerate ordering across the tested `Pi_m`, `Pi_f`, and `Pi_U` values
- at least one region must clearly outperform the central ablation controls on coarse-scan primary metrics

Observed:

- best success and best efficiency occur at `full_low_low_zero`
- fastest `MFPT_mean` occurs at `full_low_low_pos_weak`
- the productive region concentrates near `Pi_m ~ 0.3`, `Pi_f ~ 0.1`, `Pi_U in [0.0, 0.25]`
- the `full` branch outperforms `no_memory` near the central strip and remains the right main branch for coarse exploration

Decision:

- `PASS`

### Gate 3: Time-Step Adequacy

Requirement:

- production `dt` must preserve coarse ordering and keep primary metrics within a tolerable change relative to the finer run
- target tolerance for adoption as a coarse-scan default:
  - `Psucc_mean` relative change `<= 5%`
  - `eta_sigma_mean` relative change `<= 5%`
  - `MFPT_mean` relative change `<= 15%`

Observed for `dt = 0.0025` vs `dt = 0.00125`:

- `Psucc_mean` relative change: `3.37%`
- `eta_sigma_mean` relative change: `1.01%`
- `MFPT_mean` relative change: `12.26%`

Decision:

- `PASS`

Adopted default:

- `dt = 0.0025`

Rejected as coarse-scan default:

- `dt = 0.005` because `MFPT_mean` drift rises to `21.06%`

### Gate 4: Horizon Adequacy

Requirement:

- production `Tmax` must be long enough that the central candidate is not materially censored on primary metrics
- target tolerance for adoption as a coarse-scan default:
  - `Psucc_mean` relative change vs long run `<= 10%`
  - `MFPT_mean` relative change vs long run `<= 20%`
  - `eta_sigma_mean` relative change vs long run `<= 30%`

Observed:

- `Tmax = 20.0` vs `30.0`
  - `Psucc_mean`: `8.20%`
  - `MFPT_mean`: `18.35%`
  - `eta_sigma_mean`: `27.98%`
- `Tmax = 15.0` vs `30.0`
  - `Psucc_mean`: `15.57%`
  - `MFPT_mean`: `24.57%`
  - `eta_sigma_mean`: `46.80%`

Decision:

- `PASS` for using `Tmax = 30.0` as the production coarse-scan default
- `FAIL` for keeping `Tmax = 15.0`
- `MARGINAL / DO NOT ADOPT` for `Tmax = 20.0` because it remains too close to the censoring threshold

Adopted default:

- `Tmax = 30.0`

### Gate 5: Trajectory Count Adequacy

Requirement:

- the default `n_traj` must be sufficient for trend-finding on primary observables without making the coarse scan impractically expensive
- target tolerance for adoption as a coarse-scan default:
  - `MFPT_mean` relative change vs high-count run `<= 5%`
  - `Psucc_mean` relative change vs high-count run `<= 10%`
  - `eta_sigma_mean` may exceed `10%` if used only as a screening metric

Observed for `n_traj = 512` vs `1024`:

- `MFPT_mean` relative change: `2.80%`
- `Psucc_mean` relative change: `8.82%`
- `eta_sigma_mean` relative change: `13.05%`

Decision:

- `PASS` for `n_traj = 512` as the coarse-scan default
- `PASS WITH CAUTION` for interpreting `eta_sigma_mean`

Adopted default:

- `n_traj = 512`

Escalation rule:

- use `n_traj >= 1024` for refinement, ranking ties, or publication-quality confirmation

### Gate 6: Observable Readiness

Requirement:

- classify which observables are stable enough to drive coarse-scan decisions

Accepted as primary coarse-scan observables:

- `Psucc_mean`
- `MFPT_mean`
- coarse regional screening with `eta_sigma_mean`

Restricted to secondary or diagnostic use:

- precise ranking by `eta_sigma_mean`
- `Sigma_drag_mean`
- `wall_fraction_mean`
- `trap_time_mean`
- `trap_count_mean`
- `FPT_q90`

Decision:

- `PASS`

## Production Defaults

Use these settings for the next coarse scan:

- `dt = 0.0025`
- `Tmax = 30.0`
- `n_traj = 512`

Use these parameter priorities when seeding the coarse domain:

- center attention near `Pi_m ~ 0.3`
- center attention near `Pi_f ~ 0.1`
- prioritize `Pi_U` from `0.0` to `0.25`

## Go / No-Go

Decision:

- `GO` for coarse-scan planning with the benchmark-derived defaults above

Conditions:

- keep `Tmax = 30.0`
- treat `Psucc_mean` and `MFPT_mean` as the main coarse-scan ranking outputs
- treat `eta_sigma_mean` as a screening aid rather than a final ranking metric
- reserve higher `n_traj` runs for refinement and confirmation

## Non-Accepted Settings

Do not carry these forward as coarse-scan defaults:

- `dt = 0.005`
- `Tmax = 15.0`
- exact scientific ranking by `eta_sigma_mean` at coarse-scan budget

## Bottom Line

The benchmark mini-scan satisfies the acceptance criteria needed to proceed. It provides a usable productive-memory target region, confirms a practical coarse-scan configuration, and shows that the main remaining uncertainty is not workflow integrity but statistical refinement of secondary observables.
