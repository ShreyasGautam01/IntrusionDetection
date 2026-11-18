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
