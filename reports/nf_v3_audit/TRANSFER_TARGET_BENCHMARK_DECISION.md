# Target transfer benchmark and resource decision

**Decision:** keep the exact duplicate-compressed, chunked 5-NN distance and run the two transfer directions sequentially with one worker and one BLAS/OpenMP thread. Bounded timing supports the existing exact method; no approximation is selected. Target labels were not parsed or used in either inference benchmark or either five-signal smoke.

## Bounded target inference

Both inference benchmarks used the first 40,000 target rows, parsed only the frozen 46 predictors, and verified the source model against its source E1 outputs before scoring. The CIC-source refit took 7,519.99 seconds (125.3 minutes), about 17% slower than the earlier 6,431-second observation; its RF and Isolation Forest runs stayed at one worker/thread. The UNSW-source refit took 208.25 seconds. Seed-0 model caches are hash-verified and will be reused, so the 10-seed projections below count nine additional source fits per direction.

| Direction | Target rows | Target inference, all 10 seeds | RF fit per seed | RF fit peak working set | Full-target inference projection |
| --- | ---: | ---: | ---: | ---: | ---: |
| UNSW → CIC | 20,115,529 | 5,535 s (1.54 h) | 208 s | 607,154,176 B | 36,343 combined rows/s on the bounded sample |
| CIC → UNSW | 2,365,424 | 784 s (13.1 min) | 7,520 s | 4,343,848,960 B | 30,152 combined rows/s on the bounded sample |

The CIC-source Isolation Forest fit peaked at 4,548,501,504 bytes working set; this is the highest observed process peak. Target inference peaked at 1,337,589,760 bytes with the large CIC model resident. The CIC model cache is 1,208,567,339 bytes; the UNSW model cache is 3,662,110 bytes. The CIC source E1 comparison matched prediction, calibrated probability, RF disagreement, and Isolation Forest exactly for all 4,025,148 source-test rows. UNSW matched the same four outputs for all 473,171 source-test rows.

The CIC source E1 comparison took about seven minutes by event timestamps; the benchmark process did not instrument that interval separately. The remaining-run projection uses that observed time for the nine remaining CIC seeds, and scales it by source-test row count for UNSW as a rough estimate. Per-seed transfer records will capture verification timing during scoring.

## Exact feature-distance work

The distance definition remains the mean Euclidean distance to the five nearest original source-training rows after a scaler fit on source training only. Per-chunk unique-row compression retains integer multiplicities; exact top-five merging preserves duplicate rows and their effect on the original 5-NN result.

| Direction | Full source references | Full target queries | Measured exact-distance projection | Peak working set |
| --- | ---: | ---: | ---: | ---: |
| UNSW → CIC | 1,418,952 | 20,115,529 | 19,346–36,690 s (5.37–10.19 h) | 517,234,688 B |
| CIC → UNSW | 12,068,590 | 2,365,424 | 34,097–58,139 s (9.47–16.15 h) | 496,435,200 B |

Each bounded trial used 40,000 target queries, up to 1,000,000 source references, 500,000-row reference chunks, and 2,048-query batches. The exact distance is source-direction dependent and RF-seed independent; it will be computed once per direction and shared across seeds.

## Full-run and disk estimate

After the benchmarks and seed-0 caches already completed, the estimated remaining feature-only scoring work is about **37.2–48.7 hours sequentially**. This combines the measured exact-distance projections, 40,000-row inference and parsing rates, nine remaining RF/Isolation Forest fits per direction, and the source-verification estimate above. It excludes dataset hashing, final target-label evaluation, and variability in the other seeds' fit times; it is a planning range, not a deadline.

The output plan accounts for the 46-column target matrix, exact 5-NN distance/count state, final distance, and five disk-backed score arrays for each of ten seeds. It now estimates remaining model-cache space from the measured seed-0 model size with a 25% margin:

| Direction | Output arrays/state | Remaining model-cache reserve | Extra headroom | Required free space | D: free at check |
| --- | ---: | ---: | ---: | ---: | ---: |
| UNSW → CIC | 10.22 GB | 0.041 GB | 2.00 GB | 14.30 GB | 130.87 GB |
| CIC → UNSW | 1.20 GB | 13.60 GB | 2.00 GB | 17.04 GB | 130.87 GB |

The second direction's larger model reserve reflects the measured 1.21 GB CIC seed-0 RF cache. The earlier fixed 2 GB cache reserve was too low and has been replaced before full scoring.

## Frozen signals and factorization

- **Confidence:** `1 - max(calibrated class probabilities)`.
- **RF disagreement:** one minus the largest class vote fraction across the RF trees.
- **Feature-space distance:** exact mean distance to the five nearest source-training rows, shared once per source direction.
- **Split conformal:** prediction-set size minus one, using the source-fitted calibrator and disjoint source conformal subset/quantile.
- **Isolation Forest:** negative `score_samples`; fitted once per configured seed on source training.

Confidence and split conformal depend on the RF seed and source-fitted calibration; RF disagreement depends on the RF seed. Distance is independent of RF seed and is shared per direction. Isolation Forest depends on its configured seed and source training, so it is fit once for each configured seed. No additional random source was introduced.

Concurrency is fixed at one RF worker, one Isolation Forest worker, and one BLAS/OpenMP thread. All bounded inference and five-signal smoke reports record `target_labels_read: false` and their report hashes are bound by the upcoming committed direction manifests.

Evidence: [UNSW→CIC inference JSON](target_inference_benchmark_unsw_to_cic_seed0.json), [CIC→UNSW inference JSON](target_inference_benchmark_cic_to_unsw_seed0.json), [exact-distance benchmark decision](TRANSFER_EXACT_DISTANCE_BENCHMARK_DECISION.md), [CIC→UNSW smoke](target_transfer_smoke_cic_to_unsw.json), and [UNSW→CIC smoke](target_transfer_smoke_unsw_to_cic_v2.json).
