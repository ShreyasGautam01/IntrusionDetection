# Computational-cost synthesis

## Production RF execution decision

The frozen scientific model remains unchanged. RF `n_jobs` was treated as an
execution parameter and benchmarked for deterministic equivalence.

Measured bounded CIC RF benchmark:

| n_jobs | Fit time | Min free RAM | Mean CPU | Peak CPU |
|---:|---:|---:|---:|---:|
| 10 | 17.64 s | 2.87 GB | 69.8% | 84.5% |
| 12 | 17.52 s | 3.14 GB | 83.3% | 97.9% |
| 14 | 17.24 s | 3.13 GB | 97.0% | 100% |
| 16 | 16.50 s | 2.71 GB | 97.6% | 100% |

All tested settings were exactly equivalent to the `n_jobs=1` reference on
tree structure, RF probabilities, and RF disagreement. `n_jobs=10` was selected
because higher values offered only marginal additional speed while materially
increasing system CPU saturation.

## Additional transfer computation

No new training, transfer scoring, or distance computation is performed by
this analysis pipeline. This report is therefore a synthesis of the already
completed computational experiment rather than a new benchmark.
