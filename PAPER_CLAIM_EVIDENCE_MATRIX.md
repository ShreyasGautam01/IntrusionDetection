# Claim–Evidence Matrix

| Claim ID | Section | Claim | Level | Evidence / Citation | Evidence location | Scope | Statistical support | Citation required | Verified |
|---|---|---|---|---|---|---|---|---|---|
| C-001 | Introduction | Cross-domain and temporal shift can alter IDS discrimination, calibration, threshold behavior, and score interpretation. | C3 | CIT-001; CIT-002 | Sources [1], [2] | IDS deployment under shift | Not applicable | Yes | Yes |
| C-002 | Introduction | Lightweight confidence, agreement, conformal, and novelty signals have documented limitations under distribution shift. | C3 | CIT-001; CIT-002; CIT-003 | Sources [1]–[3] | Reliability monitoring | Not applicable | Yes | Yes |
| C-003 | Introduction | Recent work reports family-dependent and sometimes inverted probability-/feature-space novelty behavior. | C1/C2 | CIT-003 | Source [3] | Unseen-family novelty analysis | Source-specific | Yes | Yes |
| C-004 | Introduction | The primary datasets share a common NetFlow-v3 representation with 53 extended features. | C1 | CIT-004 | Source [4] | NF-UNSW-NB15-v3 / NF-CSE-CIC-IDS2018-v3 | Not applicable | Yes | Yes |
| C-005 | Introduction | The present study evaluates five lightweight reliability layers under a common fixed RF, source-only, bidirectional transfer protocol. | C1 | Frozen methodology + completed experiment artifacts | Methodology and transfer-analysis artifacts | UNSW↔CIC | Yes, where comparisons are stated | No external citation required | Yes |
| C-006 | Abstract | RF disagreement has the highest mean attack-miss AUPRC in UNSW→CIC (0.238). | C1 | analysis_aggregate.csv | direction=UNSW→CIC, method=RF disagreement | Primary transfer | Descriptive | No | Yes |
| C-007 | Abstract | Split conformal has the highest mean attack-miss AUPRC in CIC→UNSW (0.079). | C1 | analysis_aggregate.csv | direction=CIC→UNSW, method=split conformal | Primary transfer | Descriptive | No | Yes |
| C-008 | Abstract | Split conformal has the highest mean 5% attack-miss capture in both directions. | C1 | analysis_aggregate.csv | 5% capture rows | Operational endpoint | Descriptive | No | Yes |
| C-009 | Abstract/Introduction | No single reliability signal dominates across both directions. | C2 | analysis_aggregate.csv; paired statistics | Both directions | Primary methods | Yes; final multiplicity audit required | No | Provisional |

## Related Work claims

| Claim ID | Section | Claim | Level | Evidence / Citation | Evidence location | Scope | Statistical support | Citation required | Verified |
|---|---|---|---|---|---|---|---|---|---|
| C-010 | Related Work | Recent IDS cross-dataset studies report threshold-transfer failures and score-orientation changes under benchmark shift. | C1 | CIT-002 | Source [2] | Cross-dataset IDS | Source-specific | Yes | Yes |
| C-011 | Related Work | Recent temporal IDS work has evaluated confidence monitoring, model agreement, and conformal abstention under label-free shift. | C1 | CIT-001 | Source [1] | Temporal IDS shift | Source-specific | Yes | Yes |
| C-012 | Related Work | Recent IDS uncertainty work evaluates uncertainty-aware RF and neural approaches for trustworthy and open-set IDS. | C1 | CIT-005 | Source [5] | IDS uncertainty | Source-specific | Yes | Yes |
| C-013 | Related Work | Selective prediction formalizes a risk-coverage tradeoff through a reject option. | C1 | CIT-008 | Source [8] | General selective classification | Not applicable | Yes | Yes |
| C-014 | Related Work | Conformal prediction provides distribution-free uncertainty sets under exchangeability assumptions. | C1 | CIT-007 | Source [7] | General conformal prediction | Not applicable | Yes | Yes |
| C-015 | Related Work | Recent IDS conformal triage work reports family-dependent novelty behavior and score inversion. | C1 | CIT-003 | Source [3] | Unseen attack families | Source-specific | Yes | Yes |
| C-016 | Related Work | Recent transfer-learning IDS work improves cross-domain target performance through target-domain adaptation, which answers a different question from source-only transportability. | C1/C3 | CIT-010 | Source [10] | Cross-dataset adaptation | Source-specific | Yes | Yes |
| C-017 | Related Work | Isolation Forest is an established lightweight unsupervised anomaly-detection construction. | C1 | CIT-009 | Source [9] | General anomaly detection | Not applicable | Yes | Yes |
| C-018 | Related Work | No individual component is presented as algorithmically novel; the contribution is the controlled empirical comparison focused on attack-miss prioritization under frozen source-only transfer. | C2/C3 | CIT-001–CIT-013 + completed artifacts | Section II-E | Present study scope | Final novelty audit required | Yes | Provisional |

