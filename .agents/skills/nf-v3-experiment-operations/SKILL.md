---
name: nf-v3-experiment-operations
description: Safely inspect, resume, and monitor the NF-v3 source and transfer experiments, preserving completed outputs and per-seed checkpoints.
---

# NF-v3 experiment operations

Use this skill to launch or resume a frozen run, monitor a long computation, or recover after an interruption.

## Before starting or resuming

1. Read `AGENTS.md` and the applicable committed experiment manifest/configuration.
2. Run the research status helper and inspect the direction’s progress JSON, runner log/terminal, and output directory.
3. Check for an active process before launch. On Windows, query `Win32_Process` for the exact runner command line. If access is denied, use process CPU/RAM/start time, runner output, and checkpoint timestamps; report the process identity as uncertain and do not start a duplicate.
4. Verify the manifest is committed and clean and that frozen inputs match the current run. Never repair a provenance mismatch by editing the frozen manifest in place.

## Transfer scoring

The existing runner processes the frozen seed list sequentially, verifies and skips completed seeds, and commits the progress JSON after each seed. Start it once and leave that process running through seed 9:

```powershell
uv run python scripts/score_target_transfer.py `
  --direction unsw-to-cic `
  --manifest reports/nf_v3_audit/target_transfer_manifest_unsw_to_cic.json `
  --batch-size 8192
```

Use the matching direction manifest for CIC → UNSW. Do not launch one command per seed or rerun completed seeds blindly. If the process exits, inspect the committed checkpoint, per-seed hashes, partial directory, and logs before resuming. Preserve partial artifacts unless the runner proves them corrupt or incompatible.

Monitor progress with:

```powershell
Get-Content reports/nf_v3_audit/target_transfer_progress_unsw_to_cic.json -Raw |
  ConvertFrom-Json |
  Select-Object direction,last_completed_seed,target_labels_read,completed_utc

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*score_target_transfer.py*' } |
  Select-Object ProcessId,CommandLine
```

If process inspection is denied, do not describe the job as inactive; report the checkpoint and latest runner evidence separately.

## Checkpoints and safety

- The transfer runner commits its own progress after each completed seed. Do not create a competing checkpoint commit while it runs.
- Keep the tracked worktree clean while an auto-checkpointing runner is active; it refuses to checkpoint over unrelated tracked changes.
- For manually published evidence, validate the report, stage only the named evidence files, and confirm no data, score arrays, logs, caches, or model objects are staged.
- Do not invoke target-label evaluation until both source gates are accepted and the committed manifests validate. Feature-only scoring must retain `target_labels_read: false`.
- Do not change frozen methodology/proposal, use target labels for model or method selection, or expand the study scope.
