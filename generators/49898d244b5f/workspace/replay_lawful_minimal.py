#!/usr/bin/env python3
"""Replay three geometric boundary inputs against actual canonical Racket.

From any cwd, with existing runtime on PYTHONPATH and RACKET_PATH configured:
  python /path/to/task/workspace/replay_lawful_minimal.py --out /new/report.json
Defaults resolve beside this tool; --generator and --data accept relocated files.
This reports rule/validator facts, not a waiver of a shared heuristic warning.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
import types

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root

TASK = "49898d244b5f"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def run(generator, data_path):
    root = find_root(Path(__file__).resolve())
    ledger = canonical_path(root)
    with ledger.open() as handle:
        source = next(row["program_solution"] for line in handle
                      if (row := json.loads(line)).get("task_id") == TASK)
    rule_hash = digest(" ".join(source.split()).encode())[:12]
    data_bytes, generator_bytes = data_path.read_bytes(), generator.read_bytes()
    data = json.loads(data_bytes)
    module = types.ModuleType("lawful_minimal_subject")
    module.__file__ = str(generator)
    exec(compile(generator_bytes, str(generator), "exec"), module.__dict__)
    errors = []
    if data["task_id"] != TASK or data["rule_hash"] != rule_hash:
        errors.append("data does not match selected task and canonical rule")
    body = strip_rule_wrapper(strip_line_comments(source))
    cases = []
    bridge = RacketBridge()
    try:
        for case in data["cases"]:
            supplied = deepcopy(case["input"])
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in supplied) + ")"
            actual = bridge.eval_text(f"(let ([g {literal}]) {body})")
            mirror = module.expected_output(supplied)
            reasons = module.self_check(supplied)
            strict = module.strict_canonical_like(supplied)
            accepted = reasons == []
            strict_accepted = strict is True or strict == []
            occupied = [sum(row[c] != 0 for row in supplied) for c in range(len(supplied[0]))]
            filled = [c for c in range(len(actual[0])) if all(row[c] != 0 for row in actual)]
            checks = {
                "stored_label_matches_racket": actual == case["output"],
                "mirror_matches_racket": mirror == actual,
                "validator_matches_declared_domain": accepted == case["positive_generator_domain"],
                "strict_matches_declared_domain": strict_accepted == case["positive_generator_domain"],
                "filled_columns_match_stored_fact": filled == case["filled_columns"],
                "input_unchanged": supplied == case["input"],
            }
            for name, passed in checks.items():
                if not passed:
                    errors.append(f"{case['name']}: {name}")
            cases.append({**case, "input_sha256": grid_hash(supplied), "racket_output": actual,
                          "racket_output_sha256": grid_hash(actual), "occupied_cells_per_column": occupied,
                          "actual_filled_columns": filled, "self_check_reasons": reasons,
                          "strict_result": strict, "checks": checks})
    finally:
        bridge.shutdown()
    env = {key: os.environ[key] for key in ("TMPDIR", "PYTHONPATH", "RACKET_PATH") if key in os.environ}
    command = " ".join([*(f"{key}={shlex.quote(value)}" for key, value in env.items()),
                        shlex.join([sys.executable, *sys.argv])])
    return {"schema": "49898d244b5f-lawful-minimal-replay-v1", "task_id": TASK,
            "status": "failed" if errors else "passed", "errors": errors,
            "executed_command": command, "cwd": str(Path.cwd()),
            "generator_path": str(generator), "generator_sha256": digest(generator_bytes),
            "data_sha256": digest(data_bytes), "tool_sha256": digest(Path(__file__).read_bytes()),
            "canonical_ledger_sha256": digest(ledger.read_bytes()),
            "rule_source_sha256": digest(source.encode()), "executed_rule_hash": rule_hash,
            "case_count": len(cases), "cases": cases,
            "scope": "Three fixed geometric boundary facts labeled by actual Racket. No shared detector changes, waiver, exhaustive coverage, or production-admission claim."}


def main():
    home = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=home / "generator.py")
    parser.add_argument("--data", type=Path, default=home / "counterexamples/lawful_minimal_inputs.json")
    parser.add_argument("--out", type=Path, required=True, help="new report file; existing output refused")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must name a new file")
    report = run(args.generator.resolve(), args.data.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "executed_rule_hash", "case_count", "errors")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
