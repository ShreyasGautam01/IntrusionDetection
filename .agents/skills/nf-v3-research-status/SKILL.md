---
name: nf-v3-research-status
description: Check the NF-v3 repository, frozen-document state, source-gate reports, ignored experiment outputs, and transfer seed checkpoints without touching research data.
---

# NF-v3 research status

Use this skill when asked what is committed, what is running, or how far the NF-v3 study has progressed.

## Workflow

1. From the repository root, run `uv run python scripts/research_status.py`.
2. Report the branch, HEAD, worktree state, cached upstream relation, frozen-document state, source E1 report counts, transfer checkpoint seeds, and ignored output presence.
3. Treat process state `unknown` or `unavailable` as unknown. Do not infer that a job stopped when Windows process inspection is denied.
4. The helper reads checkpoint/report JSON and directory metadata only. It does not open raw target files, score arrays, model objects, or target labels, and it does not verify artifact hashes.
5. For seed-level scientific verification, use the project verifier or the run manifest; do not equate a directory’s presence with a verified seed.

## Guardrails

- Do not fetch, clean, reset, or alter the branch during a status check.
- Keep `research_proposal.md` and `methodology_final.md` unchanged.
- Keep ignored datasets and run artifacts local and untouched.
- Preserve the explicit `target_labels_read` state from the checkpoint report; status checks must not access labels.