## Methodology claims

| Claim ID | Section | Claim | Level | Evidence / Citation | Evidence location | Scope | Statistical support | Citation required | Verified |
|---|---|---|---|---|---|---|---|---|---|
| C-019A | Related Work | TAN-IDS explicitly evaluates direct cross-dataset NetFlow transfer without adaptation and also studies mixed-domain training and limited-label target fine-tuning, so the present source-only reliability study must be positioned as narrower. | C1/C3 | CIT-011 | Source [11] | NetFlow domain-shift evaluation | Source-specific | Yes | Yes |
C-019B | Related Work | Recent budget-aware NetFlow risk-gating work uses labeled target calibration data, distinguishing target-aware risk adaptation from the present source-only frozen reliability protocol. | C1/C3 | CIT-012 | Source [12] | Budget-aware NetFlow triage | Source-specific | Yes | Yes |
C-019C | Related Work | Recent temporal alert-stream work shows that risk-score ranking and realized alert-budget behavior can diverge under threshold transfer, reinforcing the need for explicit budgeted evaluation. | C1/C3 | CIT-013 | Source [13] | Temporal budgeted alerting | Source-specific | Yes | Yes |
C-019 | Methodology | The study evaluates a fixed RF detector plus frozen source-derived reliability layers under bidirectional source-only transfer. | C1 | Frozen transfer manifests | target_transfer_manifest_* | UNSW↔CIC | Not applicable | No | Yes |
| C-020 | Methodology | The primary predictive interface contains 46 features; seven metadata/identifier fields are excluded from predictors. | C1 | Frozen feature registry/manifests | transfer_feature_registry.csv; target manifests | Both datasets | Not applicable | No | Yes |
| C-021 | Methodology | Source partitions are deterministic 60/20/20 train/calibration/test splits based on a label-independent SHA-256 procedure. | C1 | Source manifests | source_e1_manifest.json; source_e1_cic_experiment_manifest.json | Both source directions | Not applicable | No | Yes |
| C-022 | Methodology | Probability calibration is source-only Platt/sigmoid calibration. | C1 | Source manifests; CIT-006 | source calibration configuration | Both directions | Not applicable | Yes | Yes |
| C-023 | Methodology | Split conformal uses alpha=0.10 and a disjoint source conformal-calibration subset. | C1 | Target transfer manifests; CIT-007 | reliability_signals.split_conformal | Both directions | Not applicable | Yes | Yes |
| C-024 | Methodology | Feature-space distance is mean Euclidean distance to the exact five nearest source-training rows after source-only standardization. | C1 | Target transfer manifests | distance_parameters | Both directions | Not applicable | No | Yes |
| C-025 | Methodology | Isolation Forest is source-training-only with 100 estimators and max_samples=256. | C1 | Target transfer manifests; CIT-009 | reliability_signals.isolation_forest | Both directions | Not applicable | Yes | Yes |
| C-026 | Methodology | Target review budgets are 1%, 5%, and 10%, with 5% as the primary operational endpoint. | C1 | Target transfer manifests; completed analysis | review_budgets | Both directions | Not applicable | No | Yes |
| C-027 | Methodology | Attack-miss capture ranks the highest-reliability target rows and divides selected attack misses by all target attack misses. | C1 | Frozen analysis implementation | analysis/selective artifacts | Both directions | Not applicable | No | Yes |
| C-028 | Methodology | Family-level conclusions are restricted to the documented shared DoS mapping. | C1 | transfer_family_registry.csv | family registry | Both directions | Not applicable | No | Yes |

## Experimental Setup claims

