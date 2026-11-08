"""Verify public-reference receipts and unchanged audited task files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from reviewer_support import canonical_path, find_root


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def read(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    identity = read("identity.json")
    current = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "generators" / identity["task_id"]).rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
    assert current == identity["task_file_sha256"], "audited task files changed"
    ledger_rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    current_rules = list(dict.fromkeys(row["program_solution"] for row in ledger_rows if row.get("task_id") == identity["task_id"]))
    assert current_rules == identity["canonical_rule"], "canonical rule changed"

    receipt = read("racket_apply.json")
    cases = read("oracle_cases.json")
    inputs = read("apply_inputs.json")["inputs"]
    assert receipt["generator_sha256"] == identity["generator_sha256"]
    assert receipt["executed_rule_hash"] == identity["declared_rule_hash"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == len(cases) == len(inputs) == 27
    reference_results = []
    for index, (case, result, grid) in enumerate(zip(cases, receipt["results"], inputs)):
        assert result["index"] == case["input_index"] == index
        assert result["input"] == grid
        assert result["input_sha256"] == case["input_sha256"]
        assert result["valid_output"] is True and result["error"] is None
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert result["output"] == case["expected_output"] == case["mirror_output"]
        reference_results.append({
            "index": index, "label": case["label"],
            "input_sha256": result["input_sha256"],
            "actual_racket_output": result["output"],
            "independent_expected_output": case["expected_output"],
            "rival_output": case["rival_output"],
            "generator_domain": result["generator_domain"],
        })

    audit = read("combined/result.json")
    preset = audit["audit_summary"]
    assert preset["preset_complete"] and preset["passed"]
    assert preset["generator_sha256"] == identity["generator_sha256"]
    assert preset["changed_runtime_sources"] == []
    assert preset["stages"]["semantic_gate"]["semantic_status"] == "green"
    xml = ET.parse(HERE / "combined/checks/task_tests.xml").getroot()
    tests = list(xml.iter("testcase"))
    unique_functions = {(case.get("classname"), case.get("name").split("[")[0]) for case in tests}
    assert len(tests) == 80

    finding = read("counterexample.json")
    counterexample_result = reference_results[-1]
    assert counterexample_result["actual_racket_output"] != counterexample_result["rival_output"]
    finding["public_reference"] = {
        "receipt": "racket_apply.json",
        "result_index": 26,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "executed_rule_text_sha256": receipt["rule_text_sha256"],
        "generator_sha256": receipt["generator_sha256"],
        "actual_output": counterexample_result["actual_racket_output"],
        "valid_output": True,
        "generator_domain": counterexample_result["generator_domain"],
        "input_sha256": counterexample_result["input_sha256"],
    }
    save("counterexample.json", finding)

    summary = {
        "task_id": identity["task_id"],
        "generator_sha256": identity["generator_sha256"],
        "rule_hash": receipt["executed_rule_hash"],
        "canonical_ledger_program_text_sha256": identity["canonical_rule_text_sha256"],
        "executed_rule_text_sha256": receipt["rule_text_sha256"],
        "unchanged_task_files": len(current),
        "task_files_unchanged": True,
        "canonical_rule_unchanged": True,
        "public_racket_valid_outputs": len(reference_results),
        "public_racket_matches_independent_oracle": len(reference_results),
        "public_racket_domain_accepted": len(reference_results),
        "audit_preset_passed": preset["passed"],
        "audit_requested_stages": preset["expected_stages"],
        "audit_completed_stages": preset["completed_stages"],
        "task_tests": preset["stages"]["task_tests"]["test_counts"],
        "unique_test_functions": len(unique_functions),
        "semantic_gate_status": preset["stages"]["semantic_gate"]["semantic_status"],
        "full_12_stage_battery_replayed": False,
        "battery_summary": audit["battery_summary"]["verdict_note"],
        "counterexample": counterexample_result,
    }
    save("reference_verification.json", {"summary": summary, "results": reference_results})
    probe_summary = read("probe_summary.json")
    probe_summary["racket_status"] = "27 public apply results valid and matched independent oracle"
    probe_summary["reference_verification"] = "reference_verification.json"
    save("probe_summary.json", probe_summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
