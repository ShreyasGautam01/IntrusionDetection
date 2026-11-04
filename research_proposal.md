# Finalized Research Proposal

## Title

**Evaluating the Transportability of Lightweight Reliability Signals in Network Intrusion Detection under Compound Distribution Shift**

### More descriptive alternative

**Can IDS Reliability Scores Be Trusted After Deployment Transfer? A Controlled Comparison of Lightweight Post-Hoc Signals under Unseen Attacks**

---

## 1. Executive Summary

Machine-learning intrusion detection systems (IDSs) are often evaluated on held-out data drawn from the same dataset used for training. Such evaluations can establish predictive performance, but they do not establish whether the system knows when its predictions are unreliable after deployment in a different network environment.

Recent literature has already studied many individual aspects of this problem: cross-dataset transfer, temporal drift, uncertainty quantification, calibration, unseen attacks, open-set recognition, conformal prediction, score/threshold inversion, analyst triage, and cost-aware alerting. Therefore, this proposal does **not** claim novelty from any of those topics individually.

The proposed research focuses on a narrower problem:

> **Do lightweight post-hoc reliability scores retain the same relationship with prediction failure when a fixed IDS is transferred from one network environment to another without target-domain adaptation, particularly when the target environment also contains attack families absent from training?**

The central object of study is therefore not the IDS classifier itself and not distribution shift alone. It is the **transportability of the reliability judgment**.

A fixed Random Forest IDS will be paired with several lightweight post-hoc reliability mechanisms derived from the original research project:

- predictive confidence;
- Random Forest ensemble disagreement;
- feature-space distance;
- conformal prediction;
- Isolation Forest.

The same source-trained detector, preprocessing, calibration procedure, reliability mechanisms, and thresholds will be frozen before target-domain evaluation. Target labels will not be used for model construction, calibration, threshold selection, or method selection.

The principal security endpoint will be the ability of each reliability signal to prioritize **dangerous attack false negatives** in the target domain, measured primarily using attack-miss AUPRC and operational attack capture at fixed analyst-review budgets.

The study is intended as a controlled reliability benchmark rather than a new IDS architecture.

---

# 2. Background

Machine-learning methods can detect network intrusions that may be difficult to capture with fixed signatures. However, high test accuracy does not imply that the system can recognize when its own predictions have become unreliable.

This problem becomes more important under deployment transfer.

A network IDS trained on one environment may encounter:

- different benign traffic patterns;
- different attack prevalence;
- different feature distributions;
- different capture conditions;
- new attack families;
- changes in the relationship between features and labels.

A reliability mechanism is intended to provide additional information about whether a prediction should be trusted, reviewed, or rejected.

Examples include:

- the model's predictive confidence;
- disagreement among ensemble members;
- distance from training observations;
- conformal prediction sets;
- generic anomaly scores.

However, reliability is only useful if the meaning of the reliability score survives deployment.

A score that means:

> "This prediction is likely to be wrong"

in the source domain may not necessarily mean the same thing in the target domain.

This gives rise to the central concept of this proposal:

## Reliability-score transportability

A reliability signal is transportable when its relationship with prediction failure remains sufficiently valid after moving the frozen IDS to a different environment.

Formally, let \(R(x)\) denote an unreliability score.

The source domain provides:

\[
P_S(error \mid R=r)
\]

The target domain provides:

\[
P_T(error \mid R=r)
\]

The central question is whether these relationships remain sufficiently consistent after transfer.

For security purposes, a more important quantity is:

\[
P_T(attack\ miss \mid R=r)
\]

because an IDS false negative can be more consequential than an arbitrary classification error.

---

# 3. Research Context and Literature Position

The research is deliberately positioned after the rapidly expanding 2024–2026 literature on trustworthy and deployment-aware IDS evaluation.

Recent work already establishes that:

