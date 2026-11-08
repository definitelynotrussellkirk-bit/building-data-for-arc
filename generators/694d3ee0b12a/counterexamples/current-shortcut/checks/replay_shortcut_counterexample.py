#!/usr/bin/env python3
"""Replay the exact fixed-bottom-right-key shortcut counterexample.

Run from the review packet root with:
    python3 run_with_racket.py python3 ../checks/replay_shortcut_counterexample.py

The script writes checks/shortcut-counterexample.json and exits nonzero if the
Python mirror disagrees with the selected Racket authority or if the claimed
shortcut does not fit every canonical demonstration.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET_ROOT = Path(__file__).resolve().parents[1]
REPO = PACKET_ROOT / "repo"
TASK_ID = "694d3ee0b12a"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT = PACKET_ROOT / "checks" / "shortcut-counterexample.json"

for path in (REPO, REPO / "shared" / "runtime"):
    sys.path.insert(0, str(path))

# The compact source packet stores the historical ``scripts`` modules under
# shared/tools.  Expose that directory as the package name expected by the
# rule wrapper without creating or modifying repository files.
import types
scripts_package = types.ModuleType("scripts")
scripts_package.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_package)

spec = importlib.util.spec_from_file_location(f"g_{TASK_ID}", GENERATOR)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {GENERATOR}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

canonical_row = None
with CANONICAL.open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("program_solution"):
            canonical_row = row
            break
if canonical_row is None:
    raise RuntimeError("selected canonical rule not found")

seed = 0
sample_index = 0
profile = "pair_down_right"
grid = module.generate(
    seed,
    sample_index,
    difficulty="medium",
    scene_profile=profile,
)
mirror_output = module.rule_mirror(grid)
rival_output = module.CANONICAL_SHORTCUTS["fixed_bottom_right_key"](grid)
if mirror_output is None or rival_output is None:
    raise RuntimeError("mirror or rival rejected generated witness")

differences = [
    {"row": row, "col": col, "intended": mirror_output[row][col], "rival": rival_output[row][col]}
    for row in range(len(grid))
    for col in range(len(grid[0]))
    if mirror_output[row][col] != rival_output[row][col]
]
if not differences:
    raise RuntimeError("generated witness does not refute the fixed-key shortcut")

canonical_pairs = list(canonical_row.get("train") or []) + list(canonical_row.get("test") or [])
shortcut_fits = [
    module.CANONICAL_SHORTCUTS["fixed_bottom_right_key"](pair["input"]) == pair["output"]
    for pair in canonical_pairs
]
if not canonical_pairs or not all(shortcut_fits):
    raise RuntimeError("fixed-key shortcut does not fit every canonical pair")

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def grid_literal(value: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(cell) for cell in row) + ")" for row in value)
    return f"'({rows})"

rule_source = canonical_row["program_solution"]
with RacketBridge(max_calls_before_restart=48) as bridge:
    racket_output = bridge.eval_text(f"({wrap_rule(rule_source)} {grid_literal(grid)})")
if racket_output != mirror_output:
    raise RuntimeError("Python mirror disagrees with selected Racket authority")

payload = {
    "schema": "shortcut-counterexample-v1",
    "task_id": TASK_ID,
    "generator_version": module.VERSION,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "shortcut": "Use local bottom-right interior cell (5,5) as every frame's fill key.",
    "canonical_pairs_checked": len(canonical_pairs),
    "shortcut_fits_all_canonical_pairs": all(shortcut_fits),
    "generation": {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "scene_profile": profile,
        "observed_overrides": module.observe_overrides(grid),
    },
    "input": grid,
    "authoritative_output": racket_output,
    "python_mirror_output": mirror_output,
    "shortcut_output": rival_output,
    "differing_cells": differences,
    "checks": {
        "self_check": module.self_check(grid),
        "racket_equals_python_mirror": racket_output == mirror_output,
        "shortcut_refuted": rival_output != racket_output,
    },
}
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "out": str(OUT),
    "canonical_pairs_checked": len(canonical_pairs),
    "differing_cells": differences,
    "racket_equals_python_mirror": racket_output == mirror_output,
}, sort_keys=True))
