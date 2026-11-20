# Reproduction and environment guide

**Status:** Completed-study archive  
**Authoritative branch:** `codex/e0-e05`  
**Last updated:** 2026-11-21

This file documents how to reproduce or verify the completed NetFlow-v3 transfer study. It deliberately separates **archive verification** from a **full computational rerun**: the repository contains the code, frozen study definition, manifests, compact results, figures, and provenance records, but raw datasets and large generated arrays are intentionally kept outside Git.

## 1. Study scope and authoritative records

The completed study covers:

- `NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3`
- both transfer directions: `UNSW → CIC2018` and `CIC2018 → UNSW`
- the frozen 46-predictor representation
- seeds `0–9` (ten matched seeds)
- five reliability signals:
  `confidence`, `random_forest_disagreement`, `feature_space_distance`,
  `split_conformal`, and `isolation_forest`
- attack-miss AUPRC as the primary endpoint
- attack-miss capture at a 5% analyst-review budget as the primary operational endpoint

The following records are authoritative for the archived experiment and should be preferred over reconstructing settings from narrative documents:

- `research_proposal.md` — frozen study definition
- `methodology_final.md` — frozen methodology
- `reports/nf_v3_audit/target_transfer_manifest_unsw_to_cic.json`
- `reports/nf_v3_audit/target_transfer_manifest_cic_to_unsw.json`
- `reports/nf_v3_audit/RESEARCH_ARTIFACT_MANIFEST.json`
- `reports/nf_v3_audit/FINAL_ANALYSIS_AUDIT.json`
- `reports/nf_v3_audit/FINAL_TRANSFER_ANALYSIS_REPORT.md`
- `reports/nf_v3_audit/README.md`

`reports/nf_v3_audit/analysis_completion_summary.json` records the completed 13-phase post-transfer analysis and its integrity status.

The historical `analysis_base_commit` recorded in the artifact manifest identifies the commit at which the completed analysis archive was based; it is not intended to be treated as the current branch tip.

## 2. Recreate the locked software environment

The project environment is declared in `pyproject.toml` and fully resolved in `uv.lock`.

Locked requirements:

- Python `>=3.14,<3.15` (the completed run used CPython `3.14.7`)
- `uv==0.11.19`
- NumPy `2.5.2`
- pandas `3.0.6`
- scikit-learn `1.9.1`

From a fresh checkout:

```powershell
uv sync --locked
```

The lockfile is the dependency authority. Do not replace it with an independently resolved environment when attempting an exact reproduction.

A minimal environment check is:

```powershell
uv run python -c "import sys, numpy, pandas, sklearn; print(sys.version); print('numpy', numpy.__version__); print('pandas', pandas.__version__); print('scikit-learn', sklearn.__version__)"
```

The completed study was executed on Windows. The lockfile and the committed manifests should remain the source of truth for the exact runtime.

## 3. Obtain the exact raw datasets

Raw data is intentionally not committed.

The active dataset provenance is documented in `dataset_source_manifest.md`. The exact download endpoints used for the active pair are:

- NF-UNSW-NB15-v3: `https://rdm.uq.edu.au/files/abd2f5d8-e268-4ff0-84fb-f2f7b3ca3e8f`
- NF-CSE-CIC-IDS2018-v3: `https://rdm.uq.edu.au/files/4ac221b1-6bd6-42b1-bdf7-03f4fc7efb22`

The completed transfer manifests bind the dataset bytes to these SHA-256 values:

| Dataset | SHA-256 | Rows |
|---|---|---:|
| NF-UNSW-NB15-v3 | `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5` | 2,365,424 |
| NF-CSE-CIC-IDS2018-v3 | `242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74` | 20,115,529 |

Before using a downloaded file, verify its SHA-256 against the committed direction manifests. A file with a different hash is not the locked dataset release for this study.

Raw datasets must remain read-only and must not be committed to Git.

## 4. Reproduce the frozen data/model definition

The direction manifests are the operational specification. In particular, they bind:

- the ordered 46-feature predictor matrix;
- source-train-only finite-value replacement;
- source-only fitting and calibration;
- the two binary transfer directions;
- the ten seeds;
- the Random Forest configuration;
- the five reliability signals;
- the exact 5-nearest-neighbour feature-space distance definition;
- the target batch bound;
- code, software-lock, feature-registry, and family-registry hashes.

The model is a `sklearn.ensemble.RandomForestClassifier` with 200 trees and `min_samples_leaf=5`; the remaining locked parameters should be taken from the committed transfer manifests rather than manually re-entered.

Target labels are sealed from fitting, tuning, recalibration, threshold selection, and score construction. The target-label firewall is implemented in `src/ids_research/target_lockbox.py`.

## 5. Verify the frozen transfer manifests

After the required local data/staged artifacts are available, validate each committed direction manifest before any target-label evaluation:

```powershell
uv run python scripts/validate_transfer_manifests.py --direction unsw-to-cic
uv run python scripts/validate_transfer_manifests.py --direction cic-to-unsw
```

A successful validation confirms that the current checkout still satisfies the manifest bindings required by the transfer pipeline.

Do not substitute an uncommitted or modified manifest.

## 6. Full computational rerun

A full rerun is substantially larger than the Git repository because it requires:

- both raw datasets;
- the locked source-stage arrays and manifests;
- source E1 model outputs;
- disk-backed exact feature-distance artifacts;
- per-seed target score arrays;
- checkpoints and local intermediate data.

These large artifacts are deliberately ignored by Git. The committed manifests and inventories identify their expected paths, shapes, and SHA-256 values.

The production target-scoring entry point is:

```powershell
uv run python scripts/score_target_transfer.py --direction unsw-to-cic --manifest reports/nf_v3_audit/target_transfer_manifest_unsw_to_cic.json
uv run python scripts/score_target_transfer.py --direction cic-to-unsw --manifest reports/nf_v3_audit/target_transfer_manifest_cic_to_unsw.json
```

A full rerun should only be attempted with the exact committed manifests and locked environment. Do not use target labels to decide parameters while reconstructing the run.

## 7. Reproduce the completed post-transfer analysis

The completed transfer scores and target evaluations were already produced before the analysis archive was assembled. The analysis stage does **not** fit the Random Forest again, recompute the transfer scores, or recompute the exact feature-distance arrays.

The analysis runner is:

```powershell
uv run python scripts/run_complete_transfer_analysis.py --resume
```

Its `--resume` mode works from the saved checkpoint/output state under `reports/nf_v3_audit/`. It validates the committed transfer manifests and then performs the documented offline evaluation/analysis phases.

Important: this command is an **analysis execution that reads target labels for offline evaluation**. It is therefore appropriate for intentionally reproducing the analysis from the required local artifacts, but it should not be run merely to inspect the already-archived results.

The completed archive records all 13 phases:

1. inventory
2. primary metrics
3. paired statistics
4. direction shift
5. family analysis
6. generic error
7. selective risk
8. calibration/conformal diagnostics
9. computational cost
10. plots
11. integrated report
12. integrity audit
13. experiment decision

The final integrity record is:

`reports/nf_v3_audit/FINAL_ANALYSIS_AUDIT.json`

It records:

- `pass: true`
- no integrity issues
- target labels not used for fitting
- target labels not used for tuning
- target labels not used for recalibration
- target labels not used for score construction
- no transfer-scoring rerun during analysis

## 8. Where to inspect the reproducible outputs

The compact committed analysis record is under:

`reports/nf_v3_audit/`

Start with:

1. `README.md`
2. `FINAL_TRANSFER_ANALYSIS_REPORT.md`
3. `analysis_per_seed_all_metrics.csv`
4. `analysis_aggregate.csv`
5. `analysis_paired_statistics.csv`
6. `analysis_direction_shift.csv`
7. `analysis_family_results.csv`
8. `analysis_generic_error.csv`
9. `analysis_selective_results.csv`
10. `analysis_calibration_conformal.csv`
11. `analysis_computational_cost.md`
12. `FINAL_ANALYSIS_AUDIT.json`
13. `RESEARCH_ARTIFACT_MANIFEST.json`

The five committed figures are under:

`reports/nf_v3_audit/analysis_figures/`

Large per-row score arrays, source-stage arrays, model caches, and checkpoints are not committed; their provenance is preserved in the transfer manifests and artifact inventories.

## 9. What the archived results establish

The completed analysis is descriptive for this two-dataset, ten-seed study. Performance is direction-dependent; the archive does not claim a universal best reliability signal.

The supported cross-domain family mapping is limited to the documented shared `DoS` category. The analysis does not infer broader unseen-family equivalence from dataset-local attack names.

The archive does not activate:

- NF-ToN-IoT-v3
- XGBoost
- the deferred compact 8-feature sensitivity

Those are outside the completed frozen scope.

## 10. Reproducibility and integrity rules

For any future rerun or extension:

- keep `research_proposal.md` and `methodology_final.md` unchanged unless the project owner explicitly authorizes a substantive methodological change;
- preserve raw datasets as read-only inputs;
- verify dataset SHA-256 values before use;
- use `uv.lock` rather than silently upgrading dependencies;
- use the committed transfer manifests as the experiment lock;
- preserve target-label isolation until the evaluation stage;
- never overwrite previous scientific results silently;
- do not commit raw datasets, large numerical arrays, checkpoints, or local caches.

The repository is therefore reproducible at the level of **study definition, code, environment lock, manifests, compact results, figures, and provenance**, while exact rerunning of the heavy computation additionally requires the excluded local datasets and large generated numerical artifacts.
