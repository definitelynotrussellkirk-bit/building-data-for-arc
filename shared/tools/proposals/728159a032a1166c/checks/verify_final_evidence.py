#!/usr/bin/env python3
"""Verify source binding and the decisive review receipts without rerunning them."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
EXPECTED_GENERATOR_SHA256 = "fc7217aa7f21bf87864b23620caa1c5ca58a3fc1ca2f6b84c66852ee0f37cb43"


def load(relative: str):
    return json.loads((WORK / relative).read_text())


def main() -> None:
    generator_sha = hashlib.sha256(
        (WORK / "repo/generators/43cca8eff94f/generator.py").read_bytes()
    ).hexdigest()
    task_tests = load("checks/final-verification-task-tests/result.json")
    battery = load(
        "checks/final-verification-battery/checks/43cca8eff94f_after_battery_summary.json"
    )
    census = load("checks/lesson-census.summary.json")
    solve = load("solve/summary.json")
    blind = load("solve-blind/summary.json")
    audit_one = load("checks/audit/b45771715d10/observation.json")
    audit_two = load("checks/audit/95315dd52287/observation.json")

    expected_battery_counts = {
        "total": 12,
        "green": 12,
        "advisory": 0,
        "failed": 0,
        "interrupted": 0,
        "pending": 0,
        "running": 0,
    }
    expected_census = {
        "requested": 300,
        "materialized": 300,
        "materialization_errors": 0,
        "pairs": 1500,
        "ambiguous": 0,
        "hook_warnings": 0,
        "scoring_errors": 0,
        "rotations": 1500,
        "ambiguous_rotations": 0,
        "rotation_hook_warnings": 0,
        "rotation_scoring_errors": 0,
        "unique_inputs": 1500,
    }

    assert generator_sha == EXPECTED_GENERATOR_SHA256
    assert task_tests["exit_code"] == 0 and task_tests["status"] == "completed"
    assert battery["generator_file_sha256"] == generator_sha
    assert battery["verdict"] == "all_green"
    assert battery["counts"] == expected_battery_counts
    assert census["source_binding"]["generator_sha256"] == generator_sha
    assert census["summary"] == expected_census
    assert solve["generator_hash"] == generator_sha
    assert solve["status"] == "finished" and solve["attempt_count"] == 1
    assert blind["status"] == "finished" and blind["attempt_count"] == 1
    assert audit_one["generator_sha256"] == (
        "6bac8ef4d552081848619bcd98bd35d3818618ef7c626923e68e717ce8c56dd7"
    )
    assert audit_one["requested_codes"] == [1, 1]
    assert audit_one["observed_codes"] == [1, 4]
    assert audit_two["generator_sha256"] == (
        "ee41ee644c95c867340523295ec5140835e00dc64d18a23df69a0f82d0bf2e01"
    )
    assert audit_two["generated_probe"]["sample_count"] == 60
    assert audit_two["generated_probe"]["rival_matches"] == 60
    assert audit_two["canonical_probe"]["pair_count"] == 3
    assert audit_two["canonical_probe"]["rival_matches"] == 2

    receipt = {
        "schema": "review-final-evidence-verification-v1",
        "generator_sha256": generator_sha,
        "task_tests": {"exit_code": 0, "status": "completed", "reported_passes": 65},
        "battery": {
            "verdict": battery["verdict"],
            "counts": battery["counts"],
            "run_id": battery["run_id"],
        },
        "lesson_census": census["summary"],
        "solve": {
            "status": solve["status"],
            "attempt_count": solve["attempt_count"],
            "generator_hash": solve["generator_hash"],
        },
        "blind_solve": {
            "status": blind["status"],
            "attempt_count": blind["attempt_count"],
            "task_id": blind["task_id"],
        },
        "audits": {
            "b45771715d10": {
                "generator_sha256": audit_one["generator_sha256"],
                "requested_codes": audit_one["requested_codes"],
                "observed_codes": audit_one["observed_codes"],
            },
            "95315dd52287": {
                "generator_sha256": audit_two["generator_sha256"],
                "generated_rival_matches": 60,
                "generated_total": 60,
                "canonical_rival_matches": 2,
                "canonical_total": 3,
            },
        },
    }
    output = WORK / "checks/final-evidence-verification.json"
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
