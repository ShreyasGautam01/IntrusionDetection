# Label Mapping Draft

**Status:** Draft; mapping is not frozen. Updated 2026-11-06.

## Purpose and scope

The primary task remains binary benign/attack detection. `Attack` family labels are retained for dataset description and carefully governed family-level diagnostics. The active source/target pair is NF-UNSW-NB15-v3 → NF-CSE-CIC-IDS2018-v3. NF-ToN-IoT-v3 is outside this experiment.

This document and its accompanying audit artifacts define a conservative documentation crosswalk only. They do not relabel, transform, sample, or modify either dataset, and they do not use target labels to make modeling decisions.

## Audited label inventory

The row-level mapping and exact local counts are in [family_mapping_draft.csv](reports/nf_v3_audit/family_mapping_draft.csv). The source/target relation matrix is in [family_matrix_draft.csv](reports/nf_v3_audit/family_matrix_draft.csv), and the human-readable summary is [FAMILY_MAPPING_DRAFT.md](reports/nf_v3_audit/FAMILY_MAPPING_DRAFT.md). These are generated from the audited `Attack` counts in `target_value_counts.csv`; the downloaded files remain unchanged.

Raw label strings are preserved. Canonical display names normalize UNSW `Exploits` to `Exploitation`, `Fuzzers` to `Fuzzing`, and CIC `Infilteration` to `Infiltration`. These aliases do not claim taxonomic equivalence across datasets.

## Release-count reconciliation

The local BagIt-verified UNSW file matches Table 3 of the versioned NetFlow-v3 release paper exactly. The current UQ catalogue HTML lists different UNSW counts for Analysis (2,381), Backdoor (1,226), and Shellcode (4,659), while the release paper and local audit report 1,226, 4,659, and 2,381, respectively. The page prose reports 127,639 attacks, 54 fewer than the page’s own family-table sum and the local/paper total of 127,693. This is documented as a source-page discrepancy; no raw labels or rows were changed. Per-label and total comparisons are recorded in `reports/nf_v3_audit/family_mapping_draft.csv`.

## Cross-dataset policy

- The only direct shared category in this draft is DoS. Shared naming does not imply matching attack implementations or distributions.
- UNSW DoS versus CIC DDoS remains ambiguous because UNSW does not distinguish distributed sources in its family label.
- UNSW Analysis versus CIC Web Attacks is possible overlap, not equivalence.
- UNSW Exploitation versus CIC Web Attacks or Infiltration is possible overlap, not equivalence.
- UNSW Backdoor versus CIC Infiltration is possible overlap, not equivalence; the CIC scenario is composite.
- UNSW Reconnaissance versus CIC Infiltration is possible overlap, not equivalence.
- All other pairs are recorded as having no documented equivalence in the cited descriptions. This is not proof that the attack mechanisms can never overlap.
- **No target-exclusive family is declared yet.** Claims remain withheld pending review and must not be inferred solely from differing label strings.

The `WebAttacks` canonical grouping for CIC is an inference: three audited raw labels sum to the catalogue aggregate (1,618 + 480 + 440 = 2,538). The raw names and counts remain separate in the mapping artifact, and the inference is explicitly marked there.

## Sources

- UQ NetFlow v3 catalogue and family descriptions: https://staff.itee.uq.edu.au/marius/NIDS_datasets/
- Official CIC-IDS2018 scenarios: https://www.unb.ca/cic/datasets/ids-2018.html

The mapping and matrix are review drafts, not a final label ontology. Any final mapping must be fixed before model training or target-label evaluation.
