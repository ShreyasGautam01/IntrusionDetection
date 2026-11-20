# Project Report Source

> Generated from the final QA'd Word report. This source is used to reproducibly build the GitHub Word artifact.

FRONT: TRANSPORTABILITY OF POST-HOC RELIABILITY SIGNALS FOR
NETWORK INTRUSION DETECTION UNDER SOURCE-ONLY
CROSS-DOMAIN TRANSFER

FRONT: A PROJECT REPORT

FRONT: Submitted by

FRONT: SHREYAS GAUTAM [23BAI70374]

FRONT: BHAWIKA PANCHAL [23BAI70725]

FRONT: HIMANSHI MITTAL [23BAI70177]

FRONT: ANNA TANEJA [23BAI70399]

FRONT: ADITYA MEHTA [23BAI70509]

FRONT: in partial fulfillment for the award of the degree of

FRONT: BACHELOR OF ENGINEERING

FRONT: IN

FRONT: COMPUTER SCIENCE AND ENGINEERING (AI & ML)

FIGURE_REL: rId10

FRONT: Chandigarh University

FRONT: APEX INSTITUTE OF TECHNOLOGY

FRONT: Chandigarh University, Gharuan, Mohali - 140413, Punjab, India

FRONT: [MONTH YEAR OF SUBMISSION]

FRONT: BONAFIDE CERTIFICATE

Certified that this project report titled “TRANSPORTABILITY OF POST-HOC RELIABILITY SIGNALS FOR NETWORK INTRUSION DETECTION UNDER SOURCE-ONLY CROSS-DOMAIN TRANSFER” is the bona fide work of “SHREYAS GAUTAM [23BAI70374], BHAWIKA PANCHAL [23BAI70725], HIMANSHI MITTAL [23BAI70177], ANNA TANEJA [23BAI70399], and ADITYA MEHTA [23BAI70509]” who carried out the project work under my/our supervision.

TABLE_JSON:
[["SIGNATURE", "SIGNATURE"], ["Dr. Aman Kaushik", "Dr. Bhupaesh Ghai"], ["HEAD OF THE DEPARTMENT", "SUPERVISOR"], ["Department of CSE (AI & ML)", "Professor"], ["Apex Institute of Technology", "Department of CSE (AI & ML)"], ["Chandigarh University, Gharuan, Mohali", "Apex Institute of Technology, Chandigarh University, Gharuan, Mohali - 140413"]]

Submitted for the project viva-voce examination held on 30/10/26.

INTERNAL EXAMINER                                      EXTERNAL EXAMINER

# ACKNOWLEDGEMENT

The successful completion of the project report titled “Transportability of Post-Hoc Reliability Signals for Network Intrusion Detection under Source-Only Cross-Domain Transfer” required sustained technical work, careful experimental control, critical interpretation of negative as well as positive findings, and continued academic supervision. We take this opportunity to express our sincere gratitude to everyone who supported the completion of this work.

We express our sincere gratitude to our project supervisor, Prof. (Dr.) Bhupaesh Ghai, Department of Computer Science and Engineering (AI & ML), Apex Institute of Technology, Chandigarh University. His guidance, critical feedback on the research direction, emphasis on methodological discipline, and support during the refinement of the experimental design helped shape the final study and this report.

We extend our thanks to Dr. Aman Kaushik, Head of the Department of Computer Science and Engineering (AI & ML), Apex Institute of Technology, Chandigarh University, for the academic environment, institutional support, and encouragement provided for undergraduate research.

We acknowledge Chandigarh University, Gharuan, Mohali, for providing an academic environment conducive to research and project work. We are grateful to the authors and maintainers of the public UNSW-NB15 and CSE-CIC-IDS2018 benchmark datasets, to researchers whose work informed the treatment of distribution shift, uncertainty, calibration, conformal prediction, and security-ML evaluation, and to the maintainers of the open-source scientific Python ecosystem used in the implementation.

Finally, we thank our colleagues, acquaintances, friends, and family members for their advice, patience, encouragement, and moral support throughout the project.

Place: Gharuan, Mohali

Date: [DATE OF FINAL REPORT SUBMISSION]

# TABLE OF CONTENTS

TOC: List of Figures vii

TOC: List of Tables viii

TOC: Abstract ix

TOC: Graphical Abstract xi

TOC: Abbreviations xii

TOC: Symbols xiii

TOC: CHAPTER 1: INTRODUCTION 1

TOC: 1.1 Background and Research Context 1

TOC: 1.2 Identification of Need and Stakeholder Context 2

TOC: 1.3 Contemporary Issues 2

TOC: 1.4 Problem Identification 3

TOC: 1.5 Task Identification 4

TOC: 1.6 Project Objectives 4

TOC: 1.7 Project Timeline 5

TOC: 1.8 Organization of the Report 5

TOC: CHAPTER 2: LITERATURE SURVEY 7

TOC: 2.1 Timeline of the Reported Problem 7

TOC: 2.2 Bibliometric and Thematic Analysis 8

TOC: 2.3 Proposed Solutions by Researchers 10

TOC: 2.4 Critical Comparison and Link to the Present Project 10

TOC: 2.5 Research Gap 11

TOC: 2.6 Problem Definition 11

TOC: 2.7 Goals and Objectives 12

TOC: CHAPTER 3: DESIGN FLOW / PROCESS 13

TOC: 3.1 Concept Generation 13

TOC: 3.2 Alternative Design Generation 13

TOC: 3.3 Evaluation and Selection of the Final Design 14

TOC: 3.4 Dataset and Predictive Representation 15

TOC: 3.5 Source Partitioning and Preprocessing 16

TOC: 3.6 Fixed Random Forest Detector 17

TOC: 3.7 Reliability Signal Design 18

TOC: 3.8 Source-Only Evaluation Firewall 19

TOC: 3.9 Security and Operational Endpoints 19

TOC: 3.10 Statistical Design and Repetition 20

TOC: 3.11 Engineering and Ethical Constraints 20

TOC: 3.12 Implementation Flow 21

TOC: 3.13 Reproducibility and Artifact Management 22

TOC: CHAPTER 4: RESULTS ANALYSIS AND VALIDATION 23

TOC: 4.1 Modern Engineering Tools and Environment 23

TOC: 4.2 Dataset and Partition Validation 23

TOC: 4.3 In-Domain Source-Test Baseline 24

TOC: 4.4 Cross-Domain Detector Failure 25

TOC: 4.5 Primary Attack-Miss AUPRC Results 25

TOC: 4.6 Analyst-Review Budget Results 27

TOC: 4.7 Generic Error versus Security-Critical Attack Misses 28

TOC: 4.8 Direction-Normalized Transportability 30

TOC: 4.9 Family-Level Analysis 30

TOC: 4.10 Calibration and Conformal Diagnostics 31

TOC: 4.11 Paired Seed-Level Statistical Analysis 32

TOC: 4.12 Computational Cost 32

TOC: 4.13 Integrated Interpretation of the Results 33

TOC: 4.14 Validation Status and Remaining Pre-Publication Work 34

TOC: CHAPTER 5: CONCLUSION AND FUTURE WORK 35

TOC: 5.1 Conclusion 35

TOC: 5.2 Deviation from Expected Results 36

TOC: 5.3 Limitations and Threats to Validity 37

TOC: 5.4 Future Work 38

TOC: 5.5 Way Ahead 40

TOC: REFERENCES 41

TOC: APPENDIX 1: USER MANUAL 44

TOC: APPENDIX 2: ACHIEVEMENTS 46

# LIST OF FIGURES

TOC: Figure 2.1. Literature timeline: major conceptual steps leading to the present source-only reliability-transportability study. 8

TOC: Figure 3.1. Selected source-only transportability design and evaluation flow. 15

TOC: Figure 4.1. Bidirectional attack-miss AUPRC. Filled and open markers denote the two transfer directions; error bars show seed-level standard deviation. 26

TOC: Figure 4.2. Operational attack-miss capture under 1%, 5%, and 10% analyst-review budgets. The horizontal five-percent reference is the random-review expectation. 27

TOC: Figure 4.3. Generic prediction-error ranking versus security-critical attack-miss ranking. 29

# LIST OF TABLES

TOC: Table 1.1 Project timeline and major milestones 5

TOC: Table 2.1. Thematic literature clusters and their contribution to the present research design. 8

TOC: Table 2.2. Comparative synthesis of existing solution families and the gap addressed by this project. 10

TOC: Table 3.1. Alternative design architectures considered and selection rationale. 14

TOC: Table 3.2. Dataset and source-partition configuration. 15

TOC: Table 3.3. Random Forest scientific configuration. 17

TOC: Table 3.4. Reliability signal configurations and intended interpretation. 18

TOC: Table 3.5. Security and operational evaluation endpoints. 19

TOC: Table 4.1. Software and engineering environment. 23

TOC: Table 4.2. Source-test detector baseline. 24

TOC: Table 4.3. Attack-miss AUPRC under bidirectional source-only transfer. 25

TOC: Table 4.4. Attack-miss capture at fixed review budgets. 27

TOC: Table 4.5. Generic-error and attack-miss behavior. 28

TOC: Table 4.6. Direction-normalized reliability performance. 30

TOC: Table 4.7. Calibration diagnostics. 31

TOC: Table 4.8. Selected paired seed-level effects. 32

TOC: Table 4.9. Runtime equivalence and worker-setting benchmark. 32

# ABSTRACT

Network intrusion detection systems are commonly assessed using held-out data from the same benchmark distribution used for model development, yet deployment places a trained detector in environments whose traffic composition, attack prevalence, services, and feature distributions can differ materially from the source domain. A reliability layer is often proposed as a lightweight way of identifying predictions that should receive additional analyst scrutiny. The critical question is whether such source-derived reliability information remains useful after domain transfer, and whether a signal that performs well for generic classification errors also prioritizes the security-critical attacks that the detector has incorrectly marked as benign.

This project evaluates that question using a fixed binary Random Forest detector and five source-derived post-hoc reliability mechanisms: calibrated predictive confidence, Random Forest tree disagreement, feature-space distance, split conformal prediction set-size scoring, and Isolation Forest. Two audited NetFlow-v3 datasets are used: NF-UNSW-NB15-v3, containing 2,365,424 flows, and NF-CSE-CIC-IDS2018-v3, containing 20,115,529 flows. A common 46-feature predictive representation is frozen across the two datasets. The detector and all source-dependent reliability components are fitted or calibrated using source data only, then frozen before target scoring. The protocol is evaluated bidirectionally - UNSW to CIC and CIC to UNSW - with ten matched detector seeds.

The primary security endpoint is attack-miss AUPRC, where the positive population is defined as attacks incorrectly predicted as benign by the frozen detector. Operational usefulness is measured by attack-miss capture at fixed review budgets of 1%, 5%, and 10% of the entire target population. The results show that the detector itself can fail severely under transfer: attack discrimination in UNSW to CIC is close to chance, while the reverse CIC to UNSW direction misses 127,688 of 127,693 target attacks. Among non-degenerate reliability scores, Random Forest disagreement achieves the highest mean attack-miss AUPRC in UNSW to CIC at 0.238 +/- 0.102, whereas feature-space distance is the strongest non-conformal signal in CIC to UNSW at 0.043 +/- 0.001. At a 5% review budget, Random Forest disagreement captures 12.33% of attack misses in UNSW to CIC, compared with the 5% random-review baseline, while feature-space distance captures 4.34% in CIC to UNSW.

The study further demonstrates that generic-error ranking is not an adequate proxy for security reliability. Feature-space distance and Isolation Forest produce comparatively strong generic-error ranking in UNSW to CIC but much weaker attack-miss ranking. The split-conformal arm exposes a methodological issue rather than a competitive advantage: its binary prediction-set-size scalar collapses to a highly tied -1/0 score, making the archived fixed-budget capture dependent on deterministic tie handling. The overall conclusion is that post-hoc reliability is transportable only in a conditional, failure-mode-specific sense. Reliability validation should therefore include the detector's transfer behavior, the exact security failure being prioritized, direction reversal, score orientation, and the analyst review budget. Before the quantitative comparison is treated as final, the predictor-space source split should be regenerated in a duplicate-safe manner and the conformal score should be replaced by a continuous source-derived scalar.

