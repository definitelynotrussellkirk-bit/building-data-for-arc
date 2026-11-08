#!/usr/bin/env python3
"""Reproduce and disposition the pinned interrupted-battery tool request."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from reviewer_support import load_selected_generator

TASK_ID = "2b83f40cf6d9"
TICKET_ID = "ticket-16b2eac52fb9e3a2"
REQUEST_ID = "review-576523145e686e48:v0001:F1"
EXPECTED_GENERATOR_SHA256 = "4ca15e7a48171953ca72ee9527dfcba7d62624a33ed71bbf9ce90085008586d6"
EXPECTED_REQUEST_SOURCE_SHA256 = "2cf732622eeeca12a0b3d2618fd72be588896badeb17ad67a61226d101f1b646"
EXPECTED_REQUEST_SHA256 = "303d64366fcc8fd3e720a5a74aad976a697b78bd87c7a528e6b1aa4a23995865"
EXPECTED_MANIFEST_SHA256 = "5409f18dc163322337059d113f072513dfaf5c2ebdabb6dfe115940d2ed8e6ea"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_json(argv: list[str]) -> tuple[dict, dict]:
    proc = subprocess.run(argv, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {argv}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return json.loads(proc.stdout), {
        "argv": argv,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()

    module, generator_path, generator_sha256 = load_selected_generator(TASK_ID)
    if generator_sha256 != EXPECTED_GENERATOR_SHA256:
        raise ValueError(
            f"generator differs from ticket: {generator_sha256} != {EXPECTED_GENERATOR_SHA256}"
        )

    suggestions_path = root / "REVIEW/suggestions.json"
    if sha256(suggestions_path) != EXPECTED_REQUEST_SOURCE_SHA256:
        raise ValueError("suggestion ledger differs from ticket")
    suggestions = json.loads(suggestions_path.read_text())
    request = next(
        row for row in suggestions["items"] if row.get("request_id") == REQUEST_ID
    )
    if canonical_sha256(request) != EXPECTED_REQUEST_SHA256:
        raise ValueError("request record differs from ticket")

    manifest_path = root / request["assets_manifest"]["path"]
    if sha256(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise ValueError("proposal manifest differs from ticket")
    manifest = json.loads(manifest_path.read_text())
    verified_assets = []
    for record in manifest["files"]:
        path = root / record["path"]
        actual = sha256(path)
        if actual != record["sha256"]:
            raise ValueError(f"asset hash mismatch: {path}")
        verified_assets.append(
            {"path": record["path"], "bytes": path.stat().st_size, "sha256": actual}
        )

    initial_path = root / manifest["files"][0]["path"]
    resumed_path = root / manifest["files"][1]["path"]
    initial = json.loads(initial_path.read_text())
    resumed = json.loads(resumed_path.read_text())
    if initial.get("status") != "running" or initial.get("passed") is not None:
        raise AssertionError("retained initial asset is not the expected running checkpoint")
    if resumed.get("status") != "completed" or resumed.get("resumed") is not True:
        raise AssertionError("retained resumed asset does not show completed resume")

    initial_stages = initial["battery_summary"]["stages"]
    completed_initial = [name for name, row in initial_stages.items() if row.get("status") == "green"]
    pending_initial = [name for name, row in initial_stages.items() if row.get("status") == "pending"]
    first_pending = pending_initial[0] if pending_initial else None

    legacy_dir = args.out.parent / "legacy-out"
    if legacy_dir.exists():
        shutil.rmtree(legacy_dir)
    legacy_dir.mkdir(parents=True)
    shutil.copy2(initial_path, legacy_dir / "result.json")

    status, status_command = run_json(
        [sys.executable, "-m", "arcpuzzles", "check-status", "--out", str(legacy_dir)]
    )
    help_proc = subprocess.run(
        [sys.executable, "-m", "arcpuzzles", "check-run", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    if help_proc.returncode != 0:
        raise RuntimeError(help_proc.stderr)

    managed_actions_present = all(
        token in help_proc.stdout for token in ("start", "status", "wait", "resume")
    )
    missing_requested_fields = [
        key for key in ("first_safe_stage", "resume_command", "recovery_command") if key not in status
    ]

    report = {
        "schema": "arcpuzzles-tool-reproduction-ticket-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "request_id": REQUEST_ID,
        "status": "completed",
        "bindings": {
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": generator_sha256,
            "generator_version": getattr(module, "VERSION", None),
            "request_source_path": str(suggestions_path.relative_to(root)),
            "request_source_sha256": sha256(suggestions_path),
            "request_sha256": canonical_sha256(request),
            "manifest_path": str(manifest_path.relative_to(root)),
            "manifest_sha256": sha256(manifest_path),
            "assets": verified_assets,
        },
        "retained_reproduction": {
            "initial": {
                "status": initial.get("status"),
                "passed": initial.get("passed"),
                "command": initial.get("command"),
                "completed_stages": completed_initial,
                "pending_stages": pending_initial,
                "first_pending_stage": first_pending,
                "controller_identity_present": bool(initial.get("controller")),
                "child_identity_present": bool(initial.get("child_process")),
                "verdict_note": initial["battery_summary"].get("verdict_note"),
            },
            "resumed": {
                "status": resumed.get("status"),
                "passed": resumed.get("passed"),
                "resumed": resumed.get("resumed"),
                "command": resumed.get("command"),
                "invalidated_stages": resumed.get("invalidated_stages"),
                "verdict_note": resumed["battery_summary"].get("verdict_note"),
            },
        },
        "current_tool_probe": {
            "check_status_command": status_command,
            "check_status_result": status,
            "managed_check_run_actions_present": managed_actions_present,
            "managed_help_excerpt": "\n".join(help_proc.stdout.splitlines()[:12]),
            "missing_requested_fields": missing_requested_fields,
        },
        "assessment": {
            "implemented_scope": "Managed detached runs now expose start/status/wait/resume, stable run IDs, PID-birth liveness, and source-bound safe resume for future runs. Ordinary check-status also diagnoses a stale legacy checkpoint without mutating it.",
            "remaining_gap": "The pinned legacy result has no verifiable controller/child identity, so current check-status reports liveness_unknown and resumable=false. It does not convert the checkpoint to an interrupted snapshot or print first_safe_stage/an exact supported recovery command, even though the retained journal shows defect_lint was next and the historical --resume succeeded.",
            "proposed_disposition": "Keep deferred, but narrow/split the request: close the future managed-run portion as implemented; retain a legacy-checkpoint migration/recovery-planner request that reports the next journaled stage and exact safe command without weakening liveness or source checks.",
            "runtime_approval": False,
        },
    }

    assert completed_initial == ["lint", "selfcheck", "rule_smoke"]
    assert first_pending == "defect_lint"
    assert status["status"] == "liveness_unknown"
    assert status["controller_alive"] is None
    assert status["resumable"] is False
    assert managed_actions_present
    assert set(missing_requested_fields) == {
        "first_safe_stage", "resume_command", "recovery_command"
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "initial_completed": completed_initial,
        "first_pending": first_pending,
        "current_status": status["status"],
        "resumable": status["resumable"],
        "managed_actions_present": managed_actions_present,
        "proposed_disposition": report["assessment"]["proposed_disposition"],
        "report": str(args.out),
    }, indent=2))


if __name__ == "__main__":
    main()
