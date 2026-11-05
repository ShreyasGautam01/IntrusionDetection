
# Dataset Source Manifest

**Status:** Working manifest — exact downloaded-file hashes remain pending local audit.  
**Last updated:** 2026-11-05.

## Active datasets

The current active dataset scope is deliberately limited to two datasets:

1. NF-UNSW-NB15-v3
2. NF-CSE-CIC-IDS2018-v3

These are the only datasets that should be audited and prepared for the first pilot and experiment lock.

## Deferred dataset

NF-ToN-IoT-v3 is already downloaded but is **not currently part of the active experiment pipeline**.

Keep its raw files untouched.

Do not build a second preprocessing path, family mapping, or experiment matrix for ToN-IoT at this stage.

## Authoritative catalogue

University of Queensland ML-Based NIDS Datasets:

https://staff.itee.uq.edu.au/marius/NIDS_datasets/

The catalogue states that NetFlow-v3 contains four datasets with 53 extended NetFlow features.

## Active exact download endpoints

### NF-UNSW-NB15-v3

https://rdm.uq.edu.au/files/abd2f5d8-e268-4ff0-84fb-f2f7b3ca3e8f

Reference catalogue count:

- 2,365,424 total flows
- 127,639 attack
- 2,237,731 benign

### NF-CSE-CIC-IDS2018-v3

https://rdm.uq.edu.au/files/4ac221b1-6bd6-42b1-bdf7-03f4fc7efb22

Reference catalogue count:

- 20,115,529 total flows
- 2,600,903 attack
- 17,514,626 benign

## Deferred exact endpoint

### NF-ToN-IoT-v3

https://rdm.uq.edu.au/files/343e2e8c-6e6e-4a0c-813d-a46acea1b7f4

Reference catalogue count:

- 27,520,260 total flows
- 10,728,046 attack
- 16,792,214 benign

No ToN-IoT audit should be started before the core two-dataset pipeline is stable.

## Provenance requirements

For each active dataset, record:

- canonical URL;
- download timestamp;
- file/archive name;
- byte size;
- SHA-256;
- extracted-file hash where applicable;
- schema hash;
- row count;
- column count;
- label values;
- family counts.

Required artifact:

`dataset_manifest.json`

## Raw-data policy

Do not commit raw data to GitHub.

Raw datasets are read-only inputs.