# GRAPHICAL ABSTRACT

FIGURE_REL: rId11

CAPTION: Graphical Abstract. The study freezes the source-trained detector and source-derived reliability layer before target scoring, evaluates both transfer directions, and judges reliability by security-critical attack-miss ranking and fixed analyst-review budgets.

The graphical abstract is intended to summarize the logic of the project rather than replace the detailed methodology. It shows the two benchmark corpora, the common 46-feature representation, the fixed Random Forest, the five post-hoc signals, the bidirectional source-only transfer protocol, and the two central forms of evaluation. The most important interpretive point is the final one: a reliability score is not treated as an abstract measure of uncertainty. It is judged by whether it can surface dangerous failures of the frozen detector under a constrained review budget.

# ABBREVIATIONS

TABLE_JSON:
[["Abbreviation", "Meaning"], ["NIDS", "Network Intrusion Detection System"], ["IDS", "Intrusion Detection System"], ["RF", "Random Forest"], ["AUPRC", "Area Under the Precision-Recall Curve"], ["AUROC", "Area Under the Receiver Operating Characteristic Curve"], ["ECE", "Expected Calibration Error"], ["Brier score", "Mean squared probabilistic prediction error"], ["CIC", "CSE-CIC-IDS2018"], ["UNSW", "UNSW-NB15"], ["IF", "Isolation Forest"], ["ECE", "Expected Calibration Error"], ["TPR", "True Positive Rate"], ["FNR", "False Negative Rate"], ["SOC", "Security Operations Centre"], ["SHA-256", "Secure Hash Algorithm, 256-bit"], ["CPU", "Central Processing Unit"], ["RAM", "Random Access Memory"], ["ML", "Machine Learning"], ["API", "Application Programming Interface"], ["AUPRC", "Area Under the Precision-Recall Curve"]]

# SYMBOLS

TABLE_JSON:
[["Symbol", "Meaning"], ["x_i", "Predictive feature vector for flow i"], ["y_i", "True binary label; 1 = attack, 0 = benign"], ["\\hat{y}_i", "Detector prediction for flow i"], ["p_i^(c)", "Source-calibrated probability assigned to class c"], ["r_i", "Reliability score used to prioritize analyst review"], ["v_ic", "Number of Random Forest trees voting for class c on flow i"], ["T", "Number of Random Forest trees; here T = 200"], ["z_i", "Standardized feature vector used for distance computation"], ["N_5(i)", "Five nearest source-training reference rows for target row i"], ["d_i", "Mean Euclidean distance from a target row to its five nearest source references"], ["alpha", "Conformal miscoverage level; alpha = 0.10"], ["C(x_i)", "Conformal prediction set for observation i"], ["b", "Analyst-review budget as a fraction of the target population"], ["N", "Number of rows in the target population"], ["S_b", "Set of target rows selected for review at budget b"], ["m_i", "Indicator that an observation is an attack missed by the detector"], ["e_i", "Indicator that the detector prediction is incorrect"]]

# CHAPTER 1

# INTRODUCTION

## 1.1 Background and Research Context

Network intrusion detection is traditionally evaluated as a supervised classification problem: a flow record is mapped to a binary or multiclass label indicating whether the traffic is benign or malicious. That formulation is necessary but incomplete for deployment. A detector that achieves very high accuracy on a held-out split from the same distribution may still behave unpredictably when moved to another network, capture period, or benchmark. The difficulty arises because network traffic is not a stationary visual or tabular object. It is generated by changing hosts, services, applications, protocols, user behaviour, attack campaigns, measurement pipelines, and collection configurations.

The present project is motivated by the practical observation that the most dangerous error is not necessarily the most frequent error. An attack that is predicted as benign can disappear from an alert workflow, whereas a benign flow predicted as attack is at least visible to an analyst. This asymmetry means that a reliability layer should not automatically be validated by asking only whether it ranks generic misclassifications. It should be tested against the particular failure mode that matters to the security workflow.

A post-hoc reliability signal is attractive because it can be added to an existing detector without rebuilding the entire predictive architecture. Predictive confidence can expose uncertain decisions; ensemble disagreement can indicate internal instability; feature-space distance can reveal input atypicality; conformal prediction can provide a set-valued uncertainty construction; and unsupervised anomaly detection can provide an independent novelty signal. These mechanisms are computationally lighter than training a separate large open-set architecture and can therefore be useful as monitoring layers.

However, a reliability signal can fail for exactly the same reason a detector fails: distribution shift can change score distributions, score orientation, calibration, and the relationship between 'unusual' inputs and actual security failures. The question therefore is not simply whether a signal is useful in the source domain. It is whether a source-fitted signal remains useful when the detector is frozen and transferred to a materially different target domain without target adaptation.

The final research direction adopted in this project is therefore deliberately narrower than a generic uncertainty benchmark. It asks whether source-fitted post-hoc reliability signals can prioritize the detector's attack misses under bidirectional cross-domain transfer, and whether their utility remains meaningful when the analyst can review only a fixed fraction of the total traffic.

## 1.2 Identification of Need and Stakeholder Context

The supplied project materials do not identify an external industrial client or commercial sponsor. External client: [NOT SPECIFIED IN THE SUPPLIED MATERIALS]. The project is therefore treated as an academic research and engineering study. Its principal stakeholder needs are methodological: the study should provide a defensible experimental protocol, make leakage and representation choices explicit, quantify the behaviour of reliability mechanisms under transfer, and distinguish useful findings from results that are artifacts of metric choice or implementation.

From a deployment perspective, the underlying stakeholder need can be expressed as a monitoring problem. A network-security operator cannot inspect every flow with equal depth. A reliability layer is valuable only if its ranking is aligned with the security failures that the operator actually needs to recover. Consequently, the project treats analyst review capacity as a first-class experimental variable rather than as an afterthought.

The report therefore addresses two linked needs. The first is scientific: establish a reproducible way to compare reliability mechanisms under a controlled source-only protocol. The second is operational: quantify how many dangerous detector attack misses can be surfaced when review is constrained to 1%, 5%, or 10% of the target traffic.

## 1.3 Contemporary Issues

Several contemporary issues make this problem non-trivial. First, cross-dataset generalization remains weak for many ML-NIDS configurations even when same-dataset results are strong. Second, calibration and confidence may degrade under distribution shift, so numerical probability values cannot automatically be interpreted in the target domain exactly as they were in the source domain. Third, uncertainty methods answer different questions: model uncertainty, input novelty, selective prediction, and open-set recognition are related but not interchangeable. Fourth, operational utility depends on alert or review budgets, meaning that a threshold-free ranking score and a fixed-budget triage score may rank methods differently.

The public benchmark setting also introduces data-quality concerns. Network intrusion datasets can contain artifacts introduced by capture, flow generation, feature extraction, class construction, and labelling. The project therefore treats benchmark results as controlled evidence rather than as direct evidence of deployment safety. This is especially important when the results are near chance or below chance: such values can indicate a real inversion or mismatch, but they do not by themselves prove that a method is universally useless.

A final contemporary issue is the distinction between detecting a model problem and solving the model problem. A reliability signal can indicate that a prediction deserves review without making the underlying detector accurate on the target distribution. The present project intentionally measures the former and does not claim to solve the latter.

## 1.4 Problem Identification

The project problem is defined as follows: given a source-trained binary Random Forest intrusion detector and a set of source-fitted post-hoc reliability mechanisms, determine whether those reliability scores retain meaningful ability to prioritize the detector's security-critical attack misses when the detector is transferred to a different benchmark domain without target-domain adaptation or recalibration.

This problem contains four interlocking sub-problems. The first is transport failure: the detector may itself collapse after transfer. The second is reliability alignment: the score that indicates uncertainty may not be the same score that best ranks attack misses. The third is directional instability: reversing source and target can change the relationship between the score and the security failure. The fourth is operational compression: even a good global ranking may be of little practical value if it does not capture enough dangerous errors within the review budget available to an analyst.

The key design implication is that the project cannot be reduced to a single metric or a single transfer direction. A one-way experiment could make a method appear robust simply because the selected source-target relationship favours it. A generic-error endpoint could make novelty scores look strong even when they miss dangerous attack errors. A metric without a budget constraint could hide the fact that operational usefulness depends on the small top-ranked portion of the traffic.

## 1.5 Task Identification

Define a source-only experimental protocol in which target labels cannot influence preprocessing, model fitting, calibration, score orientation, or ranking.

Freeze a common 46-feature NetFlow-v3 representation across the two audited datasets so that detector architecture and feature-interface changes do not confound the comparison.

Fit the same binary Random Forest scientific configuration for ten matched detector seeds in each transfer direction.

Construct and compare five reliability mechanisms representing different notions of uncertainty or atypicality: calibrated confidence, RF disagreement, feature-space distance, split conformal scoring, and Isolation Forest.

Evaluate the security-specific endpoint of attack-miss AUPRC and the operational endpoint of attack-miss capture at fixed 1%, 5%, and 10% review budgets.

Repeat the experiment in both UNSW to CIC and CIC to UNSW directions to reveal whether rankings survive source-target reversal.

Separate generic prediction-error ranking from attack-miss ranking and treat conformal scalarization, duplicate risk, score orientation, and family semantics as explicit validation questions.

Document the implementation environment, reproducibility artifacts, limitations, and remaining work required before the quantitative comparison should be treated as final.

## 1.6 Project Objectives

To establish a controlled and reproducible source-only cross-domain evaluation protocol for post-hoc NIDS reliability signals.

To determine which reliability signals best prioritize attack misses of a frozen Random Forest after cross-domain transfer.

To evaluate whether reliability rankings remain stable when the transfer direction is reversed.

To quantify the practical value of each score under constrained analyst-review budgets rather than relying only on threshold-free metrics.

To determine whether generic prediction-error ranking is a valid proxy for security-critical attack-miss prioritization.

To identify implementation or scalarization failures that can produce apparently strong but scientifically misleading comparisons.

To provide a defensible engineering report that clearly separates established findings, secondary observations, and analyses that require revalidation.

## 1.7 Project Timeline

The supplied materials do not provide an authoritative dated project log for the revised research version. The phase structure below therefore records the logical sequence of the work while leaving dates that require confirmation as placeholders.

CAPTION: Table 1.1. Logical project phases; exact dates are left open because they are not documented in the supplied materials.

TABLE_JSON:
[["Phase", "Major activities", "Start", "End"], ["Phase 1", "Problem definition, literature review, research-gap refinement", "[Start]", "[End]"], ["Phase 2", "Dataset audit, common-feature interface and source-only split design", "[Start]", "[End]"], ["Phase 3", "Random Forest and reliability-layer implementation; leakage controls", "[Start]", "[End]"], ["Phase 4", "Bidirectional ten-seed transfer runs and primary analysis", "[Start]", "[End]"], ["Phase 5", "Operational budget analysis, diagnostics, interpretation and validation", "[Start]", "[End]"], ["Phase 6", "Manuscript refinement, project report preparation and reproducibility review", "[Start]", "[End]"]]

The phase structure is deliberately ordered so that the research question is fixed before the final results are examined. This matters because several of the present conclusions - especially the conformal scalarization issue and the directional failure pattern - are findings about the experiment itself. They should not be retrofitted into the design only after observing the results.

## 1.8 Organization of the Report

Chapter 1 introduces the research context, need, contemporary issues, problem, tasks, objectives, timeline, and report structure. Chapter 2 reviews the evolution of network intrusion detection, uncertainty and selective prediction, open-set and novelty detection, and cross-domain generalization. It then identifies the gap that motivates the present source-only transportability benchmark.

Chapter 3 translates the research question into an engineering design. It compares alternative architectures, justifies the selected fixed-detector approach, documents the datasets, feature representation, deterministic source partitions, detector, reliability mechanisms, target-evaluation firewall, operational metrics, statistical design, and constraints. Chapter 4 reports the experimental outcomes and interprets them at increasing levels of abstraction, moving from raw results to directional transportability, generic-versus-security reliability, family semantics, calibration, and implementation validation. Chapter 5 consolidates the conclusions, deviations from the expected pattern, limitations, threats to validity, future work, and the conditions required for a defensible final version. The report then provides the references, a user/reproducibility manual, and an achievements appendix.

