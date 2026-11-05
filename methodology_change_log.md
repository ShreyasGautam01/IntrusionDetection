# Methodology Change-Control Log

This document records proposed or observed changes that may affect the research methodology.

## Policy

`research_proposal.md` and `methodology_final.md` are frozen core documents.

No ordinary refinement is applied directly to them.

A potential change is recorded here first.

A change may be promoted to a frozen document only when:

1. it fixes a substantive error or contradiction;
2. the reason is documented;
3. the user explicitly confirms the change.

## 2026-11-05 — Dataset taxonomy constraint

### Observation

The primary NetFlow-v3 datasets do not use identical attack-family taxonomies.

### Consequence

The experiment must not assume a one-to-one family mapping for the primary UNSW↔CIC transfer.

### Current action

No frozen core document changed.

Working documents updated:

- `dataset_selection.md`
- `dataset_source_manifest.md`
- `label_mapping_draft.md`

### Severity

**Methodological constraint, not currently a core-document error.**

The current methodology already states that family mapping must be defensible and that binary detection is the primary task.

### Promotion status

No change proposed to frozen methodology.
