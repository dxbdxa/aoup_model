# Precommit Gate Theory Fit Report

## Scope

This report fits the first coarse-grained pre-commit rate model for the productive-memory ridge. It estimates rates only on the pre-first-commit backbone and does not treat crossing-related transitions as central fitted rates.

- rate table: [precommit_gate_rates.csv](file:///home/zhuguolong/aoup_model/outputs/tables/precommit_gate_rates.csv)
- rate figure: [precommit_rate_comparison.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/precommit_rate_comparison.png)
- model-vs-simulation figure: [precommit_model_vs_simulation.png](file:///home/zhuguolong/aoup_model/outputs/figures/gate_theory/precommit_model_vs_simulation.png)

## Fitting Strategy

- Fit continuous-time transition hazards as `count(src -> dst before first commit) / total dwell time in src before first commit`.
- Use transient states `bulk`, `wall_sliding`, `gate_approach`, and `gate_residence_precommit`.
- Treat `gate_commit` as the absorbing target state of this first theory.
- Keep `trap_episode` only as a weak auxiliary sink if it appears before first commit.
- Collapse all other exits into an auxiliary `other_sink` so the precommit CTMC can estimate commitment reach probability without pretending to model crossing.

## Robust Fitted Rates

| canonical_label            | rate_symbol   | src                      | dst                      |   transition_count |   rate_estimate | model_role       |
|:---------------------------|:--------------|:-------------------------|:-------------------------|-------------------:|----------------:|:-----------------|
| OP_SUCCESS_TIP             | k_bw          | bulk_motion              | wall_sliding             |            1741843 |       93.2053   | backbone         |
| OP_SUCCESS_TIP             | k_ba          | bulk_motion              | gate_approach            |              91400 |        4.89078  | backbone         |
| OP_SUCCESS_TIP             |               | bulk_motion              | gate_residence_precommit |               5868 |        0.313994 | backbone         |
| OP_SUCCESS_TIP             | k_wb          | wall_sliding             | bulk_motion              |            1752693 |      211.397    | backbone         |
| OP_SUCCESS_TIP             | k_wa          | wall_sliding             | gate_approach            |              34223 |        4.12772  | backbone         |
| OP_SUCCESS_TIP             |               | wall_sliding             | gate_residence_precommit |               6020 |        0.726087 | backbone         |
| OP_SUCCESS_TIP             | k_ab          | gate_approach            | bulk_motion              |              71509 |      126.963    | backbone         |
| OP_SUCCESS_TIP             | k_aw          | gate_approach            | wall_sliding             |              36144 |       64.1733   | backbone         |
| OP_SUCCESS_TIP             | k_ar          | gate_approach            | gate_residence_precommit |              22792 |       40.467    | backbone         |
| OP_SUCCESS_TIP             |               | gate_approach            | gate_commit              |                276 |        0.490035 | absorbing_commit |
| OP_SUCCESS_TIP             | k_rb          | gate_residence_precommit | bulk_motion              |              14454 |       55.7128   | backbone         |
| OP_SUCCESS_TIP             | k_rw          | gate_residence_precommit | wall_sliding             |               7416 |       28.5849   | backbone         |
| OP_SUCCESS_TIP             | k_ra          | gate_residence_precommit | gate_approach            |               5098 |       19.6502   | backbone         |
| OP_SUCCESS_TIP             | k_rc          | gate_residence_precommit | gate_commit              |               7712 |       29.7258   | absorbing_commit |
| OP_EFFICIENCY_TIP          | k_bw          | bulk_motion              | wall_sliding             |             711014 |       89.187    | backbone         |
| OP_EFFICIENCY_TIP          | k_ba          | bulk_motion              | gate_approach            |              34011 |        4.26621  | backbone         |
| OP_EFFICIENCY_TIP          |               | bulk_motion              | gate_residence_precommit |               2609 |        0.327263 | backbone         |
| OP_EFFICIENCY_TIP          | k_wb          | wall_sliding             | bulk_motion              |             715777 |      211.152    | backbone         |
| OP_EFFICIENCY_TIP          | k_wa          | wall_sliding             | gate_approach            |              13060 |        3.85266  | backbone         |
| OP_EFFICIENCY_TIP          |               | wall_sliding             | gate_residence_precommit |               2588 |        0.763452 | backbone         |
| OP_EFFICIENCY_TIP          | k_ab          | gate_approach            | bulk_motion              |              25743 |      120.151    | backbone         |
| OP_EFFICIENCY_TIP          | k_aw          | gate_approach            | wall_sliding             |              13610 |       63.5224   | backbone         |
| OP_EFFICIENCY_TIP          | k_ar          | gate_approach            | gate_residence_precommit |               9697 |       45.2592   | backbone         |
| OP_EFFICIENCY_TIP          |               | gate_approach            | gate_commit              |                114 |        0.532076 | absorbing_commit |
| OP_EFFICIENCY_TIP          | k_rb          | gate_residence_precommit | bulk_motion              |               5948 |       52.5094   | backbone         |
| OP_EFFICIENCY_TIP          | k_rw          | gate_residence_precommit | wall_sliding             |               3014 |       26.6078   | backbone         |
| OP_EFFICIENCY_TIP          | k_ra          | gate_residence_precommit | gate_approach            |               2093 |       18.4772   | backbone         |
| OP_EFFICIENCY_TIP          | k_rc          | gate_residence_precommit | gate_commit              |               3839 |       33.891    | absorbing_commit |
| OP_SPEED_TIP               | k_bw          | bulk_motion              | wall_sliding             |             995365 |       89.0878   | backbone         |
| OP_SPEED_TIP               | k_ba          | bulk_motion              | gate_approach            |              62473 |        5.5915   | backbone         |
| OP_SPEED_TIP               |               | bulk_motion              | gate_residence_precommit |               5267 |        0.47141  | backbone         |
| OP_SPEED_TIP               | k_wb          | wall_sliding             | bulk_motion              |            1003916 |      209.654    | backbone         |
| OP_SPEED_TIP               | k_wa          | wall_sliding             | gate_approach            |              25429 |        5.3105   | backbone         |
| OP_SPEED_TIP               |               | wall_sliding             | gate_residence_precommit |               5722 |        1.19496  | backbone         |
| OP_SPEED_TIP               | k_ab          | gate_approach            | bulk_motion              |              46435 |      116.325    | backbone         |
| OP_SPEED_TIP               | k_aw          | gate_approach            | wall_sliding             |              25844 |       64.7419   | backbone         |
| OP_SPEED_TIP               | k_ar          | gate_approach            | gate_residence_precommit |              19658 |       49.2453   | backbone         |
| OP_SPEED_TIP               |               | gate_approach            | gate_commit              |                214 |        0.536092 | absorbing_commit |
| OP_SPEED_TIP               | k_rb          | gate_residence_precommit | bulk_motion              |              12334 |       52.8557   | backbone         |
| OP_SPEED_TIP               | k_rw          | gate_residence_precommit | wall_sliding             |               6302 |       27.0064   | backbone         |
| OP_SPEED_TIP               | k_ra          | gate_residence_precommit | gate_approach            |               4249 |       18.2085   | backbone         |
| OP_SPEED_TIP               | k_rc          | gate_residence_precommit | gate_commit              |               7762 |       33.263    | absorbing_commit |
| OP_BALANCED_RIDGE_MID      | k_bw          | bulk_motion              | wall_sliding             |             592234 |       87.1526   | backbone         |
| OP_BALANCED_RIDGE_MID      | k_ba          | bulk_motion              | gate_approach            |              33155 |        4.87906  | backbone         |
| OP_BALANCED_RIDGE_MID      |               | bulk_motion              | gate_residence_precommit |               2604 |        0.383202 | backbone         |
| OP_BALANCED_RIDGE_MID      | k_wb          | wall_sliding             | bulk_motion              |             596846 |      210.407    | backbone         |
| OP_BALANCED_RIDGE_MID      | k_wa          | wall_sliding             | gate_approach            |              13303 |        4.68973  | backbone         |
| OP_BALANCED_RIDGE_MID      |               | wall_sliding             | gate_residence_precommit |               2637 |        0.929626 | backbone         |
| OP_BALANCED_RIDGE_MID      | k_ab          | gate_approach            | bulk_motion              |              24834 |      117.825    | backbone         |
| OP_BALANCED_RIDGE_MID      | k_aw          | gate_approach            | wall_sliding             |              13690 |       64.9523   | backbone         |
| OP_BALANCED_RIDGE_MID      | k_ar          | gate_approach            | gate_residence_precommit |               9965 |       47.279    | backbone         |
| OP_BALANCED_RIDGE_MID      | k_rb          | gate_residence_precommit | bulk_motion              |               6155 |       52.7127   | backbone         |
| OP_BALANCED_RIDGE_MID      | k_rw          | gate_residence_precommit | wall_sliding             |               3053 |       26.1465   | backbone         |
| OP_BALANCED_RIDGE_MID      | k_ra          | gate_residence_precommit | gate_approach            |               2130 |       18.2418   | backbone         |
| OP_BALANCED_RIDGE_MID      | k_rc          | gate_residence_precommit | gate_commit              |               3868 |       33.1264   | absorbing_commit |
| OP_STALE_CONTROL_OFF_RIDGE | k_bw          | bulk_motion              | wall_sliding             |             647465 |       87.1441   | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_ba          | bulk_motion              | gate_approach            |              32685 |        4.39917  | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE |               | bulk_motion              | gate_residence_precommit |               2538 |        0.341597 | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_wb          | wall_sliding             | bulk_motion              |             651909 |      211.007    | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_wa          | wall_sliding             | gate_approach            |              13006 |        4.20972  | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE |               | wall_sliding             | gate_residence_precommit |               2729 |        0.88331  | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_ab          | gate_approach            | bulk_motion              |              24524 |      117.887    | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_aw          | gate_approach            | wall_sliding             |              13364 |       64.2407   | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_ar          | gate_approach            | gate_residence_precommit |               9775 |       46.9884   | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE |               | gate_approach            | gate_commit              |                106 |        0.509542 | absorbing_commit |
| OP_STALE_CONTROL_OFF_RIDGE | k_rb          | gate_residence_precommit | bulk_motion              |               6081 |       53.0756   | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_rw          | gate_residence_precommit | wall_sliding             |               3040 |       26.5334   | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_ra          | gate_residence_precommit | gate_approach            |               2078 |       18.137    | backbone         |
| OP_STALE_CONTROL_OFF_RIDGE | k_rc          | gate_residence_precommit | gate_commit              |               3843 |       33.5421   | absorbing_commit |

## Weak Auxiliary Sinks

| canonical_label            | src                      | dst          |   transition_count |   rate_estimate | model_role     | support_class   |
|:---------------------------|:-------------------------|:-------------|-------------------:|----------------:|:---------------|:----------------|
| OP_SUCCESS_TIP             | bulk_motion              | other_sink   |                135 |     0.0072238   | auxiliary_sink | auxiliary       |
| OP_SUCCESS_TIP             | wall_sliding             | trap_episode |                  1 |     0.000120612 | weak_sink      | weak_auxiliary  |
| OP_SUCCESS_TIP             | wall_sliding             | other_sink   |                 38 |     0.00458327  | auxiliary_sink | auxiliary       |
| OP_SUCCESS_TIP             | gate_approach            | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_SUCCESS_TIP             | gate_residence_precommit | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_EFFICIENCY_TIP          | bulk_motion              | other_sink   |                106 |     0.0132962   | auxiliary_sink | auxiliary       |
| OP_EFFICIENCY_TIP          | wall_sliding             | other_sink   |                 30 |     0.0088499   | auxiliary_sink | auxiliary       |
| OP_EFFICIENCY_TIP          | gate_approach            | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_EFFICIENCY_TIP          | gate_residence_precommit | other_sink   |                  0 |     2.84217e-14 | auxiliary_sink | auxiliary       |
| OP_SPEED_TIP               | bulk_motion              | other_sink   |                148 |     0.0132464   | auxiliary_sink | auxiliary       |
| OP_SPEED_TIP               | wall_sliding             | other_sink   |                 46 |     0.00960646  | auxiliary_sink | auxiliary       |
| OP_SPEED_TIP               | gate_approach            | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_SPEED_TIP               | gate_residence_precommit | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_BALANCED_RIDGE_MID      | bulk_motion              | other_sink   |                 88 |     0.01295     | auxiliary_sink | auxiliary       |
| OP_BALANCED_RIDGE_MID      | wall_sliding             | other_sink   |                 27 |     0.00951835  | auxiliary_sink | auxiliary       |
| OP_BALANCED_RIDGE_MID      | gate_approach            | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_BALANCED_RIDGE_MID      | gate_residence_precommit | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_STALE_CONTROL_OFF_RIDGE | bulk_motion              | trap_episode |                  1 |     0.000134593 | weak_sink      | weak_auxiliary  |
| OP_STALE_CONTROL_OFF_RIDGE | bulk_motion              | other_sink   |                 99 |     0.0133247   | auxiliary_sink | auxiliary       |
| OP_STALE_CONTROL_OFF_RIDGE | wall_sliding             | trap_episode |                  1 |     0.000323675 | weak_sink      | weak_auxiliary  |
| OP_STALE_CONTROL_OFF_RIDGE | wall_sliding             | other_sink   |                 35 |     0.0113286   | auxiliary_sink | auxiliary       |
| OP_STALE_CONTROL_OFF_RIDGE | gate_approach            | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |
| OP_STALE_CONTROL_OFF_RIDGE | gate_residence_precommit | other_sink   |                  0 |     0           | auxiliary_sink | auxiliary       |

## Model Summary By Canonical Point

| canonical_label            |   simulation_success_probability |   simulation_efficiency |   simulation_speed_proxy |   model_p_commit_before_sink |   model_p_trap_before_sink |   model_mean_time_to_commit_given_commit |   model_commit_throughput_proxy |   model_residence_recycle_ratio |
|:---------------------------|---------------------------------:|------------------------:|-------------------------:|-----------------------------:|---------------------------:|-----------------------------------------:|--------------------------------:|--------------------------------:|
| OP_SUCCESS_TIP             |                         0.974121 |             5.37406e-05 |                 0.1633   |                     0.978762 |                0.000122055 |                                  3.39357 |                        0.288417 |                         3.49689 |
| OP_EFFICIENCY_TIP          |                         0.959229 |             6.68595e-05 |                 0.235745 |                     0.966797 |                0           |                                  2.8542  |                        0.338727 |                         2.87966 |
| OP_SPEED_TIP               |                         0.868652 |             4.90769e-05 |                 0.355102 |                     0.976318 |                0           |                                  2.02583 |                        0.481935 |                         2.94834 |
| OP_BALANCED_RIDGE_MID      |                         0.952393 |             6.65677e-05 |                 0.24721  |                     0.971924 |                0           |                                  2.43179 |                        0.399675 |                         2.93123 |
| OP_STALE_CONTROL_OFF_RIDGE |                         0.948486 |             6.32371e-05 |                 0.23789  |                     0.966813 |                0.000488043 |                                  2.64598 |                        0.365389 |                         2.91413 |

## Which rates encode the productive-memory ridge before crossing?

- `k_wa = wall_sliding -> gate_approach` and `k_ar = gate_approach -> gate_residence_precommit` encode how efficiently wall-guided search converts into mouth arrival.
- `k_rc = gate_residence_precommit -> gate_commit` is comparatively stable across the ridge, so it is not the main ridge separator.
- The dominant ridge encoding appears in the effective approach-to-commit clock, which is the aggregate outcome of the search-cycle rates rather than a single dramatic change in `k_rc`.
- `k_rw = gate_residence_precommit -> wall_sliding` and `k_rb = gate_residence_precommit -> bulk_motion` encode precommit recycling and therefore how much search is lost before strong commitment.
- The stale-control penalty is not mainly a lower `k_rc`: `OP_BALANCED_RIDGE_MID` has recycle ratio `2.9312` and `OP_STALE_CONTROL_OFF_RIDGE` has `2.9141`, which are very close. The clearer separation is the slower precommit clock plus a weak trap sink.

## Interpretive Rate Trends

- `OP_SPEED_TIP` is the fastest branch because its fitted precommit clock is shortest: model conditional time to commit `2.0258`.
- `OP_SUCCESS_TIP` is the most commit-favored branch in the fitted model: model commitment reach probability `0.9788`.
- `OP_EFFICIENCY_TIP` balances a relatively high commitment reach probability `0.9668` with a moderate fitted commit time `2.8542`.
- `OP_STALE_CONTROL_OFF_RIDGE` differs from `OP_BALANCED_RIDGE_MID` mainly through slower fitted commitment timing (`2.6460` vs `2.4318`) and a nonzero weak trap sink (`0.000488` vs `0.000000`).

## Qualitative Ordering Test

- speed proxy winner from the fitted precommit model: `OP_SPEED_TIP`; expected speed-favored point: `OP_SPEED_TIP`; match: `yes`
- success proxy winner from the fitted precommit model: `OP_SUCCESS_TIP`; expected success-favored point: `OP_SUCCESS_TIP`; match: `yes`
- efficiency proxy winner from the fitted precommit model: `OP_SPEED_TIP`; expected efficiency-favored point: `OP_EFFICIENCY_TIP`; match: `no`

Interpretation:

- The precommit rate model should be judged first on whether it explains the precommit backbone, not whether it fully reproduces downstream transport objectives that still contain crossing physics.
- A match on speed and success proxies is strong evidence that the fitted backbone is meaningful.
- A mismatch on the efficiency proxy, if present, indicates that efficiency still mixes precommit organization with downstream transport costs that are outside the present theory.

## What this theory explains already, and what must wait for crossing-specific analysis?

Explains already:

- qualitative speed-favored operation through faster precommit timing
- qualitative success-favored operation through stronger commitment reach before loss
- stale-control degradation through slower precommit timing plus a weak rare trap sink
- ridge organization as a precommit recycling-and-timing problem, not a crossing-rate problem

Must wait:

- any fitted `gate_commit -> gate_crossing` rate
- any post-crossing state model
- any claim that this is a full doorway-crossing theory rather than a precommit theory
- any strong kinetic inference from the trap sink, which remains weakly supported

## Extrapolative Claims

- The fitted precommit rate trends support a reduced-theory direction for the productive-memory ridge, but they do not yet justify extrapolation to full crossing success or geometry transfer without later crossing-specific analysis.
- Use `trap_episode` only as a weak auxiliary sink in the current model.

## Practical Conclusion

The first fitted precommit model already explains the productive-memory ridge as a backbone timing-and-recycling structure. The most important fitted parameters are the search-cycle and arrival rates that set the time to first commitment, together with a weak auxiliary stale sink. What remains outside the theory is the final crossing physics after commitment.
