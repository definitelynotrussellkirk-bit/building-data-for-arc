#!/usr/bin/env python3
"""Source-bound final self-review for a two-parametric ARC review packet.

This helper executes no generator or Racket code. It checks that retained native
qualification, witness, lesson-audit, sequential-preview and copied-runtime test
evidence still bind to the current packet source bytes. Owner acceptance remains
separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--checks", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    work = repo.parent
    checks = (args.checks or work / "checks").resolve()
    out_path = (args.out or checks / "final-self-review.json").resolve()
    assignment = load(work / "ASSIGNMENT.json")
    targets = assignment.get("repair_targets")
    if not isinstance(targets, list) or len(targets) != 2:
        raise ValueError("expected exactly two repair targets")

    report: dict = {
        "schema": "arcpuzzles-two-parametric-self-review-v1",
        "assignment_id": assignment["assignment_id"],
        "status": "pass",
        "reviewer": "author-self-review-no-independent-subagent",
        "targets": {},
        "limits": [
            "Finite named-rival audits do not prove universal lesson uniqueness.",
            "Reviewer qualification is not owner acceptance or training admission.",
        ],
    }

    for target in targets:
        tid = target["task_id"]
        expected_generator = target["generator"]["generator_sha256"]
        q = load(checks / tid / "qualification" / "qualification.json")
        execution_path = checks / tid / "qualification" / "execution.json"
        execution = load(execution_path)
        witness = load(checks / tid / "witness" / "witness.json")
        replay = load(checks / tid / "witness" / "replay.json")
        audit = load(repo / f"generators/{tid}/workspace/parametric/evidence/current/lesson-audit.json")
        inventory = load(repo / f"generators/{tid}/workspace/parametric/evidence/manifest.json")
        preview = load(checks / tid / "preview" / "private" / "manifest.json")
        preview_receipt = load(checks / tid / "preview-verify-command.json")
        suite_path = checks / f"{tid}-final/checks/task_tests.xml"
        suite = ET.parse(suite_path).getroot()[0]

        source_mismatches = []
        for item in q["source_binding"]["files"]:
            path = repo / item["path"]
            actual = sha256(path)
            if actual != item["sha256"]:
                source_mismatches.append(
                    {"path": item["path"], "expected": item["sha256"], "actual": actual}
                )

        inventory_mismatches = []
        for item in inventory["files"]:
            path = repo / item["path"]
            actual = sha256(path)
            if actual != item["sha256"]:
                inventory_mismatches.append(
                    {"path": item["path"], "expected": item["sha256"], "actual": actual}
                )

        generator_hash = sha256(repo / f"generators/{tid}/generator.py")
        execution_hash_matches = sha256(execution_path) == q["execution"]["sha256"]
        witness_binding_matches = witness.get("source_binding") == q.get("source_binding")
        witness_outputs_change = all(
            case.get("output") != case.get("counterfactual_output") for case in witness.get("cases", [])
        ) and bool(witness.get("cases"))

        row = {
            "generator_sha256": generator_hash,
            "generator_matches_assignment": generator_hash == expected_generator,
            "qualification_status": q.get("status"),
            "qualification_jobs": len(q.get("jobs", [])),
            "protected_racket_evaluations": execution.get("racket_evaluations"),
            "qualification_execution_sha256": q["execution"]["sha256"],
            "qualification_execution_hash_matches": execution_hash_matches,
            "qualification_source_binding_mismatches": source_mismatches,
            "manifest_inventory_mismatches": inventory_mismatches,
            "witness_cases": len(witness.get("cases", [])),
            "witness_binding_matches": witness_binding_matches,
            "witness_outputs_change": witness_outputs_change,
            "witness_replay_status": replay.get("status"),
            "lesson_audit_status": audit.get("status"),
            "lesson_audit_summary": audit.get("summary"),
            "preview_status": preview.get("status"),
            "preview_episodes": len(preview.get("episodes", [])),
            "preview_views": len(preview.get("public_files", [])),
            "preview_verify_returncode": preview_receipt.get("returncode"),
            "preview_training_admitted": preview.get("training_admitted"),
            "final_suite": {
                "tests": int(suite.attrib["tests"]),
                "failures": int(suite.attrib["failures"]),
                "errors": int(suite.attrib["errors"]),
                "skipped": int(suite.attrib["skipped"]),
                "seconds": float(suite.attrib["time"]),
            },
            "ready": False,
        }
        row["ready"] = all(
            [
                row["generator_matches_assignment"],
                q.get("status") == "qualified",
                execution_hash_matches,
                not source_mismatches,
                not inventory_mismatches,
                witness_binding_matches,
                witness_outputs_change,
                replay.get("status") == "reviewer_replayed",
                audit.get("status") == "pass",
                preview.get("status") == "qualified_projection",
                preview_receipt.get("returncode") == 0,
                preview.get("training_admitted") is False,
                row["final_suite"]["failures"] == 0,
                row["final_suite"]["errors"] == 0,
            ]
        )
        report["targets"][tid] = row

    if not all(row["ready"] for row in report["targets"].values()):
        report["status"] = "fail"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