# CHAPTER 2

# LITERATURE SURVEY

## 2.1 Timeline of the Reported Problem as Investigated Throughout the World

The research problem addressed here sits at the intersection of several lines of work that developed over different periods. The first is selective decision making: Chow's reject-option formulation established that a classifier can trade coverage for lower error by refusing to decide on uncertain cases. This idea predates modern machine learning but directly motivates the modern analyst-review interpretation used in this project.

The second line is ensemble and anomaly-based learning. Random Forests provided an ensemble architecture whose per-tree votes can be inspected rather than treated as an opaque single score. Isolation Forest later introduced efficient unsupervised isolation as an anomaly signal. These approaches created practical ways to estimate uncertainty or atypicality without training a completely separate probabilistic model.

The third line is network intrusion detection itself. Sommer and Paxson's closed-world critique made explicit that network detectors cannot assume that future traffic will be drawn from the same distribution as the training environment. Public corpora such as UNSW-NB15 and CSE-CIC-IDS2018 then became important benchmark resources, but subsequent work also demonstrated that benchmark construction and labelling are not neutral implementation details.

The fourth line is formal uncertainty. Conformal prediction introduced prediction sets with distribution-free marginal coverage under appropriate exchangeability assumptions. Later work studied conformal prediction under covariate shift and therefore made the limitations of blindly transferring guarantees particularly relevant to the present source-only design.

The fifth line is cross-dataset and deployment-oriented evaluation. Recent work has shown that matched train/test performance can hide severe performance degradation after transfer between independent datasets or over time. More recent IDS-specific studies have also begun to examine analyst budgets, label-free monitoring, threshold transfer, and score orientation. The present project emerges from these developments but narrows the question further: instead of asking whether uncertainty is good in general, it asks whether specific source-fitted reliability signals continue to prioritize the detector's attack misses after the detector is moved to another domain.

FIGURE_REL: rId12

CAPTION: Figure 2.1. Literature timeline: major conceptual steps leading to the present source-only reliability-transportability study.

The timeline is intentionally conceptual rather than bibliometric in the statistical sense. It identifies the major methodological transitions that are most relevant to the present project: reject options, ensemble detectors, anomaly detection, closed-world limitations, benchmark datasets, conformal uncertainty, covariate shift, cross-dataset evaluation, and deployment-oriented reliability analysis.

## 2.2 Bibliometric and Thematic Analysis

The report format calls for bibliometric analysis. The supplied research paper contains a curated reference set rather than an exported bibliographic database, citation graph, or formal bibliometric dataset. It would therefore be misleading to present citation counts, co-citation centrality, keyword frequencies, or publication-network statistics as measured facts. Instead, this report presents a thematic bibliometric-style analysis: the reference set is grouped by research role, publication era, and methodological contribution.

CAPTION: Table 2.1. Thematic literature clusters and their contribution to the present research design.

TABLE_JSON:
[["Thematic cluster", "Representative works", "Role in the project"], ["NIDS foundations and evaluation", "Sommer and Paxson; Arp et al.; Viegas et al.", "Establish the closed-world, evaluation-rigor and real-world reliability problem."], ["Benchmark datasets and data quality", "Moustafa and Slay; Sharafaldin et al.; Engelen et al.; Liu et al.", "Provide benchmark corpora and evidence that dataset construction and labels influence conclusions."], ["Ensemble, confidence and calibration", "Breiman; Guo et al.; Platt; Niculescu-Mizil and Caruana; Hendrycks and Gimpel", "Motivate confidence and model-derived reliability signals."], ["Selective prediction and conformal methods", "Chow; Geifman and El-Yaniv; Angelopoulos and Bates; Tibshirani et al.", "Provide reject-option, prediction-set and uncertainty-coverage perspectives."], ["Novelty and anomaly detection", "Liu et al. (Isolation Forest) and related reliability literature", "Provide representation-level and unsupervised atypicality signals."], ["Cross-domain and deployment transport", "Apruzzese et al.; Cantone et al.; recent 2026 cross-domain studies", "Establish that source-to-target degradation and score transfer failures are deployment-relevant."], ["IDS trustworthiness and triage", "Talpini et al.; Arepalli et al.", "Connect uncertainty, conformal triage, and security-specific analyst review."]]

Three patterns emerge from this thematic organization. First, the literature is mature enough that it would be inaccurate to claim that 'uncertainty under intrusion detection' is unexplored. Second, the research questions tend to be specialized: some studies focus on model calibration, some on open-set recognition, some on cross-dataset generalization, and some on analyst triage. Third, the literature contains a methodological gap at the intersection of these concerns: a source-only, bidirectional, security-specific ranking evaluation can reveal whether a reliability mechanism remains aligned with dangerous detector failures rather than merely with generic uncertainty.

This distinction is important for project scope. A broader bibliometric study could quantify the literature itself, but that is not necessary to answer the engineering problem. The chosen thematic analysis is sufficient to demonstrate why the project needs to combine concepts that are often evaluated separately, while still keeping the experimental object controlled.

## 2.3 Proposed Solutions by Different Researchers

Researchers have proposed several broad responses to the reliability and transfer problem. One family improves the base detector itself through model adaptation, transfer learning, or mixed-domain training. This can improve target accuracy, but it uses information that the present source-only protocol intentionally excludes. Such work answers the question 'how can the detector be adapted?' rather than 'how much reliability information survives before adaptation?'.

A second family builds specialized open-set or unknown-class detectors. These approaches model open space, tail behaviour, generative structure, or explicit unknown classes. Their conceptual advantage is that they treat novelty as a first-class modelling objective rather than as a wrapper around an existing classifier. Their cost is additional architecture, training, validation burden, and another set of assumptions. For the present project, adopting one of those models as the main detector would make it harder to isolate the transportability of lightweight post-hoc signals.

A third family uses confidence or calibration. This is attractive because it is cheap and directly connected to the classifier's output. However, confidence is only useful if its ranking remains aligned with the security failure of interest. A classifier can be highly confident and wrong, especially under distribution shift.

A fourth family uses disagreement or ensemble variability. Because the Random Forest already contains multiple trees, disagreement can be measured without adding a new detector. This makes it an especially clean post-hoc signal for the present study: its underlying representation and base classifier remain shared across all comparisons.

A fifth family uses feature-space novelty, for example nearest-neighbour distance or Isolation Forest. These signals can detect traffic that looks unlike the source domain without using the classifier's predicted label. Their central limitation is semantic: atypical does not necessarily mean malicious, and attack traffic can remain geometrically close to benign or known attack traffic in the chosen representation.

A sixth family uses selective prediction and conformal prediction. Their main conceptual contribution is not necessarily a new ranking statistic; rather, they formalize when the system should abstain, how coverage and error trade off, and what assumptions underlie those guarantees. Under shift, those assumptions require particular care. The present project therefore treats conformal scoring as both a candidate reliability mechanism and an implementation audit of how a formally defined uncertainty object is exported into a scalar review ranking.

## 2.4 Critical Comparison and Link to the Present Project

CAPTION: Table 2.2. Comparative synthesis of existing solution families and the gap addressed by this project.

TABLE_JSON:
[["Solution family", "Typical approach", "Why it matters to this project"], ["Source-target adaptation", "Transfer learning / target recalibration", "Can improve target discrimination, but target information changes the question from source-only transportability to adaptation performance."], ["Specialized open-set architecture", "Generative/EVT or explicit unknown-class models", "Scientifically valuable but changes the predictive architecture and adds model-specific complexity."], ["Post-hoc confidence", "Calibrated classifier probability", "Low overhead and directly available, but may lose semantic meaning under shift."], ["RF disagreement", "Tree-vote concentration", "Uses existing ensemble structure and isolates model-internal instability without changing the detector."], ["Feature-space distance", "Distance to source-training reference", "Represents input atypicality; depends strongly on representation and does not equal security risk."], ["Split conformal", "Prediction-set or nonconformity construction", "Provides an uncertainty framework, but scalar ranking and target coverage require explicit validation under shift."], ["Isolation Forest", "Unsupervised novelty score", "Architecture-independent novelty baseline, but atypicality may not correspond to attack misses."], ["Present project", "Frozen RF + five source-only post-hoc signals + bidirectional transfer + attack-miss endpoint", "Integrates the above reliability views under one controlled comparison while keeping the detector and representation fixed."]]

## 2.5 Research Gap

The primary research gap is not the absence of reliability methods; it is the absence of a sufficiently controlled comparison of their transportability for a security-specific failure mode. A signal can rank generic errors without ranking attacks that the detector misses. A one-way cross-domain experiment cannot establish that a ranking survives reversal. A global AUPRC can conceal the operational behaviour at a small analyst review budget. A conformal method can be theoretically sound while an exported scalar is practically degenerate. These observations imply that the gap is methodological and integrative.

The project addresses the gap through five linked controls. First, the predictive architecture is fixed. Second, all source-dependent quantities are frozen before target evaluation. Third, the two transfer directions are run under the same scientific configuration. Fourth, the primary positive event is attack miss rather than generic error. Fifth, the ranking is evaluated both threshold-free and at explicit review budgets. This design makes it possible to distinguish signal quality from detector transfer failure, and global ranking from operational utility.

The project's contribution is consequently an empirical transportability benchmark rather than a new uncertainty algorithm. It does not claim to invent confidence, disagreement, distance, conformal prediction, or Isolation Forest. Its contribution is to show how the interpretation of these existing signals changes when they are placed in a common source-only cross-domain security workflow.

## 2.6 Problem Definition

Given a fixed binary Random Forest intrusion detector trained on a source network-flow domain, and a set of post-hoc reliability signals fitted or calibrated only on that source domain, determine how effectively those signals prioritize target-domain observations that are both attacks and false negatives of the frozen detector. The comparison must be bidirectional, leakage-controlled, and operationally interpretable under fixed review budgets.

Formally, the security event for observation i is defined as m_i = I(y_i = 1 and y-hat_i = 0). For a reliability score r_i, the project measures how well descending r_i ranks the positive m_i population. The primary threshold-free metric is average precision/AUPRC, while the primary operational metric is the fraction of all attack misses captured inside the top five percent of the complete target population. The one percent and ten percent budgets provide sensitivity to review capacity.

## 2.7 Goals and Objectives

To establish a controlled and reproducible source-only cross-domain evaluation protocol for post-hoc NIDS reliability signals.

To determine which reliability signals best prioritize attack misses of a frozen Random Forest after cross-domain transfer.

To evaluate whether reliability rankings remain stable when the transfer direction is reversed.

To quantify the practical value of each score under constrained analyst-review budgets rather than relying only on threshold-free metrics.

To determine whether generic prediction-error ranking is a valid proxy for security-critical attack-miss prioritization.

To identify implementation or scalarization failures that can produce apparently strong but scientifically misleading comparisons.

To provide a defensible engineering report that clearly separates established findings, secondary observations, and analyses that require revalidation.

# CHAPTER 3

# DESIGN FLOW / PROCESS

## 3.1 Concept Generation

The conceptual design begins with a fixed detector rather than with a new classifier. This is a deliberate choice: the research question concerns the reliability layer, so changing the detector during the comparison would introduce a second source of variation and make it impossible to say whether observed changes arise from reliability estimation or from model architecture.

Two audited NetFlow-v3 datasets were selected because they provide an established network-intrusion context and a common 53-feature NetFlow-v3 interface. The predictive matrix uses 46 features after excluding seven identifier or temporal fields. The two corpora differ substantially in size and traffic composition, which makes them useful as a controlled stress test for source-to-target transportability without requiring target-domain training.

The concept then separates the problem into three layers. The first is detection: what does the fixed Random Forest predict? The second is reliability: how uncertain or atypical is that prediction according to each post-hoc mechanism? The third is operations: if the analyst can review only a small part of the traffic, how many dangerous detector failures can be surfaced? The final evaluation is designed so these layers are not conflated.

