#!/usr/bin/env python3
"""Source-bound final integrity check for review-4f9d5c2115d03373."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "a631936f7715"
ASSIGNMENT_ID = "review-4f9d5c2115d03373"
EXPECTED_COUNTS = {
    "settings": 2,
    "train_pairs_per_setting": 3,
    "test_pairs_per_setting": 4,
    "episode_pairs": 14,
    "racket_executions": 28,
    "distinguishing_pairs": 14,
    "identifiable_queries": 8,
}
EXPECTED_EXPORT_COUNTS = {
    "episodes": 2,
    "demonstrations_per_episode": 3,
    "queries_per_episode": 4,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path("WORK"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    checks = workspace / "checks"
    assignment = load(workspace / "ASSIGNMENT.json")
    results = load(workspace / "RESULTS.json")
    report = load(checks / "parametric-final" / "report.json")
    artifact_root = checks / "parametric-final" / "artifacts"
    manifest = load(artifact_root / "private" / "manifest.json")
    task_before = load(checks / "task-tests-before" / "result.json")
    task_final = load(checks / "task-tests-final" / "result.json")
    adversarial = load(checks / "parametric-adversarial" / "report.json")
    parameter_ticket = load(checks / "tickets" / "ticket-fa3af06137183ff7" / "report.json")
    audit_ticket = load(checks / "tickets" / "ticket-99843c62239b8a65" / "report.json")

    require(assignment["assignment_id"] == ASSIGNMENT_ID, "assignment identity drifted")
    require(assignment["task_id"] == TASK_ID, "selected task drifted")
    require(results["assignment_id"] == ASSIGNMENT_ID, "results assignment identity drifted")
    require(results["generator_id"] == TASK_ID, "results generator identity drifted")
    require(results["completion_state"] == "complete", "results are not complete")
    require(results.get("work_scope", {}).get("assigned_question_answered") is True,
            "assigned shortcut question is not recorded complete")
    require(not (workspace / "AUDIT.md").exists(), "AUDIT.md exists without a new safety finding")

    generator = workspace / "repo" / "generators" / TASK_ID / "generator.py"
    require(sha256(generator) == assignment["generator"]["generator_sha256"],
            "production generator changed")
    require(report["schema"] == "a631936f7715-parametric-verification-v2", "wrong report schema")
    require(report["status"] == "passed", "parametric report did not pass")
    require(report["task_id"] == TASK_ID, "parametric report task drifted")
    require(report["generator_sha256"] == assignment["generator"]["generator_sha256"],
            "parametric report generator binding drifted")
    require(report["counts"] == EXPECTED_COUNTS, "parametric report counts drifted")
    require(len(report["checks"]) == 14, "expected 14 retained pairs")
    require(all(row["settings_disagree"] for row in report["checks"]),
            "a retained pair does not distinguish the settings")
    require(sum(len(row["queries"]) for row in report["identifiability"].values()) == 8,
            "expected eight retained queries")
    require(all(not row["rival_fits_demonstrations"] for row in report["identifiability"].values()),
            "declared rival still fits a demonstration set")
    require(all(query["identifiable_from_demonstrations"]
                for row in report["identifiability"].values() for query in row["queries"]),
            "a retained query is not identifiable from demonstrations")

    require(manifest["schema"] == "a631936f7715-parametric-export-v1", "wrong export schema")
    require(manifest["counts"] == EXPECTED_EXPORT_COUNTS, "export counts drifted")
    public_ids = [row["public_id"] for row in manifest["episodes"]]
    require(public_ids == sorted(public_ids), "public IDs are not sorted")
    require(len(public_ids) == len(set(public_ids)) == 2, "public IDs are not unique")

    public_records = []
    for row in manifest["episodes"]:
        public_path = artifact_root / row["public_path"]
        private_path = artifact_root / row["private_episode_path"]
        program_path = artifact_root / row["program_path"]
        require(public_path.is_file(), f"missing public artifact {row['public_path']}")
        require(private_path.is_file(), f"missing private episode {row['private_episode_path']}")
        require(program_path.is_file(), f"missing private program {row['program_path']}")
        public_hash = sha256(public_path)
        require(public_hash == row["public_id"], "public filename is not exact visible-byte hash")
        require(public_path.name == f"{row['public_id']}.json", "public filename leaks metadata")
        require(sha256(program_path) == row["program_sha256"], "private program hash drifted")
        public = load(public_path)
        require(set(public) == {"train", "test"}, "public artifact contains extra top-level fields")
        require(len(public["train"]) == 3 and len(public["test"]) == 4,
                "public artifact count drifted")
        require(all(set(pair) == {"input", "output"} for pair in public["train"]),
                "public demonstration shape drifted")
        require(all(set(pair) == {"input"} for pair in public["test"]),
                "public query leaks an answer or private field")
        raw = public_path.read_text(encoding="utf-8")
        require("component_connectivity" not in raw and '"program"' not in raw
                and '"seed"' not in raw and '"sampling"' not in raw,
                "public bytes leak private metadata")
        private = load(private_path)
        require(private["parameters"]["component_connectivity"] in (4, 8),
                "private episode lost its setting")
        require(all("output" in pair for pair in private["test"]),
                "private episode lost query answers")
        public_records.append({"public_id": row["public_id"], "bytes": public_path.stat().st_size})

    require(task_before["passed"] is True and task_before["test_counts"]["passed"] == 46,
            "baseline task-test receipt drifted")
    require(task_final["passed"] is True and task_final["test_counts"] == {
        "tests": 50, "failed": 0, "errors": 0, "skipped": 0, "passed": 50
    }, "final task-test receipt is not 50/50")
    require(adversarial["status"] == "passed", "bounded adversarial pass did not pass")
    require(adversarial["bounded_scope"]["episodes_checked"] == 192, "adversarial episode count drifted")
    require(adversarial["bounded_scope"]["pairs_checked"] == 1344, "adversarial pair count drifted")
    require(adversarial["bounded_scope"]["query_identifiability_checks"] == 832,
            "adversarial query count drifted")
    require(adversarial["writer"]["duplicate_visible_payload_rejection"] == "ValueError",
            "duplicate visible payload was not rejected")
    require(adversarial["writer"]["non_arc_numeric_rejection"] == "ValueError",
            "non-ARC numeric payload was not rejected")
    require(not adversarial["writer"]["duplicate_output_created"]
            and not adversarial["writer"]["corrupt_output_created"],
            "rejected writer input left an output directory")

    require(parameter_ticket["status"] == "passed" and parameter_ticket["failed_checks"] == [],
            "parameter-query ticket did not pass")
    require(parameter_ticket["checks"]["each_public_artifact_is_three_demo_one_query"],
            "parameter-query ticket boundary changed")
    require(parameter_ticket["checks"]["public_filenames_are_not_exact_visible_hashes"],
            "parameter-query filename finding changed")
    require(audit_ticket["status"] == "passed" and audit_ticket["failed_checks"] == [],
            "audit replay ticket did not pass")
    require(audit_ticket["replay_sha256"] == audit_ticket["retained_witness_sha256"],
            "audit replay no longer matches retained witness")
    require(audit_ticket["result"]["existing_audit_resolution"] == "unresolved",
            "audit replay improperly cleared the existing audit")

    question = (workspace / "QUESTION_ANSWER.md").read_text(encoding="utf-8")
    require("eight-connected magenta segmentation" in question,
            "assigned shortcut answer does not name the rival")
    require("28/28" in question and "all 14 retained pairs" in question,
            "assigned shortcut answer is not bound to retained evidence")

    missing_evidence = []
    referenced_evidence = []
    for command in results.get("verification_commands", []):
        for relative in command.get("evidence_paths", []):
            referenced_evidence.append(relative)
            if not (workspace / relative).is_file():
                missing_evidence.append(relative)
    for ticket in results.get("supplementary_tickets", []):
        for relative in ticket.get("evidence_paths", []):
            referenced_evidence.append(relative)
            if not (workspace / relative).is_file():
                missing_evidence.append(relative)
    require(not missing_evidence, f"missing declared evidence: {missing_evidence}")

    summary = {
        "schema": "review-4f9d5c2115d03373-final-integrity-v1",
        "status": "passed",
        "assignment_id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "production_generator_sha256": sha256(generator),
        "parametric_counts": report["counts"],
        "public_artifacts": public_records,
        "task_tests": {"before": 46, "after": 50},
        "adversarial": {
            "episodes": 192,
            "pairs": 1344,
            "query_checks": 832,
        },
        "supplementary_tickets": [parameter_ticket["ticket_id"], audit_ticket["ticket_id"]],
        "declared_evidence_paths_checked": len(referenced_evidence),
        "new_audit_file": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
