# PROJECT HANDOFF — IntrusionDetection Reliability-Transportability Study

**Handoff date:** 2026-11-08  
**Repository:** ShreyasGautam01/IntrusionDetection  
**Active branch:** `codex/e0-e05`  
**Branch status at handoff:** 23 commits ahead of `main`, 0 behind  
**Frozen core documents:** `research_proposal.md`, `methodology_final.md` — DO NOT MODIFY without explicit owner approval.

## 1. Research objective

The project studies whether lightweight post-hoc reliability signals remain useful when a fixed network IDS is transferred from one network environment to another without target-domain adaptation or recalibration, especially under compound shift where the target contains attack families not represented in source training.

Central object: **the reliability layer**, not a new IDS architecture.

Primary detector: fixed Random Forest.  
Primary datasets: NF-UNSW-NB15-v3 and NF-CSE-CIC-IDS2018-v3.  
ToN-IoT-v3 is explicitly deferred and must NOT be added now.

Primary reliability signals:
1. calibrated model confidence;
2. Random Forest tree disagreement;
3. source-reference feature-space distance;
4. split conformal prediction;
5. Isolation Forest.

Primary security endpoint: **target attack-miss AUPRC**.  
Primary operational endpoint: **attack-miss capture at 5% review**, with 1% and 10% as additional budgets.

## 2. What is actually committed

The active branch `codex/e0-e05` contains the completed NF-v3 audit and E0/E0.5 preparation artifacts. In particular:

- `reports/nf_v3_audit/REPORT.md`
- `reports/nf_v3_audit/audit.json`
- `reports/nf_v3_audit/schema.csv`
- `reports/nf_v3_audit/target_value_counts.csv`
- `reports/nf_v3_audit/E0_STATUS.md`
- `reports/nf_v3_audit/E0_TEMPORAL_CONFLICT_REPORT.md`
- `reports/nf_v3_audit/E0_SOURCE_CONTROL_REPORT.md`
- `reports/nf_v3_audit/e0_results.json`
- `reports/nf_v3_audit/e0_source_controls.json`
- `reports/nf_v3_audit/feature/family/representation/primary-feature drafts`
- `reports/nf_v3_audit/SOURCE_E1_STAGE_REPORT.md`
- `reports/nf_v3_audit/source_e1_config.json`
- `reports/nf_v3_audit/source_e1_stage_report.json`
- `reports/nf_v3_audit/unsw_train_finite_replacements.json`
- `reports/nf_v3_audit/MEMORY_FEASIBILITY_DRAFT.md`
- `reports/nf_v3_audit/E1_STABILITY_GATE_DRAFT.md`
- `pilot_lock_draft.md`
- `rf_config_draft.json`
- `RF_CONFIG_DRAFT.md`
- `pyproject.toml`
- `uv.lock`
- `scripts/*` for audit, E0 controls, finite-value policy, source staging, feature/family drafts
- `src/ids_research/target_lockbox.py`
- `target_label_firewall.md`
- updated `research_worklog.md`

The branch also contains the runtime lock:
- Python 3.14.x
- NumPy 2.5.2
- pandas 3.0.6
- SciPy 1.18.1
- scikit-learn 1.9.1
- uv 0.11.19

These are committed in `pyproject.toml` and `uv.lock`. The local `.venv` is ignored and is not in Git.

## 3. Dataset audit facts already established

Downloaded NF-v3 files passed the package/hash audit.

CIC2018:
- 20,115,529 rows
- 55 columns: 53 features + Label + Attack
- SHA-256: `242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74`
- exact duplicate rows beyond first: 628,474
- duplicate 53-feature vectors beyond first: 628,914

UNSW:
- 2,365,424 rows
- 55 columns: 53 features + Label + Attack
- SHA-256: `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`
- exact duplicate rows beyond first: 14,815
- duplicate 53-feature vectors beyond first: 14,815

Important schema facts:
- supplied feature dictionary order differs from CSV order; implementation must construct canonical vectors by column name.
- UNSW has empty/+Inf values in:
  - `SRC_TO_DST_SECOND_BYTES`
  - `DST_TO_SRC_SECOND_BYTES`