## 3.2 Alternative Design Generation

CAPTION: Table 3.1. Alternative design architectures considered and selection rationale.

TABLE_JSON:
[["Design", "Mechanism", "Strength", "Selection decision"], ["Alternative A", "Specialized open-set or deep generative model attached to each dataset.", "Would explicitly model unknowns and could be more expressive than lightweight wrappers.", "Not selected for the primary study because it changes the predictive architecture and would confound the transportability comparison."], ["Alternative B", "Source-only one-direction transfer using a fixed RF and post-hoc scores.", "Controls the detector and isolates source-to-target behaviour.", "Not selected as the final design because one transfer direction cannot establish directional transportability."], ["Alternative C", "Target-adaptive detector and reliability layer using target calibration or fine-tuning.", "Potentially improves target performance and practical deployment utility.", "Not selected because target information would answer an adaptation question rather than the source-only transportability question."], ["Alternative D", "Fixed Random Forest + five source-derived post-hoc signals + bidirectional transfer + security-specific attack-miss ranking + budgeted review.", "Keeps the detector and feature representation fixed, compares complementary reliability notions, exposes direction dependence, and connects ranking quality to operational review capacity.", "Selected as the final design."]]

## 3.3 Evaluation and Selection of the Final Design

Alternative D is selected because it best isolates the scientific object of interest while still producing an operational interpretation. Alternative A is richer but risks turning the study into a comparison of different predictive architectures. Alternative B is cleaner than A but leaves the directional question unresolved. Alternative C is operationally attractive but would use target information that the research question explicitly excludes.

The selected design therefore makes an intentional trade-off: it sacrifices the possibility of recovering target accuracy through adaptation in order to obtain a stronger causal-style statement about source-only reliability behaviour. This is not causal inference in the formal sense, but it is an experimental isolation principle: the same detector class, feature interface, source protocol, and source-derived reliability mechanisms are transported into both target domains.

The selected design also permits a second kind of comparison that earlier project versions did not emphasize sufficiently: a reliability signal can be good for generic errors but poor for attack misses. The security-specific endpoint is therefore not an optional visualization; it is part of the design definition.

FIGURE_REL: rId13

CAPTION: Figure 3.1. Selected source-only transportability design and evaluation flow.

## 3.4 Dataset and Predictive Representation

The primary evaluation uses NF-UNSW-NB15-v3 and NF-CSE-CIC-IDS2018-v3. The audited datasets contain 2,365,424 and 20,115,529 flows respectively. The attack prevalence differs substantially: 5.40% in the UNSW corpus and 12.93% in the CIC corpus. This difference is not a nuisance to be normalized away; it materially affects the base rate of attack misses and therefore the interpretation of precision-recall metrics and random-review baselines.

CAPTION: Table 3.2. Dataset and source-partition configuration.

TABLE_JSON:
[["Dataset", "Total flows", "Attack flows", "Train", "Calibration", "Source test", "Predictive features"], ["NF-UNSW-NB15-v3", "2,365,424", "127,693 (5.40%)", "1,418,952", "473,301", "473,171", "46"], ["NF-CSE-CIC-IDS2018-v3", "20,115,529", "2,600,903 (12.93%)", "12,068,590", "4,021,791", "4,025,148", "46"]]

Both corpora are represented through a common 53-field NetFlow-v3 interface, of which 46 fields are used as predictors. The seven excluded fields consist of source and destination IP addresses, source and destination transport ports, DNS query identifiers, and two absolute flow timestamps. They are excluded because they are identifier-like or temporal metadata that can encode collection-specific identity or partition information rather than generalizable traffic behaviour.

The retained predictive interface contains protocol information, packet and byte counts, duration, TCP/ICMP/DNS/FTP indicators, throughput and retransmission statistics, packet-size features, TCP window statistics, and directional inter-arrival-time variables. The feature order is frozen and recorded as a feature-registry artifact, ensuring that transfer direction changes the distribution rather than silently changing the model interface.

The target is binary: attack = 1 and benign = 0. Attack-family labels are retained only for the restricted family analysis and do not enter detector training, reliability fitting, calibration, or score construction.

## 3.5 Source Partitioning and Preprocessing

The source partitions are generated by a deterministic, label-independent hash of the canonical raw 53-feature representation. The first eight bytes of a SHA-256 digest are interpreted as a big-endian integer and reduced modulo 100. Buckets 0-59 form the source-training set, 60-79 form calibration, and 80-99 form the source-test set. This makes the split reproducible and avoids dependence on arbitrary row order.

The design contains a deliberate methodological caveat. The primary split is hashed on all 53 raw fields, whereas only 46 fields enter the predictive matrix. Consequently, two rows that differ only in an excluded IP, port, identifier, or timestamp field can cross the train/calibration/test boundary even when their 46 predictive features are identical. A secondary calibration split groups identical 46-feature float32 vectors, which reduces duplication risk inside calibration, but it does not retroactively make the primary split duplicate-safe. This limitation is therefore explicitly recorded rather than hidden.

Non-finite predictor values are handled through a source-only finite-value policy. Replacement values are estimated using source-training finite medians, with a zero fallback only when no finite source-training value exists. The resulting source-derived replacement values are reused unchanged for source calibration, source test, and target data. No target statistic is estimated.

This preprocessing choice is more conservative than target-specific imputation. It may produce a less convenient representation when target distributions differ strongly, but that is the intended consequence: any target adaptation would weaken the ability to interpret the experiment as source-only transportability.

## 3.6 Fixed Random Forest Detector

The predictive detector is a binary Random Forest implemented with scikit-learn. The scientific configuration is identical across both datasets, both transfer directions, and all ten detector seeds. The model uses 200 trees, Gini impurity, minimum five samples per leaf, unrestricted maximum depth, minimum two samples to split, square-root feature subsampling, bootstrap sampling, no class weighting, no out-of-bag scoring, and no warm start.

CAPTION: Table 3.3. Random Forest scientific configuration.

TABLE_JSON:
[["Parameter", "Setting"], ["Classifier", "RandomForestClassifier"], ["Trees", "200"], ["Criterion", "Gini"], ["Maximum depth", "None (unrestricted)"], ["Minimum samples split", "2"], ["Minimum samples leaf", "5"], ["Maximum features", "sqrt"], ["Bootstrap", "True"], ["Class weight", "None"], ["Maximum samples", "None"], ["Out-of-bag score", "False"], ["Warm start", "False"], ["Detector seeds", "0-9"]]

The detector is intentionally fixed rather than tuned separately for each transfer direction. Hyperparameter tuning on the target domain would introduce target information and change the experimental question. Tuning only on the source would be permissible, but it would introduce another optimization layer into a study whose principal purpose is to compare reliability signals. The chosen configuration therefore serves as a stable scientific backbone rather than as a claim of globally optimal Random Forest performance.

Execution-level parallelism is kept conceptually separate from the scientific model. A worker-equivalence benchmark confirmed preservation of tree structure, class probabilities, and RF disagreement across the validated worker settings. Prediction remained single-worker, and BLAS/OpenMP threading was constrained to one.

## 3.7 Reliability Signal Design

All five reliability mechanisms are converted into a common operational convention: larger score means higher review priority. This normalization is necessary so that the same ranking and budget-selection procedure can be applied without method-specific interpretation changes. It also creates an important audit obligation: the chosen orientation must remain meaningful after transfer.

CAPTION: Table 3.4. Reliability signal configurations and intended interpretation.

TABLE_JSON:
[["Signal", "Operational scalar", "Configuration", "Intended meaning"], ["Calibrated confidence", "1 - max(p_attack, p_benign)", "Source-only sigmoid/Platt calibration", "Lower confidence = higher review priority"], ["RF disagreement", "1 - max(tree-vote fraction)", "200 tree votes", "More internal disagreement = higher review priority"], ["Feature-space distance", "Mean Euclidean distance to 5 nearest source-training rows", "Standardized feature space; k = 5", "Greater distance = higher review priority"], ["Split conformal", "/C(x)/ - 1 (archived scalar)", "alpha = 0.10", "Audit only; scalar is highly tied"], ["Isolation Forest", "Negative of scikit-learn sample score", "100 trees; max_samples = 256", "More anomalous = higher review priority"]]

Calibrated confidence is derived from the maximum class probability after a source-only probability calibrator is fitted. The score increases as the classifier becomes less decisive. RF disagreement measures how concentrated the 200 tree votes are; perfect agreement gives a low score and dispersed voting gives a higher score. Feature-space distance measures input atypicality relative to the source-training reference population and is computed using the mean Euclidean distance to the five nearest source-training rows after source-only standardization.

The split-conformal construction uses the source calibration set to estimate a finite-sample quantile at alpha = 0.10. However, the archived scalar is the prediction-set size minus one. In the binary setting this yields a highly discrete -1/0 score with very little variation. The formal conformal object is validly constructed from source calibration data, but the exported ranking scalar is not a good continuous review score under the present implementation. This distinction is central to the interpretation of the results.

Isolation Forest is fitted only on source-training features. It is intentionally treated as a separate novelty baseline rather than as a replacement for the fixed detector or as an oracle for unknown attacks. Its role is to test whether generic source-domain atypicality can prioritize detector failures after transfer.

## 3.8 Source-Only Evaluation Firewall

The source-only firewall is the most important procedural constraint in the design. Before any target labels are exposed, the experiment fixes the predictive feature order, source preprocessing values, Random Forest parameters and fitted trees, source probability calibrator, conformal quantile, source standardization parameters, feature-space reference data, Isolation Forest model, score orientation, ranking rules, and review-budget tie-breaking.

Target data are transformed only with source-derived quantities. Target labels are read only after all target scores and detector predictions have been generated and stored. This prevents target labels from influencing preprocessing, fitting, calibration, score orientation, threshold selection, or ranking. The completed label-isolation audit passes these four conditions.

The target detector threshold is fixed at an attack probability of at least 0.5. No target-side threshold optimization is permitted. The review benchmark ranks the entire target population instead of only the predicted-benign queue. This is a deliberate abstraction: it allows the ranking quality of the reliability signal to be measured independently of additional alert-filtering logic that a production SOC might use.

## 3.9 Security and Operational Endpoints

The primary security event is an attack miss. For each target observation i, m_i = 1 when the true label is attack and the frozen detector predicts benign; otherwise m_i = 0. A reliability signal is evaluated by how well descending score ranks the m_i = 1 population. Average precision/AUPRC is the primary threshold-free metric.

The primary operational endpoint is attack-miss capture at a 5% review budget. If N is the target population size and b is the review fraction, the top floor(bN) rows by reliability score are reviewed. Capture is the fraction of all attack misses included in that reviewed subset. Random review has an expected capture equal to the review fraction, so the 5% budget supplies a direct and intuitive baseline.

The 1% and 10% budgets are secondary. They demonstrate whether a method's utility is stable across low, moderate, and more generous review capacity. This is important because a ranking that is excellent across the full score distribution can still be poor in the operational top tail, and the reverse can also occur.

CAPTION: Table 3.5. Security and operational evaluation endpoints.

TABLE_JSON:
[["Endpoint class", "Metric", "Purpose"], ["Primary threshold-free", "Attack-miss AUPRC", "Ranks attacks that are false negatives of the frozen detector."], ["Primary operational", "Attack-miss capture @ 5%", "Measures how many dangerous misses are surfaced when only 5% of all target flows are reviewed."], ["Secondary operational", "Capture @ 1% and @ 10%", "Tests sensitivity to stricter and more generous review capacity."], ["Secondary reliability", "Attack-miss AUROC", "Provides a threshold-free ranking metric complementary to AUPRC."], ["Secondary diagnostic", "Generic-error AUPRC/AUROC", "Tests whether generic error detection is a valid proxy for attack-miss detection."], ["Secondary diagnostic", "Calibration, Brier score, ECE", "Characterizes probability quality without redefining the security endpoint."], ["Secondary diagnostic", "Score tie mass and orientation", "Detects scalarization failures and semantic inversion."], ["Secondary diagnostic", "Family analysis", "Used only where the frozen semantic crosswalk supports a defensible comparison."]]

