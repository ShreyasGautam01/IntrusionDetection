# CIC RF execution-equivalence decision

**Production RF fit execution: `n_jobs=10`.** This is an execution parameter only; the frozen scientific RF definition remains unchanged, including configured `n_jobs=1`. Prediction threads remain 1, with BLAS/OpenMP at 1.

The bounded, deterministic CIC source benchmark showed exact equality to the v1 `n_jobs=1` reference for tree structure, RF probabilities, and disagreement for candidates 6, 8, 10, 12, 14, and 16. The selected candidate 10 took 17.64 seconds, retained 2.87 GB minimum available RAM, and used 69.8% mean / 84.5% peak system CPU. Candidate 12 was only marginally faster; 14 and 16 approached full CPU saturation for small additional gains, so 10 is the operational choice.

The full source E1 exact-verification gate remains mandatory before each seed's target scoring. Target labels were not read by these benchmarks. Evidence is recorded in `cic_rf_n_jobs_production_execution_evidence_v2.json` and the versioned bounded reports. No scientific manifest was changed.
