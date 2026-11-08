#!/usr/bin/env python3
"""Execute the pinned Racket rule on repaired boundary cases and one lesson."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "9acebbb8a360"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = TASK_DIR / "generator.py"
SPEC = importlib.util.spec_from_file_location("racket_probe_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _sha(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def _load_rule() -> str:
    canonical = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in canonical.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rule = row.get("program_solution")
            if not rule:
                raise RuntimeError(f"canonical task {TASK_ID} has no program_solution")
            return rule
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _rule_application(rule: str, grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"({wrap_rule(rule)} '({rows}))"


def main() -> None:
    rule = _load_rule()
    cases = [
        {"label": "known_same_color_regression", "seed": 1, "sample": 0},
        {
            "label": "minimum_declared_canvas",
            "seed": 31,
            "sample": 7,
            "difficulty": "easy",
            "grid_h": 8,
            "grid_w": 10,
        },
        {
            "label": "maximum_declared_canvas",
            "seed": 31,
            "sample": 8,
            "difficulty": "hard",
            "grid_h": 13,
            "grid_w": 16,
        },
    ]

    results = []
    lesson_pairs = []
    bridge = RacketBridge(max_calls_before_restart=16)
    try:
        for case in cases:
            kwargs = {
                key: case[key]
                for key in ("difficulty", "grid_h", "grid_w")
                if key in case
            }
            grid = GEN.generate(case["seed"], case["sample"], **kwargs)
            racket_out = bridge.eval_text(_rule_application(rule, grid))
            mirror_out = GEN.rule_mirror(grid)
            assert racket_out == mirror_out, case["label"]
            assert GEN.self_check(grid) == []
            results.append(
                {
                    "label": case["label"],
                    "shape": [len(grid), len(grid[0])],
                    "input_sha256": _sha(grid),
                    "output_sha256": _sha(racket_out),
                    "racket_equals_mirror": True,
                }
            )
            lesson_pairs.append({"input": grid, "output": racket_out})
        assert GEN.lesson_identifiable(lesson_pairs[:2], lesson_pairs[2]) == []
    finally:
        bridge.shutdown()

    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "rule_hash": GEN.RULE_HASH,
                "cases": results,
                "lesson": {
                    "demos": 2,
                    "queries": 1,
                    "identifiable": True,
                    "rivals": sorted(GEN.LESSON_COMPETITORS),
                },
                "status": "pass",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
