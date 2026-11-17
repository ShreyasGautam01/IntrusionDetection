# Current Literature Positioning Checkpoint

**Evidence cutoff:** 2026-11-18

This memo is a research-positioning control for the manuscript. It is not a claim that the present study has priority over the cited work. Its purpose is to define the contribution boundary that must survive the full literature audit.

## 1. Most important adjacent evidence

### 1.1 Wali Ahmed et al., Frontiers in Artificial Intelligence (2026)

**The Dashboard Says Perfect: A Systematic Audit of Label-Free Model Monitoring and Test-Time Adaptation Under Temporal Distribution Shift in Network Intrusion Detection**

This is directly adjacent. It audits label-free confidence-based accuracy estimation, cross-model agreement, and conformal abstention under temporal distribution shift, with CIC-IDS2017/CSE-CIC-IDS2018 and the two transfer directions. It explicitly keeps target-year labels out of training, adaptation, hyperparameters, and model selection.

**Implication:** The manuscript must not claim that strict source-only transfer of confidence/agreement/conformal reliability in IDS is itself novel.

The defensible distinction must come from the exact endpoint, feature interface, benchmark composition, fixed RF experiment, security-specific false-negative prioritization, and operational analysis—provided the literature audit confirms those combinations are not already covered.

### 1.2 Arepalli et al., 2026

**Conformal prediction for network intrusion triage and analysis of unseen attack families**

This work explicitly combines conformal prediction, novelty signals, triage behavior, temporal evaluation, and unseen attack-family analysis.

**Implication:** The paper must not claim novelty for merely combining conformal uncertainty with unseen-family analysis or analyst triage.

### 1.3 Jin and Lee, Electronics (2026)

**Benchmark-Shift-Aware Intrusion Detection for Evolving Network Traffic: Cross-Dataset Generalization, Calibrated Alerting, and Score-Orientation Diagnostics**

This work explicitly studies cross-dataset generalization, source-fitted calibration, alert budgets, and score-orientation instability.

**Implication:** Score inversion and alert-budget diagnostics cannot be presented as novel concepts by themselves.

### 1.4 Farmani et al., Scientific Reports (2026)

**Toward deployment-oriented benchmarking of intrusion detection systems: integrating threshold dynamics, distribution shift, and interpretability into comparative model evaluation**

This work argues for scenario-aware, distribution-shift-aware, threshold-dependent and deployment-oriented IDS benchmarking.

**Implication:** The manuscript should position itself as a narrowly controlled reliability-layer study rather than as the first deployment-oriented IDS benchmark.

### 1.5 Li and Zhou, Electronics (2026)

**From Risk Scores to Budget-Constrained Alert Streams: Temporal Evaluation of Flow-Level Network Intrusion Detection**

This work evaluates risk scores under budget constraints and explicitly studies threshold transfer, realized false-positive budgets, and attack coverage across CICIDS2017, UNSW-NB15, and NF-ToN-IoT-v3.

**Implication:** A general "alert-budget evaluation" claim is insufficiently distinctive.

### 1.6 Barrett et al., Electronics (2026)

**FADES: Adaptive Drift Estimation via Conformal Signals for Streaming Intrusion Detection**

This work studies conformal drift signals, representation-space drift detection, multiple seeds/runs, and cross-dataset transfer involving UNSW-NB15 and CICIDS2018.

**Implication:** The manuscript should not frame repeated-seed cross-dataset conformal evaluation as novel by itself.

## 2. Provisional defensible niche

The most promising contribution boundary is not:

> "Reliability under distribution shift in IDS has not been studied."

That statement is too broad.

The stronger candidate is:

> **A controlled empirical evaluation of lightweight post-hoc reliability signals as prioritizers of detector false negatives, with attack-miss AUPRC as the primary security endpoint, under a fixed RF backbone and frozen common NetFlow-v3 representation, using bidirectional source-only transfer and an explicit analyst-review budget.**

Even this wording remains provisional until the full search verifies whether the exact combination has already been reported.

## 3. Required comparison matrix

The literature review must compare adjacent studies against this study on:

- source/target datasets;
- representation;
- detector backbone;
- reliability methods;
- target-label usage;
- calibration;
- transfer direction;
- temporal versus cross-domain shift;
- attack-family handling;
- generic-error endpoint;
- attack-miss endpoint;
- AUPRC usage;
- analyst-review budget;
- score orientation;
- seed-level paired inference;
- compute reporting.

## 4. Consequence for manuscript strategy

The paper should emphasize **controlled evidence and a security-specific endpoint**, not broad novelty in uncertainty estimation.

The Results should answer:

1. Does reliability transportability differ by transfer direction?
2. Does generic-error usefulness predict attack-miss usefulness?
3. Which signals are operationally useful at a fixed review budget?
4. Are reliability semantics stable under transfer?
5. What can be concluded without target adaptation?

The Discussion should explicitly distinguish these findings from work that:

- proposes new detectors;
- adapts to target data;
- focuses on temporal drift;
- evaluates conformal coverage rather than post-hoc attack-miss triage;
- focuses on threshold/FPR transfer rather than reliability ranking;
- uses different feature representations or model families.

## 5. Novelty gate

Before submission, the paper must pass this statement:

> No single recent study found in the final search was shown to evaluate the same combination of fixed RF backbone, frozen 46-feature NetFlow-v3 representation, five reliability signals, bidirectional source-only transfer, attack-miss AUPRC as the primary endpoint, and fixed-budget attack-miss capture.

If this statement cannot be supported, the contribution must be narrowed again.

## 6. Future-work implications

The literature also shows several natural directions for future work:

- temporal drift and stale-calibration evaluation;
- target-label-efficient reliability adaptation;
- multi-domain replication;
- family-conditional reliability;
- composite reliability signals;
- streaming and budget-constrained alert evaluation.

These are appropriate future directions because they arise directly from the current study's controlled scope and established literature.
