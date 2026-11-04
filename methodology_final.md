# Final Research Methodology Plan
## Evaluating the Transportability of Lightweight Reliability Signals in Network Intrusion Detection under Compound Distribution Shift

**Status:** Methodology finalization draft  
**Purpose:** Experimental protocol, controls, dataset strategy, analysis plan, safety controls, and presentation plan  
**Date:** 2026-11-05

---

## 0. Executive Decision

This project should be executed as a **controlled reliability-layer benchmark**, not as a broad new IDS-development project.

The core experimental object is:

> **A fixed source-trained intrusion detector plus a frozen source-derived reliability layer.**

The principal question is:

> **After a fixed IDS is transferred to a new network domain without target-domain adaptation or recalibration, which lightweight reliability signals retain their ability to prioritize the detector's dangerous false-negative attacks, particularly when the target also contains attack families absent from source training?**

The methodology must therefore prevent the experiment from quietly becoming a detector-comparison study, a domain-adaptation study, or a new open-set algorithm.

The default final design is:

- **Primary detector:** Random Forest.
- **Primary data:** NF-UNSW-NB15-v3 and NF-CSE-CIC-IDS2018-v3.
- **Replication/stress-test data:** NF-ToN-IoT-v3.
- **Primary representation:** common 53-feature NetFlow-v3 interface.
- **Representation sensitivity control:** compact 8-feature NetFlow interface inspired by TAN-IDS.
- **Reliability signals:** confidence, Random Forest disagreement, feature-space distance, conformal prediction, Isolation Forest.
- **Primary transfer condition:** source-only frozen transfer.
- **Primary difficult condition:** compound shift = cross-domain shift + target attack-family support not represented in source.
- **Primary security endpoint:** target attack-miss AUPRC.
- **Primary operational endpoint:** attack-miss capture at 5% analyst review.
- **Review budgets:** 1%, 5%, 10%.
- **Secondary robustness:** XGBoost only after the Random Forest study is locked and completed.
- **No live attack generation is required or desired.**

The study should be treated as successful even if no reliability signal consistently wins. A pattern of method-specific failure is itself a result.

---

# 1. Methodology Principles

The entire study follows seven principles.

## Principle 1 — Change one thing at a time

The detector must be held constant while reliability signals are compared.

If the reliability score changes, the detector does not.

If the dataset changes, all signals see exactly the same target observations.

If the review budget changes, the ranking does not.

If the backbone robustness check is run, it is a separate predefined experiment.

## Principle 2 — Freeze before target evaluation

No target labels are allowed to influence:

- preprocessing parameters;
- feature selection;
- model hyperparameters;
- probability calibration;
- conformal quantiles;
- distance-reference construction;
- Isolation Forest fitting;
- score orientation;
- thresholds;
- method selection.

Target labels exist only behind an evaluation firewall.

## Principle 3 — Separate scientific controls from headline experiments

Not every experiment is a contribution.

The project has:

1. data-integrity controls;
2. in-domain controls;
3. standard transfer experiments;
4. compound-shift experiments;
5. operational budget experiments;
6. optional robustness experiments.

This prevents the paper from turning into a collection of unrelated tables.

## Principle 4 — Use the target labels only after the system is locked

A target label may be used to calculate:

- attack-miss AUPRC;
- AUROC;
- calibration error;
- attack capture;
- per-family performance;
- confidence intervals.

It may not be used to change the system that generated those measurements.

## Principle 5 — Treat negative results as first-class outcomes

If all reliability signals degrade, report this.

If one signal is good only on one dataset, report this.

If confidence wins in one domain and distance wins in another, report this.

The experiment is not designed to prove that one method is best.

## Principle 6 — Reproduce before extending

Do not add more methods, datasets, or model classes until the core pipeline produces stable, auditable results.

## Principle 7 — Do not claim novelty for components already established in the literature

The novelty claim remains the controlled investigation of **transportability of existing reliability signals under strict source-only transfer**, not the individual signals themselves.

