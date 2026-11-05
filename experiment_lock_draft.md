# Experiment Lock Draft

**Status:** Draft — do not treat as final lock until dataset audit and pilot are complete.  
**Last updated:** 2026-11-05.

## Purpose

This document converts `methodology_final.md` into an executable protocol. It is intentionally separate from the frozen methodology document.

## 1. Core scientific variable

Primary independent variable:

- reliability signal

Core signals:

1. confidence;
2. Random Forest disagreement;
3. feature-space distance;
4. split conformal prediction;
5. Isolation Forest.

The detector is not varied in the core study.

## 2. Primary detector

Random Forest.

Candidate starting configuration:

- 300 estimators;
- sqrt feature sampling;
- source-selected class weighting if required;
- fixed seed per run.

The exact final hyperparameters must be selected using source-only evidence and then frozen.

## 3. Core data configurations

### Core

- UNSW → UNSW
- CIC2018 → CIC2018
- UNSW → CIC2018
- CIC2018 → UNSW

### Replication

- UNSW → ToN
- ToN → UNSW
- CIC2018 → ToN
- ToN → CIC2018

The replication directions are conditional on the dataset and label audits.

## 4. Conditions

### C0 — In-domain control

Source and target come from the same dataset.

### C1 — Cross-domain supported-family transfer

Target domain changes, but analysis is restricted to observations whose semantic family has a defensible source analogue where such a family analysis is required.

### C2 — Compound shift

Target domain changes and the evaluation contains target attack families that are absent from the source training support.

C2 is the headline difficult condition.

## 5. Freeze boundary

Before target scoring, freeze:

- feature schema;
- feature order;
- feature exclusions;
- preprocessing;
- model hyperparameters;
- trained model;
- probability calibration;
- conformal calibration;
- distance reference set;
- Isolation Forest;
- reliability-score orientation;
- source thresholds;
- seed;
- target sample membership.

No target label may cross this boundary.

## 6. Target-label firewall

The production scoring path must receive:

- target feature matrix only.

The target label file must be accessible only to the evaluation process.

The scorer must output:

- sample identifier;
- predicted class;
- probability;
- each reliability score;
- run metadata.

The evaluator may then join predictions with target labels.

## 7. Primary endpoint

Target attack-miss AUPRC.

Definition:

Attack miss = true attack predicted as benign.

For every target observation:

`attack_miss = (true_label == attack) AND (prediction == benign)`

The reliability score ranks target observations from most unreliable to least unreliable.

AUPRC is calculated using attack misses as the positive event.

## 8. Primary operational endpoint

Attack-miss capture at a 5% review budget.

Secondary:

- 1%;
- 10%.

Random ranking must be shown as a baseline.

Optional oracle ranking may be shown as an upper bound.

## 9. Secondary endpoints

- generic error AUPRC;
- generic error AUROC;
- attack-miss AUROC;
- per-family attack-miss AUPRC;
- capture@1%;
- capture@5%;
- capture@10%;
- score-distribution shift;
- orientation/inversion;
- calibration error;
- conformal coverage;
- selective risk;
- scoring time;
- memory.

## 10. Transportability calculations

For each signal:

`source_error_ap`

`target_error_ap`

`source_attack_miss_ap`

`target_attack_miss_ap`

`transport_drop = source - target`

For attack misses, this is the central transport quantity.

Do not correlate source and target sample ranks directly because the observations are not paired.

Use:

- performance degradation;
- source-defined score bins;
- score-distribution diagnostics;
- orientation analysis;
- source-threshold transfer behavior.

## 11. Source score bins

Where a binned analysis is used:

1. compute bins on source data;
2. freeze bin boundaries;
3. apply exactly those boundaries to target;
4. estimate target empirical error and attack-miss rates within each bin.

Do not construct target quantiles for the headline transportability test.

## 12. Reliability definitions

### Confidence

`U_conf = 1 - max_y p(y|x)`

### RF disagreement

`U_rf = 1 - max_y vote_fraction_y`

### Distance

Primary candidate: kNN distance in source-fitted standardized feature space.

The exact k and reference sample policy must be selected before target evaluation.

### Conformal

Store:

- prediction set;
- set size;
- coverage;
- abstention;
- derived review score.

Do not collapse all conformal outputs into one generic number without reporting the original validity metrics.

### Isolation Forest

Fit only on source data.

Freeze contamination/reference choices from source-only evidence.

## 13. Sampling rules

If a dataset is too large for full processing:

- define the sample rule before looking at method results;
- use a fixed seed;
- store selected row hashes;
- use identical target membership across methods.

Never re-sample to rescue a weak result.

## 14. Seed policy

Initial candidate seeds:

`11, 23, 37, 41, 59, 71, 83, 97, 101, 113`

At least five seeds are required for the core study. Ten are preferred.

The same seeds must be used across methods within a matched experiment.

## 15. Statistical policy

Primary inference targets:

1. target attack-miss AUPRC;
2. attack-miss transport degradation;
3. capture@5%.

Secondary:

- all other diagnostics.

Use:

- paired bootstrap where feasible;
- block-aware bootstrap when observations are dependent;
- paired non-parametric testing for transfer-level method comparisons;
- multiple-comparison correction for families of confirmatory tests.

Effect sizes and confidence intervals are mandatory.

## 16. Sanity controls

Every core transfer must include:

- random reliability ranking;
- score-orientation check;
- prediction-count check;
- no-NaN/Inf check;
- schema check;
- target-label firewall check;
- reproducibility check.

Optional:

- shuffled score negative control;
- shuffled-label sanity test.

## 17. Invalid-run rules

A run is invalid if:

- target labels entered fitting/calibration;
- preprocessing was fitted on target;
- target data changed a hyperparameter;
- target sample membership changed by method;
- score orientation was manually changed after evaluation;
- a source/target overlap is discovered;
- results cannot be regenerated from the run manifest.

Invalid runs are never silently repaired in-place.

## 18. Run manifest

Every run must record:

- run ID;
- source;
- target;
- condition;
- representation;
- seed;
- model hash;
- preprocessing hash;
- split hashes;
- signal configuration hash;
- code commit;
- environment identifier;
- timestamp;
- status.

## 19. Core result tables

### Table A — Primary reliability

- method;
- source attack-miss AP;
- target attack-miss AP;
- transport degradation;
- capture@5%.

### Table B — Family reliability

- family;
- method;
- attack count;
- attack-miss AP;
- capture@5%.

### Table C — Operational

- method;
- capture@1%;
- capture@5%;
- capture@10%;
- reviewed benign count;
- scoring cost.

## 20. Main figures

1. Protocol diagram.
2. Source-vs-target transportability plot.
3. Attack-miss capture vs review budget.
4. Family-level heatmap.
5. Source-defined reliability bins vs target failure rate.
6. Optional runtime plot.

## 21. Pilot gate

Before the core experiment:

1. run one dataset;
2. one source-target direction;
3. one seed;
4. all five signals;
5. verify every metric;
6. verify target-label firewall;
7. verify result reproducibility.

Only after this passes should `experiment_lock.md` replace this draft.

## 22. Scope guardrails

Do not add:

- additional detector architectures;
- new reliability methods;
- additional datasets;
- online adaptation;
- active learning;
- adversarial attack generation

before the core results exist.

## 23. Change policy

This document may evolve during pilot work.

Changes must be recorded in `research_worklog.md`.

The frozen core documents remain unchanged unless a substantive error is found and separately confirmed.
