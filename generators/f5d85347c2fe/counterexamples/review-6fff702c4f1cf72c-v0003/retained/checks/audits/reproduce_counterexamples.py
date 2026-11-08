#!/usr/bin/env python3
"""Replay the two assigned adversarial-audit domain counterexamples.

This is evidence, not a repository source change.  ``run_with_racket.py``
changes into ``repo/``, so run it from the packet root via:
    python3 run_with_racket.py python3 ../checks/audits/reproduce_counterexamples.py
"""
from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "repo"), str(ROOT / ".review/audit_runtime"), str(ROOT / "repo/src"), str(ROOT / "repo/shared/runtime")]

# ``puzzle_generators.rule_wrap`` imports the repository utility through the
# historical module path ``scripts.comment_solutions``.  Full review packets
# store that utility under ``repo/shared/tools`` and do not return the private
# ``.review/audit_runtime`` directory, so bind the packaged file explicitly.
scripts_package = sys.modules.setdefault("scripts", types.ModuleType("scripts"))
scripts_package.__path__ = []
comment_path = ROOT / "repo/shared/tools/comment_solutions.py"
comment_spec = importlib.util.spec_from_file_location("scripts.comment_solutions", comment_path)
if comment_spec is None or comment_spec.loader is None:
    raise RuntimeError(f"could not load {comment_path}")
comment_module = importlib.util.module_from_spec(comment_spec)
sys.modules["scripts.comment_solutions"] = comment_module
comment_spec.loader.exec_module(comment_module)
scripts_package.comment_solutions = comment_module

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def _norm_grid(grid):
    return [[int(value) for value in row] for row in grid]


def _grid_literal(grid):
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"\'({rows})"


def rule_application(source, grid):
    return f"({wrap_rule(source)} {_grid_literal(grid)})"

CASES = {
    "b37eb391ddc0": [
        [2, 3],
        [0, 2],
    ],
    "f5d85347c2fe": [
        [5, 5, 5, 5, 5],
        [5, 2, 0, 2, 5],
        [5, 0, 0, 0, 5],
        [5, 5, 5, 5, 5],
    ],
}


def canonical_sources() -> dict[str, str]:
    wanted = set(CASES)
    found: dict[str, str] = {}
    ledger = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        task_id = row.get("task_id")
        if task_id in wanted and isinstance(row.get("program_solution"), str):
            found[task_id] = row["program_solution"]
    missing = sorted(wanted - set(found))
    if missing:
        raise RuntimeError(f"missing canonical rule source for {missing}")
    return found


def main() -> None:
    sources = canonical_sources()
    bridge = RacketBridge()
    records = []
    try:
        for task_id, grid in CASES.items():
            module = importlib.import_module(f"generators.{task_id}.generator")
            authority_output = bridge.eval_text(rule_application(sources[task_id], _norm_grid(grid)))
            findings = module.self_check([row[:] for row in grid])
            records.append(
                {
                    "task_id": task_id,
                    "input": grid,
                    "canonical_authority_output": authority_output,
                    "generator_self_check_findings": findings,
                    "domain_mismatch_reproduced": bool(findings),
                }
            )
    finally:
        bridge.close()
    payload = {"schema": "assigned-audit-counterexamples-v1", "records": records}
    out = ROOT / "checks/audits/counterexamples.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not all(record["domain_mismatch_reproduced"] for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
