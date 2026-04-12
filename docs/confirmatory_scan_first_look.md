# Confirmatory Scan First Look

## Scope

This note gives a first-pass interpretation of the confirmatory ridge scan with uncertainty reduction.

Primary outputs:

- [summary.parquet](file:///home/zhuguolong/aoup_model/outputs/summaries/confirmatory_scan/summary.parquet)
- [final_front_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/final_front_candidates.csv)
- [confirmatory_front_analysis.json](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/confirmatory_front_analysis.json)

## Confidence Summary

The confirmatory pass quantifies uncertainty for:

- `Psucc_mean`
- `MFPT_mean`
- `eta_sigma_mean`
- `trap_time_mean`

The trap-time interval is reported as a bootstrap confidence interval on the persisted trap-duration observable used by the wrapper summary.

## Recommended Operating Points

### Success

- label: `full_final_candidate_resample_pm0p08_pf0p025_pu0p1_n8192`
- `Pi_m = 0.08`
- `Pi_f = 0.025`
- `Pi_U = 0.1`
- `Psucc_mean = 0.97412109375`
- `Psucc 95% CI = [0.970454288114538, 0.97734345041294]`
- supporting metrics: `MFPT_mean = 6.123713972431078`, `eta_sigma_mean = 5.374062449901737e-05`, `trap_time_mean = 0.5125000000000001`

### Efficiency

- label: `full_confirmatory_ridge_grid_pm0p18_pf0p018_pu0p15_n4096`
- `Pi_m = 0.18`
- `Pi_f = 0.018`
- `Pi_U = 0.15`
- `eta_sigma_mean = 6.685949490215236e-05`
- `eta_sigma 95% CI = [6.415550898232491e-05, 6.968156530021476e-05]`
- supporting metrics: `Psucc_mean = 0.959228515625`, `MFPT_mean = 4.241863069483329`, `trap_time_mean = 0.0`

### Speed

- label: `full_final_candidate_resample_pm0p1_pf0p018_pu0p3_n8192`
- `Pi_m = 0.1`
- `Pi_f = 0.018`
- `Pi_U = 0.3`
- `MFPT_mean = 2.816089797639123`
- `MFPT 95% CI = [2.759000002870452, 2.871498713967931]`
- supporting metrics: `Psucc_mean = 0.86865234375`, `eta_sigma_mean = 4.907688716564512e-05`, `trap_time_mean = 0.0`

## Do The Fronts Stay Distinct?

- winner locations remain distinct: `True`
- the main ordering still runs along `Pi_U`
- the winning points stay pinned near `Pi_f = 0.02`

Pairwise winner checks on each objective's own metric:

- `Psucc_mean` winner vs `eta_sigma_mean` winner on `Psucc_mean`: `separated_by_ci = True`
- `Psucc_mean` winner vs `MFPT_mean` winner on `Psucc_mean`: `separated_by_ci = True`
- `eta_sigma_mean` winner vs `Psucc_mean` winner on `eta_sigma_mean`: `separated_by_ci = True`
- `eta_sigma_mean` winner vs `MFPT_mean` winner on `eta_sigma_mean`: `separated_by_ci = True`
- `MFPT_mean` winner vs `Psucc_mean` winner on `MFPT_mean`: `separated_by_ci = True`
- `MFPT_mean` winner vs `eta_sigma_mean` winner on `MFPT_mean`: `separated_by_ci = True`

Top-set overlap counts:

- `Psucc_mean` vs `eta_sigma_mean`: `0`
- `Psucc_mean` vs `MFPT_mean`: `0`
- `eta_sigma_mean` vs `MFPT_mean`: `0`
- all three top-10 sets: `0`

## Final Candidate Table

The recommended shortlist is recorded in [final_front_candidates.csv](file:///home/zhuguolong/aoup_model/outputs/figures/confirmatory_scan/final_front_candidates.csv).

Top candidates:

| scan_label                                               | selection_reason   | analysis_source   |   analysis_n_traj |   Pi_m |   Pi_f |   Pi_U |   Psucc_mean |   Psucc_ci_low |   Psucc_ci_high |   MFPT_mean |   MFPT_ci_low |   MFPT_ci_high |   eta_sigma_mean |   eta_sigma_ci_low |   eta_sigma_ci_high |   trap_time_mean |   trap_time_ci_low |   trap_time_ci_high |   rank_psucc |   rank_eta_sigma |   rank_mfpt |   rank_trap_time |   rank_sum | recommended_for_success   | recommended_for_efficiency   | recommended_for_speed   | recommended_objectives   | result_json                                                                                                                                     |
|:---------------------------------------------------------|:-------------------|:------------------|------------------:|-------:|-------:|-------:|-------------:|---------------:|----------------:|------------:|--------------:|---------------:|-----------------:|-------------------:|--------------------:|-----------------:|-------------------:|--------------------:|-------------:|-----------------:|------------:|-----------------:|-----------:|:--------------------------|:-----------------------------|:------------------------|:-------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------|
| full_confirmatory_ridge_grid_pm0p18_pf0p018_pu0p15_n4096 | efficiency         | base_4096         |              4096 |   0.18 |  0.018 |   0.15 |     0.959229 |       0.952729 |        0.964867 |     4.24186 |       4.14884 |        4.33578 |      6.68595e-05 |        6.41555e-05 |         6.96816e-05 |         0        |             0      |              0      |           42 |                1 |          73 |                1 |        117 | False                     | True                         | False                   | efficiency               | /home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/9beee898d7d18af934ddfa47cdbf9a209e95fa432a19704229965012b9180fd8/result.json |
| full_confirmatory_ridge_grid_pm0p15_pf0p02_pu0p2_n4096   | efficiency         | base_4096         |              4096 |   0.15 |  0.02  |   0.2  |     0.952393 |       0.945437 |        0.9585   |     4.04514 |       3.93109 |        4.15877 |      6.65677e-05 |        6.3636e-05  |         6.97894e-05 |         0        |             0      |              0      |           55 |                2 |          65 |                1 |        123 | False                     | False                        | False                   | nan                      | /home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/181524afebbc4aebe66657720a3fbcd82725feb117fb2f78cf45a970f3605c6b/result.json |
| full_final_candidate_resample_pm0p1_pf0p018_pu0p3_n8192  | speed              | resampled_8192    |              8192 |   0.1  |  0.018 |   0.3  |     0.868652 |       0.861165 |        0.875794 |     2.81609 |       2.759   |        2.8715  |      4.90769e-05 |        4.72291e-05 |         5.11848e-05 |         0        |             0      |              0      |          122 |              118 |           1 |                1 |        242 | False                     | False                        | True                    | speed                    | /home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/d8ac3f6916b42704da93aadfe921a239524b896aa5ea9634c9ee2ad8c218a8c7/result.json |
| full_confirmatory_ridge_grid_pm0p08_pf0p022_pu0p3_n4096  | speed              | base_4096         |              4096 |   0.08 |  0.022 |   0.3  |     0.845947 |       0.834568 |        0.856678 |     2.82694 |       2.75262 |        2.91906 |      4.34618e-05 |        4.11408e-05 |         4.61356e-05 |         0        |             0      |              0      |          140 |              139 |           2 |                1 |        282 | False                     | False                        | False                   | nan                      | /home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/57baa7f15527860eea3d598025b1c0daf88d8731b81ac132e2084fdccbfe8cdb/result.json |
| full_final_candidate_resample_pm0p08_pf0p025_pu0p1_n8192 | success            | resampled_8192    |              8192 |   0.08 |  0.025 |   0.1  |     0.974121 |       0.970454 |        0.977343 |     6.12371 |       6.02765 |        6.20873 |      5.37406e-05 |        5.25759e-05 |         5.49634e-05 |         0.5125   |             0.5125 |              0.5125 |            1 |               98 |         138 |               68 |        305 | True                      | False                        | False                   | success                  | /home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/ef03f0693256a5221d09247a0043b36d2743255468b8358ef3f77935414eb378/result.json |
| full_confirmatory_ridge_grid_pm0p08_pf0p018_pu0p1_n4096  | success            | base_4096         |              4096 |   0.08 |  0.018 |   0.1  |     0.973633 |       0.968264 |        0.978114 |     6.07903 |       5.94773 |        6.21003 |      5.39333e-05 |        5.23452e-05 |         5.56599e-05 |         0.523333 |             0.5    |              0.565  |            2 |               96 |         137 |               83 |        318 | False                     | False                        | False                   | nan                      | /home/zhuguolong/aoup_model/outputs/runs/confirmatory_scan/maze_v1/bdff9088cbe7d728a3c167ac0569b6abdfeb6cd1d81498c4704252449dc926f6/result.json |

## Bottom Line

- the confirmatory pass does not collapse the three objectives onto one point
- `Pi_f` remains tightly localized near `0.02`
- the success point stays at lower flow, the efficiency point stays at moderate flow, and the speed point stays at the high-flow edge
- the final operating point should therefore remain objective-specific rather than forced into a single compromise