- cross-dataset transfer can substantially degrade IDS performance;
- source-derived thresholds may fail or invert under transfer;
- calibration can deteriorate under distribution shift;
- confidence can become misleading for unseen attacks;
- uncertainty and novelty behavior can differ by attack family;
- conformal methods can be used for triage and rejection;
- analyst review can be evaluated under bounded budgets;
- adaptation methods can partially recover transfer performance.

Consequently, the proposal makes **no novelty claim** for these individual components.

Instead, the study asks whether the **reliability layer itself** can be isolated experimentally and compared under a common frozen-detector, source-only transfer protocol.

The proposed contribution is therefore methodological and empirical:

> **A controlled, apples-to-apples evaluation of the transportability of existing lightweight post-hoc reliability signals under cross-domain transfer with compound shift and security-focused false-negative endpoints.**

---

# 4. Research Gap

## 4.1 What is already covered

The following areas are established research directions and are not claimed as novel by themselves:

- IDS uncertainty estimation;
- model calibration;
- cross-dataset generalization;
- temporal/concept drift;
- unseen or zero-day attack detection;
- open-set recognition;
- conformal prediction;
- anomaly detection;
- analyst triage;
- review-budget prioritization;
- cost-sensitive alerting;
- threshold transfer;
- score-orientation inversion.

Recent work has demonstrated these phenomena separately and, increasingly, in overlapping combinations.

Therefore, a paper claiming:

> "We are the first to study distribution shift and IDS reliability"

would be indefensible.

Likewise, a paper claiming:

> "We combine cross-dataset evaluation, unseen attacks, conformal prediction, and analyst review"

would no longer constitute a sufficiently strong novelty claim on its own.

---

## 4.2 The remaining candidate gap

The remaining gap is more specific:

> **There is limited controlled evidence on whether lightweight post-hoc reliability signals themselves retain their semantic relationship with prediction failure after strict deployment transfer, when the underlying IDS is frozen, source-derived calibration is frozen, target-domain adaptation is prohibited, and the target domain may contain attack families absent from training.**

The literature increasingly studies:

- whether a detector transfers;
- whether a detector can recognize unknown attacks;
- whether a detector is calibrated;
- whether analysts can prioritize alerts.

The proposed study instead isolates:

> **whether the reliability judgment transfers.**

This distinction matters because an IDS may degrade under transfer while a reliability score remains useful, or it may degrade while the reliability score becomes misleading.

The reliability mechanism therefore represents a separate object of empirical study.

---

## 4.3 Compound-shift aspect

The strongest version of the transfer problem combines two sources of uncertainty:

```text
Source training
       |
       v
   Fixed IDS
       |
       v
Target deployment
       |
       +----------------------+
       |                      |
       v                      v
Different environment   Attack family absent
                           from training
       |                      |
       +-----------+----------+
                   |
                   v
          Compound shift
                   |
                   v
        Reliability judgment
                   |
                   v
      Dangerous false negatives
```

This is different from evaluating:

1. cross-dataset shift alone, or
2. unseen attack families within a single dataset.

The key question is whether a reliability score remains useful when **both environment and attack support can change simultaneously**.

---

# 5. Problem Statement

Network intrusion detection systems are commonly evaluated using predictive metrics measured on held-out data. However, successful in-domain prediction does not establish that a reliability mechanism remains trustworthy when the same detector is deployed in another environment.

Existing literature shows that confidence, calibration, thresholds, novelty scores, conformal predictions, and other monitoring signals can deteriorate or become misleading under distribution shift. It also shows that performance may vary substantially between attack families.

The unresolved methodological problem addressed by this proposal is therefore:

> **How should lightweight post-hoc reliability signals attached to a fixed IDS be evaluated for transportability when the detector is moved to a new network environment without target-domain adaptation, particularly when the target includes attack families absent from training?**

The study operationalizes this problem through:

1. source-only calibration;
2. frozen detector and reliability layer;
3. strict cross-domain transfer;
4. compound-shift evaluation;
5. attack false-negative analysis;
6. attack-family analysis;
7. fixed analyst-review budgets.

---

# 6. Aim

## Primary aim

