# Paper Research Harness

## 1. Purpose

This harness is the quality-control contract for the research paper.

It is designed to prevent four classes of failure:

1. **Scientific drift** — the manuscript silently changes the experiment.
2. **Evidence drift** — prose claims become stronger than the saved results.
3. **Statistical drift** — descriptive differences are presented as proven superiority.
4. **Publication drift** — formatting or word-count pressure removes methodological information needed for reproducibility.

The harness is run repeatedly during manuscript production and once immediately before submission.

A failed gate means the affected manuscript section is not publication-ready.

---

# 2. Immutable scientific contract

These quantities are treated as study invariants.

| Item | Locked value |
|---|---|
| Detector | Random Forest |
| Detector trees | 200 |
| Minimum leaf size | 5 |
| Primary datasets | NF-UNSW-NB15-v3, NF-CSE-CIC-IDS2018-v3 |
| Transfer directions | UNSW→CIC, CIC→UNSW |
| Predictive representation | frozen 46-feature interface |
| Seeds | 0–9 |
| Reliability signals | confidence, RF disagreement, feature-space distance, split conformal, Isolation Forest |
| Transfer regime | source-only frozen transfer |
| Primary security endpoint | attack-miss AUPRC |
| Primary operational endpoint | attack-miss capture at 5% review |
| Secondary review budgets | 1%, 10% |
| Primary family evidence | only frozen, defensible semantic mappings |
| Target-label rule | labels only after frozen transfer scoring |
| RF production fit setting | n_jobs=10 |
| RF prediction setting | n_jobs=1 |
| BLAS/OpenMP | 1 |

Any manuscript sentence that contradicts an invariant fails the harness.

---

# 3. Claim-strength hierarchy

Every substantive claim belongs to one of four levels.

## C1 — Directly measured

Example:

> RF disagreement had the highest mean attack-miss AUPRC in UNSW→CIC.

Evidence required:

- aggregate results file;
- direction;
- metric;
- method;
- seed count.

## C2 — Statistically supported

Example:

> The paired difference between method A and method B was positive across the ten matched seeds.

Evidence required:

- paired statistics file;
- effect estimate;
- interval;
- statistical test.

## C3 — Mechanistic interpretation

Example:

> The signal may be sensitive to the target feature distribution.

Evidence required:

- supporting diagnostic;
- compatible score behavior;
- literature support or clearly marked interpretation.

## C4 — Generalization claim

Example:

> This reliability mechanism is robust for deployed IDS.

This is prohibited unless the evidence base actually supports the scope.

Default rule:

> The manuscript should prefer C1/C2 claims, use C3 claims cautiously, and avoid C4 claims unless independently supported.

---

# 4. Claim ledger requirement

Every manuscript claim that contains a number, comparison, methodological assertion, or causal interpretation must be recorded in a claim ledger.

Minimum fields:

| Field | Description |
|---|---|
| Claim ID | stable identifier |
| Manuscript section | Intro / Methods / Results / Discussion / Conclusion |
| Claim | exact intended sentence or proposition |
| Claim level | C1/C2/C3/C4 |
| Evidence file | CSV/JSON/figure/table/reference |
| Evidence location | row/column/section |
| Scope | dataset/direction/method |
| Statistical support | yes/no/not applicable |
| Citation required | yes/no |
| Verified | yes/no |

No C1/C2 claim may enter the final manuscript without an evidence location.

No C3 claim may enter the Discussion without its supporting evidence being named.

C4 claims require explicit approval during the final scientific review.

---

# 5. Automatic integrity gates

The following checks must pass before manuscript drafting proceeds.

## Gate A — Artifact integrity

Require:

- `FINAL_ANALYSIS_AUDIT.json` exists;
- `pass == true`;
- `issues == []`;
- `all_primary_transfer_artifacts_checked == true`.

Reject when any integrity issue is present.

## Gate B — Leakage integrity

Require:

- `target_labels_used_for_fitting == false`;
- `target_labels_used_for_tuning == false`;
- `target_labels_used_for_recalibration == false`;
- `target_labels_used_for_score_construction == false`.

Reject when any value is true.

## Gate C — Seed integrity

Require:

- exactly ten seeds;
- seed set = {0,1,2,3,4,5,6,7,8,9};
- every primary method has all ten seed records in both directions.

Reject partial or duplicated seed sets.

## Gate D — Direction integrity

Require both:

- `unsw-to-cic`;
- `cic-to-unsw`.

Reject a manuscript that reports one direction as though it were the complete study.

## Gate E — Method integrity

Require exactly the five primary reliability methods:

- confidence;
- random_forest_disagreement;
- feature_space_distance;
- split_conformal;
- isolation_forest.

A method cannot disappear from the primary table merely because its performance is weak.

## Gate F — Primary endpoint integrity

Require:

- attack-miss AUPRC;
- 5% attack-miss capture.

These are the only metrics allowed to determine the primary headline ranking.

---

# 6. Numerical consistency harness

For every table in the paper:

1. identify the machine-readable source;
2. load the source;
3. regenerate the displayed value;
4. round only at presentation time;
5. compare with the manuscript.

Never compute a manuscript number by manually copying a value from another manuscript table.

### Required checks

- direction;
- method;
- seed aggregation;
- numerator/denominator;
- unit;
- percentage vs fraction;
- decimal rounding;
- missing values;
- sign;
- metric definition.

### Rounding rule

Keep full precision in source artifacts.

Use consistent presentation precision in the manuscript.

Do not use more decimal places merely because a tiny difference appears statistically interesting.

---

# 7. Statistical harness

Before the Results section is finalized:

## 7.1 Primary comparisons

Create a short list of the comparisons that answer the research questions.

Do not turn every pairwise comparison into a headline finding.

## 7.2 Paired structure

The same seed must correspond to the same experimental pairing across methods wherever a paired comparison is claimed.

## 7.3 Effect first

For every comparison state:

1. estimated difference;
2. interval;
3. direction;
4. p-value if relevant.

Never write:

> Method A is significantly better.

without stating the estimated difference.

## 7.4 Multiple comparisons

The complete pairwise matrix may contain many tests.

Before publication:

- identify the predeclared primary comparisons;
- select and document an appropriate multiplicity treatment;
- distinguish confirmatory from exploratory comparisons.

The paper must not select "significant" pairs after looking at all p-values.

## 7.5 Small number of seeds

The paper must report that inference is based on ten repeated seeds.

Do not use the ten seeds to imply that the experiment represents ten independent deployments.

---

# 8. Metric semantics harness

## 8.1 Attack-miss endpoint

Verify that the positive event is exactly:

> true attack + detector predicts benign.

This must be implemented consistently across all methods.

## 8.2 Generic-error endpoint

Verify that generic error means:

> detector prediction differs from ground truth.

Do not substitute attack detection for generic error.

## 8.3 Reliability direction

All manuscript-facing reliability scores must obey:

> higher = more deserving of review.

If the implementation uses the reverse raw score, the transformation must be documented.

## 8.4 Review-budget capture

For each budget:

1. sort by the frozen review score;
2. select the highest-scoring fraction;
3. calculate attack-miss capture;
4. retain the denominator used.

No target-optimal threshold may be chosen.

---

# 9. Score-semantic harness

Every reliability signal must pass a semantic audit.

For each direction and method inspect:

- attack-miss AUROC;
- attack-miss AUPRC;
- score distribution;
- ties;
- prevalence;
- direction of association.

Classify each signal as:

- useful;
- weak;
- approximately non-informative;
- inverted;
- indeterminate.

Do not replace an inverted score with its negative after observing target performance. The target behavior is itself an evaluation result.

If a signal is inverted in a target direction, report that fact rather than silently repairing it.

---

# 10. Calibration and conformal harness

Calibration and conformal results require additional validation because their definitions are easy to misreport.

## 10.1 Calibration

Verify:

- calibration data are source-only;
- calibration transform is frozen;
- target recalibration is absent;
- Brier score definition;
- ECE binning definition;
- number of bins;
- handling of empty bins.

## 10.2 Conformal

Verify:

- prediction-set definition;
- nonconformity score;
- calibration split;
- alpha;
- quantile rule;
- tie handling;
- set-size definition;
- coverage denominator.

Reject any conformal statement containing:

- impossible rates;
- undefined denominators;
- unverified quantiles;
- unverified coverage;
- conditional-coverage claims from a marginal procedure.

A conformal result is not publication-ready merely because the code completed successfully.

---

# 11. Family-analysis harness

Family claims require a separate semantic gate.

For every family-level sentence verify:

1. source label;
2. target label;
3. canonical mapping;
4. documentation source;
5. reason for equivalence;
6. sample size;
7. metric definition.

When the mapping is ambiguous:

> do not infer equivalence from similar names.

Use:

- documented family;
- or explicitly state that the mapping is unavailable.

The paper must never manufacture a comprehensive unseen-family story from incomplete semantic crosswalks.

---

# 12. Literature harness

Before the Introduction and Related Work are frozen:

## 12.1 Search freshness

Run a final literature search close to submission.

## 12.2 Direct-adjacency screen

Any paper overlapping at least three of:

- IDS;
- distribution shift;
- reliability/uncertainty;
- source-only transfer;
- analyst triage;
- false-negative prioritization;
- unseen attack-family evaluation;

must be reviewed in full.

## 12.3 Claim verification

For every statement such as:

- "prior work has not...";
- "few studies...";
- "existing methods...";
- "first...";
- "unexplored...";

require a direct literature audit.

Default language:

> "limited controlled evidence"

rather than:

> "no prior work"

unless the search genuinely supports the stronger statement.

## 12.4 Novelty collision test

For every proposed contribution ask:

1. Does a recent paper already do this?
2. Does it use the same datasets?
3. Does it use the same reliability signals?
4. Does it evaluate the same endpoint?
5. Does it use the same source-only protocol?
6. Does it already include review-budget analysis?
7. Does it already analyze score inversion?
8. Does it already evaluate unseen families?

