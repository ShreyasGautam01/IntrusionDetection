# Research Paper Production Plan

## Working study title

**Transportability of Lightweight Reliability Signals for Network Intrusion Detection under Source-Only Cross-Domain Transfer**

The final title will be selected only after the literature audit and claim audit. It must describe what the completed evidence actually establishes and must not imply broader unseen-family, representation-invariance, adaptation, or algorithmic novelty than the experiment supports.

---

## 1. Purpose of this document

This document is the governing production plan for converting the completed transfer study into a research paper.

It defines:

- the final scientific scope;
- the research question hierarchy;
- the evidence that must support each claim;
- the order in which the paper will be constructed;
- the analyses that must be checked before manuscript drafting;
- the figures and tables required;
- the statistical and reproducibility gates;
- the literature and novelty audit;
- the manuscript review sequence;
- the publication-readiness criteria.

The paper is an **empirical evaluation/benchmark study**, not a proposal for a new intrusion-detection architecture. The scientific contribution must therefore come from the rigor, control, comparison, and security relevance of the evaluation.

The paper will not present process history. The manuscript will contain only the final study definition, final methodology, validated findings, limitations, and justified conclusions.

---

# 2. Final study definition

## 2.1 Core question

The central question is:

> When a fixed network intrusion detector is deployed in a new network domain without target-domain adaptation or recalibration, how well do lightweight post-hoc reliability signals continue to prioritize the detector's dangerous false-negative attacks?

The paper will answer this at the level of:

- transfer direction;
- reliability mechanism;
- attack-miss ranking;
- analyst-review budget;
- score semantic stability;
- family-level behavior where the frozen family evidence is defensible.

## 2.2 Fixed experimental object

The object being evaluated is:

> **A fixed source-trained Random Forest IDS plus a frozen source-derived reliability layer.**

The detector is not redesigned between target domains.

The reliability signals are not tuned using target labels.

The target data are evaluated only after the source-trained system and all source-derived reliability components are frozen.

## 2.3 Final core scope

The paper will cover:

- NF-UNSW-NB15-v3;
- NF-CSE-CIC-IDS2018-v3;
- the common frozen 46-predictor representation derived from the NetFlow-v3 feature governance;
- Random Forest as the fixed detector;
- ten random seeds;
- both transfer directions;
- five lightweight reliability signals:
  - source-calibrated confidence;
  - Random Forest tree disagreement;
  - exact feature-space 5-nearest-neighbour distance;
  - split conformal;
  - Isolation Forest;
- source-only calibration/fitting;
- target attack-miss AUPRC as the primary endpoint;
- attack-miss capture at 5% analyst review as the primary operational endpoint;
- 1% and 10% review as secondary operational points;
- generic-error analysis;
- directional degradation analysis;
- score-orientation/semantic-stability diagnostics;
- family-level analysis only where the frozen family mapping supports a defensible comparison;
- computational cost reporting;
- full integrity and reproducibility controls.

The paper will not claim that these results apply to every IDS architecture, every dataset, every representation, or every deployment regime.

---

# 3. Research questions for the paper

The manuscript will organize the study around four primary questions and two supporting questions.

### RQ1 — Transportability

How much does each reliability signal's ability to prioritize dangerous attack misses change after source-only transfer between the two network domains?

### RQ2 — Security relevance

Does a reliability signal that ranks generic prediction errors well also rank the subset of errors that are attacks and were falsely classified as benign?

### RQ3 — Directional robustness

Are reliability signals transportable symmetrically, or does the source-target direction materially change their usefulness?

### RQ4 — Operational utility

At a fixed analyst-review budget, which reliability signals capture the largest fraction of attack misses?

### RQ5 — Semantic stability

Do reliability scores retain their intended direction across domains, or can a score become weakly informative, non-informative, or inverted?

### RQ6 — Failure structure

Where supported by the locked family evidence, are reliability failures concentrated in particular attack families or classes of target traffic?

These questions deliberately keep the paper centered on **reliability transportability and security triage**, rather than turning it into a general detector-comparison paper.

---

# 4. What the paper is and is not claiming

## 4.1 Claims the evidence can support

The paper can directly support statements such as:

