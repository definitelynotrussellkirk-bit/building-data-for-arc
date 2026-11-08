#!/usr/bin/env python3
"""Revalidate the existing constant-output audit on the pinned source hash."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
TASK = "2ed2f53ebb44"
AUDIT = WORK / "checks" / "audit" / TASK
CANONICAL = WORK / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"
GENERATOR = WORK / "repo" / "generators" / TASK / "generator.py"


def load_task() -> dict:
    for line in CANONICAL.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK:
            return record
    raise RuntimeError(f"missing canonical task {TASK}")


def main() -> None:
    canonical = load_task()
    constant = canonical["train"][0]["output"]
    canonical_fit = [pair["output"] == constant for pair in canonical["train"]]
    held_out = canonical.get("test")
    held_out_fit = bool(isinstance(held_out, dict) and held_out.get("output") == constant)
    assert all(canonical_fit) and held_out_fit

    racket = json.loads((AUDIT / "racket.json").read_text())
    result = racket["results"][0]
    actual = result["output"]
    assert actual != constant

    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "finding": (
            "All five canonical demonstrations have the same 3x3 matrix, so a constant-output rival fits all. "
            "The retained generated six-component input is in-domain and produces a different 6x6 matrix."
        ),
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "generation": {"seed": 424242, "sample_index": 8, "difficulty": "hard", "overrides": {}},
        "canonical_demonstrations_checked": len(canonical_fit),
        "canonical_rival_fit": canonical_fit,
        "canonical_held_out_checked": 1,
        "canonical_held_out_fit": held_out_fit,
        "documented_generator_domain": result["generator_domain"]["status"] == "valid",
        "self_check_errors": result["generator_domain"]["errors"],
        "input": result["input"],
        "actual_racket_output": actual,
        "rival_name": "constant_canonical_3x3_matrix",
        "rival_output": constant,
        "prior_audit_lead": "review-4cd35f21d087afc9:v0001",
        "command": {
            "cwd": "WORK",
            "argv": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                "--input", "../checks/audit/2ed2f53ebb44/input.json", "--check-generator-domain",
                "--out", "../checks/audit/2ed2f53ebb44/racket.json",
            ],
        },
    }
    (AUDIT / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