| Claim ID | Section | Claim | Level | Evidence / Citation | Evidence location | Scope | Statistical support | Citation required | Verified |
|---|---|---|---|---|---|---|---|---|---|
| C-029 | Experimental Setup | The audited datasets contain 2,365,424 and 20,115,529 total flows, respectively, with deterministic source partitions as reported. | C1 | Frozen transfer manifests; CIT-004 | target_transfer_manifest_* | Both datasets | Not applicable | Yes for dataset context | Yes |
| C-030 | Experimental Setup | Each transfer direction uses ten fixed seeds 0–9. | C1 | Frozen target manifests | seeds | Both directions | Not applicable | No | Yes |
| C-031 | Experimental Setup | Target-label isolation passes for fitting, tuning, recalibration, and score construction. | C1 | FINAL_ANALYSIS_AUDIT.json | audit fields | Both directions | Not applicable | No | Yes |
| C-032 | Experimental Setup | Five reliability signals are evaluated under a common high-score-means-review orientation. | C1 | Frozen transfer manifests | reliability_signals | Both directions | Not applicable | No | Yes |
| C-033 | Experimental Setup | Review budgets are 1%, 5%, and 10%, with 5% primary. | C1 | Frozen target manifests | review_budgets | Both directions | Not applicable | No | Yes |
| C-034 | Experimental Setup | Results are retained per seed and paired comparisons use the same seed across methods. | C1/C2 | analysis_per_seed_all_metrics.csv; analysis_paired_statistics.csv | analysis artifacts | Both directions | Yes | No | Yes |
| C-035 | Experimental Setup | The computational environment is pinned through the repository lockfile and versioned artifacts. | C1 | REPRODUCTION.md; uv.lock; artifact manifest | environment records | Entire study | Not applicable | No | Yes |


## Results claims — V-A Primary Security Endpoint

| Claim ID | Section | Claim | Level | Evidence / Citation | Evidence location | Scope | Statistical support | Citation required | Verified |
|---|---|---|---|---|---|---|---|---|---|
| C-036 | Results V-A | RF disagreement has the highest mean attack-miss AUPRC in UNSW→CIC at 0.237903. | C1 | analysis_aggregate.csv | unsw-to-cic / random_forest_disagreement / attack_miss_auprc | 10 seeds | Descriptive | No | Yes |
| C-037 | Results V-A | Split conformal has the highest mean attack-miss AUPRC in CIC→UNSW at 0.079389. | C1 | analysis_aggregate.csv | cic-to-unsw / split_conformal / attack_miss_auprc | 10 seeds | Descriptive | No | Yes |
| C-038 | Results V-A | RF disagreement versus confidence differs by 0.045789 AUPRC in UNSW→CIC. | C2 | analysis_paired_statistics.csv | unsw-to-cic / attack_miss_auprc | Matched seeds | Paired CI and raw exact sign-flip p | No | Yes |
| C-039 | Results V-A | RF disagreement versus split conformal differs by 0.141751 AUPRC in UNSW→CIC. | C2 | analysis_paired_statistics.csv | unsw-to-cic / attack_miss_auprc | Matched seeds | Paired CI and raw exact sign-flip p | No | Yes |
| C-040 | Results V-A | Split conformal has the smallest absolute directional mean gap in attack-miss AUPRC at 0.016764. | C1 | analysis_direction_shift.csv | attack_miss_auprc rows | Two directions | Descriptive | No | Yes |
| C-041 | Results V-A | RF disagreement has the largest absolute directional mean gap in attack-miss AUPRC at 0.203221. | C1 | analysis_direction_shift.csv | attack_miss_auprc rows | Two directions | Descriptive | No | Yes |
| C-042 | Results V-A | The best mean attack-miss ranking changes when transfer direction is reversed. | C2 | analysis_aggregate.csv; analysis_direction_shift.csv | both directions | Primary methods | Descriptive cross-direction comparison | No | Yes |

