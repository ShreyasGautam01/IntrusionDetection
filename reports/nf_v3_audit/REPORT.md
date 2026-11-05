# NF-v3 dataset acquisition and audit

Audit generated: 2026-11-05T09:49:15.525258+00:00
Source folder: `D:\NF-v3-datasets`

## Findings

The downloaded files are extracted BagIt packages attributed in their bag metadata to the University of Queensland dataset `NFV3DATA-A11964-A11964` (RAiD `https://hdl.handle.net/102.100.100/602564`). The supplied folder contains extracted package trees rather than archive files. Each observed CSV has the expected dataset-specific NF-v3 filename. BagIt manifest checks are reported per package below.

The completed row-level audit covers 2 datasets in the current two-dataset research scope. Each audited schema contains the expected 53 NetFlow-v3 features plus `Label` and `Attack`. The 53-feature dictionary is supplied in the packages as `NetFlow_v3_Features.csv`; the full column-by-column audit is in `schema.csv`. The JSON records both feature-set completeness and whether observed feature order matches the dictionary order.
NF-ToN-IoT-v3 is present in the downloaded folder but its full row-level audit is deferred: NF-ToN-IoT-v3 is not in RQ1's current two-dataset UNSW/CIC transfer plan; the v3 experiment record says adding ToN-IoT would be a separate broader multi-domain experiment.
A prior completed full-table pass processed all 27,520,260 ToN-IoT rows and found 1,816,137 repeated rows/53-feature vectors. Its full label and per-column quality report was not preserved, so ToN-IoT is marked deferred here.

No rows were changed, cleaned, relabeled, sampled, or transformed. Target labels were counted for inventory only and were not used for modeling decisions.

## File inventory and integrity

| Dataset | Size (bytes) | Rows | Columns | Features match | SHA-256 | BagIt SHA-1 |
|---|---:|---:|---:|---|---|---|
| NF-CSE-CIC-IDS2018-v3 | 4222783755 | 20115529 | 55 | 53/53 | `242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74` | PASS |
| NF-UNSW-NB15-v3 | 577360958 | 2365424 | 55 | 53/53 | `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5` | PASS |

### Extracted package structure

**NF-CSE-CIC-IDS2018-v3** (`D:\NF-v3-datasets\f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964`)

```text
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\bag-info.txt (839 bytes)
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\bagit.txt (55 bytes)
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\data\NetFlow_v3_Features.csv (2935 bytes)
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\data\NF-CICIDS2018-v3.csv (4222783755 bytes)
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\FurtherInformation.txt (143 bytes)
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\manifest-sha1.txt (137 bytes)
f78acbaa2afe1595_NFV3DATA-A11964_A11964\f78acbaa2afe1595_NFV3DATA-A11964_A11964\tagmanifest-sha1.txt (164 bytes)
```

**NF-UNSW-NB15-v3** (`D:\NF-v3-datasets\f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964`)

```text
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\bag-info.txt (839 bytes)
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\bagit.txt (55 bytes)
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\data\NetFlow_v3_Features.csv (2935 bytes)
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\data\NF-UNSW-NB15-v3.csv (577360958 bytes)
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\FurtherInformation.txt (143 bytes)
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\manifest-sha1.txt (136 bytes)
f7546561558c07c5_NFV3DATA-A11964_A11964\f7546561558c07c5_NFV3DATA-A11964_A11964\tagmanifest-sha1.txt (164 bytes)
```


## Labels and attack-family values

### NF-CSE-CIC-IDS2018-v3

**Label**

| Exact value | Rows |
|---|---:|
| `0` | 17514626 |
| `1` | 2600903 |

**Attack family (Attack)**

| Exact value | Rows |
|---|---:|
| `Benign` | 17514626 |
| `Bot` | 207703 |
| `Brute_Force_-Web` | 1618 |
| `Brute_Force_-XSS` | 480 |
| `DDOS_attack-HOIC` | 1032311 |
| `DDOS_attack-LOIC-UDP` | 3450 |
| `DDoS_attacks-LOIC-HTTP` | 288589 |
| `DoS_attacks-GoldenEye` | 61300 |
| `DoS_attacks-Hulk` | 100076 |
| `DoS_attacks-SlowHTTPTest` | 105550 |
| `DoS_attacks-Slowloris` | 36040 |
| `FTP-BruteForce` | 386720 |
| `Infilteration` | 188152 |
| `SQL_Injection` | 440 |
| `SSH-Bruteforce` | 188474 |

### NF-UNSW-NB15-v3

**Label**

| Exact value | Rows |
|---|---:|
| `0` | 2237731 |
| `1` | 127693 |

**Attack family (Attack)**

| Exact value | Rows |
|---|---:|
| `Analysis` | 1226 |
| `Backdoor` | 4659 |
| `Benign` | 2237731 |
| `DoS` | 5980 |
| `Exploits` | 42748 |
| `Fuzzers` | 33816 |
| `Generic` | 19651 |
| `Reconnaissance` | 17074 |
| `Shellcode` | 2381 |
| `Worms` | 158 |

## Data quality and duplicate audit

| Dataset | Malformed-width rows | Exact duplicate rows beyond first | Duplicate 53-feature vectors beyond first |
|---|---:|---:|---:|
| NF-CSE-CIC-IDS2018-v3 | 0 | 628474 | 628914 |
| NF-UNSW-NB15-v3 | 0 | 14815 | 14815 |

Per-column empty values, explicit null markers, NaN, positive/negative infinity, invalid numeric values, negative finite numeric values, and finite ranges are tabulated in `schema.csv`. Only expected numeric features are checked for nonnumeric values; the IPv4 address features are treated as textual identifiers.

## Potential identifier, session, and time leakage fields

The feature schema includes source and destination IPv4 addresses, source and destination ports, flow start and end timestamps, and `DNS_QUERY_ID`. These can identify hosts/services, capture periods, or transactions and should be reviewed against the frozen methodology before any modeling. This report makes no modeling recommendation based on target values.

## Processing and reproducibility

The script uses Python's standard-library CSV reader and processes one record at a time. SHA-256 is streamed in 8 MiB blocks. Duplicate detection fingerprints parsed rows and the 53 feature values with SHA-256 and stores fingerprints in a temporary SQLite table on disk; the temporary table is deleted after a successful run. It does not load a dataset into RAM. The audit performed a full scan of every CSV; no row sampling was used.

Run from the repository root:

```powershell
python scripts/audit_nf_v3_datasets.py --root 'D:\NF-v3-datasets' --output 'reports/nf_v3_audit'
```

## Artifact guide

- `audit.json`: complete dataset, package, hash, schema, target-value and duplicate results.
- `schema.csv`: one row per observed column per dataset, with values-quality totals and leakage notes.
- `target_value_counts.csv`: exact value/count pairs for `Label` and `Attack`.
- `REPORT.md`: this human-readable summary.

The audit does not substitute datasets, change the research question, or modify the frozen `research_proposal.md` or `methodology_final.md`.
