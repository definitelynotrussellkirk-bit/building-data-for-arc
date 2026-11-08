#!/usr/bin/env python3
"""Final source/evidence binding check for review-7658b78f8d983c43."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "c5a69e7cd8c8"
ASSIGNMENT_ID = "review-7658b78f8d983c43"
EXPECTED_GENERATOR = "132987cd4a2c9f6e2634c8edc5e54db1ff5a493c9a7b3ba6d8c3246150f4b6a0"
EXPECTED_CANONICAL = "03d3bbfe24372c5265a508a27e2c5f30e4ab859cb23e6aa35e75cc7955c568a0"
EXPECTED_CANONICAL_RULE = "cd162c43ed682af8c42df94bcb1c099d019115b65f32e70077f02d447664267d"
EXPECTED_ALTERNATE_RULE = "d4f0f2b1c93e83e8f2a7e02e6ca2f58cc2b82640fd9ff4c9c1371288371ef58e"
EXPECTED_PROTOTYPE = "cf808d05e72b649559dc5b8fcf71f9bbb42732a96f6f7e405f4e625b05a09d56"
RELATIONS = {"opposite_opening", "through_opening"}
EVIDENCE = ROOT / "checks/parametric/c5a69e7cd8c8-ray-relation-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    failures: list[str] = []
    checks: dict[str, object] = {}

    def expect(condition: bool, label: str, detail: object = True) -> None:
        checks[label] = detail if condition else False
        if not condition:
            failures.append(label)

    assignment = load(ROOT / "ASSIGNMENT.json")
    expect(assignment.get("assignment_id") == ASSIGNMENT_ID, "assignment_id")
    expect(assignment.get("task_id") == TASK_ID, "task_id")

    generator = ROOT / f"repo/generators/{TASK_ID}/generator.py"
    canonical = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
    prototype = ROOT / f"repo/generators/{TASK_ID}/workspace/parametric/prototype.py"
    expect(sha(generator) == EXPECTED_GENERATOR, "production_generator_unchanged", sha(generator))
    expect(sha(canonical) == EXPECTED_CANONICAL, "canonical_ledger_unchanged", sha(canonical))
    expect(sha(prototype) == EXPECTED_PROTOTYPE, "prototype_source_bound", sha(prototype))

    report = load(EVIDENCE / "report.json")
    manifest = load(EVIDENCE / "manifest.json")
    verify = load(ROOT / "checks/parametric/c5a69e7cd8c8-ray-relation-v1.verify.stdout.json")
    materialize = load(ROOT / "checks/parametric/c5a69e7cd8c8-ray-relation-v1.materialize.stdout.json")
    expect(report == materialize, "materialize_receipt_matches_report")
    expect(report.get("status") == "no_ambiguity_found", "materialize_status")
    expect(report.get("prototype_source_sha256") == EXPECTED_PROTOTYPE, "report_prototype_binding")
    expect(report.get("generator_sha256") == EXPECTED_GENERATOR, "report_generator_binding")
    expect(report.get("canonical_sha256") == EXPECTED_CANONICAL_RULE, "report_canonical_rule_binding")
    expect(report.get("rule_sha256") == {
        "opposite_opening": EXPECTED_CANONICAL_RULE,
        "through_opening": EXPECTED_ALTERNATE_RULE,
    }, "report_rule_bindings")
    expect(report.get("counts") == {"episodes": 2, "demonstrations": 6, "queries": 8}, "report_counts")

    episodes = report.get("episodes", [])
    episode_relations = {
        row.get("parameters", {}).get("ray_relation") for row in episodes if isinstance(row, dict)
    }
    expect(len(episodes) == 2 and episode_relations == RELATIONS, "unique_setting_coverage")
    expect(all(row.get("demonstrations") == 3 and row.get("queries") == 4 for row in episodes),
           "episode_counts")
    expect(len({row.get("public_id") for row in episodes}) == 2, "distinct_public_ids")

    manifest_files = manifest.get("files", {})
    expect(len(manifest_files) == 8, "manifest_file_count", len(manifest_files))
    manifest_ok = True
    for relative, meta in manifest_files.items():
        path = EVIDENCE / relative
        if not path.is_file() or path.stat().st_size != meta.get("bytes") or sha(path) != meta.get("sha256"):
            manifest_ok = False
            break
    expect(manifest_ok, "manifest_bytes_and_hashes")
    public_ids_ok = all(
        sha(EVIDENCE / row["public_path"]) == row["public_id"]
        and Path(row["public_path"]).stem == f"challenge-{row['public_id']}"
        for row in episodes
    )
    expect(public_ids_ok, "public_content_ids")
    expect(sha(EVIDENCE / "rules/opposite-opening.rkt") == EXPECTED_CANONICAL_RULE,
           "canonical_rule_exact")
    expect(sha(EVIDENCE / "rules/through-opening.rkt") == EXPECTED_ALTERNATE_RULE,
           "alternate_rule_exact")
    expect(verify == {
        "schema": "arcpuzzles-ray-relation-prototype-v1-verification-v1",
        "status": "pass",
        "episodes_checked": 2,
        "manifest_files_checked": 8,
        "errors": [],
    }, "independent_verify_receipt")

    test_result = load(ROOT / "checks/c5a69e7cd8c8-task-tests-final-v3/result.json")
    xml_root = ET.parse(ROOT / "checks/c5a69e7cd8c8-task-tests-final-v3/checks/task_tests.xml").getroot()
    suite = xml_root.find("testsuite")
    expect(test_result.get("passed") is True and test_result.get("status") == "completed",
           "selected_task_result_passed")
    expect(suite is not None and suite.get("tests") == "47" and suite.get("failures") == "0"
           and suite.get("errors") == "0", "selected_task_47_green")

    expect((ROOT / "checks/final-review-verifier-red.exit-status.txt").read_text().strip() == "1",
           "verifier_regression_red")
    expect((ROOT / "checks/final-review-verifier-green.exit-status.txt").read_text().strip() == "0",
           "verifier_regression_green")
    expect((ROOT / "checks/final-review-path-red.exit-status.txt").read_text().strip() == "1",
           "path_regression_red")
    expect((ROOT / "checks/final-review-path-green.exit-status.txt").read_text().strip() == "0",
           "path_regression_green")
    expect((ROOT / "checks/final-review-report-contract-red.exit-status.txt").read_text().strip() == "1",
           "report_contract_regression_red")
    expect((ROOT / "checks/final-review-report-contract-green.exit-status.txt").read_text().strip() == "0",
           "report_contract_regression_green")
    expect((ROOT / "checks/final/fresh-full-suite.exit-status.txt").read_text().strip() == "0",
           "fresh_full_suite_exit_zero")
    fresh_suite = ET.parse(ROOT / "checks/final/fresh-full-suite.xml").getroot().find("testsuite")
    expect(fresh_suite is not None and fresh_suite.get("tests") == "47"
           and fresh_suite.get("failures") == "0" and fresh_suite.get("errors") == "0",
           "fresh_full_suite_47_green")
    expect((ROOT / "checks/final/pycompile.exit-status.txt").read_text().strip() == "0",
           "pycompile_green")

    first_ticket = load(ROOT / "checks/tickets/ticket-ee286ae09f5cd6cb/result.json")
    second_ticket = load(ROOT / "checks/tickets/ticket-abdbdbca9ff76d39/result.json")
    expect(first_ticket.get("status") == "finding"
           and first_ticket.get("source_sha256") == "4c2410e8d185cd87ac946f28775c30046545fcd8a384b102c54c98e6705a860a"
           and first_ticket.get("comparison", {}).get("invalid_just_below_lower_boundary", {}).get("accepted") is True,
           "api_boundary_finding_bound")
    expect(second_ticket.get("status") == "completed" and second_ticket.get("reproduced") is True
           and second_ticket.get("identity", {}).get("source_sha256") == "ef8a2f160f6d5bdbcb9ec90ea9386db674688001eedba51fce050a5df56d482f"
           and second_ticket.get("sampler", {}).get("draws") == 300
           and second_ticket.get("shortcut", {}).get("generated_matches") == 64,
           "audit_replay_bound")
    expect((ROOT / "checks/tickets/ticket-ee286ae09f5cd6cb/exit-status.txt").read_text().strip() == "0",
           "api_ticket_exit_zero")
    expect((ROOT / "checks/tickets/ticket-abdbdbca9ff76d39/exit-status.txt").read_text().strip() == "0",
           "audit_ticket_exit_zero")

    audit = (ROOT / "AUDIT.md").read_text()
    headings = re.findall(r"^## ([0-9a-f]{12})$", audit, flags=re.MULTILINE)
    expect(headings == ["a3aafc2fb148"], "single_source_bound_audit_heading", headings)
    feedback = (ROOT / "FEEDBACK_TO_CODEX.md").read_text()
    expect("## F1: Biggest avoidable friction: machine-readable run receipts" in feedback,
           "substantive_feedback_present")

    results = load(ROOT / "RESULTS.json")
    rows = results.get("supplementary_tickets", [])
    expect([(row.get("ticket_id"), row.get("status")) for row in rows] == [
        ("ticket-ee286ae09f5cd6cb", "finding"),
        ("ticket-abdbdbca9ff76d39", "completed"),
    ], "exactly_two_ticket_rows")
    referenced = [
        path
        for command in results.get("verification_commands", [])
        for path in command.get("evidence_paths", [])
        if path != "checks/final/handoff-result.json"
    ]
    expect(all((ROOT / path).is_file() for path in referenced), "all_result_evidence_exists")
    expect("task-tests-parametric-green" not in (ROOT / "RESULTS.json").read_text(),
           "no_stale_result_paths")
    expect("task-tests-parametric-green" not in
           (ROOT / f"repo/generators/{TASK_ID}/workspace/parametric/README.md").read_text(),
           "no_stale_readme_paths")

    output = {
        "schema": "arcpuzzles-review-handoff-check-v1",
        "assignment_id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "summary": {
            "selected_task_tests": 47,
            "episodes": 2,
            "demonstrations": 6,
            "queries": 8,
            "manifest_files": 8,
            "supplementary_tickets": 2,
        },
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
