#!/usr/bin/env python3
"""Replay this task's retained seven outputs against actual canonical Racket.

From any cwd, use PYTHONPATH=/path/to/repo/shared/runtime and a working
RACKET_PATH, or invoke the packet's run_with_racket.py wrapper. Example:
  python /path/to/task/workspace/replay_counterexamples.py --out /new/report.json
Paths are discovered from this tool, never another packet or the current cwd.
This finite replay verifies stored labels and the named original lesson only;
it does not certify all generated inputs or unique rule induction.
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

TASK = "366cda05b486"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def load_generator(path):
    source = path.read_bytes()
    module = types.ModuleType("counterexample_replay_subject")
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module, sha(source)


def replay(generator, data_path):
    root = find_root(generator)
    ledger = canonical_path(root)
    with ledger.open(encoding="utf-8") as handle:
        source = next(row["program_solution"] for line in handle
                      if (row := json.loads(line)).get("task_id") == TASK)
    source_hash = sha(source.encode())
    rule_hash = sha(" ".join(source.split()).encode())[:12]
    body = strip_rule_wrapper(strip_line_comments(source))
    if not body.lstrip().startswith("(let "):
        raise ValueError("this task replay requires its known canonical let body")
    data_bytes = data_path.read_bytes()
    data = json.loads(data_bytes)
    if data.get("task_id") != TASK:
        raise ValueError("counterexample data belongs to a different task")
    module, generator_hash = load_generator(generator)
    errors = []
    if rule_hash != data.get("rule_hash") or rule_hash != module.RULE_HASH:
        errors.append("stored/selected/canonical rule hashes disagree")
    lesson = data["largest_cluster_lesson"]
    subjects = [(f"lesson_train_{i}", pair, False) for i, pair in enumerate(lesson["train"])]
    subjects += [(f"lesson_test_{i}", pair, False) for i, pair in enumerate(lesson["test"])]
    subjects += [(pair["name"], pair, True) for pair in data["boundaries"]]
    if len(subjects) != 7:
        errors.append(f"expected seven stored pairs, found {len(subjects)}")
    records = []
    bridge = RacketBridge()
    try:
        for name, pair, boundary in subjects:
            before = deepcopy(pair["input"])
            record = {"name": name, "boundary": boundary, "input_sha256": grid_hash(before),
                      "expected_output_sha256": grid_hash(pair["output"])}
            try:
                actual = bridge.eval_text(f"(let ([g {literal(before)}]) {body})")
                findings = module.self_check(before)
                record.update({"racket_output": actual, "racket_output_sha256": grid_hash(actual),
                               "matches_stored_output": actual == pair["output"],
                               "self_check": findings, "input_unchanged": before == pair["input"]})
                if actual != pair["output"]:
                    errors.append(f"{name}: Racket disagrees with stored output")
                if findings:
                    errors.append(f"{name}: self_check rejected retained input: {findings}")
                if before != pair["input"]:
                    errors.append(f"{name}: checker mutated input")
            except Exception as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
                errors.append(f"{name}: {record['error']}")
            records.append(record)
    finally:
        bridge.shutdown()
    demos, query = deepcopy(lesson["train"]), deepcopy(lesson["test"][0])
    reasons = module.lesson_identifiable(demos, query)
    largest = module.SEMANTIC_RIVALS["largest_cluster"]
    fits = all(largest(pair["input"]) == pair["output"] for pair in demos)
    differs = largest(query["input"]) != query["output"]
    if not isinstance(reasons, list) or not any("largest_cluster" in reason for reason in reasons):
        errors.append("lesson guard did not expose original largest_cluster ambiguity")
    if not fits or not differs:
        errors.append("largest_cluster does not fit demos and change query as stored")
    environment = {name: os.environ[name] for name in ("TMPDIR", "PYTHONPATH", "RACKET_PATH")
                   if name in os.environ}
    command = " ".join([*(f"{name}={shlex.quote(value)}" for name, value in environment.items()),
                        shlex.join([sys.executable, *sys.argv])])
    tool = Path(__file__).resolve()
    return {"schema": "366cda05b486-counterexample-racket-replay-v1", "task_id": TASK,
            "status": "passed" if not errors else "failed", "errors": errors,
            "executed_command": command, "cwd": str(Path.cwd()),
            "generator_path": str(generator), "generator_sha256": generator_hash,
            "tool_path": str(tool), "tool_sha256": sha(tool.read_bytes()),
            "data_path": str(data_path), "data_sha256": sha(data_bytes),
            "canonical_ledger_path": str(ledger), "canonical_ledger_sha256": sha(ledger.read_bytes()),
            "rule_source_sha256": source_hash, "executed_rule_hash": rule_hash,
            "baseline_generator_sha256": data.get("baseline_generator_sha256"),
            "outputs_checked": len(records),
            "outputs_matching": sum(record.get("matches_stored_output", False) for record in records),
            "boundary_inputs_accepted": sum(record.get("boundary", False) and record.get("self_check") == []
                                             for record in records),
            "records": records,
            "largest_cluster_lesson": {"guard_reasons": reasons, "rival_fits_demonstrations": fits,
                                       "rival_changes_query": differs,
                                       "query_prediction": largest(query["input"])},
            "scope": "Actual canonical Racket replay of seven stored labels, retained-input self_check acceptance, and original largest-cluster lesson guard. Finite evidence only; no training admission or approval."}


def main():
    home = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new evidence JSON; existing files refused")
    parser.add_argument("--generator", type=Path, default=home / "generator.py")
    parser.add_argument("--data", type=Path, default=home / "counterexamples/contact_regressions.json")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must name a new file")
    report = replay(args.generator.resolve(), args.data.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "outputs_checked",
                                                 "outputs_matching", "boundary_inputs_accepted", "errors")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