- deterministic replacements are fitted from UNSW training rows only and applied unchanged at inference.
- identifier/time-like fields were explicitly reviewed; do not silently treat them as ordinary predictive variables.

CIC duplicate feature-vector label conflict checks, temporal coverage, attack episodes, exact boundary intersections, source controls, family inventory/crosswalk, and compact representation checks are committed as E0 artifacts.

## 4. E0/E0.5 status

E0/E0.5 preparation is substantially complete on GitHub.

The branch's `E0_STATUS.md` states that the following are generated:
- duplicate-vector label conflict analysis;
- temporal coverage and attack-episode summaries;
- draft feature registry;
- label-blind split design;
- source-only finite/non-finite handling;
- exact feature-vector intersection checks;
- family inventory and conservative crosswalk;
- compact 8-feature mapping draft;
- source temporal/host/session controls;
- source E1 staging.

However, **the project is NOT yet experiment-locked**. Review/freeze decisions remain.

## 5. Source E1 staging already completed

UNSW source arrays were staged locally under ignored `data/processed/source-e1-lock-1`.

Rows:
- Train: 1,418,952
- Calibration: 473,301
- Source test: 473,171

Feature matrix:
- 46 proposed primary columns
- float32

The raw dataset was not modified.

The staged arrays and hashes are summarized in:
- `reports/nf_v3_audit/SOURCE_E1_STAGE_REPORT.md`
- `reports/nf_v3_audit/source_e1_stage_report.json`

## 6. CRITICAL: what did NOT happen

The frozen Random Forest five-signal study is **NOT complete**.

Before this handoff, no final target-transfer experiment was evidenced in GitHub.

More specifically:
- no frozen pilot lock was committed;
- no source-only E1 stability gate was completed;
- no final Random Forest reliability scores were produced;
- no CIC2018 target scoring was performed;
- no target labels were unlocked;
- no UNSW→CIC2018 transfer metrics exist;
- no CIC2018→UNSW transfer metrics exist;
- no compound-shift results exist;
- no final review-budget results exist;
- no family-level transfer results exist;
- no 8-feature sensitivity results exist.

The prior Codex session then ran a **source-only UNSW Random Forest pilot** after the user explicitly authorized proceeding despite the memory concern. It completed seeds **0–5** locally. Seeds 6–9 were not started. The Codex session ran out of usage while attempting to consolidate those results and write this handoff.

Therefore, **do not claim seeds 0–5 are committed or complete unless the next Codex verifies them locally.** GitHub currently contains no committed seed-result files from that interrupted run.

## 7. Exact resume point

Resume from:

> **Verify and recover the local source-only seed 0–5 results, then commit useful source-only evidence and consolidate the handoff. Do not start any target evaluation yet.**

First inspect the local working tree rather than rerunning anything.

Recommended commands from `D:/IntrusionDetection`:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -20
git remote -v
git rev-parse HEAD
git rev-parse origin/codex/e0-e05
```

Then inspect likely result directories:

```powershell
Get-ChildItem -Recurse -File . | Where-Object {
  $_.FullName -match 'result|results|seed|e1|pilot|metric'
} | Select-Object FullName,Length,LastWriteTime
```

Also inspect ignored local artifacts:

```powershell
git status --ignored --short
Get-ChildItem data/processed/source-e1-lock-1 -Force
```

Find recently modified files:

```powershell
Get-ChildItem -Recurse -File | Sort-Object LastWriteTime -Descending |
  Select-Object -First 100 FullName,Length,LastWriteTime