> **To determine whether lightweight post-hoc reliability signals remain trustworthy and security-useful after strict cross-domain transfer of a fixed network intrusion detector, particularly under compound shift involving previously unseen attack families.**

## Secondary aim

To identify which reliability mechanisms are most stable and operationally useful under this transfer setting without introducing target-domain labels or adaptation.

---

# 7. Research Objectives

## Objective 1 — Measure reliability-score transportability

Determine whether each reliability signal retains its ability to rank prediction failures when the frozen IDS is transferred from a source environment to a target environment.

This includes measuring:

- source error-ranking performance;
- target error-ranking performance;
- degradation in ranking quality;
- score distribution changes;
- orientation/monotonicity changes;
- inversion when present.

Score inversion is not claimed as a new phenomenon. It is treated as one diagnostic of reliability-score instability.

---

## Objective 2 — Evaluate reliability under compound shift

Determine whether reliability signals remain useful when target traffic differs from source traffic and includes attack families not represented in the source training set.

The central security outcome is:

> **Can the reliability signal prioritize target-domain attack false negatives?**

---

## Objective 3 — Quantify family-level reliability behavior

Determine whether reliability transportability is consistent across attack families.

For each sufficiently represented family, evaluate:

- attack recall;
- attack false-negative rate;
- attack-miss AUPRC;
- attack-miss AUROC;
- reliability-score distributions;
- review-budget capture.

The purpose is to identify whether aggregate reliability performance conceals failure for particular attack families.

---

## Objective 4 — Evaluate operational value under bounded review

Determine how many dangerous attack false negatives can be identified when analysts can only review a fixed proportion of observations.

Primary review budgets:

- 1%;
- 5%;
- 10%.

The key operational measure will be:

> **fraction of attack false negatives captured at a fixed review budget.**

Review budgets are not proposed as a novel concept; they are used as the operational test of whether a reliability score provides useful security prioritization.

---

# 8. Research Questions

### RQ1 — Transportability

How does the error-ranking performance of lightweight reliability signals change when a fixed IDS is transferred to a different network environment without target adaptation?

### RQ2 — Semantic stability

Does a reliability score maintain the same relationship with prediction failure after cross-domain transfer?

### RQ3 — Compound shift

How do reliability signals behave when the target environment simultaneously differs from the source and contains attack families absent from source training?

### RQ4 — Security relevance

Which reliability signal most effectively prioritizes target-domain attack false negatives?

### RQ5 — Family dependence

Does reliability-score transportability vary substantially across attack families?

### RQ6 — Operational usefulness

At a fixed analyst-review budget, which reliability signal captures the greatest proportion of dangerous attack misses?

---

# 9. Hypotheses

## H1 — Transfer instability

Reliability signals that perform strongly under in-domain evaluation will experience measurable degradation under strict cross-domain transfer.

This hypothesis is not claimed as novel; it establishes the transfer setting.

## H2 — Signal-dependent transportability

Different reliability mechanisms will exhibit different degrees of transportability under the same transfer conditions.

This is the primary comparative hypothesis.

## H3 — Security-specific behavior

A reliability signal's ability to identify generic prediction errors will not necessarily predict its ability to prioritize dangerous attack false negatives.

## H4 — Family dependence

Reliability-score transportability and attack-miss prioritization will vary across attack families.

## H5 — Operational ranking differences

The ranking of methods by generic error-detection metrics will not necessarily match their ranking by attack capture at a fixed review budget.

---

# 10. Conceptual Framework

The research can be represented as:

```text
                  SOURCE DOMAIN
                       |
                       v
             +-------------------+
             |   Fixed IDS       |
             | Random Forest     |
             +-------------------+
                       |
                       v
              Source calibration
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
 Confidence      Disagreement       Distance
       |               |               |
       +---------------+---------------+
                       |
               +-------+-------+
               |               |
               v               v
         Conformal         Isolation
         prediction         Forest
               |               |
               +-------+-------+
                       |
                       v
              EVERYTHING FROZEN
                       |
                       v
               TARGET DOMAIN
                       |
       +---------------+----------------+
       |                                |
       v                                v
 Different environment          Unseen attack family
       |                                |
       +----------------+---------------+
                        |
                        v
             Compound deployment shift
                        |
                        v
            Reliability-score evaluation
                        |
          +-------------+-------------+
          |                           |
          v                           v
    Generic errors             Attack false negatives
          |                           |
          +-------------+-------------+
                        |
                        v
                Analyst review
                  budget test
```

