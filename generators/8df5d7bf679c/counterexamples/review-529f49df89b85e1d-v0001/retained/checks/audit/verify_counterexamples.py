from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def compare(task_id: str, demo_count: int, metadata_name: str | None = None) -> dict:
    here = ROOT / task_id
    racket = json.loads((here / "racket.json").read_text())
    rivals = json.loads((here / "rival_outputs.json").read_text())
    outputs = [row["output"] for row in racket["results"]]
    if len(outputs) != len(rivals):
        raise AssertionError((len(outputs), len(rivals)))
    differences = []
    agreements = []
    for expected, rival in zip(outputs, rivals):
        diff = [
            [r, c, expected[r][c], rival[r][c]]
            for r in range(len(expected))
            for c in range(len(expected[0]))
            if expected[r][c] != rival[r][c]
        ]
        differences.append(diff)
        agreements.append(not diff)
    report = {
        "schema": "arcpuzzles-audit-authority-comparison-v1",
        "task_id": task_id,
        "generator_sha256": racket["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "catalog_rule_hash": racket["catalog_rule_hash"],
        "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
        "demonstration_count": demo_count,
        "demonstration_agreements": agreements[:demo_count],
        "query_agreement": agreements[demo_count],
        "query_differences": differences[demo_count],
        "all_outputs_valid": all(row["valid_output"] and row["error"] is None for row in racket["results"]),
        "racket_path": f"checks/audit/{task_id}/racket.json",
        "rival_outputs_path": f"checks/audit/{task_id}/rival_outputs.json",
        "input_path": f"checks/audit/{task_id}/input.json",
    }
    if metadata_name:
        report["generation_metadata_path"] = f"checks/audit/{task_id}/{metadata_name}"
    if not all(report["demonstration_agreements"]):
        raise AssertionError(f"{task_id}: rival does not fit every demonstration")
    if report["query_agreement"]:
        raise AssertionError(f"{task_id}: rival does not disagree on query")
    if not report["all_outputs_valid"]:
        raise AssertionError(f"{task_id}: invalid authority output")
    (here / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


reports = [
    compare("8df5d7bf679c", 4, "generation_metadata.json"),
    compare("0c2ab7de69d1", 3, "search_report.json"),
]
print(json.dumps(reports, indent=2))
