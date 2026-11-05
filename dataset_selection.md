# Dataset Selection and Locking Protocol

**Status:** Working document  
**Last updated:** 2026-11-05  
**Frozen core docs:** `research_proposal.md` and `methodology_final.md` are not modified by this document.

## 1. Decision

The study will use the NetFlow-v3 collection as the primary data layer.

Primary pair:

- NF-UNSW-NB15-v3
- NF-CSE-CIC-IDS2018-v3

Replication/stress-test:

- NF-ToN-IoT-v3

Optional:

- NF-BoT-IoT-v3 only if the core study is complete and the additional dataset passes the same compatibility and leakage audits.

The NetFlow-v3 catalogue states that v3 consists of four datasets with 53 extended NetFlow features, adding 10 temporal features to the previous 43-feature representation.

Source: https://staff.itee.uq.edu.au/marius/NIDS_datasets/

## 2. Current published dataset facts

The current UQ catalogue reports:

### NF-UNSW-NB15-v3

- Total flows: 2,365,424
- Attack: 127,639 (5.4%)
- Benign: 2,237,731 (94.6%)
- Attack families: Fuzzers, Analysis, Backdoor, DoS, Exploits, Generic, Reconnaissance, Shellcode, Worms

### NF-CSE-CIC-IDS2018-v3

- Total flows: 20,115,529
- Attack: 2,600,903 (12.93%)
- Benign: 17,514,626 (87.07%)
- Attack families: BruteForce, Bot, DoS, DDoS, Infiltration, Web Attacks

### NF-ToN-IoT-v3

- Total flows: 27,520,260
- Attack: 10,728,046 (38.98%)
- Benign: 16,792,214 (61.02%)
- Attack families: Backdoor, DoS, DDoS, Injection, MITM, Password, Ransomware, Scanning, XSS

These are catalogue/reference counts only. The experiment must report the counts of the exact downloaded files after integrity checks and any predeclared cleaning.

## 3. Why the primary pair is suitable

UNSW-NB15-v3 and CSE-CIC-IDS2018-v3:

- use the same NetFlow-v3 feature interface;
- have materially different attack prevalence;
- have different attack-family taxonomies;
- represent different traffic-generation environments;
- provide a natural source-to-target transfer test;
- avoid introducing feature-space incompatibility as the primary confound.

## 4. Dataset provenance requirements

For every downloaded dataset, record:

- canonical source URL;
- download timestamp;
- file/archive name;
- archive size;
- SHA-256 hash;
- extracted file hashes where practical;
- dataset release/version;
- schema hash;
- row count;
- column count;
- label counts;
- attack-family counts.

Required artifact:

`dataset_manifest.json`

The raw datasets must not be committed to GitHub.

## 5. Dataset lock states

A dataset progresses through:

1. **Candidate** — identified as potentially useful.
2. **Downloaded** — exact release obtained.
3. **Verified** — hash and schema checked.
4. **Audited** — duplicates, invalid values, labels, temporal metadata inspected.
5. **Locked** — eligible for core experiments.

Only locked datasets can enter the experiment lock.

## 6. Feature compatibility

The primary representation is the 53-feature NetFlow-v3 representation.

A compact 8-feature representation inspired by TAN-IDS will be evaluated later as a sensitivity analysis.

TAN-IDS uses an 8-dimensional interoperable NetFlow representation and explicitly separates in-dataset, source-only cross-dataset transfer, mixed-domain training, and target fine-tuning. Source-only preprocessing is fitted on training data to prevent leakage.

Source: https://doi.org/10.1371/journal.pone.0346801

## 7. Label policy

The model's main target is binary:

- benign
- attack

Attack-family labels are retained separately for evaluation.

A family is only called **target-exclusive** when:

- it is present in the target evaluation data;
- it is absent from source model-training data;
- there is no defensible semantic equivalent used by the source model.

Ambiguous cross-dataset family mappings are not forced.

Required artifact:

`label_mapping.csv`

## 8. Important family-overlap observation

The primary pair does not have a simple one-to-one attack taxonomy.

Shared/equivalent-looking families include broad categories such as DoS/DDoS, but the source and target taxonomies are not identical.

Therefore:

- binary detection is the primary cross-domain task;
- family analysis is dataset-local by default;
- cross-dataset "unseen family" claims require an explicit mapping rationale.

This is preferable to pretending that every family label has a perfect semantic counterpart.

## 9. Duplicate and leakage audit

Before model training:

- exact duplicate rows;
- repeated feature vectors;
- conflicting labels for identical features;
- capture/session duplicates where metadata permits;
- temporal overlaps;
- identifiers/metadata that could encode dataset membership.

No cleaning decision may depend on target performance.

Required artifact:

`leakage_audit.md`

## 10. Large-data policy

NF-ToN-IoT-v3 is large enough that the primary pipeline should support chunked processing.

The target evaluation must not require loading all target rows into memory.

Required implementation characteristics:

- deterministic chunk ordering;
- deterministic sampling where sampling is necessary;
- no per-method resampling;
- same target membership for every reliability method;
- persisted prediction/score blocks.

## 11. Dataset decision gate

A dataset is rejected from the core study if:

- schema cannot be aligned cleanly;
- source/target label semantics cannot be documented;
- leakage cannot be adequately controlled;
- the downloaded release cannot be reproduced;
- attack-family metadata is unusable for the planned evaluation;
- the same target sample cannot be evaluated across all methods.

## 12. References

- University of Queensland ML-Based NIDS Datasets:
  https://staff.itee.uq.edu.au/marius/NIDS_datasets/
- Luay et al., NetFlow-v3 dataset work:
  https://arxiv.org/abs/2503.04404
- Ha Thanh, TAN-IDS:
  https://doi.org/10.1371/journal.pone.0346801
