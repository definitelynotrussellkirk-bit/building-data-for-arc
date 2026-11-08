#!/usr/bin/env python3
"""Cross-check both reviewer-ready parametric handoffs without accepting them.

This is intentionally an owner-side convenience validator, not an admission tool.
It binds the current source tree to the retained manifests, qualification/execution
receipts, public projections, protected-Racket causal witnesses, and staged tests.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


WORK = Path(__file__).resolve().parents[1]
REPO = WORK / "repo"
TARGETS = ("0e4adc584fa1", "b37eb391ddc0")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return sum(len(row) for row in left) + sum(len(row) for row in right)
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def verify_execution(qualification_path: Path, expected_demos: int) -> tuple[dict[str, Any], dict[str, Any]]:
    qualification = read_json(qualification_path)
    if qualification.get("status") != "qualified":
        raise AssertionError(f"qualification is not qualified: {qualification_path}")
    jobs = qualification.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise AssertionError(f"qualification has no jobs: {qualification_path}")
    demo_counts = {job.get("demos") for job in jobs if isinstance(job, dict)}
    query_counts = {job.get("queries") for job in jobs if isinstance(job, dict)}
    if demo_counts != {expected_demos} or query_counts != {4}:
        raise AssertionError(
            f"qualification job counts mismatch at {qualification_path}: "
            f"demos={sorted(demo_counts)}, queries={sorted(query_counts)}"
        )
    execution_ref = qualification.get("execution")
    if not isinstance(execution_ref, dict):
        raise AssertionError(f"missing execution reference: {qualification_path}")
    execution_path = qualification_path.parent / str(execution_ref.get("path"))
    if not execution_path.is_file() or sha256(execution_path) != execution_ref.get("sha256"):
        raise AssertionError(f"execution hash mismatch: {execution_path}")
    execution = read_json(execution_path)
    racket = execution.get("racket")
    if not isinstance(racket, dict) or racket.get("backend") != "racket" or racket.get("protected") is not True:
        raise AssertionError(f"qualification did not use protected Racket: {execution_path}")
    racket_evaluations = execution.get("racket_evaluations")
    if not isinstance(racket_evaluations, int) or racket_evaluations <= 0:
        raise AssertionError(f"invalid Racket evaluation count: {execution_path}")
    return qualification, execution


def validate_target(task: str) -> dict[str, Any]:
    home = REPO / "generators" / task / "workspace" / "parametric"
    manifest_path = home / "evidence" / "manifest.json"
    manifest = read_json(manifest_path)

    manifest_hashes: dict[str, str] = {}
    for record in manifest.get("files", []):
        if not isinstance(record, dict):
            raise AssertionError(f"invalid manifest record for {task}")
        relative = record.get("path")
        if not isinstance(relative, str):
            raise AssertionError(f"manifest path is not a string for {task}")
        path = REPO / relative
        if not path.is_file():
            raise AssertionError(f"manifest file missing: {relative}")
        actual = sha256(path)
        if actual != record.get("sha256") or path.stat().st_size != record.get("bytes"):
            raise AssertionError(f"manifest mismatch for {relative}")
        manifest_hashes[relative] = actual

    qdir = WORK / "checks" / task / "qualification"
    qualification, execution = verify_execution(qdir / "qualification.json", expected_demos=3)

    source_binding = qualification.get("source_binding")
    if not isinstance(source_binding, dict):
        raise AssertionError(f"{task} qualification has no source binding")
    source_records = source_binding.get("files")
    if not isinstance(source_records, list) or not source_records:
        raise AssertionError(f"{task} qualification source binding is empty")
    source_hashes: dict[str, str] = {}
    for record in source_records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise AssertionError(f"{task} invalid source-binding record")
        relative = record["path"]
        path = REPO / relative
        if not path.is_file() or sha256(path) != record.get("sha256"):
            raise AssertionError(f"{task} qualification source binding is stale: {relative}")
        source_hashes[relative] = record["sha256"]

    overlap = set(manifest_hashes) & set(source_hashes)
    if not overlap:
        raise AssertionError(f"{task} manifest and qualification bind no common files")
    for relative in overlap:
        if manifest_hashes[relative] != source_hashes[relative]:
            raise AssertionError(f"{task} manifest/qualification mismatch: {relative}")
    if source_binding.get("generator_sha256") != manifest.get("generator_sha256"):
        raise AssertionError(f"{task} generator hash differs between manifest and qualification")
    if source_binding.get("canonical_program_sha256") != manifest.get("canonical_program_sha256"):
        raise AssertionError(f"{task} canonical program hash differs between manifest and qualification")

    witness_path = WORK / "checks" / task / "causal" / "witness.json"
    witness = read_json(witness_path)
    if witness.get("source_binding") != source_binding:
        raise AssertionError(f"{task} witness source binding differs from qualification")
    if witness.get("racket") != {"backend": "racket", "protected": True}:
        raise AssertionError(f"{task} witness is not protected Racket")
    cases = witness.get("cases")
    if not isinstance(cases, list) or not cases:
        raise AssertionError(f"{task} witness contains no cases")
    case_diffs: list[int] = []
    for case in cases:
        if not isinstance(case, dict):
            raise AssertionError(f"{task} malformed causal case")
        delta = changed_cells(case["output"], case["counterfactual_output"])
        if delta <= 0:
            raise AssertionError(f"{task} causal counterfactual did not change output")
        case_diffs.append(delta)

    public = read_json(WORK / "checks" / task / "public-check.json")
    if public.get("status") != "passed" or public.get("files_checked") != 16 or public.get("findings"):
        raise AssertionError(f"{task} public projection check failed")

    task_tests = read_json(WORK / "checks" / task / "task-tests" / "result.json")
    if not task_tests.get("passed") or task_tests.get("exit_code") != 0:
        raise AssertionError(f"{task} staged task tests failed")

    boundaries: dict[str, dict[str, int]] = {}
    total_racket = int(execution["racket_evaluations"])
    for demos in (2, 6):
        boundary_dir = WORK / "checks" / task / f"qualification-d{demos}"
        boundary_q, boundary_e = verify_execution(boundary_dir / "qualification.json", expected_demos=demos)
        boundaries[str(demos)] = {
            "jobs": len(boundary_q["jobs"]),
            "racket_evaluations": int(boundary_e["racket_evaluations"]),
        }
        total_racket += int(boundary_e["racket_evaluations"])

    audit = read_json(WORK / "checks" / task / "finite-audit-64.json")
    if audit.get("failures"):
        raise AssertionError(f"{task} finite audit has failures")
    if audit.get("episodes") != 384:
        raise AssertionError(f"{task} finite audit episode count changed")

    jobs = qualification["jobs"]
    return {
        "task_id": task,
        "manifest_sha256": sha256(manifest_path),
        "manifest_files": len(manifest_hashes),
        "qualification_bound_files": len(source_hashes),
        "manifest_qualification_overlap": len(overlap),
        "generator_sha256": manifest["generator_sha256"],
        "canonical_program_sha256": manifest["canonical_program_sha256"],
        "qualification": {
            "jobs": len(jobs),
            "demos": sorted({job["demos"] for job in jobs}),
            "queries": sorted({job["queries"] for job in jobs}),
            "racket_evaluations": execution["racket_evaluations"],
        },
        "demo_boundaries": boundaries,
        "total_qualification_racket_evaluations": total_racket,
        "finite_audit_episodes": audit["episodes"],
        "public_views": public["files_checked"],
        "causal_changed_cells": case_diffs,
        "task_tests": {
            "passed": task_tests["passed"],
            "test_counts": task_tests.get("test_counts"),
            "evidence_sha256": task_tests.get("evidence_sha256"),
        },
        "status": "reviewer_ready",
        "owner_acceptance": False,
        "training_admitted": False,
    }


def main() -> int:
    report = {
        "schema": "arcpuzzles-two-parametric-handoff-check-v1",
        "targets": [validate_target(task) for task in TARGETS],
        "limits": (
            "Cross-artifact current-source/hash/schema/protected-replay evidence check only; "
            "it does not grant owner acceptance or training admission."
        ),
    }
    out = WORK / "checks" / "two-handoff-validation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
