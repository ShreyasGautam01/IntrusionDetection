# Active-Pair Family Mapping Audit (Draft)

**Status:** Draft; no family mapping has been frozen. This audit reads the already-audited label counts and does not train or evaluate a model.

## Scope and method

Only NF-UNSW-NB15-v3 (source candidate) and NF-CSE-CIC-IDS2018-v3 (target candidate) are included. NF-ToN-IoT-v3 is outside the active experiment. Raw `Attack` values and audited row counts are retained. Binary labels are shown only as dataset metadata; this artifact does not use labels to make modeling decisions.

Canonical groupings below are a documentation crosswalk, not relabeling of data. UNSW `Exploits` is rendered as `Exploitation`, `Fuzzers` as `Fuzzing`, and CIC `Infilteration` as `Infiltration` for readable canonical names while exact raw values remain in the CSV. CIC `WebAttacks` is inferred because the three local raw web labels sum exactly to the UQ catalogue aggregate (2,538).

## Release-count reconciliation

The BagIt-verified local UNSW file matches the family counts in Table 3 of the NetFlow-v3 release paper exactly, including Analysis 1,226, Backdoor 4,659, and Shellcode 2,381. The current UQ catalogue HTML table instead lists 2,381, 1,226, and 4,659 for those labels, respectively. Its prose total says 127,639 attacks, while its own family table sums to 127,693; the local file and v3 release paper both report 127,693. This is a discrepancy in the current catalogue page, not evidence to relabel the local file. Raw labels and BagIt-verified data are retained unchanged; family-level claims use the v3 release paper and remain draft pending review.

## Audited local family inventory

Counts come from `target_value_counts.csv`, not catalogue estimates.

### NF-UNSW-NB15-v3

| Canonical family | Rows | Raw `Attack` values |
|---|---:|---|
| Analysis | 1,226 | `Analysis` (1,226) |
| Backdoor | 4,659 | `Backdoor` (4,659) |
| DoS | 5,980 | `DoS` (5,980) |
| Exploitation | 42,748 | `Exploits` (42,748) |
| Fuzzing | 33,816 | `Fuzzers` (33,816) |
| Generic | 19,651 | `Generic` (19,651) |
| Reconnaissance | 17,074 | `Reconnaissance` (17,074) |
| Shellcode | 2,381 | `Shellcode` (2,381) |
| Worms | 158 | `Worms` (158) |

### NF-CSE-CIC-IDS2018-v3

| Canonical family | Rows | Raw `Attack` values |
|---|---:|---|
| Bot | 207,703 | `Bot` (207,703) |
| BruteForce | 575,194 | `FTP-BruteForce` (386,720), `SSH-Bruteforce` (188,474) |
| DDoS | 1,324,350 | `DDOS_attack-HOIC` (1,032,311), `DDOS_attack-LOIC-UDP` (3,450), `DDoS_attacks-LOIC-HTTP` (288,589) |
| DoS | 302,966 | `DoS_attacks-GoldenEye` (61,300), `DoS_attacks-Hulk` (100,076), `DoS_attacks-SlowHTTPTest` (105,550), `DoS_attacks-Slowloris` (36,040) |
| Infiltration | 188,152 | `Infilteration` (188,152) |
| WebAttacks | 2,538 | `Brute_Force_-Web` (1,618), `Brute_Force_-XSS` (480), `SQL_Injection` (440) |

## Cross-dataset interpretation

- The only direct shared category supported by this conservative crosswalk is **DoS**. This means shared category name/documentation, not identical attack implementations or feature distributions.
- UNSW DoS vs CIC DDoS is **ambiguous**: UNSW does not split its family by distributed source while CIC does.
- UNSW Analysis vs CIC WebAttacks, Exploitation vs WebAttacks/Infiltration, Backdoor vs Infiltration, and Reconnaissance vs Infiltration are marked possible semantic overlap, not equivalence.
- All target-exclusive claims remain withheld pending explicit human review of the frozen ontology. No family is declared unseen from string mismatch alone.
- Every source/target family pair and rationale appears in `family_matrix_draft.csv`; raw values and mapping basis appear in `family_mapping_draft.csv`.

## Sources and inference

- NetFlow-v3 release paper, Table 3 (release-matched family counts): https://arxiv.org/html/2503.04404v3
- UQ NetFlow v3 catalogue HTML (current family descriptions and count discrepancy): https://staff.itee.uq.edu.au/marius/NIDS_datasets/
- Official CIC-IDS2018 scenario documentation: https://www.unb.ca/cic/datasets/ids-2018.html
- CIC `WebAttacks` aggregate correspondence is an inference from exact local raw-label counts: 1,618 + 480 + 440 = 2,538, matching the published aggregate. Retain this as provisional until reviewed.