---

# 2. Final Research Questions

### RQ1 — Reliability transportability

How much does each reliability signal's ability to identify prediction failures degrade when a fixed IDS is transferred from a source domain to a different target domain?

### RQ2 — Security relevance

Does a reliability signal that detects ordinary model errors also identify the much more security-relevant subset of attack false negatives?

### RQ3 — Compound shift

Does reliability-score behavior deteriorate further when the target contains attack families that have no corresponding representation in source training?

### RQ4 — Family dependence

Are reliability failures concentrated in particular target attack families?

### RQ5 — Operational utility

At a fixed analyst-review budget, which reliability signal captures the largest fraction of dangerous attack misses?

### RQ6 — Representation sensitivity

How sensitive are reliability conclusions to the choice between a richer standardized NetFlow representation and a compact deployment-oriented representation?

---

# 3. Hypotheses

## H1 — Cross-domain degradation

Reliability signals will perform better in-domain than after source-only cross-domain transfer.

This is a validation hypothesis rather than the central novelty claim.

## H2 — Signal-specific transportability

Different reliability mechanisms will experience materially different amounts of transport degradation.

## H3 — Generic errors versus attack misses

A method's ranking of generic errors will not necessarily match its ranking of attack false negatives.

## H4 — Compound-shift penalty

At least some signals will degrade more strongly under compound shift than under ordinary cross-domain transfer.

## H5 — Family dependence

Reliability-score quality will vary substantially across attack families.

## H6 — Operational ranking can differ

The method that performs best on generic error AUPRC will not necessarily capture the most attack misses at the same review budget.

---

# 4. Dataset Strategy

## 4.1 Primary dataset family