## 3.10 Statistical Design and Repetition

Each transfer direction is repeated for ten matched detector seeds, 0 through 9. The same seed is therefore used for every reliability method in a given direction, enabling paired seed-level comparisons. Feature-space distance is seed independent and is computed once per direction. Results are retained at seed level before aggregation.

Descriptive summaries report mean and standard deviation. Selected paired contrasts are examined using exact sign-flip permutation tests and seed-level bootstrap intervals. The purpose is not to create a large matrix of significance claims; the primary interpretation remains effect magnitude, uncertainty interval, direction consistency, and operational behaviour. With ten seeds, the smallest nonzero two-sided sign-flip p-value is 0.00195, so p-values are used as supporting evidence rather than as a substitute for effect interpretation.

The main comparison family is defined in advance as attack-miss AUPRC and 5% attack-miss capture in each transfer direction. Generic-error metrics, 1% and 10% capture, calibration diagnostics, family analysis, and conformal tie behaviour are secondary or exploratory.

## 3.11 Engineering and Ethical Constraints

TABLE_JSON:
[["Constraint area", "Treatment", "Reasoning"], ["Economic and computational", "Use a CPU-manageable Random Forest and lightweight post-hoc scores; avoid GPU-only dependencies in the scientific design.", "Keeps the benchmark reproducible and proportionate to an undergraduate research project."], ["Privacy and regulatory", "Exclude identifier-like fields; use public benchmark data only; do not claim live-traffic authorization or regulatory certification.", "Reduces direct privacy exposure and prevents deployment claims not supported by the study."], ["Safety and operational responsibility", "Treat rejected or high-review-priority flows as REVIEW/UNKNOWN candidates rather than automatically blocking them.", "Avoids turning uncertainty into an unjustified automatic security action."], ["Professional ethics", "Report negative results, model transfer failures, score inversions, scalarization problems, and remaining methodological risks.", "Prevents selective reporting and overclaiming."], ["Environmental impact", "Use CPU-based processing and record computational choices; energy consumption was not directly measured.", "The project has no physical manufacturing component; its main resource footprint is computation."], ["Health / social / political", "No direct health or political endpoint is evaluated. Operational implications are discussed in terms of analyst workload and the consequences of false positives and false negatives.", "Keeps claims within the evidence provided by the experiment."], ["Manufacturability", "Not applicable to a software-only study; the equivalent engineering concern is reproducible deployment packaging.", "No physical production process is involved."]]

These constraints matter because the project is intended as an engineering research report rather than a model demonstration. A sophisticated metric is not considered successful if it creates an avoidable leakage path, depends on target labels, or encourages unsafe operational interpretation. The project's scientific design therefore treats constraints as part of correctness rather than as peripheral documentation.

## 3.12 Implementation Flow

Validate dataset files, row counts, feature registry and cryptographic integrity records.

Construct deterministic source training, calibration and source-test partitions from the canonical 53-field representation.

Fit source-only preprocessing values and freeze the common 46-feature predictive interface.

Fit the 200-tree Random Forest for detector seeds 0 through 9.

Fit the source probability calibrator, conformal quantile, feature-space reference index, and Isolation Forest from source information only.

Generate target detector predictions and reliability scores without reading target labels.

After target scores are frozen, expose target labels only to offline evaluation code.

Compute attack-miss AUPRC, fixed-budget capture, generic-error diagnostics, directional comparisons, calibration diagnostics, and selected paired effects.

Repeat the entire process in the reverse transfer direction and retain seed-level and artifact-level outputs.

## 3.13 Reproducibility and Artifact Management

The repository is treated as an archival reproducibility location for code, manifests, environment definitions, feature registries, transfer manifests, score artifacts, and analysis outputs. The scientific environment recorded in the manuscript is Python 3.14.7 with NumPy 2.5.2, pandas 3.0.6, scikit-learn 1.9.1, and the corresponding uv lockfile.

Cryptographic hashes are used to make dataset, registry, transfer-manifest, and score-artifact identities explicit. This is more reliable than recording only a file name because benchmark files can be replaced or modified without changing their visible path. The report therefore treats the manifest and hash chain as part of the experimental record.

One reproducibility requirement remains unresolved: the primary source split should be regenerated using a duplicate-safe rule applied to the 46-feature predictor space, not only the 53-feature raw representation. A second requirement is a rerun of the conformal ranking with a continuous source-derived scalar and randomized-tie or expected-tie budget capture. These are not cosmetic improvements; they affect the scientific interpretability of the affected results.

# CHAPTER 4

# RESULTS ANALYSIS AND VALIDATION

## 4.1 Modern Engineering Tools and Environment

CAPTION: Table 4.1. Software and engineering environment.

TABLE_JSON:
[["Tool / component", "Version / status", "Use in the project"], ["Python", "3.14.7", "Primary scientific and orchestration environment."], ["NumPy", "2.5.2", "Numerical operations and array processing."], ["pandas", "3.0.6", "Tabular flow-data processing and validation."], ["scikit-learn", "1.9.1", "Random Forest, calibration, Isolation Forest, metrics and related utilities."], ["uv lockfile", "Repository-pinned", "Dependency resolution and reproducibility."], ["Git/GitHub", "Repository archive", "Version control, code history, manifests and reproducibility artifacts."], ["Matplotlib / plotting stack", "Repository-dependent", "Figure generation and visual diagnostics."], ["Operating system", "[NOT SPECIFIED IN THE LATEST PAPER]", "Insert exact OS/version used for final reproducibility record."]]

The implementation uses modern engineering practice in two ways. First, the scientific configuration is separated from execution-level configuration, preventing worker counts or threading from becoming hidden experimental variables. Second, the project retains machine-readable artifacts rather than relying on manually copied numerical results. These choices matter because the study includes repeated runs, large datasets, and several dependent analysis stages.

The latest paper reports a validated equivalence benchmark for Random Forest fitting across worker settings. This is a useful engineering validation because a faster execution mode is acceptable only if it produces the same scientific object. The benchmark therefore serves as a check against accidentally trading reproducibility for runtime.

## 4.2 Dataset and Partition Validation

The two audited corpora provide substantially different scales and attack prevalences. NF-UNSW-NB15-v3 contains 2.365 million flows with 5.40% attacks, while NF-CSE-CIC-IDS2018-v3 contains 20.116 million flows with 12.93% attacks. The deterministic partitions preserve the source-only design and provide stable training, calibration, and test counts.

The validation result is not merely that the row counts are correct. It is that the same conceptual role exists in both datasets: source training supplies the detector and source-derived reliability components; source calibration supplies the probability and conformal calibration functions; source test provides an in-domain reference; and the entire target corpus remains untouched until scoring is complete.

A more subtle validation result is negative. The current primary split is not fully duplicate-safe in the 46-feature predictor space. This does not invalidate the source-only logic, but it weakens the interpretation of the split as a fully leakage-resistant partition because identical predictor vectors can cross the boundary if their excluded metadata differ. This issue is therefore recorded as a pre-publication correction rather than concealed as an implementation detail.

## 4.3 In-Domain Source-Test Baseline

CAPTION: Table 4.2. Source-test detector baseline.

TABLE_JSON:
[["Source dataset", "Attack AUPRC", "Attack AUROC", "Observed source-test attack misses"], ["NF-UNSW-NB15-v3", "~1.000", "~1.000", "10 attack misses / 25,608 attacks"], ["NF-CSE-CIC-IDS2018-v3", "0.976", "0.990", "~26 attack misses / 520,568 attacks"]]

The source-test results establish that the detector is not intrinsically weak in the in-domain setting. On UNSW, the attack AUPRC and AUROC are both approximately 1.000 and only ten attack flows are missed among 25,608 attacks. On CIC, the attack AUPRC remains very high at 0.976 and attack AUROC is 0.990, with approximately 26 attack misses across 520,568 attacks.

This baseline is essential to interpret the cross-domain results. If the detector had been poor even in-domain, a low target attack-miss ranking could not be attributed specifically to transport. The strong source-test baseline instead establishes a useful contrast: the later target behaviour reflects the fact that a detector that is highly discriminative on its source distribution may become unreliable on a different domain.

The baseline also demonstrates why conventional in-domain performance alone is insufficient for deployment confidence. The same model family can appear close to ideal in its source environment and still become operationally unsafe when the traffic-generating environment changes.

## 4.4 Cross-Domain Detector Failure

The transfer experiment produces the most important structural result before reliability is even considered. In UNSW to CIC, target attack AUROC is approximately 0.51, which is close to chance. The mean attack-miss prevalence is approximately 9.62%. In the reverse CIC to UNSW direction, the detector misses approximately 127,688 of 127,693 attacks. The reverse direction is therefore close to a near-blind attack detector.

This asymmetry is scientifically significant. The two transfer directions use the same detector class, the same feature interface, the same reliability mechanisms, and the same seed protocol. Reversing the source and target nevertheless changes the severity and structure of failure. That means transportability cannot be reduced to a single scalar property of a reliability method. The method interacts with the source domain from which its parameters were learned and with the target distribution into which those parameters are transported.

The near-blind CIC to UNSW detector also changes the meaning of secondary diagnostics. Generic errors and attack misses become almost the same population because nearly all attacks are predicted benign. In such a regime, a generic-error metric can no longer serve as an independent validation of security reliability. The experimental design therefore treats the detector's failure regime as an interpretation layer rather than as a reason to discard the direction.

## 4.5 Primary Attack-Miss AUPRC Results

CAPTION: Table 4.3. Attack-miss AUPRC under bidirectional source-only transfer.

TABLE_JSON:
[["Reliability signal", "UNSW -> CIC", "CIC -> UNSW"], ["Confidence", "0.192 +/- 0.051", "0.033 +/- 0.001"], ["RF disagreement", "0.238 +/- 0.102", "0.035 +/- 0.001"], ["Feature-space distance", "0.109 +/- 0.009", "0.043 +/- 0.001"], ["Split conformal†", "0.096 +/- 0.007", "0.079 +/- 0.025"], ["Isolation Forest", "0.077 +/- 0.008", "0.036 +/- 0.001"]]

FIGURE_REL: rId14

CAPTION: Figure 4.1. Bidirectional attack-miss AUPRC. Filled and open markers denote the two transfer directions; error bars show seed-level standard deviation.

In UNSW to CIC, Random Forest disagreement achieves the highest non-degenerate mean attack-miss AUPRC at 0.238, followed by confidence at 0.192, feature-space distance at 0.109, Isolation Forest at 0.077, and the conformal audit scalar at 0.096. In CIC to UNSW, the ordering changes: feature-space distance becomes the strongest non-conformal signal at 0.043, while confidence and RF disagreement fall to approximately 0.033 and 0.035.

The largest interpretive lesson is not that RF disagreement is 'the best method'. The stronger conclusion is that the preferred non-degenerate signal changes when the source and target domains are reversed. In the first direction, model-internal disagreement is relatively more aligned with attack misses. In the second direction, representation-level distance becomes comparatively stronger. This demonstrates that reliability is relational: the score is evaluated against a detector, a representation, and a source-target pair.

The directional shift is also visible in the spread. RF disagreement has a large standard deviation of 0.102 in UNSW to CIC, indicating greater seed-to-seed variability than the other non-conformal signals. The CIC to UNSW values are much tighter because the detector failure itself is much more extreme. The smaller standard deviations in the reverse direction should not be mistaken for stronger reliability; they partly reflect a nearly deterministic failure regime.

The conformal value of 0.079 in the reverse direction is numerically above the other signals, but it is not interpreted as a competitive win because the exported scalar is dominated by equal-value ties. A method cannot be fairly compared by AUPRC when its score carries almost no meaningful ordering information and deterministic row order resolves much of the apparent ranking.

## 4.6 Analyst-Review Budget Results

CAPTION: Table 4.4. Attack-miss capture at fixed review budgets.

