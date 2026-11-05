# Codex Research Execution Rules

## Scope

This repository contains the research project:
"Evaluating the Transportability of Lightweight Reliability Signals in Network Intrusion Detection under Compound Distribution Shift."

## Frozen core documents

Do not modify these files during ordinary implementation or experimentation:

- research_proposal.md
- methodology_final.md

A change to either file requires a substantive-error rationale and explicit confirmation from the project owner.

## Dataset rules

Raw datasets may be available locally under:

- data/raw/

These files are intentionally ignored by Git.

Never:

- commit raw datasets;
- upload raw dataset files to GitHub;
- modify original dataset files in place;
- delete raw data automatically;
- silently rename or replace a dataset release.

Treat raw datasets as read-only inputs.

## First task: dataset audit

Before modeling, implement and run a reproducible audit that produces small text/JSON/CSV artifacts, including:

- SHA-256 file hashes;
- file names and sizes;
- schema and column order;
- row counts;
- data types;
- missing/NaN/Inf counts;
- unique values for label columns;
- binary benign/attack counts;
- attack-family counts;
- duplicate statistics;
- temporal metadata where available.

Do not infer or alter labels.

## Label mapping

Do not force attack-family equivalence across datasets.

Produce a draft mapping artifact and mark ambiguous mappings explicitly.

Binary attack/benign is the primary cross-domain task.

## Target-label firewall

When building the later experimental pipeline:

- scoring/model construction must not read target labels;
- target labels must be accessible only to evaluation code;
- no target-derived preprocessing, thresholds, calibration, sampling, or hyperparameter selection.

Architect the code so this rule is enforceable rather than relying only on comments.

## Dataset handling

Use chunked reads for large files.

Prefer lazy/streaming processing where practical.

Never load the entire largest dataset into memory merely because it is possible.

All deterministic samples must have recorded seeds and membership hashes.

## Safety

Do not perform:

- network scanning;
- exploitation;
- credential testing;
- traffic generation against external systems;
- interaction with third-party network hosts.

This is an offline benchmark-data research project.

## Reproducibility

Every generated audit or experiment artifact must record:

- date/time;
- Git commit;
- dataset file hash;
- configuration identifier;
- software/environment version where practical.

Never silently overwrite previous scientific results.

## Git

Commit code, configuration, documentation, manifests, audits, and small summaries.

Do not commit:

- raw datasets;
- large generated arrays;
- checkpoints;
- temporary caches.

## Working style

Before making a broad implementation change, inspect the current repository state and relevant documentation.

Prefer small, reviewable commits.

If an implementation detail appears to contradict the frozen methodology, stop and document the issue rather than silently changing the methodology.
