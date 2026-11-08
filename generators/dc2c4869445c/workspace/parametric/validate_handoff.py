"""Validate the native handoff's cross-artifact bindings and causal replay.

This is deliberately independent of qualification generation.  It verifies the
reported source inventory, the qualification/execution link, the owner-facing
sequential witness schema, and replays both witness programs through protected
Racket.  Run through ``review.py run`` from the packet root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root

ROOT = find_root(__file__)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate(
    qualification_path: Path,
    witness_path: Path,
    manifest_path: Path,
    audit_path: Path,
    task_test_result: Path,
) -> dict[str, Any]:
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness

    qualification = _load(qualification_path)
    witness = _load(witness_path)
    manifest = _load(manifest_path)
    audit = _load(audit_path)
    tests = _load(task_test_result)

    if qualification.get("status") != "qualified":
        raise ValueError("qualification is not qualified")
    execution = qualification.get("execution", {})
    execution_path = qualification_path.parent / execution.get("path", "")
    if not execution_path.is_file() or _sha(execution_path) != execution.get("sha256"):
        raise ValueError("qualification/execution hash mismatch")

    checked_files = 0
    for row in manifest.get("files", []):
        source = ROOT / row["path"]
        if not source.is_file() or _sha(source) != row["sha256"]:
            raise ValueError(f"manifest source mismatch: {row.get('path')}")
        checked_files += 1
    if checked_files == 0:
        raise ValueError("empty source manifest")

    dependency = {
        key: witness[key]
        for key in ("step_a", "intermediate", "step_b", "why_b_depends_on_a")
    }
    dependency["witness_path"] = "checks/dc2c4869445c/sequential-witness.json"
    progress = {"sequential_dependency": dependency}
    read = lambda _name: witness_path.read_bytes()
    static = validate_sequential_witness(progress, qualification, read)
    replay = replay_witness(ROOT, witness)

    if audit.get("status") != "passed" or audit.get("racket_evaluations") != 206:
        raise ValueError("task-local finite audit is absent or changed")
    if not tests.get("passed") or tests.get("exit_code") != 0:
        raise ValueError("final staged task tests are not green")
    if witness["cases"][0].get("changed_output_cells") != 10:
        raise ValueError("causal difference count changed")

    return {
        "schema": "dc2c4869445c-handoff-validation-v1",
        "status": "passed",
        "task_id": "dc2c4869445c",
        "manifest_files_checked": checked_files,
        "qualification_jobs": len(qualification.get("jobs", [])),
        "qualification_racket_evaluations": _load(execution_path).get("racket_evaluations"),
        "audit_racket_evaluations": audit.get("racket_evaluations"),
        "task_tests_passed": tests.get("passed"),
        "static_witness": static,
        "protected_witness_replay": replay,
        "owner_acceptance": "pending",
        "training_admitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--task-tests", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(f"choose a new output path: {args.out}")
    result = validate(
        args.qualification,
        args.witness,
        args.manifest,
        args.audit,
        args.task_tests,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"],
        "manifest_files_checked": result["manifest_files_checked"],
        "qualification_jobs": result["qualification_jobs"],
        "witness_cases": result["static_witness"]["cases"],
        "witness_replay_evaluations": result["protected_witness_replay"]["evaluations"],
    }, indent=2))


if __name__ == "__main__":
    main()
