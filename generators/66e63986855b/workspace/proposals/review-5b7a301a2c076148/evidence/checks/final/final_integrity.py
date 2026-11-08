from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
TASK_ID = "66e63986855b"
TASK = WORK / "repo" / "generators" / TASK_ID
EXPECTED_GENERATOR = "8f78ef0944e40e80f9b86e9d5fdb2c9515fd05240e400d097e9993c5af79bc2f"
EXPECTED_PROTOTYPE = "5b8160bf5ff039397ceaee787458c069b5e739a8ccddd9733dd97b3467007255"
EXPECTED_EVIDENCE = "9c0070b4e6e9c6e9d848a1c715956f3c91855c757aca81d9cf26d2d7c56ae72c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_exit(path: Path) -> int:
    return int(path.read_text(encoding="utf-8").strip())


def main() -> int:
    assignment = json.loads((WORK / "ASSIGNMENT.json").read_text(encoding="utf-8"))
    evidence_path = WORK / "checks" / "parametric" / "reflection-extent-v1" / "report.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    results = json.loads((WORK / "RESULTS.json").read_text(encoding="utf-8"))

    baseline_mismatches = []
    for relative, expected in assignment["baseline_sha256"].items():
        current = WORK / relative
        actual = sha(current) if current.is_file() else None
        if actual != expected:
            baseline_mismatches.append({"path": relative, "expected": expected, "actual": actual})
    expected_changed_baseline = {"repo/generators/66e63986855b/notes.md"}

    public_records = []
    for path in sorted((evidence_path.parent / "public").glob("*.json")):
        payload = path.read_bytes()
        visible = json.loads(payload)
        public_records.append(
            {
                "path": str(path.relative_to(WORK)),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "filename_matches_visible_sha256": path.stem == hashlib.sha256(payload).hexdigest(),
                "train_count": len(visible.get("train", [])),
                "query_count": len(visible.get("test", [])),
                "query_outputs_present": any("output" in pair for pair in visible.get("test", [])),
            }
        )

    ticket_reports = []
    for ticket_id in ("ticket-c6b782850181d186", "ticket-9bf180a44d26a83a"):
        path = WORK / "checks" / "tickets" / ticket_id / "report.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        ticket_reports.append(
            {
                "ticket_id": ticket_id,
                "status": payload.get("status"),
                "checks_all_true": all(payload.get("checks", {}).values()),
                "sha256": sha(path),
            }
        )

    missing_result_evidence = []
    for command in results.get("verification_commands", []):
        for relative in command.get("evidence_paths", []):
            if not (WORK / relative).is_file():
                missing_result_evidence.append(relative)
    for ticket in results.get("supplementary_tickets", []):
        for relative in ticket.get("evidence_paths", []):
            if not (WORK / relative).is_file():
                missing_result_evidence.append(relative)

    checks = {
        "production_generator_unchanged": sha(TASK / "generator.py") == EXPECTED_GENERATOR,
        "prototype_matches_materialized_source_hash": sha(TASK / "workspace" / "parametric" / "prototype.py") == EXPECTED_PROTOTYPE == evidence["sources"]["prototype_sha256"],
        "evidence_report_hash_stable": sha(evidence_path) == EXPECTED_EVIDENCE,
        "all_materialization_checks_true": all(evidence["checks"].values()),
        "public_files_content_addressed": all(row["filename_matches_visible_sha256"] for row in public_records),
        "public_files_have_four_unlabeled_queries": all(row["query_count"] == 4 and not row["query_outputs_present"] for row in public_records),
        "fresh_selected_suite_exit_zero": read_exit(WORK / "checks" / "final" / "fresh-task-tests.exit") == 0,
        "fresh_selected_suite_reports_40_passed": "40 passed" in (WORK / "checks" / "final" / "fresh-task-tests.stdout").read_text(encoding="utf-8"),
        "fresh_adversarial_exit_zero": read_exit(WORK / "checks" / "final" / "fresh-adversarial.exit") == 0,
        "fresh_adversarial_reports_zero_findings": json.loads((WORK / "checks" / "final" / "fresh-adversarial.stdout").read_text(encoding="utf-8"))["findings"] == [],
        "only_expected_baseline_file_changed": {row["path"] for row in baseline_mismatches} == expected_changed_baseline,
        "ticket_reports_completed_and_green": all(row["status"] == "completed" and row["checks_all_true"] for row in ticket_reports),
        "results_completed": results.get("completion_state") == "complete" and results.get("remaining_failures") == [],
        "all_results_evidence_paths_exist": not missing_result_evidence,
        "no_parametric_pycache": not any((TASK / "workspace" / "parametric").rglob("__pycache__")),
    }

    report = {
        "schema": "review-final-integrity-v1",
        "assignment_id": assignment["assignment_id"],
        "task_id": TASK_ID,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "baseline_mismatches": baseline_mismatches,
        "public_records": public_records,
        "ticket_reports": ticket_reports,
        "missing_result_evidence": sorted(set(missing_result_evidence)),
        "limits": [
            "Integrity check validates retained artifacts and selected scope; package_return remains the authority for delta/allowed-path validation.",
            "It does not repeat arbitrary-program rival search or model evaluation.",
        ],
    }
    out = Path(__file__).with_name("final-integrity-report.json")
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "report": str(out)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