```

Do NOT delete local result directories until their provenance is understood.

## 8. What to verify about seeds 0–5

The interrupted Codex reported:
- seed 0 completed;
- seed 1 completed;
- seed 2 completed;
- seeds 3–5 completed after the parallel-worker cleanup;
- seeds 6–9 were never launched;
- no target data was used;
- the Random Forest was 200 trees;
- seed 0 fit took about 226 seconds;
- process memory stayed around 0.55 GiB;
- the source split was the staged UNSW split.

These claims must be verified from actual files/logs, not trusted merely because they appeared in chat.

For each seed found locally, verify:
- seed identifier;
- input/config hash;
- feature count/order;
- train/calibration/test hashes or row counts;
- model parameters;
- source-test predictions;
- calibrated probabilities if produced;
- all five reliability scores if produced;
- source-test metrics;
- runtime;
- software/runtime versions;
- whether any target file was opened.

If complete and reproducible enough, commit the **small result summaries and provenance**, not huge model binaries or raw arrays unless explicitly necessary.

## 9. Do NOT let the next Codex repeat the earlier process problem

The project owner wants implementation to proceed efficiently.

Do not spend another long session producing review drafts that merely restate already-known gates.

The remaining review decisions should be handled minimally and concretely:

1. approve/freeze the 46-feature primary set;
2. approve/freeze RF parameters and seeds;
3. decide the source-only stability rule;
4. freeze the compact 8-feature mapping;
5. create one machine-readable freeze manifest;
6. run source-only E1;
7. only after E1 passes, unlock target scoring.

If a methodological choice is genuinely ambiguous, surface it in one short decision record rather than generating multiple speculative drafts.

## 10. Target-label firewall

Never open or inspect target `Label`/`Attack` during model fitting, preprocessing, feature selection, calibration, seed selection, or configuration selection.

`src/ids_research/target_lockbox.py` and `target_label_firewall.md` are intended to enforce this.

Do not weaken the firewall to make implementation easier.

## 11. Frozen-doc policy

Do not modify:
- `research_proposal.md`
- `methodology_final.md`

unless a substantive error is discovered that would invalidate the experiment. If such an error is found, stop and report it to the project owner before changing the frozen document.

Normal implementation changes belong in working files and a change log.

## 12. Scope policy

Active study:
- UNSW-v3
- CIC2018-v3

Deferred:
- ToN-IoT-v3
- BoT-IoT-v3
- XGBoost robustness

Do not expand scope until the core RF study is completed and stable.

## 13. Expected next milestones

### M1 — Recover/verify seeds 0–5
No new training unless a missing/corrupt result requires it.

### M2 — Commit source-only evidence
Commit concise metrics/provenance and update `research_worklog.md`.

### M3 — Freeze experiment manifest
Bind:
- dataset hashes;
- feature registry hash;
- split definition;
- finite-value policy;
- RF configuration;
- reliability definitions;
- seeds;
- software lock.

### M4 — Complete source-only E1
Run all declared seeds, one at a time or in carefully controlled parallelism according to available RAM. Preserve every result.

### M5 — Target transfer
Only after the source-only gate is accepted:
- UNSW→CIC2018;
- CIC2018→UNSW;
- standard transfer;
- compound-shift analysis;
- attack-miss AUPRC;
- review budgets;
- family-level analysis.

### M6 — Representation sensitivity
Run the compact 8-feature analysis only after the core result is stable.

## 14. Interpretation discipline

The study is not designed to prove one signal wins.

Potential valid outcomes include:
- all signals degrade under transfer;
- confidence is strong in-domain but unstable under shift;
- distance is sensitive to representation;
- conformal prediction retains coverage but does not prioritize attack misses;
- Isolation Forest detects novelty without ranking dangerous false negatives well;
- different signals win in different domains/families.

Do not turn any outcome into a novelty claim until compared with the latest literature.

## 15. Current GitHub state

At handoff, `codex/e0-e05` is ahead of `main` by 23 commits and behind by 0. The default branch `main` intentionally does not contain these working E0/E0.5 artifacts.

The active branch is the correct continuation point. Do not merge it into `main` merely to continue experimentation.

## 16. Definition of “done” for the next Codex session

The next session should end with one of these states:

**Preferred:** seeds 0–5 are recovered and verified, their useful summaries are committed, and the exact next experiment step is documented.

**Also acceptable:** if the local results are missing/corrupt, report exactly what is missing and run only the minimum necessary source-only recovery.

**Not acceptable:** starting target evaluation, changing frozen methodology, adding ToN-IoT, or generating another large batch of drafts without completing the actual source-only experiment.