- reliability signals do not have a universal cross-domain ranking;
- performance differs materially by transfer direction;
- generic error detection is not equivalent to attack-miss detection;
- a signal can be useful at a fixed review budget without being the best generic-error detector;
- source-only reliability behavior can deteriorate under cross-domain transfer;
- different reliability mechanisms respond differently to the same shift;
- the best operational signal in one direction need not be the best in the reverse direction;
- some signals exhibit semantic instability or inversion under transfer;
- the completed RF experiment provides controlled evidence about these behaviors on the two NetFlow-v3 datasets studied.

## 4.2 Claims that are prohibited unless new evidence explicitly supports them

The manuscript must not claim:

- a universally best reliability signal;
- universal IDS robustness;
- universal superiority of conformal prediction, confidence, distance, disagreement, or Isolation Forest;
- that target-domain adaptation is ineffective in general;
- that target recalibration is unnecessary in general;
- comprehensive unseen-attack-family generalization when the family crosswalk does not support it;
- representation-invariant conclusions;
- superiority over arbitrary modern IDS architectures;
- "first ever" novelty unless an exhaustive literature audit actually establishes it;
- that benchmark results automatically transfer to live operational networks;
- that a reliability signal detects attacks rather than prioritizing detector errors, unless the experiment specifically tests that claim;
- strong causal explanations for score inversion that were not experimentally identified.

---

# 5. Contribution strategy

The contribution statement will be framed as an **evaluation contribution**, not a new algorithm.

The likely contribution structure is:

1. **Controlled source-only benchmark of lightweight reliability layers.**
   A fixed RF detector is paired with five post-hoc reliability signals under identical source/target data, feature representation, seeds, and frozen transfer conditions.

2. **Security-specific false-negative evaluation.**
   The central endpoint is attack-miss ranking rather than generic error detection or ordinary attack classification.

3. **Bidirectional transportability analysis.**
   The same reliability layer is evaluated in both source-target directions, exposing direction-dependent behavior that a one-way transfer result would hide.

4. **Operational review-budget analysis.**
   Reliability signals are evaluated as prioritization mechanisms under fixed analyst-review budgets rather than only through threshold-free ranking metrics.

5. **Failure-mode characterization.**
   Generic errors, attack misses, score orientation, family-level behavior, and computational burden are separated rather than collapsed into a single accuracy number.

The final contribution wording will be revised after the literature audit. The standard for acceptance is that each contribution must be both:

- distinct from recent work; and
- demonstrated directly by the completed experiment.

---

# 6. Literature and novelty audit

This stage is mandatory and occurs **before writing the introduction or contribution claims**.

Recent literature already contains work on:

- cross-dataset IDS generalization;
- calibrated alerting and alert budgets;
- score-orientation instability;
- uncertainty-aware IDS;
- conformal intrusion triage;
- unseen attack-family analysis;
- source-only or label-free monitoring under distribution shift.

For example, recent 2026 work evaluates benchmark-shift-aware IDS with calibrated alerting, alert budgets, and score-orientation diagnostics; another 2026 study evaluates conformal prediction, probability-space novelty, feature-space novelty, and unseen attack families on UNSW-NB15/CIC-IDS2017; and a 2026 audit studies confidence, agreement, conformal abstention, and adaptation under temporal IDS shift. These papers make a broad "cross-domain IDS reliability is underexplored" claim unsafe without further qualification.

The novelty audit must therefore compare the completed study against the closest literature along at least these axes:

| Dimension | This study | Prior-study comparison required |
|---|---|---|
| Detector | fixed RF | same / different |
| Reliability mechanisms | confidence, disagreement, distance, conformal, IF | identify overlap |
| Source-only transfer | yes | protocol overlap |
| Bidirectional transfer | yes | compare direction handling |
| Data representation | common NetFlow-v3 | compare feature harmonization |
| Target endpoint | attack-miss AUPRC | determine whether prior work evaluates the same endpoint |
| Review budget | 1/5/10%, primary 5% | compare operational triage |
| Score inversion | diagnostic | determine prior coverage |
| Generic-vs-security-error separation | explicit | determine prior coverage |
| Seed-level paired inference | ten matched seeds | compare statistical rigor |
| Family analysis | constrained documented mapping | compare family semantics |
| Compute analysis | explicit | compare reporting |