---

# 11. Research Design

The study is a controlled empirical benchmark.

## Independent variable

Reliability mechanism:

- confidence;
- ensemble disagreement;
- feature-space distance;
- conformal prediction;
- Isolation Forest.

## Controlled variable

Primary predictive architecture:

- fixed Random Forest configuration.

## Primary transfer variable

Source-target dataset/environment pair.

## Additional transfer variable

Presence or absence of attack families in source training.

## Primary outcome

Target-domain attack-miss AUPRC.

## Secondary outcomes

- attack-miss AUROC;
- ordinary error AUPRC/AUROC;
- per-family false-negative rate;
- reliability-score stability;
- score-orientation instability;
- attack capture at fixed review budget;
- computational overhead.

---

# 12. IDS Backbone

The primary backbone will be a fixed Random Forest.

The Random Forest is retained because it is:

- lightweight;
- naturally capable of exposing per-tree vote disagreement;
- compatible with the original benchmark;
- widely used in IDS studies;
- suitable for controlled post-hoc reliability experiments.

The backbone configuration will be frozen before final evaluation.

### Important limitation

The study will not claim that conclusions are universally architecture-independent.

Instead, the contribution is explicitly:

> a controlled reliability-layer comparison for a standardized Random Forest IDS.

### Optional robustness check

If resources permit, one secondary backbone such as XGBoost may be evaluated on a reduced set of transfer experiments.

This is a robustness analysis, not a second research objective.

---

# 13. Reliability Signals

## 13.1 Predictive confidence

For binary prediction:

\[
U_{conf}(x)=1-\max_y p(y|x)
\]

Higher values indicate lower predictive confidence.

This is the simplest baseline.

---

## 13.2 Random Forest ensemble disagreement

Let \(v_y(x)\) be the proportion of trees voting for class \(y\).

Define:

\[
U_{dis}(x)=1-\max_y v_y(x)
\]

This measures disagreement among ensemble members.

---

## 13.3 Feature-space distance

Measure how far a target observation is from a source-domain reference population.

Candidate implementation:

- standardized feature space;
- k-nearest-neighbor distance;
- a small predefined set of \(k\) values;
- source-only reference population.

The final parameterization will be frozen before target evaluation.

---

## 13.4 Conformal prediction

Conformal prediction will be treated as a coverage/abstention mechanism rather than assuming it is simply another anomaly score.

Evaluate:

- empirical coverage;
- class-conditional coverage where feasible;
- prediction-set size;
- abstention rate;
- selective risk.

Its behavior under target shift will be reported empirically rather than treated as guaranteed by the source-domain calibration.

---

## 13.5 Isolation Forest

Isolation Forest will represent a generic anomaly/novelty mechanism.

Its purpose is to determine whether generic anomaly structure remains useful for dangerous failure prioritization after transfer.

---

# 14. Dataset Strategy

The primary candidates are standardized NetFlow-style datasets compatible with common flow representations:

- NF-UNSW-NB15-v3;
- NF-CSE-CIC-IDS2018-v3;
- NF-ToN-IoT-v3.

A fourth dataset may be used only as an external stress test if it can be integrated without compromising methodological control.

## Dataset selection criteria

The final dataset set must provide:

1. sufficiently compatible feature representation;
2. attack-family information;
3. adequate sample counts;
4. sufficient benign traffic;
5. meaningful source-target transfer possibilities;
6. defensible leakage controls;
7. reproducible releases.

Exact dataset statistics will be generated from the exact downloaded releases used in the experiment.

