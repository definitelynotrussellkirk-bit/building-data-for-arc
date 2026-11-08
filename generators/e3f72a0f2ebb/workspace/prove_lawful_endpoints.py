"""Retain Racket-backed evidence for this task's lawful minimal inputs.

This does not waive or alter the shared defect linter. It checks explicit task
claims, including negative validator controls, and saves the actual authority
outputs for a maintainer to judge the linter's generic warnings.

Run via run_with_racket.py from WORK, or the outer review.py run wrapper.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK = "e3f72a0f2ebb"
EXPECTED_RULE_HASH = "8d3a7f6a327b"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def build_cases():
    cases = []
    for color in (1, 3, 9):
        for name in ("singleton", "short_line", "solid_2x2", "full_one_color"):
            grid = [[0] * 10 for _ in range(8)]
            if name == "singleton":
                grid[4][5] = color
            elif name == "short_line":
                grid[4][:4] = [color] * 4
            elif name == "solid_2x2":
                grid[0][:2] = [color] * 2
                grid[1][:2] = [color] * 2
            else:
                grid = [[color] * 10 for _ in range(8)]
            # These expectations come from the endpoint geometry, not the
            # generator's component or frame helper.
            expected = [row[:] for row in grid]
            if name == "full_one_color":
                expected = [[color if r in (0, 7) or c in (0, 9) else 0
                             for c in range(10)] for r in range(8)]
            cases.append({"name": name, "foreground": color,
                          "input": grid, "expected_output": expected,
                          "expected_validator_acceptance": True})
    return cases


def record_exception(report, stage, exc, **context):
    error = {"stage": stage, "type": type(exc).__name__,
             "message": str(exc), **context}
    # Public Catalog failures carry the bounded child-process receipt here.
    # Keep it even when no successful reference payload was returned.
    if getattr(exc, "run", None) is not None:
        error["run"] = exc.run
    report["execution_errors"].append(error)
    report["failures"].append({"execution_error": len(report["execution_errors"]) - 1})
    return error


def check_validator(gen, case, report, stage, index):
    if gen is None:
        return
    try:
        case["validator_messages"] = gen.self_check(case["input"])
        case["validator_status"] = "completed"
    except Exception as exc:
        case["validator_status"] = "error"
        case["validator_error"] = record_exception(
            report, stage, exc, case=index, name=case["name"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite evidence: {args.out}")
    cases = build_cases()
    # Build all case records before loading or executing the subject. A failed
    # operation must leave an explicit unknown/error, not an omitted case.
    negatives = [{"name": name, "input": grid} for name, grid in [
        ("empty", []), ("all_background", [[0] * 10 for _ in range(8)]),
        ("ragged", [[0, 1], [0]]), ("bool_cell", [[True]]),
        ("outside_palette", [[10]]), ("overlapping_boxes", None),
    ]]
    for case in cases + negatives:
        case.update(validator_messages=None, validator_status="not_run",
                    validator_error=None)
    for case in cases:
        case.update(actual_output=None, reference_matches_expected=None, passed=False)
    for case in negatives:
        case.update(expected_validator_acceptance=False, rejected=False)
    report = {
        "schema": "outline-lawful-endpoints-v1", "task_id": TASK,
        "generator_sha256": None,
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "expected_rule_hash": EXPECTED_RULE_HASH, "rule_hash": None,
        "argv": sys.argv, "cwd": str(Path.cwd()),
        "status": "running", "completed": False,
        "lawful_cases": len(cases), "lawful_cases_passed": 0,
        "negative_controls": len(negatives), "negative_controls_rejected": 0,
        "cases": cases, "negative_cases": negatives,
        "failures": [], "execution_errors": [],
        "reference_receipt": None, "reference_status": "not_run",
        "limitations": "Finite task-specific evidence. Shared defect-lint status is unchanged; these results neither suppress warnings nor approve a source.",
    }
    failures = report["failures"]
    root = source = gen = None
    try:
        root = find_root(__file__)
        source = root / "generators" / TASK / "generator.py"
        report["generator_sha256"] = digest(source.read_bytes())
    except Exception as exc:
        record_exception(report, "source_preparation", exc)
    if source is not None and report["generator_sha256"] is not None:
        try:
            negatives[-1]["input"] = json.loads((source.parent / "counterexamples" /
                "baseline-frame-interference-seed503-index26.json").read_text())["input"]
        except Exception as exc:
            negatives[-1]["input_error"] = record_exception(report, "negative_input_preparation", exc)
        try:
            spec = importlib.util.spec_from_file_location("outline_endpoint_subject", source)
            loaded = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loaded)
            gen = loaded
        except Exception as exc:
            record_exception(report, "generator_import", exc)

    results = []
    if root is not None:
        try:
            actual = Catalog(root=root).apply(TASK, [c["input"] for c in cases], timeout=180)
            report["reference_receipt"] = actual
            if not isinstance(actual, dict):
                raise TypeError("Catalog.apply did not return a result object")
            report["rule_hash"] = actual.get("executed_rule_hash")
            rows = actual.get("results", [])
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise TypeError("Catalog.apply results must be a list of result objects")
            results = rows
            report["reference_status"] = "completed"
            if actual.get("executed_rule_hash") != EXPECTED_RULE_HASH or not actual.get("rule_hash_matches_catalog"):
                failures.append("selected Racket authority does not match the reviewed rule")
            if actual.get("generator_sha256") != report["generator_sha256"]:
                failures.append("reference receipt generator source differs from the proof subject")
            if len(results) != len(cases):
                failures.append("Racket result count mismatch")
        except Exception as exc:
            report["reference_status"] = "error"
            record_exception(report, "reference_execution", exc)

    for index, case in enumerate(cases):
        if report["reference_status"] == "completed":
            case["actual_output"] = results[index].get("output") if index < len(results) else None
            case["reference_matches_expected"] = case["actual_output"] == case["expected_output"]
            if not case["reference_matches_expected"]:
                failures.append({"reference_mismatch": index, "name": case["name"],
                                 "foreground": case["foreground"]})
        check_validator(gen, case, report, "positive_validator", index)
        accepted = case["validator_status"] == "completed" and not case["validator_messages"]
        if case["validator_status"] == "completed" and not accepted:
            failures.append({"lawful_case_rejected": index, "name": case["name"],
                             "foreground": case["foreground"]})
        case["passed"] = case["reference_matches_expected"] is True and accepted
    for index, case in enumerate(negatives):
        if case["input"] is not None:
            check_validator(gen, case, report, "negative_validator", index)
        case["rejected"] = case["validator_status"] == "completed" and bool(case["validator_messages"])
        if case["validator_status"] == "completed" and not case["rejected"]:
            failures.append({"negative_control_accepted": case["name"]})

    if source is not None and report["generator_sha256"] is not None:
        try:
            report["generator_sha256_after"] = digest(source.read_bytes())
            if report["generator_sha256_after"] != report["generator_sha256"]:
                failures.append("generator source changed during the proof")
        except Exception as exc:
            record_exception(report, "source_verification", exc)
    report.update(status="failed" if failures else "passed", completed=True,
                  lawful_cases_passed=sum(c["passed"] for c in cases),
                  negative_controls_rejected=sum(c["rejected"] for c in negatives))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2) + "\n"
    try:
        with args.out.open("x") as handle:
            handle.write(payload)
    except FileExistsError:
        parser.error(f"refusing to overwrite evidence: {args.out}")
    print(json.dumps({k: report[k] for k in ("status", "lawful_cases_passed", "lawful_cases", "negative_controls_rejected", "negative_controls", "generator_sha256")}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
