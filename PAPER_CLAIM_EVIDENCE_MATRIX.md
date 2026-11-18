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
| C-018 | Related Work | No individual component is presented as algorithmically novel; the contribution is the controlled empirical comparison focused on attack-miss prioritization under frozen source-only transfer. | C2/C3 | CIT-001–CIT-010 + completed artifacts | Section II-E | Present study scope | Final novelty audit required | Yes | Provisional |

## Methodology claims

| Claim ID | Section | Claim | Level | Evidence / Citation | Evidence location | Scope | Statistical support | Citation required | Verified |
|---|---|---|---|---|---|---|---|---|---|
| C-019 | Methodology | The study evaluates a fixed RF detector plus frozen source-derived reliability layers under bidirectional source-only transfer. | C1 | Frozen transfer manifests | target_transfer_manifest_* | UNSW↔CIC | Not applicable | No | Yes |
| C-020 | Methodology | The primary predictive interface contains 46 features; seven metadata/identifier fields are excluded from predictors. | C1 | Frozen feature registry/manifests | transfer_feature_registry.csv; target manifests | Both datasets | Not applicable | No | Yes |
| C-021 | Methodology | Source partitions are deterministic 60/20/20 train/calibration/test splits based on a label-independent SHA-256 procedure. | C1 | Source manifests | source_e1_manifest.json; source_e1_cic_experiment_manifest.json | Both source directions | Not applicable | No | Yes |
| C-022 | Methodology | Probability calibration is source-only Platt/sigmoid calibration. | C1 | Source manifests; CIT-006 | source calibration configuration | Both directions | Not applicable | Yes | Yes |
| C-023 | Methodology | Split conformal uses alpha=0.10 and a disjoint source conformal-calibration subset. | C1 | Target transfer manifests; CIT-007 | reliability_signals.split_conformal | Both directions | Not applicable | Yes | Yes |
| C-024 | Methodology | Feature-space distance is mean Euclidean distance to the exact five nearest source-training rows after source-only standardization. | C1 | Target transfer manifests | distance_parameters | Both directions | Not applicable | No | Yes |
| C-025 | Methodology | Isolation Forest is source-training-only with 100 estimators and max_samples=256. | C1 | Target transfer manifests; CIT-009 | reliability_signals.isolation_forest | Both directions | Not applicable | Yes | Yes |
| C-026 | Methodology | Target review budgets are 1%, 5%, and 10%, with 5% as the primary operational endpoint. | C1 | Target transfer manifests; completed analysis | review_budgets | Both directions | Not applicable | No | Yes |
| C-027 | Methodology | Attack-miss capture ranks the highest-reliability target rows and divides selected attack misses by all target attack misses. | C1 | Frozen analysis implementation | analysis/selective artifacts | Both directions | Not applicable | No | Yes |
| C-028 | Methodology | Family-level conclusions are restricted to the documented shared DoS mapping. | C1 | transfer_family_registry.csv | family registry | Both directions | Not applicable | No | Yes |