| C-043 | Results V-B | Split conformal has the highest mean 5% attack-miss capture in both transfer directions: 17.37% and 14.73%. | C1 | analysis_aggregate.csv | capture_0.05 rows | Both directions | Descriptive | No | Yes |
| C-044 | Results V-B | In UNSW→CIC, RF disagreement has the highest mean 10% capture among the non-conformal signals at 24.68%. | C1 | analysis_aggregate.csv | unsw-to-cic / capture_0.10 | Secondary operational | Descriptive | No | Yes |
| C-045 | Results V-B | The operational ranking can differ from the attack-miss AUPRC ranking: RF disagreement leads AUPRC in UNSW→CIC, while split conformal leads 5% capture. | C2 | analysis_aggregate.csv | Sections V-A and V-B | UNSW→CIC | Descriptive cross-metric comparison | No | Yes |
| C-046 | Results V-B | RF disagreement minus split conformal at 5% capture is -0.0504 in UNSW→CIC, with a bootstrap interval spanning zero. | C2 | analysis_paired_statistics.csv | unsw-to-cic / capture_0.05 / RF vs split conformal | Matched seeds | Paired CI | No | Yes |
| C-047 | Results V-B | RF disagreement minus split conformal at 5% capture is -0.1385 in CIC→UNSW, with a bootstrap interval entirely below zero. | C2 | analysis_paired_statistics.csv | cic-to-unsw / capture_0.05 / RF vs split conformal | Matched seeds | Paired CI | No | Yes |
| C-048 | Results V-B | Review-budget behavior is signal- and direction-dependent. | C2 | analysis_aggregate.csv | capture_0.01/0.05/0.10 | Both directions | Descriptive | No | Yes |

| C-049 | Results V-C | In UNSW→CIC, feature-space distance and Isolation Forest have generic-error AUPRC of 0.859 and 0.847 but attack-miss AUPRC of 0.109 and 0.077. | C1 | analysis_generic_error.csv; analysis_aggregate.csv | direction/method rows | UNSW→CIC | Descriptive | No | Yes |
| C-050 | Results V-C | In UNSW→CIC, Isolation Forest attack-miss AUROC is below 0.5 on all but one seed, with mean 0.379. | C1 | analysis_generic_error.csv | isolation_forest rows | UNSW→CIC | Descriptive semantic diagnostic | No | Yes |
| C-051 | Results V-C | In CIC→UNSW, generic-error AUPRC is approximately identical to attack-miss AUPRC for each signal because generic errors are almost entirely attack misses. | C1 | analysis_generic_error.csv; analysis_per_seed_all_metrics.csv | both direction/method rows | CIC→UNSW | Descriptive | No | Yes |
| C-052 | Results V-C | In CIC→UNSW, confidence, RF disagreement, feature-space distance, and Isolation Forest have mean attack-miss AUROC below 0.5 and inversion flags for all ten seeds. | C1 | analysis_generic_error.csv | attack_miss_auroc and inversion_flag fields | CIC→UNSW | Descriptive semantic diagnostic | No | Yes |
| C-053 | Results V-C | In CIC→UNSW, split conformal is the only signal with attack-miss AUROC above 0.5 for all ten seeds, with mean 0.545. | C1 | analysis_generic_error.csv | split_conformal rows | CIC→UNSW | Descriptive semantic diagnostic | No | Yes |
| C-054 | Results V-C | Generic prediction-error ranking is not sufficient to characterize security-critical attack-miss prioritization. | C2 | Table VI; C-049–C-053 | Section V-C | Both directions | Supported by contrastive descriptive evidence | No | Yes |

| C-055 | Results V-D | RF disagreement has the largest directional attack-miss AUPRC gap (0.203) and 5% capture gap (0.115). | C1 | analysis_direction_shift.csv | RF disagreement rows | Both directions | Descriptive | No | Yes |
| C-056 | Results V-D | Split conformal has the smallest directional attack-miss AUPRC gap (0.017). | C1 | analysis_direction_shift.csv | split_conformal attack_miss_auprc | Both directions | Descriptive | No | Yes |
| C-057 | Results V-D | Feature-space distance has a higher mean 5% capture in CIC→UNSW (4.34%) than in UNSW→CIC (0.58%). | C1 | analysis_aggregate.csv; analysis_direction_shift.csv | feature_space_distance capture_0.05 | Both directions | Descriptive | No | Yes |
| C-058 | Results V-D | Small directional change does not necessarily imply useful reliability utility, as illustrated by Isolation Forest. | C3 | analysis_aggregate.csv; analysis_direction_shift.csv | isolation_forest | Both directions | Descriptive interpretation | No | Yes |
| C-059 | Results V-D | Bidirectional evaluation changes the identity of the highest mean attack-miss AUPRC signal, from RF disagreement to split conformal. | C1/C2 | analysis_aggregate.csv | Sections V-A and V-D | Both directions | Descriptive | No | Yes |

