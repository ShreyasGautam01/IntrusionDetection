---
name: nf-v3-transfer-manifest-audit
description: Run the strict NF-v3 transfer-lock validation before target scoring or label evaluation and explain failures without weakening the lock.
---

# NF-v3 transfer manifest audit

Use this skill when asked whether transfer manifests are valid, current, committed, or safe to use.

Run the read-only validator from the repository root:

```powershell
uv run python scripts/validate_transfer_manifests.py
```

The validator delegates to `ids_research.target_lockbox.validate_both_transfer_manifests`, which requires both core direction manifests and checks their commit ancestry, clean state, direction, inputs, configuration, feature/family registries, source-gate evidence, code hashes, and software lock. It prints the validated manifest hashes and lock commit. A nonzero exit means scoring/evaluation must stop until the cause is understood and corrected through a new reviewed checkpoint.

Validation streams the raw source and target files to verify their byte hashes. It does not parse target rows or read target labels. Because those full-file hashes can take time, use the validator at a gate or before a new run, not for routine progress polling; the scorer also validates its locks before scoring.

Never bypass a failed check, rewrite a frozen manifest to fit changed inputs, access target labels before both locks validate, or treat a draft/uncommitted manifest as authorization to evaluate.
