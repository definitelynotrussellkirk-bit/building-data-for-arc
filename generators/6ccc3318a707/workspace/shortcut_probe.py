#!/usr/bin/env python3
"""Reproduce semantic shortcut disagreements for generator 6ccc3318a707.

Run from anywhere inside the review repository:
    python3 generators/6ccc3318a707/workspace/shortcut_probe.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "6ccc3318a707"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SOURCE}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

COLLISION_INPUT = [
    [2, 0, 0, 0, 0, 4],
    [0, 5, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 3],
]


def main() -> None:
    intended = gen.rule_mirror(COLLISION_INPUT)
    rival = gen.CANONICAL_SHORTCUTS["keep_occupied_pairs"](COLLISION_INPUT)
    generated = [gen.generate(1729, index, difficulty="medium") for index in range(12)]
    report = {
        "task_id": TASK_ID,
        "rule_hash": gen.RULE_HASH,
        "collision_input": COLLISION_INPUT,
        "intended_output": intended,
        "keep_occupied_pairs_output": rival,
        "disagrees": intended != rival,
        "generated_cases_checked": len(generated),
        "generated_cases_with_occupied_pair_witness": sum(
            int(gen.SEMANTIC_WITNESSES["occupied_pair_swaps"](grid))
            for grid in generated
        ),
        "all_declared_rivals_refuted_per_case": [
            all(fn(grid) != gen.rule_mirror(grid) for fn in gen.SEMANTIC_RIVALS.values())
            for grid in generated
        ],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
