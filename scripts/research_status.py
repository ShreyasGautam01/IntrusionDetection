#!/usr/bin/env python3
"""Read-only, compact status for the NF-v3 research repository."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports" / "nf_v3_audit"


def git(*args: str) -> str:
    safe = ROOT.as_posix()
    result = subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "-C", str(ROOT), *args],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip()


def process_snapshot(run: Callable = subprocess.run) -> dict:
    """Return unknown on permission/platform errors; never equate errors with idle."""
    if os.name != "nt":
        return {"status": "unavailable", "reason": "Windows process query is unavailable"}
    command = r"""
$ErrorActionPreference = 'Stop'
try {
  $items = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction Stop |
    Select-Object ProcessId, CommandLine)
  ConvertTo-Json -InputObject $items -Compress
} catch {
  [Console]::Error.WriteLine($_.Exception.Message)
  exit 3
}
"""
    try:
        result = run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "reason": str(exc)}
    if result.returncode:
        return {"status": "unavailable", "reason": result.stderr.strip() or "process query failed"}
    try:
        items = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {"status": "unavailable", "reason": f"invalid process-query output: {exc}"}
    if isinstance(items, dict):
        items = [items]
    processes = [
        {"pid": item.get("ProcessId"), "command_line": item.get("CommandLine")}
        for item in items if isinstance(item, dict)
    ]
    matching = [p for p in processes if "score_target_transfer.py" in (p["command_line"] or "")]
    return {"status": "available", "python_processes": processes,
            "transfer_runner_pids": [p["pid"] for p in matching],
            "transfer_runner_active": bool(matching)}


def summarize_progress(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    completed = value.get("completed_seeds", [])
    seeds = sorted(
        int(row["seed"]) for row in completed
        if isinstance(row, dict) and "seed" in row
    ) if isinstance(completed, list) else []
    expected = value.get("expected_seeds")
    count = value.get("completed_seed_count", value.get("complete_seed_count", len(seeds)))
    return {
        "report": path.name,
        "direction": value.get("direction"),
        "completed_seeds": seeds,
        "completed_seed_count": count,
        "expected_seeds": expected,
        "last_completed_seed": value.get("last_completed_seed"),
        "completed_utc": value.get("completed_utc"),
        "target_labels_read": value.get("target_labels_read"),
        "all_per_seed_outputs_integrity_verified": value.get("all_per_seed_outputs_integrity_verified"),
    }


def source_result(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    return {"report": path.name, "direction": value.get("direction"),
            "complete_seed_count": value.get("complete_seed_count"),
            "all_per_seed_outputs_integrity_verified": value.get("all_per_seed_outputs_integrity_verified")}


def artifact_state(relative: str) -> dict:
    path = ROOT / relative
    try:
        ignored = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT),
             "check-ignore", "-q", "--", relative], check=False,
            capture_output=True,
        ).returncode == 0
    except OSError:
        ignored = None
    count = sum(1 for _ in path.iterdir()) if path.is_dir() else None
    return {"path": relative, "exists": path.exists(), "entry_count": count, "ignored": ignored}


def collect_status() -> dict:
    status_lines = git("status", "--porcelain=v1", "--untracked-files=normal").splitlines()
    upstream = None
    ahead_behind = None
    try:
        upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
        counts = git("rev-list", "--left-right", "--count", f"HEAD...{upstream}").split()
        ahead_behind = {"ahead": int(counts[0]), "behind": int(counts[1])}
    except subprocess.CalledProcessError:
        pass
    frozen_status = git("status", "--porcelain=v1", "--",
                        "research_proposal.md", "methodology_final.md").splitlines()
    progress_paths = sorted(
        path for path in AUDIT.glob("*.json")
        if "progress" in path.name.casefold() and "target_transfer_progress_" in path.name
    )
    source_progress_paths = [AUDIT / "cic_source_e1_seed_progress.json"]
    progress = [summarize_progress(path) for path in [*progress_paths, *source_progress_paths] if path.is_file()]
    source_results = [source_result(path) for path in (
        AUDIT / "source_e1_final_results.json", AUDIT / "source_e1_cic_final_results.json"
    ) if path.is_file()]
    artifact_paths = (
        "data/processed/source-e1-lock-1/full_runs",
        "data/processed/source-e1-cic-lock-1/full_runs",
        "data/processed/target-transfer-v1/unsw-to-cic/scores",
        "data/processed/target-transfer-v1/cic-to-unsw/scores",
    )
    return {
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "worktree_clean": not status_lines,
        "changed_paths": [line[3:] for line in status_lines],
        "upstream_ref": upstream,
        "cached_upstream_relation": ahead_behind,
        "frozen_documents_clean": not frozen_status,
        "frozen_document_changes": [line[3:] for line in frozen_status],
        "source_e1_results": source_results,
        "transfer_progress": progress,
        "ignored_local_artifacts": [artifact_state(path) for path in artifact_paths],
        "processes": process_snapshot(),
        "target_labels_read_by_status_helper": False,
    }


def main() -> None:
    print(json.dumps(collect_status(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
