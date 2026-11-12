# Exact target feature-distance benchmark decision

**Decision:** retain the frozen exact duplicate-compressed, chunked 5-NN definition for both transfer directions. Bounded measurements support a long, sequential single-job computation on this machine. No reference-bank approximation or distance-definition change is selected.

Both benchmarks used the first contiguous 40,000 target feature rows, source reference prefixes up to 1,000,000 rows, 500,000-row reference chunks, 2,048-query batches, one nearest-neighbor worker, and BLAS/OpenMP thread limits of one. The input target file was byte-hashed for identity, while only the frozen 46 predictors were parsed; target labels were not selected or used. Reports bind code commit `333f920be21f714499dbad4c6543f7d2a2aa841c` and SHA-256 hashes of the benchmark and distance implementation files.

| Direction | Full target rows | Source train rows | Bounded trial range | Largest-case throughput | Peak working set | Exact-distance projection |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| CIC → UNSW | 2,365,424 | 12,068,590 | 100k–1m references; 2.5k–40k queries | 1,068 queries/s | 496,435,200 bytes | 34,097–58,139 s (9.47–16.15 h) |
| UNSW → CIC | 20,115,529 | 1,418,952 | 100k–1m references; 2.5k–40k queries | 2,349 queries/s | 517,234,688 bytes | 19,346–36,690 s (5.37–10.19 h) |

The projections use the measured per-reference-chunk wall time multiplied by the full target query-row count and full source reference-chunk count. Across both directions, the projected exact distance work is about 14.85–26.34 hours when run sequentially. These are distance-only estimates; target feature parsing and RF/Isolation Forest inference are separate. CPU use stayed near one core (about 6% of the 16 logical-CPU capacity). The CIC-source benchmark reused the hash-verified source StandardScaler cache; the scaler's parameters match the source E1 distance provenance. The measured distance process stayed below 0.5 GiB working set in both reports, with about 8.05 GB of system memory available after the runs.

The implementation sorts each reference chunk into unique feature rows, retains integer multiplicities, queries an exact Euclidean KDTree, and merges the exact top-five distances with multiplicities. This preserves the original reference multiset's five-neighbor result, including duplicate rows. The bounded benchmarks check finite outputs at each tested size; they do not claim full-run validation. Full target distance remains gated on committed direction manifests, an inference benchmark, and confirming disk capacity for resumable outputs.

Evidence:

- [`target_exact_distance_benchmark_cic_to_unsw.json`](target_exact_distance_benchmark_cic_to_unsw.json)
- [`target_exact_distance_benchmark_unsw_to_cic.json`](target_exact_distance_benchmark_unsw_to_cic.json)