### Literature search procedure

Search at minimum:

- IEEE Xplore;
- ACM Digital Library;
- SpringerLink;
- ScienceDirect;
- PubMed where applicable;
- arXiv;
- Google Scholar or equivalent broad scholarly index.

Search families:

- "network intrusion detection" AND "distribution shift";
- "intrusion detection" AND "cross-dataset" AND uncertainty;
- "network intrusion" AND "calibration";
- "network intrusion" AND "conformal prediction";
- "intrusion detection" AND "selective classification";
- "intrusion detection" AND "false negative" AND uncertainty;
- "intrusion detection" AND "review budget";
- "network intrusion" AND "score inversion";
- "intrusion detection" AND "unseen attack families";
- "NetFlow" AND "cross-domain" AND reliability.

Date window:

- prioritize 2021–2026;
- inspect older seminal work for methods/theory;
- perform a final freshness search immediately before submission.

### Literature screening rule

A paper is "directly adjacent" when it overlaps at least three of:

- network IDS;
- cross-domain or shifted evaluation;
- post-hoc reliability/uncertainty;
- analyst triage/review budget;
- unseen-family or false-negative prioritization;
- source-only target evaluation.

Directly adjacent papers receive full comparison in the related-work matrix.

The novelty claim will be narrowed if direct overlap is stronger than expected.

---

## 6A. Literature freshness audit — 2026-11-18

The final-freshness pass identified three directly adjacent 2026 publications that were not in the original registry:

- TAN-IDS: a deployment-oriented NetFlow evaluation framework covering direct cross-dataset transfer without adaptation and limited-label target fine-tuning [11].
- RiskGate-IDS: budget-aware NetFlow risk gating using labeled target calibration, which is methodologically distinct from the source-only frozen protocol used here [12].
- A temporal budget-constrained alert-stream study examining threshold provenance, realized alert budgets, and attack coverage after score-to-alert conversion [13].

These works do not invalidate the study, but they narrow its positioning. The manuscript therefore presents the contribution as a controlled empirical evaluation of lightweight post-hoc reliability signals for **attack-miss prioritization under source-only bidirectional transfer**, rather than as a general deployment-evaluation framework, a budget-aware target-adaptation method, or a general study of alert-threshold transfer.

The literature positioning remains subject to one final submission-time freshness search.

# 7. Source-of-truth hierarchy

When documents disagree, use this hierarchy:

1. validated experiment artifacts and machine-readable result files;
2. frozen methodology and locked experiment manifests;
3. integrity audit and artifact manifest;
4. finalized dataset/schema records;
5. repository documentation;
6. literature sources;
7. general background knowledge.

The paper must never reverse this hierarchy by changing the narrative first and then searching for numbers that fit it.

If a prose report conflicts with a machine-readable artifact, the machine-readable artifact wins and the prose must be corrected.

---

# 8. Pre-manuscript scientific audit

Before drafting prose, perform a final audit of the completed experiment.

## 8.1 Reproducibility identity

Confirm:

- exact commit used for analysis;
- exact study manifests;
- software environment;
- dataset hashes;
- feature registry;
- family registry;
- seeds 0–9;
- both transfer directions;
- five score artifacts per seed;
- all primary metrics;
- all analysis outputs.

## 8.2 Leakage firewall

Confirm and preserve evidence that:

- target labels were not used for fitting;
- target labels were not used for tuning;
- target labels were not used for recalibration;
- target labels were not used to construct reliability scores;
- target labels entered only after transfer scoring for evaluation.

This is a central methodological claim and must be stated clearly in the Methods.

## 8.3 Numerical integrity

Reconcile every headline number in the report against its machine-readable source.

For every table cell:

1. identify the source CSV/JSON;
2. verify direction;
3. verify method;
4. verify metric;
5. verify aggregation;
6. verify rounding.

No manually retyped result may enter the final manuscript without a source record.

## 8.4 Statistical integrity

The completed analysis uses ten matched seeds and paired seed-level inference. Before final manuscript language is written:

- identify every planned primary comparison;
- separate primary comparisons from exploratory comparisons;
- decide how multiple pairwise comparisons will be handled;
- verify confidence-interval construction;
- verify the exact sign-flip permutation implementation;
- verify that seed-level pairing is preserved;
- report effect sizes, not only p-values.

A p-value must never be the sole basis for a sentence such as "method A is better."

## 8.5 Conformal/calibration audit

The calibration/conformal outputs must be inspected at code level before they become headline results.

Any diagnostic field that produces impossible values, missing denominators, or non-interpretable coverage summaries must be excluded from the paper until its definition and implementation are validated.

Conformal coverage claims must be stated only when:

- the prediction-set definition is explicit;
- the source calibration quantile is recoverable;
- the target coverage denominator is explicit;
- the assumptions relevant to the guarantee are stated;
- the manuscript distinguishes marginal coverage from conditional/family-specific behavior.

---

# 9. Results interpretation hierarchy

Results will be interpreted in this order:

### Level 1 — Descriptive

What happened?

Example:

> RF disagreement had the highest mean attack-miss AUPRC in UNSW→CIC.

### Level 2 — Matched-seed evidence

Is the difference stable across the ten paired seeds?

Use:

- paired effect;
- confidence interval;
- exact sign-flip result.

### Level 3 — Mechanistic interpretation

Why might the pattern occur?

Only offer explanations supported by:

- score distributions;
- generic-error comparison;
- family results;
- calibration diagnostics;
- shift diagnostics;
- prior literature.

### Level 4 — Deployment implication

What does the pattern imply for analyst triage?

Use review-budget capture and score stability.

The paper must not jump directly from a mean metric to a broad deployment claim.

---

# 10. Primary results package

The manuscript will use a compact main-results architecture.

## Table 1 — Study and dataset definition

Include:

- dataset;
- rows;
- attack prevalence;
- feature representation;
- source/target role;
- transfer directions.

Purpose: establish what was actually evaluated.

## Table 2 — Reliability signal definitions

For each method:

- mechanism;
- source-only inputs;
- score orientation;
- target-label dependence: none;
- primary hyperparameters.

Purpose: make the benchmark reproducible.

## Table 3 — Primary security results

Columns:

- direction;
- confidence;
- RF disagreement;
- feature-space distance;
- split conformal;
- Isolation Forest;
- attack-miss AUPRC;
- 5% capture.

Purpose: answer RQ1 and RQ4 directly.

The visual emphasis should be on the primary endpoint and the 5% operational endpoint.

## Table 4 — Paired directional effects

Report selected, predeclared pairwise comparisons:

- effect estimate;
- interval;
- exact p-value;
- direction.

Purpose: prevent the narrative from relying on mean ranks alone.

Secondary tables may move to supplementary material.

---

# 11. Primary figures

## Figure 1 — Experimental workflow

Show:

source data
→ source split
→ RF training
→ source calibration/reliability fitting
→ frozen transfer
→ target scoring
→ attack-miss evaluation
→ analyst review simulation.

The figure should make the target-label firewall visually obvious.

## Figure 2 — Attack-miss AUPRC by direction

A compact paired visualization across the two transfer directions.

Purpose:

- show direction asymmetry;
- show absence of a universal winner.

## Figure 3 — Review-budget capture curves

For each direction, plot attack-miss capture as the review budget increases.

Mark:

- 1%;
- 5%;
- 10%.

Purpose:

- translate ranking quality into operational triage.

## Figure 4 — Generic-error versus attack-miss behavior

Use a compact comparison showing where a method's ranking of generic errors diverges from its ranking of attack misses.

Purpose:

- answer RQ2.

## Optional Figure 5 — Reliability semantic stability

Show attack-miss AUROC or an equivalent orientation diagnostic across methods and directions.

Purpose:

- identify weak or inverted score semantics without presenting inversion as a novelty claim.

Family-specific visualizations may be placed in supplementary material unless a family result becomes central to the final contribution.

---

# 12. Manuscript structure

## Section 1 — Introduction

Target:

- problem;
- deployment motivation;
- reliability-layer framing;
- precise research gap;
- study questions;
- contribution summary.