---

# 15. Data Integrity and Leakage Control

Because network IDS datasets can contain duplicated or highly related observations, leakage control is a first-class methodological requirement.

Audit:

- exact duplicates;
- near duplicates where feasible;
- repeated flows;
- capture blocks;
- sessions;
- source/destination groupings where appropriate;
- temporal ordering;
- attack episode structure.

Random row splitting will not be the sole evidence for generalization.

---

# 16. Split Protocol

Every experiment will use three logically separate stages.

```text
SOURCE DATA
    |
    +----------------------+
    |                      |
    v                      v
 TRAIN                 CALIBRATION
    |                      |
    +----------+-----------+
               |
               v
      FROZEN IDS + RELIABILITY
               |
               v
        TARGET TEST DATA
        (labels hidden during
         system construction)
```

## Training split

Used for:

- Random Forest fitting;
- source preprocessing;
- distance reference construction;
- Isolation Forest fitting.

## Calibration split

Used for:

- probability calibration where necessary;
- conformal calibration;
- source reliability thresholds;
- review-budget decision thresholds.

## Target test split

Used only for final evaluation.

Target labels are permitted for reporting final scientific metrics but never for:

- model fitting;
- threshold selection;
- hyperparameter tuning;
- calibration;
- method selection;
- interpretation-driven retuning before the final run.

---

# 17. Experiment 1 — In-Domain Control

This experiment establishes the source-domain baseline.

## Protocol

1. Train the fixed Random Forest.
2. Construct each reliability mechanism using source training/calibration data.
3. Evaluate on held-out source data.
4. Measure error-ranking and calibration behavior.

## Metrics

- error AUROC;
- error AUPRC;
- Brier score;
- calibration error;
- risk-coverage;
- confident error rate.

This is a control experiment, not the main contribution.

---

# 18. Experiment 2 — Standard Cross-Domain Transfer

For each valid source-target direction:

1. train on source;
2. calibrate on source;
3. freeze everything;
4. evaluate on target;
5. calculate post-hoc metrics using target labels only after the system is frozen.

Candidate directions:

- UNSW → CIC;
- UNSW → ToN;
- CIC → UNSW;
- CIC → ToN;
- ToN → UNSW;
- ToN → CIC.

Only directions passing the dataset compatibility and label-mapping audit will be used.

---

# 19. Experiment 3 — Compound Shift

This is the central experiment.

The target domain should differ in both:

1. environment/distribution;
2. attack-family support.

The experimental design will construct source training conditions in which selected attack families are absent, while target evaluation contains those families.

The exact family mapping must be defined before seeing final results.

Families should only be considered "corresponding" across datasets when the semantic mapping is defensible. Otherwise, dataset-local family analyses will be reported separately.

---

# 20. Primary Security Endpoint: Attack-Miss Ranking

The central security event is:

\[
AttackMiss = \{x: y=Attack,\ \hat{y}=Benign\}
\]

The research asks whether high unreliability scores concentrate these events.

## Primary metric

### Attack-miss AUPRC

AUPRC is prioritized because attack misses may be relatively uncommon and because it directly evaluates ranking of the relevant security event.

## Additional metrics

- attack-miss AUROC;
- top-k attack-miss capture;
- attack-miss enrichment among highest-unreliability observations;
- missed attacks per 1,000 reviewed observations.

---

# 21. Reliability-Score Transportability Analysis

For each signal, compare source and target behavior.

Measure:

### A. Ranking quality

- source error AUPRC/AUROC;
- target error AUPRC/AUROC;
- source attack-miss ranking;
- target attack-miss ranking.

### B. Performance degradation

\[
\Delta AUPRC = AUPRC_{source} - AUPRC_{target}
\]

and similarly for AUROC.

### C. Score distribution change

Compare:

- score location;
- spread;
- quantiles;
- overlap between correct and incorrect predictions.

### D. Monotonicity

Check whether increasing unreliability continues to correspond to increasing empirical failure probability.

### E. Orientation/inversion