TABLE_JSON:
[["Signal", "UNSW→CIC 1%", "UNSW→CIC 5%", "UNSW→CIC 10%", "CIC→UNSW 1%", "CIC→UNSW 5%", "CIC→UNSW 10%"], ["Confidence", "0.90%", "8.19%", "19.60%", "0.03%", "0.77%", "1.40%"], ["RF disagreement", "2.46%", "12.33%", "24.68%", "0.03%", "0.88%", "1.46%"], ["Feature-space distance", "0.07%", "0.58%", "0.64%", "0.56%", "4.34%", "5.09%"], ["Split conformal†", "0.0001%", "17.37%", "20.40%", "4.91%", "14.73%", "22.53%"], ["Isolation Forest", "0.14%", "0.75%", "1.76%", "0.05%", "0.45%", "0.82%"]]

FIGURE_REL: rId15

CAPTION: Figure 4.2. Operational attack-miss capture under 1%, 5%, and 10% analyst-review budgets. The horizontal five-percent reference is the random-review expectation.

At the primary 5% budget, random review captures an expected 5% of attack misses. In UNSW to CIC, RF disagreement captures 12.33%, which is approximately 2.47 times the random baseline. Confidence captures 8.19%, also above random, while feature distance and Isolation Forest remain close to or below random. In CIC to UNSW, feature-space distance is the strongest non-conformal signal at 4.34%, still slightly below the random 5% expectation.

The budget curves reveal a second pattern that the AUPRC table alone cannot show. Operational ranking changes with review capacity. For example, feature-space distance is relatively weak in UNSW to CIC but becomes the strongest non-conformal signal in the reverse direction. The conformal curve shows very high capture at some budgets, but this is precisely the behaviour that must not be interpreted as a method win because the score is dominated by ties. Deterministic row-offset tie handling can produce apparently strong capture simply by selecting particular rows among a large tied population.

The operational result therefore changes the way a research user should read a reliability benchmark. AUPRC describes ranking quality across the entire score distribution. Budgeted capture describes the fraction of dangerous failures an analyst can actually see under a limited review capacity. The two are related but not interchangeable. A deployment study that reports only AUPRC can miss this distinction.

The benchmark ranks the full target population rather than only flows already predicted benign. This makes the result a controlled ranking experiment, not a complete SOC simulation. In a production workflow, the review pool may be smaller and structurally different because already-detected attacks are handled through a separate alert pipeline. The whole-target design is retained because it cleanly measures the incremental ability of the reliability layer to surface failures of the detector itself.

## 4.7 Generic Error versus Security-Critical Attack Misses

CAPTION: Table 4.5. Generic-error and attack-miss behavior.

TABLE_JSON:
[["Signal", "UNSW→CIC generic-error AUPRC", "UNSW→CIC attack-miss AUPRC", "UNSW→CIC attack-miss AUROC", "CIC→UNSW generic-error AUPRC", "CIC→UNSW attack-miss AUPRC", "CIC→UNSW attack-miss AUROC"], ["Confidence", "0.738", "0.192", "0.701", "0.033", "0.033", "0.228"], ["RF disagreement", "0.736", "0.238", "0.712", "0.035", "0.035", "0.248"], ["Feature-space distance", "0.859", "0.109", "0.575", "0.043", "0.043", "0.345"], ["Split conformal†", "0.518", "0.096", "0.500", "0.079", "0.079", "0.545"], ["Isolation Forest", "0.847", "0.077", "0.379", "0.036", "0.036", "0.284"]]

FIGURE_REL: rId16

CAPTION: Figure 4.3. Generic prediction-error ranking versus security-critical attack-miss ranking.

The UNSW to CIC direction provides the clearest evidence that generic error detection and security reliability are different objectives. Feature-space distance achieves generic-error AUPRC 0.859 and Isolation Forest 0.847, both stronger than RF disagreement's generic-error AUPRC of 0.736. Yet their attack-miss AUPRC values are only 0.109 and 0.077, whereas RF disagreement reaches 0.238.

The implication is direct: a score can be very good at identifying observations on which the classifier is generally likely to be wrong while still being poor at identifying attacks that the classifier has mistaken for benign. This happens because 'incorrect prediction' is a mixed population. It includes false positives and false negatives, and not all incorrect predictions have equal security consequences.

The reverse CIC to UNSW direction behaves differently. The detector is so heavily biased toward missing attacks that generic errors and attack misses nearly coincide. For the non-conformal signals, generic-error and attack-miss AUPRC values are identical to three decimals in the reported summary. This convergence does not validate the generic metric; it shows that the generic metric has lost independence from the security event because the detector has entered a near-blind regime.

The broad pattern is therefore stronger than either direction alone. Generic reliability is not a sufficient proxy for security reliability, and the degree of divergence depends on the detector's transfer regime. This validates the decision to make attack-miss AUPRC the primary endpoint.

## 4.8 Direction-Normalized Transportability

CAPTION: Table 4.6. Direction-normalized reliability performance.

TABLE_JSON:
[["Signal", "AUPRC lift (UNSW/CIC)", "5% capture lift (UNSW/CIC)"], ["Confidence", "2.00 / 0.61", "1.64 / 0.15"], ["RF disagreement", "2.47 / 0.64", "2.47 / 0.18"], ["Feature-space distance", "1.13 / 0.80", "0.12 / 0.87"], ["Split conformal†", "1.00 / 1.47", "3.47 / 2.95"], ["Isolation Forest", "0.80 / 0.66", "0.15 / 0.09"]]

Raw cross-direction values can be misleading because attack-miss prevalence changes between targets. Direction-normalized metrics therefore compare each method against the baseline available in that direction. For AUPRC, the baseline is the attack-miss prevalence. For 5% capture, the baseline is the five-percent random-review expectation.

RF disagreement retains the strongest normalized AUPRC lift in UNSW to CIC at 2.47 times the attack-miss prevalence, and it also achieves the strongest non-conformal 5% capture lift in that direction at 2.47 times the random baseline. In CIC to UNSW, feature-space distance becomes comparatively stronger on the 5% capture endpoint, with a lift of 0.87 rather than a raw capture above the 5% random baseline. This is a useful reminder that normalized performance can reveal stability or weakness that absolute values obscure.

The normalized table also reinforces why no universal winner is justified. RF disagreement has strong first-direction performance but collapses in absolute terms in the reverse direction. Distance is more stable in relative terms but still modest in absolute security value. Isolation Forest remains low utility in both directions. Conformal values are not interpreted competitively.

## 4.9 Family-Level Analysis

Family-level interpretation is intentionally restricted to the locked semantic crosswalk. Only the documented shared DoS category is treated as a defensible cross-domain family correspondence; labels that look similar across datasets are not assumed to mean the same operational phenomenon.

The family evidence is insufficient to support a broad unseen-family conclusion. In UNSW to CIC, the shared DoS mapping contains no target rows. In CIC to UNSW, all 5,980 mapped DoS target rows are recorded as attack misses, producing an attack-miss AUPRC of 1.0 for every reliability signal. Because every mapped row is already in the positive attack-miss population, this is tautological rather than evidence of method superiority.

This result illustrates a broader methodological principle: semantic validity and statistical variation are both necessary for a family-level benchmark. A cross-domain label mapping is not useful if the mapped category is empty in one direction or if every row in the category shares the same detector outcome in the other. The correct engineering response is to narrow the claim rather than manufacture family-level evidence.

Accordingly, the project does not claim comprehensive unseen-family generalization. The primary contribution remains aggregate source-only transportability of reliability signals against the detector's attack misses.

## 4.10 Calibration and Conformal Diagnostics

CAPTION: Table 4.7. Calibration diagnostics.

TABLE_JSON:
[["Direction", "Mean target Brier score", "Mean 15-bin ECE"], ["UNSW→CIC", "0.245", "0.317"], ["CIC→UNSW", "0.075", "0.153"]]

The calibration diagnostics show that the source-calibrated probabilities do not retain the same interpretation across directions. The mean target Brier score is 0.245 and ECE is 0.317 in UNSW to CIC, compared with 0.075 and 0.153 in CIC to UNSW. These values are descriptive secondary diagnostics, not replacements for the attack-miss endpoint.

The important interpretation is that confidence should not be read as an absolute probability guarantee after transfer. The score remains useful only as a ranking mechanism if its ordering is still aligned with the security failure being targeted. The AUPRC results show that this alignment can weaken substantially.

The conformal diagnostic requires an even stronger caution. The archived prediction-set-size scalar is highly discrete, with values effectively collapsing to -1 or 0. Because a large proportion of the target population can share the same score, the five-percent budget can be determined largely by input-row order rather than by meaningful uncertainty differences. The correct conclusion is therefore not that conformal prediction is weak, but that this particular scalarization is insufficient for a fair comparative ranking study.

A publication-quality conformal comparison should use a continuous source-derived conformal p-value or nonconformity score and should evaluate fixed-budget capture using randomized ties or expected tie handling. Until that rerun occurs, the conformal results are treated as an implementation audit.

## 4.11 Paired Seed-Level Statistical Analysis

CAPTION: Table 4.8. Selected paired seed-level effects.

TABLE_JSON:
[["Direction", "Comparison", "Metric", "Mean difference", "Bootstrap interval", "Exact p"], ["UNSW→CIC", "RF disagreement - split conformal", "Attack-miss AUPRC", "+0.142", "[0.082, 0.206]", "0.00195"], ["UNSW→CIC", "RF disagreement - split conformal", "5% capture", "-0.050", "[-0.110, 0.016]", "0.168"], ["CIC→UNSW", "RF disagreement - split conformal", "Attack-miss AUPRC", "-0.045", "[-0.061, -0.031]", "0.00195"], ["CIC→UNSW", "Feature distance - split conformal", "Attack-miss AUPRC", "-0.036", "[-0.052, -0.023]", "0.00195"], ["CIC→UNSW", "RF disagreement - split conformal", "5% capture", "-0.139", "[-0.169, -0.111]", "0.00195"], ["UNSW→CIC", "RF disagreement - confidence", "Attack-miss AUPRC", "+0.046", "[0.014, 0.088]", "0.00781"]]

The matched-seed design permits paired comparisons because every method is evaluated on the same target rows under the same detector seed. In UNSW to CIC, RF disagreement exceeds confidence by 0.046 AUPRC on average, with a bootstrap interval excluding zero and an exact sign-flip p-value of 0.00781. This supports a direction-specific contrast, not a universal superiority claim.

The RF-versus-conformal AUPRC contrast in the same direction is larger, but the conformal score's degeneracy makes that contrast methodologically less informative. In the reverse direction, the paired contrasts show that conformal's larger raw AUPRC is not supported as a validated method advantage when the continuous ordering is absent.

The broader lesson is that inferential statistics can only validate a comparison whose underlying score is meaningful. Statistical significance cannot rescue an invalid scalarization. The report therefore interprets paired tests as supporting evidence within the controlled design and not as a substitute for methodological validity.

## 4.12 Computational Cost

CAPTION: Table 4.9. Runtime equivalence and worker-setting benchmark.

TABLE_JSON:
[["Worker setting", "RF fitting time", "Interpretation"], ["10 workers", "17.64 s", "Reference for bounded CIC RF fit benchmark"], ["16 workers", "16.50 s", "Near-maximum tested parallelism; substantial CPU saturation"], ["Production choice", "10 workers", "Selected because it retained most of the speedup without the highest CPU saturation"]]

The runtime benchmark separates computational convenience from scientific configuration. Moving from ten to sixteen workers reduces fitting time only modestly, while increasing CPU saturation substantially. The production setting therefore used ten workers. Because the worker-equivalence check verified tree structure, class probabilities, and RF disagreement, the choice changes runtime but not the scientific object.

This result is modest but useful. In a research project with large network-flow corpora, execution decisions can become hidden variables if they affect numerical behaviour or reproducibility. The explicit equivalence test makes the runtime optimization auditable.

## 4.13 Integrated Interpretation of the Results

The evidence can be organized into four layers. Layer 1 is detector transport: the source-trained Random Forest can be near-perfect on source test and close to chance or nearly blind after transfer. Layer 2 is reliability alignment: the signal that best tracks attack misses changes with direction. Layer 3 is operational compression: the best threshold-free score is not necessarily the best score under a fixed review budget. Layer 4 is methodological validity: scalarization, duplicate handling, semantic mapping, and score orientation must themselves be audited.