The introduction must not begin with "accuracy is high" as a generic cliché. It should move quickly to the operational problem:

> a detector can make dangerous false-negative attacks under domain shift, while the reliability layer intended to prioritize questionable predictions can itself lose transportability.

The final paragraph should state:

- what is fixed;
- what varies;
- what is measured;
- why attack-miss ranking is the central endpoint.

## Section 2 — Related Work

Organize by problem, not by paper chronology:

### 2.1 Cross-domain IDS generalization

Discuss domain shift and cross-dataset degradation.

### 2.2 Reliability and uncertainty in IDS

Discuss confidence, disagreement, OOD/novelty scores, conformal prediction.

### 2.3 Operational triage and selective prediction

Discuss analyst review, reject options, alert budgets.

### 2.4 What remains unresolved

This paragraph must be the most carefully sourced part of the introduction.

The paper should not claim that no prior work examines these topics individually.

Instead identify the exact combination still needing controlled comparison, if the final literature audit supports that position.

## Section 3 — Methodology

Use the following subsections:

3.1 Research questions and evaluation protocol  
3.2 Datasets and common representation  
3.3 Source-only data partitioning  
3.4 Fixed Random Forest detector  
3.5 Reliability signals  
3.6 Target-label firewall  
3.7 Primary and secondary endpoints  
3.8 Statistical analysis  
3.9 Computational implementation

## Section 4 — Results

Order:

4.1 Primary attack-miss results  
4.2 Review-budget results  
4.3 Directional transportability  
4.4 Generic errors versus attack misses  
4.5 Score semantic stability  
4.6 Family-specific results  
4.7 Calibration/conformal diagnostics  
4.8 Computational cost

The first two subsections must contain the strongest evidence.

## Section 5 — Discussion

Answer the RQs directly.

The discussion should emphasize:

- no universal winner;
- direction dependence;
- difference between generic errors and attack misses;
- operational consequences of score ranking;
- what can and cannot be inferred from the two-domain study.

## Section 6 — Limitations

State explicitly:

- two primary domains;
- fixed RF backbone;
- frozen feature representation;
- finite number of seeds;
- family mapping limitations;
- benchmark-to-deployment gap;
- no target adaptation in the primary protocol;
- any validated limitations of calibration/conformal metrics.

Limitations should be framed as scope boundaries, not apologies.

## Section 7 — Conclusion

Three components only:

1. what was evaluated;
2. what was learned;
3. what the result means for use of lightweight reliability signals in source-only IDS transfer.

---

# 13. Writing sequence

The manuscript will not be written from beginning to end in one pass.

Use this order:

### Pass A — Evidence skeleton

Write only:

- table titles;
- figure titles;
- result sentences;
- exact numerical claims;
- method definitions;
- limitations.

No rhetorical prose.

### Pass B — Methods

Write the methodology while directly checking each sentence against the frozen manifests and implementation.

### Pass C — Results

Write from tables and figures, not from memory.

### Pass D — Discussion

Interpret only the results that survived the statistical and QA audits.

### Pass E — Related work

Write after the novelty matrix exists.

### Pass F — Introduction

Write only after the contribution boundary is settled.

### Pass G — Abstract and title

Write last.

This order prevents the introduction from dictating the results.

---

# 14. Abstract construction

The abstract will have five logical sentences/blocks:

1. deployment problem;
2. experimental design;
3. primary metrics;
4. main result pattern;
5. implication.

It must state that the study is source-only and bidirectional.

It should not claim one method universally wins.

It should include the security-specific target:

> prioritization of attack false negatives.

---

# 15. Discussion logic

For each RQ, the discussion will use:

**Finding → Evidence → Interpretation → Boundary**

Example pattern:

> RF disagreement ranked attack misses most strongly in UNSW→CIC, but split conformal was strongest in the reverse direction. The matched-seed comparison confirms that the ranking difference is not explained solely by one seed. This indicates direction-dependent transportability rather than a universally superior reliability mechanism. The result is limited to the evaluated RF/NetFlow-v3 source-only setting.

This sentence architecture should be used repeatedly.

---

# 16. Statistical reporting standard

The paper will report:

- mean and dispersion across seeds;
- paired effect estimates for selected method comparisons;
- confidence intervals;
- exact/permutation p-values where appropriate;
- the number of seeds;
- the primary endpoint;
- multiple-comparison handling.

Do not report a giant matrix of p-values in the main text.

Use the main paper for the predeclared comparisons that answer the RQs.

Place exploratory pairwise matrices in supplementary material.

If a multiple-testing correction changes which findings are conventionally significant, the manuscript must reflect that change explicitly.

---

# 17. Metric reporting standard

Primary:

- attack-miss AUPRC;
- attack-miss capture at 5% review.

Secondary:

- attack-miss capture at 1% and 10%;
- attack-miss AUROC;
- generic-error AUPRC/AUROC;
- selective risk;
- calibration diagnostics;
- family-level results;
- computational cost.

Use AUPRC rather than accuracy as the main ranking metric because the positive event is a subset of the target population: detector attack misses.

Always report enough context to interpret AUPRC, especially the attack-miss prevalence.

---

# 18. Reviewer-risk analysis

Before submission, simulate the questions a skeptical reviewer is most likely to ask.

### Risk 1 — "This is only another cross-dataset IDS study."

Response required in the manuscript:

- explicitly distinguish detector performance from reliability-layer transportability;
- show that the detector is held fixed;
- show that reliability scores themselves are the evaluated object;
- emphasize attack-miss triage.

### Risk 2 — "These methods are old; what is new?"

Response:

- no novelty is claimed for the individual methods;
- novelty is in the controlled comparative evaluation if the literature audit supports that distinction;
- cite the closest 2024–2026 work directly.

### Risk 3 — "Why attack-miss AUPRC?"

Response:

- generic model errors include benign false positives;
- a security analyst must prioritize missed attacks;
- the endpoint directly operationalizes the danger being studied.

### Risk 4 — "Why only two datasets?"

Response:

- they form a common NetFlow-v3 representation;
- the experiment is deliberately controlled;
- the paper states that replication across additional datasets is future work.

### Risk 5 — "Why Random Forest?"

Response:

- the paper isolates the reliability layer rather than detector architecture;
- RF is fixed to prevent backbone confounding.

### Risk 6 — "Did the target labels leak into the system?"

Response:

- show the explicit target-label firewall and integrity audit.

### Risk 7 — "Are the family claims valid?"

Response:

- show the locked family crosswalk;
- explicitly omit unsupported mappings.

### Risk 8 — "Do the results prove deployment reliability?"

Response:

- no;
- they establish benchmark-level transfer evidence under a defined source-only protocol.

---

# 19. Venue-selection stage

Venue selection comes **after** the paper has a defensible contribution statement.

Evaluate candidate venues on:

- acceptance of empirical/benchmark studies;
- cybersecurity relevance;
- ML reliability/uncertainty relevance;
- page limits;
- supplementary-material policy;
- reproducibility expectations;
- dataset/code availability expectations;
- publication cost;
- review cycle;
- whether the venue expects a novel algorithm.

The paper should initially be written in a venue-neutral structure.

Only after the target venue is selected should:

- page count be compressed;
- citation style be changed;
- figure dimensions be finalized;
- section headings be adapted;
- supplementary material be split.

Do not force the science into a five-page layout before selecting the venue.

---

# 20. Reproducibility package

The final submission package should contain, where venue policy allows:

- code;
- environment specification;
- dataset acquisition instructions;
- dataset hashes;
- feature registry;
- label/family registry;
- experiment manifests;
- seed definitions;
- analysis scripts;
- generated aggregate tables;
- figure-generation scripts;
- artifact manifest;
- README with reproduction order.

Raw datasets and large ignored arrays need not be redistributed if licensing or repository size prevents it; provide exact acquisition and integrity instructions instead.

---

# 21. Supplementary material

Move detail out of the main paper only after the main story is complete.

Candidate supplementary contents:

- all per-seed results;
- complete paired-comparison matrix;
- additional review-budget points;
- full family-level tables;
- calibration plots;
- score distributions;
- computational profiling;
- implementation pseudocode;
- exact hyperparameter/configuration tables;
- reproducibility instructions.