Detect whether the source relationship reverses in the target.

Orientation instability is a diagnostic, not the claimed novelty.

---

# 22. Attack-Family Analysis

For each sufficiently represented family:

- attack recall;
- false-negative rate;
- attack-miss AUPRC;
- attack-miss AUROC;
- review capture;
- reliability-score distribution.

The analysis will identify:

- consistently robust methods;
- family-specific failures;
- source-target interaction effects;
- whether aggregate metrics conceal catastrophic family-level behavior.

---

# 23. Fixed Review-Budget Analysis

The operational evaluation asks what happens when analyst capacity is limited.

For each method:

1. rank target observations by unreliability;
2. select the top 1%, 5%, and 10%;
3. route them to hypothetical analyst review;
4. leave the remainder automatically accepted;
5. count dangerous attack misses captured and remaining.

## Main operational metric

\[
AttackCapture@B =
\frac{\text{attack misses sent to review}}{\text{all attack misses}}
\]

where \(B\) is the review budget.

Secondary measures:

- benign review load;
- attack misses remaining;
- accepted false-negative rate;
- total samples reviewed;
- attack capture per unit review effort.

---

# 24. Computational Evaluation

Computational cost is a secondary practical dimension.

For every reliability mechanism, measure:

- training overhead;
- calibration time;
- reliability-score computation time;
- inference latency;
- throughput;
- peak RAM;
- model/reference storage;
- preprocessing overhead.

The comparison will distinguish:

- cost already incurred by the IDS;
- incremental reliability-layer cost.

This prevents the term "lightweight" from being an unsupported assumption.

---

# 25. Statistical Design

Because reliability ranking is evaluated on the same observations across methods, comparisons will be paired where possible.

## Repeated runs

Use multiple seeds, preferably at least 10 where computationally practical.

## Confidence intervals

Report:

- mean;
- standard deviation;
- 95% confidence intervals.

## Bootstrap

Where possible, bootstrap meaningful groups:

- attack episodes;
- sessions;
- capture blocks;
- temporal blocks.

Avoid treating every network flow as an independent statistical unit when dependency is evident.

## Primary comparisons

The principal comparisons should be declared before final testing:

1. reliability-signal target attack-miss AUPRC;
2. reliability-signal transport degradation;
3. attack capture at 5% review.

Secondary analyses should be clearly labelled.

---

# 26. Primary and Secondary Endpoints

## Primary endpoint

**Target-domain attack-miss AUPRC under compound shift.**

## Co-primary operational endpoint

**Attack-miss capture at a 5% analyst-review budget.**

## Secondary endpoints

- target error AUPRC/AUROC;
- attack-miss AUROC;
- per-family attack-miss AUPRC;
- score-semantic stability;
- inversion rate;
- selective risk;
- conformal coverage;
- review burden;
- computational overhead.

---

# 27. What Would Count as a Meaningful Result?

The research is not predicated on one reliability method winning.

Three outcomes are scientifically meaningful.

## Result A — A method transfers reliably

One signal may retain strong ranking ability across most transfer directions.

This would support using it as a practical lightweight reliability layer.

## Result B — Different methods fail differently

For example:

- confidence may remain useful in some transfers but become overconfident elsewhere;
- disagreement may track model instability;
- distance may respond strongly to geometric novelty;
- conformal prediction may maintain useful coverage in some conditions but degrade under non-exchangeability;
- Isolation Forest may detect generic novelty without identifying the dangerous errors.

This would demonstrate that reliability mechanisms are not interchangeable.

## Result C — Reliability itself becomes unreliable

If multiple signals fail systematically under compound shift, that would provide evidence that source-derived reliability scores require independent deployment monitoring or recalibration.

This would be an important negative result rather than a failed project.

---

# 28. Expected Scientific Contribution

The proposed contribution should be stated conservatively.

### Contribution 1 — Reliability-layer isolation

A common frozen IDS allows direct comparison of reliability mechanisms without simultaneously changing the predictive architecture.