If the answer is yes for the central contribution, narrow or reframe the contribution.

---

# 13. Methods reproducibility harness

A reader should be able to reconstruct the experiment from the Methods section.

The Methods must specify:

- datasets;
- versions/hashes;
- feature selection;
- excluded fields;
- missing/infinite handling;
- data partitions;
- source calibration;
- detector hyperparameters;
- RF seeds;
- five reliability definitions;
- distance definition;
- conformal definition;
- Isolation Forest configuration;
- source-only restrictions;
- target-label firewall;
- metrics;
- statistical tests;
- review budgets;
- compute settings.

Any "standard" method that affects the result must still be defined precisely enough to reproduce the implementation.

---

# 14. Figure harness

Every figure must answer a research question.

For each figure verify:

- purpose;
- x-axis;
- y-axis;
- units;
- direction;
- method labels;
- seed aggregation;
- uncertainty;
- sample size;
- legend;
- caption;
- source artifact.

A figure fails when:

- the axis can be interpreted in two ways;
- a mean is shown without explaining the aggregation;
- error bars are undefined;
- colors encode information not explained in the caption;
- the visual implies a stronger claim than the data.

---

# 15. Table harness

Every table must contain enough context to stand alone.

Required:

- table title;
- units;
- direction;
- method names;
- metric definition;
- aggregation definition;
- footnote for statistical notation.

Primary tables should not contain ten competing metrics in a way that makes the central endpoint disappear.

---

# 16. Manuscript section harness

## Introduction

Must contain:

- concrete problem;
- precise gap;
- why attack misses matter;
- study design;
- contribution boundary.

Must not contain:

- results that belong in Results;
- unsupported novelty claims;
- broad claims about all IDS deployments.

## Related Work

Must contain:

- cross-domain IDS;
- reliability/uncertainty;
- operational triage/selective prediction;
- closest recent work;
- exact distinction from this study.

## Methods

Must be implementation-reconstructable.

## Results

Must be evidence-first.

## Discussion

Must distinguish:

- observation;
- statistical evidence;
- interpretation;
- limitation.

## Limitations

Must state the study boundary directly.

## Conclusion

Must not introduce a new result.

---

# 17. Reviewer-attack harness

Before submission, perform a hostile review.

Ask:

### Novelty attack
"What is actually new here?"

The answer must be one paragraph and must cite the closest competing studies.

### Method attack
"Could the result be an artifact of the feature representation?"

The answer must acknowledge the fixed representation boundary.

### Leakage attack
"Could target labels have influenced the reliability score?"

The answer must point to the firewall and integrity audit.

### Statistical attack
"Are the reported differences robust across seeds?"

The answer must use paired seed-level evidence.

### Dataset attack
"Why only these two environments?"

The answer must explain the controlled common representation and scope.

### Operational attack
"Why should an analyst care?"

The answer must point to review-budget capture of attack misses.

### Generalization attack
"Why should these benchmark results generalize to live SOCs?"

The answer must not overclaim.

---

# 18. Final citation harness

For every external factual statement:

- verify source;
- verify date;
- verify wording;
- cite the primary or authoritative source when practical.

For every method definition:

- cite the original method paper where appropriate.

For every dataset claim:

- cite the dataset source.

For every comparison with prior work:

- cite the exact paper being compared.

Avoid citations that merely support a broad topic while failing to support the specific claim made.

---

# 19. Reproducibility harness

The final release should make these items traceable:

`dataset`
→ `feature registry`
→ `source split`
→ `model configuration`
→ `reliability configuration`
→ `transfer manifest`
→ `score artifact`
→ `metric artifact`
→ `table/figure`
→ `manuscript claim`

This chain is the paper's evidence provenance.

A broken link in the chain is a release blocker.

---

# 20. Final submission gate

The paper can move to submission only when:

- [ ] scientific invariants pass;
- [ ] integrity audit passes;
- [ ] leakage audit passes;
- [ ] seed audit passes;
- [ ] numerical audit passes;
- [ ] statistical audit passes;
- [ ] conformal/calibration audit passes or those claims are removed;
- [ ] family claims pass semantic audit;
- [ ] literature novelty audit passes;
- [ ] every headline claim has evidence;
- [ ] every external factual claim is cited;
- [ ] all figures regenerate correctly;
- [ ] all tables reconcile with machine-readable outputs;
- [ ] the abstract matches the final Results;
- [ ] the conclusion contains no new claims;
- [ ] the venue format is satisfied;
- [ ] the reproducibility package is complete.

---

# 21. Operating rule

The harness follows one governing principle:

> **The manuscript must be a faithful compression of the validated experiment, not a new experiment invented through prose.**

When the writing and the evidence disagree, change the writing.

When the evidence itself is invalid, stop the affected claim.

When the literature overlaps the proposed contribution, narrow the contribution.

When a result is inconvenient, report it.

When a result cannot be defended, remove the claim rather than inventing an explanation.