| C-060 | Results V-E | The frozen cross-domain family analysis supports only a documented shared DoS category and does not justify broad unseen-family claims. | C1 | transfer_family_registry.csv; analysis_family_scope.md | family registry/scope | Both directions | Not applicable | No | Yes |
| C-061 | Results V-E | UNSW→CIC has zero target rows in the saved shared-DoS family-analysis subset. | C1 | analysis_family_results.csv | unsw-to-cic / DoS | UNSW→CIC | Descriptive | No | Yes |
| C-062 | Results V-E | CIC→UNSW has 5,980 mapped DoS rows, all of which are attack misses, making within-family AUPRC 1.0 for every signal. | C1 | analysis_family_results.csv | cic-to-unsw / DoS | CIC→UNSW | Descriptive; trivial by construction | No | Yes |
| C-063 | Results V-E | The family analysis is insufficient for a general unseen-family robustness claim. | C3 | C-060–C-062 | Section V-E | Both directions | Not applicable | No | Yes |

| C-064 | Results V-F | Mean target Brier score and ECE are 0.245 and 0.317 in UNSW→CIC, versus 0.075 and 0.153 in CIC→UNSW. | C1 | analysis_calibration_conformal.csv | brier_score/ece_15bin by direction | Both directions | Descriptive | No | Yes |
| C-065 | Results V-F | The saved target conformal ambiguity/set-size diagnostics are internally inconsistent with binary prediction-set cardinality and are withheld from quantitative manuscript claims. | C1/C3 | analysis_calibration_conformal.csv; harness QA | target_ambiguity_rate; target_mean_prediction_set_size | Both directions | QA finding | No | Yes |
| C-066 | Results V-F | The transfer integrity audit confirms no target labels were used for fitting, tuning, recalibration, or score construction. | C1 | FINAL_ANALYSIS_AUDIT.json | audit fields | Both directions | Not applicable | No | Yes |

| C-067 | Results V-G | RF disagreement exceeds split conformal by 0.142 attack-miss AUPRC in UNSW→CIC, with CI [0.082, 0.206]. | C2 | analysis_paired_statistics.csv | unsw-to-cic / attack_miss_auprc | Matched seeds | Exact sign-flip p and bootstrap CI | No | Yes |
| C-068 | Results V-G | In UNSW→CIC, RF disagreement minus split conformal at 5% capture is -0.050 with CI [−0.110, 0.016], so the paired interval spans zero. | C2 | analysis_paired_statistics.csv | unsw-to-cic / capture_0.05 | Matched seeds | Exact sign-flip p and bootstrap CI | No | Yes |
| C-069 | Results V-G | In CIC→UNSW, split conformal exceeds RF disagreement by 0.045 attack-miss AUPRC and feature-space distance by 0.036, with intervals excluding zero. | C2 | analysis_paired_statistics.csv | cic-to-unsw / attack_miss_auprc | Matched seeds | Exact sign-flip p and bootstrap CI | No | Yes |
| C-070 | Results V-G | In CIC→UNSW, split conformal exceeds RF disagreement by 0.139 in mean 5% attack-miss capture, with CI [0.111, 0.169]. | C2 | analysis_paired_statistics.csv | cic-to-unsw / capture_0.05 | Matched seeds | Exact sign-flip p and bootstrap CI | No | Yes |
| C-071 | Results V-G | Secondary pairwise p-values are interpreted as support for individual contrasts rather than a single global ranking because multiple comparisons are present. | C3 | Research harness; analysis_paired_statistics.csv | statistical interpretation | Entire study | Multiplicity policy | No | Yes |

| C-072 | Results V-H | The RF execution benchmark showed 17.64 s at n_jobs=10 and 16.50 s at n_jobs=16 on the bounded benchmark, while higher worker settings saturated CPU more strongly. | C1 | analysis_computational_cost.md; n_jobs benchmark artifacts | RF execution benchmark | Bounded benchmark | Descriptive | No | Yes |
| C-073 | Results V-H | RF n_jobs was treated as an execution parameter rather than a scientific factor because tested settings were exactly equivalent to the n_jobs=1 reference on tree structure, probabilities, and disagreement. | C1 | computational benchmark decision | equivalence audit | RF implementation | Not applicable | No | Yes |