The supplement should verify the main paper rather than introduce a second story.

---

# 22. Major future-work directions

Future work must contain only directions that arise naturally from the study's limitations and have clear research value.

## 22.1 Multi-dataset replication

Extend the same frozen protocol to additional NetFlow-v3 environments to test whether the direction-dependent ranking observed here persists across more domain pairs.

## 22.2 Natural temporal/streaming shift

Evaluate stale source-derived reliability layers over chronological target streams rather than only static cross-dataset transfer.

This would test how long a reliability signal remains useful as the deployment distribution evolves.

## 22.3 Label-efficient adaptation

Study when a small, explicitly controlled amount of target labeling or recalibration can recover reliability-layer utility without converting the evaluation into unrestricted domain adaptation.

## 22.4 Family-conditional reliability

Investigate whether family-conditional or class-conditional calibration can reduce the failure of marginal reliability signals for rare or previously unsupported attack families.

## 22.5 Composite reliability policies

Study whether confidence, disagreement, distance, and conformal evidence can be combined using source-only training into a more stable triage policy, with strict protection against target-label tuning.

These belong in Future Work, not in the completed experiment.

---

# 23. Final manuscript acceptance gates

The paper is ready for submission only when all of the following are true.

### Scientific gates

- [ ] Research questions are answerable from the completed experiment.
- [ ] Every headline conclusion is directly supported.
- [ ] No universal-winner claim remains.
- [ ] No unsupported unseen-family claim remains.
- [ ] No unsupported deployment-generalization claim remains.
- [ ] No target adaptation or recalibration is implied.
- [ ] All method definitions are exact.

### Statistical gates

- [ ] Primary comparisons are predeclared in the manuscript.
- [ ] Seed pairing is preserved.
- [ ] Confidence intervals are verified.
- [ ] Multiple comparisons are handled consistently.
- [ ] Effect sizes accompany significance statements.

### Reproducibility gates

- [ ] All headline numbers trace to artifacts.
- [ ] Figures regenerate from saved data.
- [ ] Tables regenerate from saved data.
- [ ] Dataset hashes are recorded.
- [ ] Code/environment provenance is recorded.
- [ ] The integrity audit passes.

### Writing gates

- [ ] Introduction matches the actual gap.
- [ ] Related work contains the closest current papers.
- [ ] Methods can reproduce the experiment.
- [ ] Results contain no unsupported interpretation.
- [ ] Limitations are explicit.
- [ ] Abstract matches the final results.
- [ ] Title matches the final scope.

### Publication gates

- [ ] Venue is selected.
- [ ] Author guidelines are current.
- [ ] Page limits are satisfied.
- [ ] Citation style is correct.
- [ ] Supplementary files are correctly separated.
- [ ] Reproducibility statement is included where required.

---

# 24. Execution order

The paper-production sequence is therefore:

**Stage 1**
Scientific/evidence audit

→ **Stage 2**
Statistical audit and primary-comparison lock

→ **Stage 3**
Literature and novelty matrix

→ **Stage 4**
Contribution statement and title boundary

→ **Stage 5**
Tables and figures

→ **Stage 6**
Methods section

→ **Stage 7**
Results section

→ **Stage 8**
Discussion and limitations

→ **Stage 9**
Related work

→ **Stage 10**
Introduction

→ **Stage 11**
Abstract and title

→ **Stage 12**
Internal reviewer-style critique

→ **Stage 13**
Citation/factual/numerical audit

→ **Stage 14**
Venue formatting

→ **Stage 15**
Final reproducibility and submission audit

No later stage is allowed to silently change a scientific decision made at an earlier locked stage. If a later audit reveals a scientific problem, the manuscript returns to the earliest affected stage and the affected evidence is corrected before drafting continues.

---

# 25. Standard for the final paper

The final paper should make one central argument:

> **Lightweight reliability signals should not be assumed to transport with a fixed network intrusion detector merely because they work well in-domain; their security value must be evaluated explicitly against attack false negatives, transfer direction, and analyst review budget under a strict source-only protocol.**

The paper succeeds if it establishes that argument with controlled evidence and clearly bounded claims. It does not require a universal winning method.
