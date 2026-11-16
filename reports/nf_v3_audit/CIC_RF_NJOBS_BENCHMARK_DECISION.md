# CIC RF `n_jobs` Equivalence and Execution Decision

Benchmark report SHA-256: `5ab5d92cb7fd9229da9bd2058286aba4885cd2bf5e1d1036bdd6df88c61f0b16`.
Source dataset SHA-256: `242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74`.
Source stage SHA-256: `a0c3e3f618f35c5bbed7ad1fb3b252f06f215b2146a79aa511b9574f4f414665`.

| RF fit `n_jobs` | Sample fit seconds | Peak process-tree working set | Minimum free physical RAM | Mean machine CPU utilization | Tree / probability / disagreement exact |
|---:|---:|---:|---:|---:|:---|
| 1 | 63.26 | 1.14 GB | 4.62 GB | 6.6% | True / True / True |
| 2 | 36.40 | 1.15 GB | 4.64 GB | 12.7% | True / True / True |
| 4 | 23.07 | 1.17 GB | 4.78 GB | 25.2% | True / True / True |

Selected fit setting: **`n_jobs=4`** (2.74× sampled speedup; 4.78 GB minimum free RAM).

The selection required identical tree structures, probabilities, and RF disagreement, finite outputs, at least 2 GB free system RAM, and at least 1.20× speedup for any parallel setting. The frozen RF configuration remains `n_jobs=1`; the selected value is recorded as an execution-only fit override. Serialized models use `n_jobs=1` for prediction. Every full-seed refit must still reproduce that seed's source E1 test arrays exactly before target scoring.

Observed seed-1 full-source fit: 16407.478613200015 seconds. Using the bounded measured speedup as a projection gives about 1.66 hours for one parallel full-source fit; this is an estimate, not a guarantee.

Target files and labels were not read by the benchmark. `target_labels_read` is false.
