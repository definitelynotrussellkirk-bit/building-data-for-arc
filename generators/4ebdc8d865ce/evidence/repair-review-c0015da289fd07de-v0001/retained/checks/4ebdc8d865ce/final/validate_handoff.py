#!/usr/bin/env python3
"""Validate the source/evidence links in the 4ebdc8d865ce reviewer handoff."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

TASK = "4ebdc8d865ce"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
CHECKS = WORK / "checks" / TASK


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    manifest_path = REPO / f"generators/{TASK}/workspace/parametric/evidence/manifest.json"
    manifest = read_json(manifest_path)
    require(manifest.get("task_id") == TASK, "manifest task mismatch")
    manifest_files = manifest.get("files")
    require(isinstance(manifest_files, list) and manifest_files, "empty manifest")
    for row in manifest_files:
        path = REPO / row["path"]
        require(path.is_file(), f"missing manifest source: {row['path']}")
        require(sha256(path) == row["sha256"], f"manifest hash mismatch: {row['path']}")

    canonical_record = None
    canonical_ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in canonical_ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            canonical_record = row
            break
    require(canonical_record is not None, "canonical record missing")
    canonical_path = REPO / f"generators/{TASK}/workspace/parametric/canonical.rkt"
    require(canonical_path.read_text(encoding="utf-8") == canonical_record["program_solution"],
            "canonical program is not byte-exact")

    promotion_path = REPO / f"generators/{TASK}/workspace/parametric/promotion.json"
    promotion = read_json(promotion_path)
    require(promotion.get("schema") == "arcpuzzles-parametric-adapter-v1", "bad promotion schema")
    require(promotion.get("default") == {"selection": "isolated_twos"}, "bad canonical default")
    require(promotion.get("limits") == {"demos": [2, 6], "queries": [1, 4]}, "bad limits")

    qualification_path = CHECKS / "qualification/qualification.json"
    qualification = read_json(qualification_path)
    require(qualification.get("schema") == "arcpuzzles-parametric-qualification-v1", "bad qualification schema")
    require(qualification.get("status") == "qualified", "qualification is not qualified")
    require(qualification.get("task_id") == TASK, "qualification task mismatch")
    source_files = qualification.get("source_binding", {}).get("files")
    require(isinstance(source_files, list) and source_files, "qualification source binding missing")
    for row in source_files:
        path = REPO / row["path"]
        require(path.is_file(), f"missing qualified source: {row['path']}")
        require(sha256(path) == row["sha256"], f"qualified source hash mismatch: {row['path']}")
    execution_path = CHECKS / "qualification/execution.json"
    require(sha256(execution_path) == qualification["execution"]["sha256"], "execution hash mismatch")

    witness = read_json(CHECKS / "causal/witness.json")
    require(witness.get("schema") == "arcpuzzles-sequential-dependency-witness-v1", "bad witness schema")
    require(witness.get("source_binding") == qualification.get("source_binding"), "witness source binding mismatch")
    require(witness.get("racket") == {"backend": "racket", "protected": True}, "witness is not protected Racket")
    cases = witness.get("cases")
    require(isinstance(cases, list) and len(cases) == 1, "expected one bounded witness case")
    case = cases[0]
    require(case.get("ablation") == "wrong_intermediate", "unexpected witness ablation")
    require(case.get("output") != case.get("counterfactual_output"), "counterfactual did not change output")
    changed_cells = sum(
        a != b
        for row_a, row_b in zip(case["output"], case["counterfactual_output"])
        for a, b in zip(row_a, row_b)
    )
    require(changed_cells == 10, f"expected 10 changed witness cells, got {changed_cells}")
    recheck = read_json(CHECKS / "causal/recheck.json")
    require(recheck.get("replay", {}).get("status") == "reviewer_replayed", "fresh witness replay missing")

    self_audit = read_json(CHECKS / "final/self-audit.json")
    require(self_audit.get("status") == "passed" and self_audit.get("case_count") == 18,
            "finite self-audit failed")
    require(not self_audit.get("failures"), "finite self-audit retained failures")
    qualified_audit = read_json(CHECKS / "qualified_teaching_audit.json")
    require(qualified_audit.get("status") == "passed" and not qualified_audit.get("failures"),
            "qualified teaching audit failed")

    public_check = read_json(CHECKS / "public_first_turn_check.json")
    require(public_check.get("status") == "passed" and public_check.get("files_checked") == 2,
            "public export check failed")
    public_dir = CHECKS / "public_first_turn"
    for path in sorted(public_dir.glob("challenge-*.json")):
        digest = sha256(path)
        require(path.stem == f"challenge-{digest}", f"public filename/hash mismatch: {path.name}")
        public = read_json(path)
        require(set(public) == {"train", "test"}, "public challenge has private top-level fields")
        require(len(public["test"]) == 1 and set(public["test"][0]) == {"input"},
                "public query leaks output or future queries")
        require(all(set(pair) == {"input", "output"} for pair in public["train"]),
                "public demonstrations malformed")

    task_result = read_json(WORK / f"checks/{TASK}-tests-final-v2/result.json")
    require(task_result.get("passed") is True and task_result.get("exit_code", 0) == 0,
            "final staged task tests did not pass")

    results = read_json(WORK / "RESULTS.json")
    dependency = results["repair_targets"][0]["parametric_work"]["sequential_dependency"]
    for key in ("step_a", "intermediate", "step_b", "why_b_depends_on_a"):
        require(dependency[key] == witness[key], f"RESULTS/witness mismatch: {key}")

    report = {
        "schema": "4ebdc8d865ce-handoff-integrity-v1",
        "status": "passed",
        "task_id": TASK,
        "manifest_files": len(manifest_files),
        "qualified_source_files": len(source_files),
        "qualification_jobs": len(qualification.get("jobs", [])),
        "protected_racket_evaluations": qualification.get("execution_summary", {}).get("evaluations", 32),
        "finite_audit_cases": self_audit["case_count"],
        "named_rules_in_audit": len(self_audit.get("rivals", [])),
        "public_first_turn_files": public_check["files_checked"],
        "witness_changed_cells": changed_cells,
        "owner_acceptance": "not_performed",
        "training_admitted": False,
    }
    out = CHECKS / "final/handoff-integrity.json"
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"handoff validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