The study should use the **NetFlow-v3 collection** because it provides multiple datasets in a common 53-feature NetFlow representation. The University of Queensland dataset catalogue states that NetFlow-v3 contains four datasets with 53 extended NetFlow features, created by extending the earlier 43-feature representation with 10 temporal features. The available v3 datasets include NF-UNSW-NB15-v3, NF-CSE-CIC-IDS2018-v3, NF-ToN-IoT-v3, and NF-BoT-IoT-v3. [Dataset catalogue](https://staff.itee.uq.edu.au/marius/NIDS_datasets/) and [Luay et al.](https://doi.org/10.1109/ACCESS.2026.3688204)

The exact downloaded file versions must be recorded by:

- URL;
- download date;
- file hash;
- archive hash;
- file size;
- dataset release/version;
- label schema;
- feature schema.

Do not silently substitute a mirror or older release after the experiment begins.

## 4.2 Core source-target pair

The first and most important pair is:

**NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3**

This pair is methodologically attractive because:

- both are NetFlow-v3 datasets;
- the representation is standardized;
- they have substantially different traffic distributions;
- both contain multiple attack categories;
- neither requires adapting the IDS architecture to a completely different feature schema.

The currently published dataset catalogue reports approximately:

- NF-UNSW-NB15-v3: 2,365,424 flows, 127,639 attack and 2,237,731 benign;
- NF-CSE-CIC-IDS2018-v3: 20,115,529 flows, 2,600,903 attack and 17,514,626 benign.

These counts are documentation values; the experiment must report the exact counts of the actual downloaded release after integrity checks and any predeclared cleaning. [Dataset catalogue](https://staff.itee.uq.edu.au/marius/NIDS_datasets/)

## 4.3 Replication/stress-test dataset

NF-ToN-IoT-v3 is the preferred third dataset because it is also part of NetFlow-v3 and is much larger and has a substantially different class mix.

The current catalogue reports 27,520,260 flows, including 10,728,046 attack flows and 16,792,214 benign flows, with attack categories including Backdoor, DoS, DDoS, Injection, MITM, Password, Ransomware, Scanning, and XSS.

Because of its scale, the experiment should not blindly load all data into memory.

Instead, a deterministic, pre-registered sampling/streaming strategy must be defined during the dataset-lock phase.

## 4.4 Optional fourth dataset

NF-BoT-IoT-v3 may be used only as an external stress test if:

- storage permits;
- its extreme class imbalance does not dominate the main analysis;
- the same preprocessing interface works;
- the core study has already completed.

It is not necessary for the main paper.

The project must not add datasets merely to increase the number of tables.

---

# 5. Representation Strategy

There are two valid representation layers.

## 5.1 Primary representation: NetFlow-v3 53 features

Use the standardized NetFlow-v3 representation as the main feature interface.

This has several advantages:

- it is explicitly designed for consistent cross-dataset representation;
- it includes temporal/inter-packet-arrival features;
- it is available for the primary datasets;
- it allows a direct cross-domain experiment without manually reconstructing features from incompatible source schemas.

The v3 dataset work explicitly describes 53 features, formed from the earlier 43-feature set plus temporal features. [Luay et al.](https://doi.org/10.1109/ACCESS.2026.3688204)

## 5.2 Representation control: compact 8-feature interface

TAN-IDS provides an independent compact 8-feature NetFlow interface designed to reduce feature-semantic incompatibility in cross-dataset transfer. It uses a common representation for UNSW-NB15 and NF-CSE-CIC-IDS2018 and explicitly evaluates source-only cross-dataset transfer. [TAN-IDS](https://doi.org/10.1371/journal.pone.0346801)

Use this as a **sensitivity analysis**, not a competing main method.

The question is:

> Does the conclusion about reliability transportability survive when the feature representation is deliberately restricted to a smaller, deployment-oriented common interface?

If yes, the conclusion is stronger.

If no, that is scientifically important because distance-based reliability may depend strongly on feature representation.

---

# 6. Feature Governance

## 6.1 Allowed feature types

The primary feature matrix may include:

- numeric NetFlow features;
- temporal features;
- explicitly documented categorical encodings if present.

## 6.2 Prohibited leakage features

Do not allow:

- target labels;
- attack family names;
- row indexes;
- file names;
- dataset names;
- source/target domain identifiers;
- split identifiers;
- hand-built “attack” metadata;
- future information relative to a flow's timestamp;
- labels encoded indirectly in preprocessing artifacts.

## 6.3 Identifier fields

Fields that identify machines, sessions, or timestamps require special handling.

They may be retained in an **audit metadata layer** to build grouped/chronological splits, but should not automatically be included in the predictive feature vector.

For example:

- IP addresses;
- port pair identifiers;
- timestamps;
- capture IDs;
- file/PCAP provenance.

The decision must be written into a feature registry before model training.

---

# 7. Attack Label Strategy

This is one of the most important controls.

Cross-dataset attack taxonomies do not line up perfectly.

Therefore the main detector task should be:

**binary intrusion detection**

\[
Y \in \{Benign, Attack\}
\]

This avoids pretending that "Fuzzers," "DDoS," "BruteForce," "Exploits," etc. are identical semantic classes across datasets.

Attack family labels remain in the metadata layer.

They are used only for:

- family-level evaluation;
- compound-shift definition;
- descriptive analysis.

This gives the primary detector a stable output space while retaining family-level security analysis.

---

# 8. Canonical Attack-Family Mapping

Before any model is fitted, construct a **locked attack-family ontology**.

Each dataset label must be mapped into one of:

- a documented canonical family;
- `Other/Unmapped`;
- `Benign`.

The mapping must use dataset documentation and published semantics, not test results.

Example canonical categories may include:

- DoS;
- DDoS;
- scanning/reconnaissance;
- brute-force/password attack;
- bot/botnet;
- web/application;
- injection;
- backdoor;
- exploitation;
- infiltration;
- malware/ransomware;
- other.

Do not force a questionable semantic equivalence simply to increase the number of shared families.

Every questionable mapping should be recorded in a `label_mapping.md` artifact with:

- source label;
- target/canonical family;
- decision;
- source documentation;
- rationale;
- confidence;
- alternative interpretation.

---

# 9. Operational Definition of "Unseen Attack Family"

An attack family is considered **target-unseen relative to the source** when:

1. its canonical family is absent from the source training set;
2. the target contains sufficient examples of that family;
3. the family definition was frozen before target evaluation;
4. no target labels were used to choose which families would be called unseen.

This creates a clean rule.

The binary detector does not receive attack-family labels at inference time.

Therefore, "unseen family" means:

> target traffic belongs to a semantically defined family not represented among the source attack families used to train the detector.

This is not a claim that the detector has an explicit unknown class.

---

# 10. Data Audit Phase

Before any modeling, run a data-audit pipeline.

## Audit A — Schema

Check:

- column names;
- datatypes;
- missing values;
- infinities;
- constants;
- duplicate columns;
- unsupported features;
- categorical fields.

## Audit B — Label integrity

Check:

- unique labels;
- label counts;
- unknown labels;
- duplicated labels;
- attack/benign consistency.

## Audit C — Temporal structure

Check:

- timestamp availability;
- time range;
- day/session/capture boundaries;
- attack episodes;
- temporal clustering.

## Audit D — Duplication

Check:

- exact duplicate rows;
- duplicate feature vectors;
- duplicate flow keys;
- near duplicate records where practical.

## Audit E — Domain leakage

Check whether an apparently harmless feature encodes:

- dataset identity;
- capture source;
- timestamp block;
- attack-generation artifact.

The data-audit report must be generated before model fitting.

---

# 11. Split Design

The primary split must not be just a random 70/15/15 split.

The baseline design should use:

- **training**;
- **source calibration**;
- **source validation/test**;
- **target test**.

The exact proportions may be adjusted after dataset audit, but they must be fixed before final experiments.

Recommended starting point:

- 60% source training;
- 20% source calibration;
- 20% source control evaluation.

For computationally large datasets, deterministic sampling may be applied inside each logical partition.

---

# 12. Time-Aware Control

Where timestamps are available, add a secondary temporal control.

For example:

```text
Earlier source period
        |
        v
    training
        |
        v
    calibration
        |
        v
Later source period
        |
        v
   source temporal test
```

This determines whether a signal already fails under milder temporal movement before being tested on full cross-domain transfer.

This is a control, not the headline experiment.

---

# 13. Host/Session Leakage Control

Where identifiers are available, construct a second split that prevents the same host/session grouping from appearing on both sides when practical.

The purpose is to test whether reliability scores depend on memorized flow-level regularities.

If a host-disjoint split is not possible for one dataset, document why.

Do not invent grouping variables.

---

# 14. Primary Detector

Use a fixed Random Forest classifier.

Recommended initial configuration:

- `n_estimators = 200`;
- `min_samples_leaf = 5`;
- fixed random seeds;
- all other parameters explicitly recorded.

The exact configuration must be fixed during the experiment-design stage.

No per-dataset model tuning using target performance is allowed.

A small source-only hyperparameter selection can be permitted only if:

1. the search space is predetermined;
2. selection is based only on source training/validation data;
3. the selected configuration is frozen;
4. the same selection rule is used for every source dataset.

To maximize methodological clarity, the default should be a common fixed configuration.

---

# 15. Probability Calibration

Raw Random Forest probabilities are not automatically treated as calibrated.

Use a source-only calibration stage.

Preferred first implementation:

**Platt/sigmoid calibration** or another explicitly selected calibration procedure.

The calibration transform is fitted only on the source calibration set.

It is then frozen.

No target recalibration occurs in the primary study.

Report:

- raw confidence;
- calibrated confidence;
- source calibration quality;
- target calibration degradation.

This also creates a useful distinction between:

> model uncertainty score

and

> source-calibrated confidence.

---

# 16. Reliability Signal 1 — Confidence

Define:

\[
R_{conf}(x)=1-\max_y \hat p(y|x)
\]

Higher values mean less confidence.

For binary detection this reduces to an equivalent distance from the predicted class probability.

Report:

- source error AUPRC;
- target error AUPRC;
- source attack-miss AUPRC;
- target attack-miss AUPRC;
- score distribution;
- calibration error.

---

# 17. Reliability Signal 2 — Random Forest Disagreement

For each sample, extract each tree's class prediction.

Let:

\[
v_y(x)=\frac{1}{T}\sum_{t=1}^{T}I(f_t(x)=y)
\]

Define:

\[
R_{RF}(x)=1-\max_y v_y(x)
\]

Higher values indicate more ensemble disagreement.

Do not use target labels to choose a different disagreement formulation.

---

# 18. Reliability Signal 3 — Feature-Space Distance

The initial method should be:

**k-nearest-neighbor distance to the source training reference set.**

Reasons:

- interpretable;
- direct;
- closely related to existing novelty-triage literature;
- applicable to both RF and common feature spaces.

Important controls:

- fit scaling only on source training data;
- reference points come only from source training;
- do not add target points to the reference set;
- fix the distance metric;
- fix \(k\) before target evaluation.

A practical starting configuration is \(k=5\).

A source-only sensitivity analysis may compare a small predetermined set such as \(k \in \{1,5,10\}\).

Do not select \(k\) using target labels.

---

# 19. Reliability Signal 4 — Conformal Prediction

Conformal prediction must be implemented explicitly rather than treating "conformal" as a generic score.

Primary construction:

**split conformal classification**

using the source calibration set.

Potential nominal miscoverage levels:

- 5%;
- 10%;
- 20%.

Select the headline level before target testing, for example:

\[
\alpha=0.10
\]

The other levels become sensitivity analyses.

For each target observation record:

- prediction set;
- set size;
- whether the set is singleton;
- conformal nonconformity score;
- coverage event where the true target label is available for evaluation;
- abstention/triage status.

For comparability, create a scalar uncertainty score only through a predetermined mapping, such as:

\[
R_{CP}(x)=\frac{|C(x)|-1}{K-1}
\]

for a \(K\)-class construction, with the exact formulation documented and frozen.

For the binary model, prediction-set size is especially constrained, so the operational metric may need to be defined using conformal nonconformity or abstention status rather than raw set size alone.

The manuscript must make this explicit because conformal prediction is fundamentally a set-valued method, not merely another confidence score.

---

# 20. Reliability Signal 5 — Isolation Forest

Train Isolation Forest only on the source reference data.

Do not use target samples to fit or update it.

Record the raw anomaly score and orient it so:

> higher = more unreliable.

Hyperparameters must be fixed in advance.

The main question is not:

> Does Isolation Forest detect anomalies?

but:

> Do its source-fitted anomaly rankings identify target detector failures, particularly dangerous attack misses?

---

# 21. Common Reliability Interface

Every signal must produce the same logical output schema:

```text
sample_id
prediction
predicted_probability
reliability_score
reliability_rank
method
source_domain
target_domain
seed
```

`reliability_score` must always have:

> **higher = more deserving of review**

This avoids sign confusion.

The original/raw score should also be retained for auditability.

---

# 22. Experiment Matrix

The finalized experiment structure should be:

| ID | Experiment | Purpose | Priority |
|---|---|---|---|
| E0 | Data audit | Integrity and leakage control | Mandatory |
| E1 | In-domain control | Establish baseline reliability | Mandatory |
| E2 | Temporal source control | Test mild deployment movement | Mandatory if timestamps valid |
| E3 | Cross-domain transfer | Measure standard transportability | Mandatory |
| E4 | Compound shift | Main scientific experiment | **Primary** |
| E5 | Review-budget analysis | Operational usefulness | **Primary** |
| E6 | Per-family analysis | Explain failure | Primary supporting |
| E7 | Representation sensitivity | Check feature-space dependence | Strong secondary |
| E8 | XGBoost robustness | Check backbone dependence | Optional secondary |
| E9 | Runtime/memory | Deployment practicality | Secondary |

---

# 23. Experiment E0 — Data Audit

This experiment has no model.

Deliverables:

- dataset inventory;
- feature inventory;
- class distribution;
- temporal distribution;
- duplicate statistics;
- missing/infinite statistics;
- label mapping;
- source-target family matrix;
- potential leakage fields.

Stop condition:

> If the feature/label mapping cannot be justified across datasets, the affected transfer direction is removed before modeling.

---

# 24. Experiment E1 — In-Domain Control

Purpose:

Verify that the reliability signals behave sensibly before transfer.

For each dataset:

1. split source data;
2. train RF;
3. calibrate probabilities;
4. fit reliability layers;
5. evaluate on held-out source test data.

Outputs:

- detector metrics;
- generic error ranking;
- attack-miss ranking;
- calibration;
- score distributions.

Acceptance gate:

> The pipeline must reproduce stable results across seeds before any target-domain analysis is unlocked.

---

# 25. Experiment E2 — Temporal Control

Where temporal data permit:

1. train on earlier source traffic;
2. calibrate using a later source block that remains chronologically prior to test;
3. test on later source traffic;
4. keep all reliability components frozen.

This establishes a progression:

```text
Same distribution
       ↓
Temporal movement
       ↓
Cross-domain movement
       ↓
Cross-domain + unseen families
```

That hierarchy helps the paper explain where reliability begins to break.

---

# 26. Experiment E3 — Standard Cross-Domain Transfer

Primary directions:

- UNSW → CIC;
- CIC → UNSW.

Replication directions using ToN-IoT:

- UNSW → ToN;
- ToN → UNSW;
- CIC → ToN;
- ToN → CIC.

Because the three-dataset matrix creates six directions, the first full run should complete the core two directions before the four replication directions are started.

This provides a natural project-management checkpoint.

---

# 27. Experiment E4 — Compound Shift

For each source-target direction:

1. define canonical attack families;
2. determine which target families are absent from source;
3. freeze the family mapping;
4. evaluate target observations by family.

The primary compound-shift result should compare:

### Known/support-overlap target traffic

Target families represented by a semantically corresponding source family.

versus

### Target-exclusive families

Target families absent from source.

Then compare:

\[
\text{Reliability performance}_{shared}
\]

against

\[
\text{Reliability performance}_{unseen}
\]

This is more interpretable than simply saying "the datasets are different."

---

# 28. Experiment E5 — Review-Budget Simulation

For each method:

1. compute frozen target reliability scores;
2. sort descending;
3. select top 1%, 5%, and 10%;
4. mark those samples as "analyst reviewed";
5. calculate how many attack false negatives are captured.

Important:

The oracle analyst does not repair or retrain the detector.

This is only a prioritization experiment.

The detector remains fixed.

---

# 29. Primary Review-Budget Table

The main paper should include a table like:

| Method | 1% capture | 5% capture | 10% capture | Review precision |
|---|---:|---:|---:|---:|
| Confidence | | | | |
| RF disagreement | | | | |
| Distance | | | | |
| Conformal | | | | |
| Isolation Forest | | | | |

The 5% column should receive the greatest visual emphasis because it is the primary operational endpoint.

The exact budget is not a universal SOC assumption; it is a standardized experimental operating point.

---

# 30. Attack-Miss AUPRC Definition

For every target observation define:

\[
M(x)=
\begin{cases}
1 & \text{if } y=Attack \land \hat y=Benign\\
0 & \text{otherwise}
\end{cases}
\]

The reliability score is evaluated as a ranking signal for \(M(x)\).

This gives:

\[
AUPRC(R, M)
\]

where positive examples are detector attack misses.

This is the core security metric.

Importantly, the metric evaluates:

> **Can the reliability signal tell the analyst which attacks the detector missed?**

not merely:

> Can the reliability signal detect attacks?

---

# 31. Generic Error Analysis

Define:

\[
E(x)=I(y\neq\hat y)
\]

Evaluate reliability against \(E\) separately.

This creates the key comparison:

```text
Generic error ranking