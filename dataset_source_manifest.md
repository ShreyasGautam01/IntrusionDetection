# Dataset Source Manifest

**Status:** Working manifest — exact downloaded-file hashes remain pending dataset acquisition.  
**Last updated:** 2026-11-05.

## Authoritative catalogue

University of Queensland ML-Based NIDS Datasets:

https://staff.itee.uq.edu.au/marius/NIDS_datasets/

The catalogue states that NetFlow-v3 contains four datasets with 53 extended NetFlow features and is the only version in the collection incorporating the additional temporal features.

## Exact current download endpoints

### NF-UNSW-NB15-v3

Catalogue entry:

https://staff.itee.uq.edu.au/marius/NIDS_datasets/

Current download endpoint exposed by the catalogue:

https://rdm.uq.edu.au/files/abd2f5d8-e268-4ff0-84fb-f2f7b3ca3e8f

Reference catalogue count:

- 2,365,424 total flows
- 127,639 attack
- 2,237,731 benign

### NF-CSE-CIC-IDS2018-v3

Current download endpoint exposed by the catalogue:

https://rdm.uq.edu.au/files/4ac221b1-6bd6-42b1-bdf7-03f4fc7efb22

Reference catalogue count:

- 20,115,529 total flows
- 2,600,903 attack
- 17,514,626 benign

### NF-ToN-IoT-v3

Current download endpoint exposed by the catalogue:

https://rdm.uq.edu.au/files/343e2e8c-6e6e-4a0c-813d-a46acea1b7f4

Reference catalogue count:

- 27,520,260 total flows
- 10,728,046 attack
- 16,792,214 benign

## Important provenance note

The RDM endpoints are the current download targets exposed by the UQ catalogue as of the methodology preparation date. They are not yet the experiment's locked file hashes.

After download, record:

- final file name;
- byte size;
- SHA-256;
- extracted file hash if archived;
- schema hash;
- row count;
- column count;
- exact label values;
- exact family counts.

## Dataset versions

The experiment uses **NetFlow-v3**, not the older NetFlow-v1 or v2 files.

The v3 dataset paper is:

Majed Luay, Siamak Layeghy, Seyedehfaezeh Hosseininoorbin, Mohanad Sarhan, Nour Moustafa, Marius Portmann,
"Temporal Analysis of NetFlow Datasets for Network Intrusion Detection Systems."

Preprint:
https://arxiv.org/abs/2503.04404

Current catalogue citation instructions should be followed in the eventual paper.

## Release-selection rule

Do not replace a downloaded v3 release with an older release merely because a preprocessing script expects another schema.

If the downloaded release differs from the catalogue counts, first investigate whether the difference is due to:

- file segmentation;
- an updated release;
- archive contents;
- extraction errors;
- filtering;
- corrupted download.

Do not call it a methodological difference until the provenance issue is resolved.

## Raw-data handling

The raw datasets are not committed to GitHub.

Only provenance, checksums, schemas, mappings, split manifests, and code are committed.