These layers produce a broader pattern. Reliability is not a property that can be separated from the detector and distribution. A score is useful only relative to a failure definition, and a failure definition is useful only when the operational workflow is made explicit. This is why the project rejects the idea of a universal post-hoc uncertainty winner. The evidence instead supports a conditional statement: different reliability mechanisms reveal different aspects of detector weakness, and those aspects are not equally transportable.

The contrast between RF disagreement and feature-space distance is particularly informative. RF disagreement is produced from the detector's own ensemble structure and therefore captures model-internal instability. Distance is representation-dependent and measures how far a flow lies from source references. The directional reversal shows that neither notion dominates universally. A target flow can be geometrically unusual without causing the detector to be uncertain, or the detector can be uncertain on a flow that is not particularly distant in feature space.

The contrast between generic error and attack miss is equally important. Generic-error ranking is tempting because it is easy to define, but it blends false positives and false negatives. Security prioritization is inherently asymmetric. A reliability layer should therefore be validated against the failure that the analyst workflow intends to recover. This is arguably the most important methodological lesson of the project.

Finally, the conformal issue shows why implementation details can become scientific conclusions. The formal method may be well motivated, but the scalar used for ranking can destroy the intended information. A research report that only lists the resulting AUPRC would risk presenting a tie artifact as a substantive comparison. The present report explicitly separates the formal concept from the archived scalarization.

## 4.14 Validation Status and Remaining Pre-Publication Work

Target-label isolation audit: PASS. Target labels are not used for fitting, tuning, recalibration, score orientation, or ranking.

Scientific configuration consistency: PASS. The same detector and reliability configurations are used across both directions and ten seeds.

Source-test baseline validation: PASS at the descriptive level; source performance is strong and provides a meaningful contrast for transfer failure.

Worker-equivalence validation: PASS for the tested Random Forest execution settings.

Family semantic validity: CONSERVATIVE by design; the available shared DoS relation is insufficient for a broad family-generalization claim.

Primary source split duplicate safety: [PENDING]. The 46-feature predictor-space split should be regenerated so identical predictors cannot cross source boundaries.

Conformal ranking scalarization: [PENDING]. A continuous conformal p-value or nonconformity ranking should replace the archived binary set-size scalar.

Randomized-tie / expected-tie budget analysis: [PENDING]. This is required before conformal budget-capture values can be interpreted competitively.

Final publication status of the revised project report: [PENDING USER / INSTITUTIONAL CONFIRMATION].

# CHAPTER 5

# CONCLUSION AND FUTURE WORK

## 5.1 Conclusion

This project set out to determine whether lightweight post-hoc reliability signals remain useful when a fixed network intrusion detector is transferred to a different benchmark domain without target-domain adaptation or recalibration. The experiment used two audited NetFlow-v3 datasets, a common 46-feature predictive interface, a fixed 200-tree Random Forest, five source-derived reliability mechanisms, and ten matched detector seeds in both transfer directions.

The first conclusion is that detector transport failure is severe and directional. The in-domain detector is near-perfect on UNSW source test and highly strong on CIC source test, yet attack discrimination falls to approximately chance in UNSW to CIC and the reverse CIC to UNSW detector misses 127,688 of 127,693 attacks. The reliability question therefore arises in a genuinely difficult regime: the score is asked to help an analyst identify failures of a model that may itself be substantially misaligned with the target domain.

The second conclusion is that no single non-degenerate reliability signal remains strongest across both directions. RF disagreement has the highest attack-miss AUPRC in UNSW to CIC at 0.238 +/- 0.102, while feature-space distance is strongest among the non-conformal signals in CIC to UNSW at 0.043 +/- 0.001. The change in ranking under source-target reversal is direct evidence against treating reliability as a direction-independent property.

The third conclusion is operational. At five percent review, RF disagreement captures 12.33% of attack misses in UNSW to CIC compared with the five percent random baseline. In CIC to UNSW, feature-space distance captures 4.34%, which is slightly below random. The method that ranks best overall is therefore not necessarily the method that produces a strong operational gain in every deployment direction.

The fourth conclusion is methodological. Generic prediction-error ranking cannot be assumed to represent security reliability. In UNSW to CIC, feature distance and Isolation Forest are relatively strong generic-error rankers but relatively weak attack-miss rankers. The most relevant positive population is therefore the security failure the workflow actually intends to recover.

The fifth conclusion concerns conformal prediction. The method's source-only construction is conceptually appropriate, but the archived prediction-set-size scalar becomes highly tied in the binary setting. The resulting budget capture is strongly affected by deterministic tie handling. This is an implementation audit finding, not evidence that conformal prediction as a framework is intrinsically ineffective.

Taken together, the results support a deliberately narrow conclusion: source-derived reliability is transportable only conditionally, and it must be validated jointly with detector transfer behaviour, direction, failure mode, score orientation, and analyst review capacity. The study does not establish a universal reliability winner, universal open-set robustness, or target-domain accuracy recovery.

## 5.2 Deviation from Expected Results

The supplied project history does not contain a formal preregistered quantitative hypothesis for the revised version. The most reasonable qualitative expectation, however, would be that at least one lightweight reliability signal would remain consistently useful across both transfer directions and would track the security-critical errors sufficiently well for analyst review.

That expectation was not supported. The relative ranking changes when the source and target are reversed, the detector itself becomes severely unreliable in the reverse direction, generic-error ranking diverges from attack-miss ranking in the more informative transfer direction, and the conformal scalarization becomes too discrete for a fair competitive comparison.

These deviations are not treated as failures of the project. They are the most important findings because they prevent a simplistic claim of a universal uncertainty wrapper. The research objective is better served by demonstrating the conditions under which reliability claims break than by selecting a winner from a metric table. The final interpretation therefore becomes more conservative but also more defensible.

## 5.3 Limitations and Threats to Validity

Dataset and domain scope: conclusions are based on two NetFlow-v3 datasets and two transfer directions. They do not establish transportability across all organizations, traffic types, collection periods, or live networks.

Fixed detector architecture: the study isolates a Random Forest backbone. Results may differ for neural, linear, gradient-boosted, streaming, or hybrid detectors.

Predictor-space duplicate risk: the primary source split hashes the 53-field representation, not the 46-field predictor space. A predictor-space duplicate-safe split is required before treating the comparison as final.

Ten seeds are repeated detector fits, not ten independent organizations or network deployments. The seed-level uncertainty therefore does not capture all sources of field variability.

Family analysis is deliberately restricted by the semantic crosswalk. It is not evidence of comprehensive unseen-family generalization.

Conformal scalarization is tie-dominated and must be replaced by a continuous score for a fair method comparison.

No target adaptation or recalibration is permitted. This isolates the source-only question but does not show what could happen after a small amount of trusted target information is introduced.

The review benchmark ranks the entire target population rather than a production predicted-benign queue. It is an operational abstraction and not a complete SOC simulation.

Public benchmark labels may contain construction or labelling errors, and flow records may not be statistically independent because multiple rows can arise from related sessions or temporal episodes.

The analysis contains several secondary metrics and pairwise tests. The report therefore does not interpret the set of p-values as proof of one global method ordering.

Distance and anomaly scores depend on the selected 46-feature representation. The conclusions are not representation-invariant.

All scores are normalized to a larger-score-equals-higher-review convention. The transfer experiments demonstrate why this orientation should be validated rather than assumed.

## 5.4 Future Work

TABLE_JSON:
[["Direction", "Proposed extension", "Purpose"], ["Temporal deployment drift", "Evaluate the same reliability signals as source calibration becomes stale over time, separating temporal drift from cross-dataset shift.", "Determine whether the same reliability transportability failures emerge when source calibration becomes stale over time."], ["Target-label-efficient recalibration", "Measure how much trusted target information is needed to recover calibration or score orientation without full detector retraining.", "Quantify the minimum trusted target information needed to restore calibration or score orientation without full retraining."], ["Broader domain replication", "Repeat the bidirectional protocol across additional NetFlow-v3 and other standardized flow datasets to test whether direction dependence persists.", "Test whether direction dependence is specific to this dataset pair or persists across additional domains and benchmark families."], ["Family-conditional reliability", "Build an independently validated semantic ontology with sufficient within-family variation to support meaningful family-specific analysis.", "Enable valid attack-family comparisons using a larger, independently validated semantic crosswalk."], ["Continuous conformal ranking", "Replace prediction-set size with a continuous p-value or nonconformity score and rerun budget analysis with randomized or expected ties.", "Remove the current binary, tie-dominated scalar and make conformal ranking comparable to continuous reliability signals."], ["Duplicate-safe source partitioning", "Regenerate the source split on the exact 46-feature predictor representation so identical predictive rows cannot cross the train/calibration/test boundaries.", "Eliminate predictor-space duplicate leakage risk across the train, calibration, and source-test partitions."], ["Composite reliability policies", "Test whether combinations of RF disagreement, confidence and distance provide more stable triage than any individual signal while preserving source-only constraints.", "Test whether combined signals provide more stable budgeted triage than any individual signal while preserving source-only controls."], ["Operational SOC simulation", "Move from whole-target ranking to predicted-benign queues, alert deduplication, temporal incidents, analyst workload and realistic review capacity.", "Evaluate whether findings persist when review is restricted to predicted-benign queues and more realistic SOC workflows."], ["Resource benchmarking", "Measure end-to-end memory use, inference throughput, storage footprint and energy where deployment constraints make such factors material.", "Quantify actual memory, latency, storage, and throughput costs under deployment-like workloads."]]

## 5.5 Way Ahead

The immediate way ahead is not to add more methods to the current paper. It is to close the two methodological gaps that the present experiment has exposed: predictor-space duplicate safety and conformal scalar continuity. Once those are resolved, the project can either retain the same scope with stronger validity or extend selectively into target-aware recalibration and broader domain replication.

A successful next version should preserve the source-only firewall as the baseline condition. Any target-aware adaptation should be presented as a separate experimental arm so that adaptation gains are not confused with source-only reliability transportability. Likewise, any new reliability mechanism should be evaluated against the same attack-miss population and the same fixed review budgets.

The practical deployment path is therefore staged. First, validate the reliability score on an independently collected target domain with trustworthy labels. Second, verify score orientation and fixed-budget capture. Third, determine whether a target-aware recalibration layer is justified. Only after these steps should the reliability signal be considered for integration into an analyst workflow. The present research establishes a disciplined baseline for that process rather than claiming that the problem is solved.

# REFERENCES

1. Ahmed, W. A., Rahaman, M. A., Roy, P., and Alam, P. (2026). “The dashboard says perfect: A systematic audit of label-free model monitoring and test-time adaptation under temporal distribution shift in network intrusion detection.” Frontiers in Artificial Intelligence, 9, Article 1928858. doi:10.3389/frai.2026.1928858.

2. Alalisalem, D., Almohsen, A., Albudair, K., and Aljughaiman, A. (2026). “Cross-Dataset Generalization in Intrusion Detection Systems Using Transfer Learning.” IEEE Access, 14, pp. 90334-90353. doi:10.1109/ACCESS.2026.3700037.

3. Angelopoulos, A. N., and Bates, S. (2021). “A gentle introduction to conformal prediction and distribution-free uncertainty quantification.” arXiv:2107.07511.

4. Apruzzese, G., Pajola, L., and Conti, M. (2022). “The cross-evaluation of machine learning-based network intrusion detection systems.” IEEE Transactions on Network and Service Management, 19(4), pp. 5152-5169. doi:10.1109/TNSM.2022.3157344.

5. Arepalli, S. V., Irrinki, U. S. G., Morampudi, A., and Surapani, R. K. (2026). “Conformal prediction for network intrusion triage and analysis of unseen attack families.” Discover Informatics, 1, Article 33. doi:10.1007/s44564-026-00033-y.

6. Arp, D., Quiring, E., Pendlebury, F., Warnecke, A., Pierazzi, F., Wressnegger, C., Cavallaro, L., and Rieck, K. (2022). “Dos and don'ts of machine learning in computer security.” Proceedings of the 31st USENIX Security Symposium, pp. 3971-3988.