| C-074 | Discussion VI-A | Reliability ranking is not universally transportable; the best AUPRC signal changes with transfer direction. | C2 | Results V-A/V-D | Both directions | Supported by completed results | No | Yes |
| C-075 | Discussion VI-B | Input atypicality and detector-failure reliability are distinct objectives. | C3 | Results V-C; CIT-003 | UNSW→CIC | Interpretive | Yes | Yes |
| C-076 | Discussion VI-B | Score orientation can reverse after transfer, creating a risk of systematically misdirected review if high-score semantics are assumed unchanged. | C2/C3 | Results V-C; CIT-002/CIT-003 | CIC→UNSW | Descriptive + literature context | Yes | Yes |
| C-077 | Discussion VI-C | Split conformal shows comparatively stable attack-miss AUPRC across directions, but this study does not establish target-domain conformal coverage guarantees. | C2 | Results V-A/V-D; CIT-007 | Both directions | Primary transfer | Yes | Yes |
| C-078 | Discussion VI-D | Source-only monitoring is a baseline for frozen deployment rather than a replacement for target-domain adaptation. | C3 | Methodology; CIT-010 | Study scope | Conceptual | Yes | Yes |
| C-079 | Discussion VI-E | The present contribution is empirical transportability analysis rather than algorithmic novelty. | C3 | Literature audit; complete study | Entire study | Novelty claim | Yes | Provisional pending final literature audit |
| C-080 | Discussion VI-F | Temporal drift, target-label-efficient recalibration, broader domain replication, family-conditional analysis, and composite reliability are major logical extensions. | C3 | Results; CIT-001/CIT-003 | Future work | Not applicable | Yes | Yes |

| C-081 | Limitations VII-A | Findings are based on two NetFlow-v3 datasets and two transfer directions. | C1 | target transfer manifests | dataset/domain scope | Not applicable | No | Yes |
| C-082 | Limitations VII-B | The fixed RF backbone limits architectural generalization. | C1 | methodology/transfer manifests | detector scope | Not applicable | No | Yes |
| C-083 | Limitations VII-C | Ten seeds quantify repeated training variability, not independent deployments. | C1 | frozen manifests | seed design | Not applicable | No | Yes |
| C-084 | Limitations VII-D | Family analysis does not support a comprehensive unseen-family conclusion. | C1 | family registry + Results V-E | family scope | Not applicable | No | Yes |
| C-085 | Limitations VII-E | Conformal target ambiguity/set-size diagnostics are withheld because their saved values are internally inconsistent. | C1 | calibration CSV + QA harness | conformal diagnostics | QA | No | Yes |
| C-086 | Limitations VII-F | No target adaptation or recalibration is evaluated. | C1 | frozen transfer manifests | source-only protocol | Not applicable | No | Yes |
| C-087 | Limitations VII-G | Offline benchmark review budgets are an abstraction of SOC analyst workflows. | C3 | methodology + literature | deployment scope | Not applicable | Yes | Yes |
| C-088 | Limitations VII-H | Multiple methods and secondary endpoints require cautious interpretation of individual p-values. | C3 | statistical harness; paired statistics | inference scope | Multiplicity | No | Yes |
| C-089 | Limitations VII-I | Reliability conclusions remain representation dependent, particularly distance and novelty signals. | C3 | methodology; feature registry | 46-feature interface | No | No | Yes |

| C-090 | Conclusion VIII | The study shows reliability transportability is direction dependent. | C2 | Results V-A/V-D | Both directions | Descriptive + paired effects | No | Yes |
| C-091 | Conclusion VIII | Split conformal has the highest mean 5% attack-miss capture in both directions. | C1 | Results V-B | Both directions | Primary operational endpoint | No | Yes |
| C-092 | Conclusion VIII | Generic-error ranking is not a sufficient substitute for attack-miss prioritization. | C2 | Results V-C | Both directions | Security endpoint | No | Yes |
| C-093 | Conclusion VIII | Several reliability scores can reverse semantic orientation after cross-domain transfer. | C2 | Results V-C | CIC→UNSW primarily | Semantic diagnostic | No | Yes |
| C-094 | Conclusion VIII | The study does not establish a universal best signal or comprehensive unseen-family robustness. | C1/C3 | Entire study scope | Entire study | Scope limitation | No | Yes |
