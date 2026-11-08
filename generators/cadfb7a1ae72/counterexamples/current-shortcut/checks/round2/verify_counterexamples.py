from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "repo" / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(ROOT / "repo" / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_pkg)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "cadfb7a1ae72"
TASK = ROOT / "repo" / "generators" / TASK_ID
CANONICAL = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"


def grid_literal(grid):
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def sha_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def find_rule():
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical rule not found")


def check_one(bridge, rule, filename, rivals):
    path = TASK / "workspace" / filename
    report = json.loads(path.read_text())
    actual = bridge.eval_text(f"({wrap_rule(rule)} {grid_literal(report['input'])})")
    intended = report["intended_output"]
    results = {
        "report": f"repo/generators/{TASK_ID}/workspace/{filename}",
        "input_sha256": sha_grid(report["input"]),
        "profile": report["recognized_profile"],
        "dimensions": report["dimensions"],
        "racket_matches_python_mirror": actual == intended,
        "racket_output": actual,
        "python_mirror_output": intended,
        "rivals": {
            name: {
                "first_disagreement": report["rivals"][name]["first_disagreement"],
                "output": report["rivals"][name]["output"],
            }
            for name in rivals
        },
    }
    if filename == "example_projection_report.json":
        left, right = report["objects"][1], report["objects"][3]
        results["structural_collision"] = {
            "object_indices": [1, 3],
            "exact_symmetry_classes": [left["symmetry_class"], right["symmetry_class"]],
            "projection_symmetry_classes": [left["projection_symmetry_class"], right["projection_symmetry_class"]],
            "hole_regions": [left["holes"], right["holes"]],
            "normalized_cells": [left["normalized_cells"], right["normalized_cells"]],
        }
    if filename == "example_binary_holes_report.json":
        left, right = report["objects"][0], report["objects"][2]
        results["structural_collision"] = {
            "object_indices": [0, 2],
            "hole_regions": [left["holes"], right["holes"]],
            "enclosed_zero_cells": [left["enclosed_zero_cells"], right["enclosed_zero_cells"]],
            "exact_symmetry_classes": [left["symmetry_class"], right["symmetry_class"]],
            "normalized_cells": [left["normalized_cells"], right["normalized_cells"]],
        }
    if actual != intended or any(results["rivals"][name]["first_disagreement"] is None for name in rivals):
        raise RuntimeError(f"counterexample verification failed: {filename}")
    return results


def main():
    rule = find_rule()
    bridge = RacketBridge(max_calls_before_restart=8)
    try:
        examples = [
            check_one(bridge, rule, "example_projection_report.json", ["projection_symmetry"]),
            check_one(bridge, rule, "example_binary_holes_report.json", ["binary_holes", "enclosed_hole_cells"]),
        ]
    finally:
        bridge.close()
    result = {
        "task_id": TASK_ID,
        "canonical_rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
        "examples": examples,
        "all_racket_matches": all(item["racket_matches_python_mirror"] for item in examples),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