7. Breiman, L. (2001). “Random forests.” Machine Learning, 45(1), pp. 5-32. doi:10.1023/A:1010933404324.

8. Cantone, M., Marrocco, C., and Bria, A. (2024). “Machine learning in network intrusion detection: A cross-dataset generalization study.” IEEE Access, 12, Article 144489. doi:10.1109/ACCESS.2024.3472907.

9. Chow, C. K. (1970). “On optimum recognition error and reject tradeoff.” IEEE Transactions on Information Theory, 16(1), pp. 41-46. doi:10.1109/TIT.1970.1054406.

10. Engelen, G., Rimmer, V., and Joosen, W. (2021). “Troubleshooting an intrusion detection dataset: The CICIDS2017 case study.” Proceedings of the 2021 IEEE Security and Privacy Workshops, pp. 7-12. doi:10.1109/SPW53761.2021.00009.

11. S. Gautam et al. (2026). “IntrusionDetection: Transportability of Post-Hoc Reliability Signals for Network Intrusion Detection.” GitHub repository. Available: https://github.com/ShreyasGautam01/IntrusionDetection.

12. Geifman, Y., and El-Yaniv, R. (2017). “Selective classification for deep neural networks.” Advances in Neural Information Processing Systems 30, pp. 4878-4887.

13. Guo, C., Pleiss, G., Sun, Y., and Weinberger, K. Q. (2017). “On calibration of modern neural networks.” Proceedings of the 34th International Conference on Machine Learning, PMLR 70, pp. 1321-1330.

14. Hendrycks, D., and Gimpel, K. (2017). “A baseline for detecting misclassified and out-of-distribution examples in neural networks.” Proceedings of the International Conference on Learning Representations.

15. Jin, H., and Lee, H. (2026). “Benchmark-Shift-Aware Intrusion Detection for Evolving Network Traffic: Cross-Dataset Generalization, Calibrated Alerting, and Score-Orientation Diagnostics.” Electronics, 15(17), Article 3761. doi:10.3390/electronics15173761.

16. Li, H., and Zhou, Z. (2026). “From Risk Scores to Budget-Constrained Alert Streams: Temporal Evaluation of Flow-Level Network Intrusion Detection.” Electronics, 15(20), Article 4854.

17. Liu, F. T., Ting, K. M., and Zhou, Z.-H. (2008). “Isolation forest.” Proceedings of the 8th IEEE International Conference on Data Mining, pp. 413-422. doi:10.1109/ICDM.2008.17.

18. Liu, L., Engelen, G., Lynar, T., Essam, D., and Joosen, W. (2022). “Error prevalence in NIDS datasets: A case study on CIC-IDS-2017 and CSE-CIC-IDS-2018.” Proceedings of the 2022 IEEE Conference on Communications and Network Security, pp. 254-263. doi:10.1109/CNS56114.2022.9947235.

19. Luay, M., Layeghy, S., Hosseininoorbin, S., Sarhan, M., Moustafa, N., and Portmann, M. (2026). “Temporal Analysis of NetFlow Datasets for Network Intrusion Detection Systems.” IEEE Access. doi:10.1109/ACCESS.2026.3688204.

20. Moustafa, N., and Slay, J. (2015). “UNSW-NB15: a comprehensive data set for network intrusion detection systems.” Proceedings of the 2015 Military Communications and Information Systems Conference, Canberra, Australia, pp. 1-6. doi:10.1109/MilCIS.2015.7348942.

21. Niculescu-Mizil, A., and Caruana, R. (2005). “Predicting good probabilities with supervised learning.” Proceedings of the 22nd International Conference on Machine Learning, pp. 625-632. doi:10.1145/1102351.1102430.

22. Ovadia, Y., Fertig, E., Ren, J., Nado, Z., Sculley, D., Nowozin, S., Dillon, J. V., Lakshminarayanan, B., and Snoek, J. (2019). “Can you trust your model's uncertainty? Evaluating predictive uncertainty under dataset shift.” Advances in Neural Information Processing Systems, 32.

23. Platt, J. C. (1999). “Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods.” In Advances in Large Margin Classifiers, MIT Press, pp. 1-11.

24. Saito, T., and Rehmsmeier, M. (2015). “The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets.” PLoS ONE, 10(3), Article e0118432. doi:10.1371/journal.pone.0118432.

25. Sarhan, M., Layeghy, S., and Portmann, M. (2022). “Towards a standard feature set for network intrusion detection system datasets.” Mobile Networks and Applications, 27, pp. 357-370. doi:10.1007/s11036-021-01843-0.

26. Sharafaldin, I., Habibi Lashkari, A., and Ghorbani, A. A. (2018). “Toward generating a new intrusion detection dataset and intrusion traffic characterization.” Proceedings of the 4th International Conference on Information Systems Security and Privacy, pp. 108-116. doi:10.5220/0006639801080116.

27. Talpini, J., Sartori, F., and Savi, M. (2024). “Enhancing trustworthiness in ML-based network intrusion detection with uncertainty quantification.” Journal of Reliable Intelligent Environments, 10, pp. 501-520. doi:10.1007/s40860-024-00238-8.

28. Ha Thanh, D. (2026). “A transfer-aware, deployment-oriented evaluation framework for NetFlow-based intrusion detection systems (TAN-IDS).” PLOS ONE, 21(4), Article e0346801. doi:10.1371/journal.pone.0346801.

29. Ha Thanh, D. (2026). “Budget-aware two-stage NetFlow intrusion detection for high-traffic critical information infrastructure under domain shift.” International Journal of Critical Infrastructure Protection, 54. doi:10.1016/j.ijcip.2026.100876.

30. Tibshirani, R. J., Barber, R. F., Candes, E., and Ramdas, A. (2019). “Conformal prediction under covariate shift.” Advances in Neural Information Processing Systems, 32, pp. 2530-2540.

31. Viegas, E. K., Santin, A. O., and Oliveira, L. S. (2017). “Toward a reliable anomaly-based intrusion detection in real-world environments.” Computer Networks, 127, pp. 200-216. doi:10.1016/j.comnet.2017.08.013.

32. Viegas, E. K., Santin, A. O., and Tedeschi, P. (2023). “Toward a reliable evaluation of machine learning schemes for network-based intrusion detection.” IEEE Internet of Things Magazine, 6(2), pp. 70-75. doi:10.1109/IOTM.001.2300106.

# APPENDIX 1: USER MANUAL

This appendix converts the experimental protocol into a reproducibility-oriented operating procedure. Exact dataset paths and the final experiment entry-point command are not specified in the latest paper and are therefore deliberately left as placeholders rather than invented.

## A. Environment Setup

Obtain the project repository from https://github.com/ShreyasGautam01/IntrusionDetection.

Check out the exact scientific revision used for the report: branch/ref codex/e0-e05, or insert the final release tag here: [FINAL RELEASE TAG / COMMIT].

Install or provision Python 3.14.7 and synchronize the repository's locked dependencies using the project's documented environment manager. Exact command: [INSERT FINAL ENVIRONMENT SETUP COMMAND].

Confirm the scientific package versions: NumPy 2.5.2, pandas 3.0.6, scikit-learn 1.9.1.

Record the execution operating system and hardware configuration: [INSERT OS, CPU, RAM, STORAGE, AND OPTIONAL GPU INFORMATION].

## B. Dataset Placement and Integrity Validation

Obtain lawful copies of NF-UNSW-NB15-v3 and NF-CSE-CIC-IDS2018-v3 from their documented public sources.

Place the source files in the repository paths expected by the current implementation. Exact paths: [INSERT DATASET PATHS].

Validate file hashes against the repository manifests before running experiments. Expected manifest names / locations: [INSERT MANIFEST PATHS].

Confirm the audited total row counts: 2,365,424 for NF-UNSW-NB15-v3 and 20,115,529 for NF-CSE-CIC-IDS2018-v3.

Confirm the common 53-field NetFlow-v3 interface and the frozen 46-feature predictive registry.

Check that attack labels are mapped to 1 and benign labels to 0 for binary evaluation, while raw family labels remain in evaluation metadata only.

## C. Preprocessing and Partitioning

Construct the deterministic source partitions using the repository's canonical SHA-256 rule over the raw 53-feature representation.

Use buckets 0-59 for source training, 60-79 for source calibration, and 80-99 for source test.

Fit non-finite-value replacement medians using source training only and reuse them unchanged for calibration, source test and target data.

Do not fit a scaler, imputer, calibrator, threshold or reference set using target statistics.

Before final publication, verify that the corrected duplicate-safe predictor-space split has replaced the archived primary split.

## D. Detector and Reliability Execution

Fit the fixed Random Forest with 200 trees, minimum leaf size five, unrestricted depth, sqrt feature selection, bootstrap sampling, no class weighting, and seeds 0 through 9.

Fit source-only probability calibration on the designated source calibration subset.

Fit the source-only conformal calibration at alpha = 0.10.

Build the source-training feature-space distance index and compute mean distance to the five nearest source-training rows.

Fit the source-training Isolation Forest using 100 trees and max_samples = 256.

Generate the complete target prediction and reliability score artifacts without reading target labels.

Freeze all target scores before entering the evaluation stage.

## E. Evaluation and Reporting

Compute target attack-miss AUPRC for each non-degenerate signal.

Compute attack-miss capture at 1%, 5%, and 10% review budgets, retaining the deterministic tie rule only for the archived baseline.

Compare results against random-review expectations.

Compute generic-error AUPRC/AUROC separately from attack-miss metrics.

Run the bidirectional transfer direction that was not used as the source of the current artifact and verify the same configuration is used.

Record all seed-level outputs before calculating means and standard deviations.

Generate the tables and figures used in Chapter 4.

## F. Validation Checklist

Target labels absent from fitting/tuning/calibration/score orientation: [PASS / FAIL].

Dataset hashes match manifests: [PASS / FAIL].

Feature registry matches source and target: [PASS / FAIL].

Predictor-space duplicate-safe split implemented: [PASS / PENDING].

Continuous conformal scalarization implemented: [PASS / PENDING].

Randomized or expected tie handling implemented: [PASS / PENDING].

Runtime and hardware record complete: [PASS / PENDING].

Exact experiment entry point documented: [INSERT COMMAND].

## G. Screenshots / Pictures Required for Final Manual

[INSERT SCREENSHOT: repository checkout and exact revision/commit used for the final report.]

[INSERT SCREENSHOT: environment installation / dependency lock confirmation.]

[INSERT SCREENSHOT: dataset and manifest validation output.]

[INSERT SCREENSHOT: experiment invocation and successful completion.]

[INSERT SCREENSHOT: representative generated result artifact / figure.]

# APPENDIX 2: ACHIEVEMENTS

## A. Research Manuscript

A research manuscript titled “Transportability of Post-Hoc Reliability Signals for Network Intrusion Detection under Source-Only Cross-Domain Transfer” was prepared by Shreyas Gautam, Bhawika Panchal, Himanshi Mittal, Anna Taneja, and Aditya Mehta, under the supervision of Prof. (Dr.) Bhupaesh Ghai. The manuscript represents the revised research direction documented in this report.

## B. Reproducibility Artifact

Repository: https://github.com/ShreyasGautam01/IntrusionDetection

The repository contains the experimental implementation, scientific configuration, reproducibility manifests, and the current research manuscript. Final release tag / archival DOI: [INSERT IF AVAILABLE].

## C. Academic-Integrity Screening

The prior October 2026 project report recorded an overall Turnitin similarity index of 5% after bibliography filtering, with zero integrity flags, and an AI-writing overview of 0% detected. Those values belong to the earlier report and should not be presented as the screening status of this revised report. Current screening results for this final version: [INSERT UPDATED TURNITIN / INTEGRITY SCREENING RESULT].

## D. Publication / Submission Status

The prior project report listed the International Conference on computing,communication and wireless Networks as a conference / journal submission context. Current submission venue, manuscript status, and submission date for the revised study: [INSERT CURRENT STATUS].

## E. Project Recognition / Other Achievements

[INSERT any awards, presentations, conference acceptance, project demonstrations, certifications, or institutional recognition associated with the revised research project. No additional achievement was identifiable from the supplied current materials.]
