#!/usr/bin/env python3
"""Replay the canonical ambiguity and decisive counterexample for 6098a755202d.

The canonical demonstrations use distinct seed colours, so the plausible rival
"any tie between seed cells stays zero" matches every demonstrated output.  The
canonical Racket program instead removes duplicate *colours* before resolving a
tie.  This tool proves both facts and emits a small, copy-pastable witness.

Run from any directory:

    python3 workspace/analyze_shortcut.py
    python3 workspace/analyze_shortcut.py --racket
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

TASK_ID = "6098a755202d"
GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GENERATOR_DIR.parents[1]
GENERATOR_PATH = GENERATOR_DIR / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
TOOLS_ROOT = REPO_ROOT / "shared" / "tools"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
# Runtime modules use the relocated package name ``scripts.*``.  In a source
# checkout those files live flat under shared/tools, so expose the same namespace
# without copying or depending on a prepared runtime.
if "scripts" not in sys.modules:
    scripts_package = types.ModuleType("scripts")
    scripts_package.__path__ = [str(TOOLS_ROOT)]
    scripts_package.__package__ = "scripts"
    sys.modules["scripts"] = scripts_package

WITNESS_ROWS = (
    "000000000",
    "055555550",
    "052000250",
    "050000050",
    "050000050",
    "050030050",
    "055555550",
    "000000000",
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_shortcut_analysis", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list):
        raise TypeError(f"expected grid list, got {type(value).__name__}")
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def _canonical_row() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} is missing")


def _pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    test = row.get("test") or []
    tests = test if isinstance(test, list) else [test]
    return [*(row.get("train") or []), *tests]


def _rule_application(program: str, grid: list[list[int]]) -> str:
    from puzzle_generators.rule_wrap import wrap_rule

    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    )
    return f"({wrap_rule(program)} '({rows}))"


def _racket_output(program: str, grid: list[list[int]]) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        output = bridge.eval_text(_rule_application(program, grid))
    return _grid(output)


def analyze(*, use_racket: bool = False) -> dict[str, Any]:
    generator = _load_generator()
    canonical = _canonical_row()
    canonical_checks = []
    for index, pair in enumerate(_pairs(canonical)):
        input_grid = _grid(pair["input"])
        expected = _grid(pair["output"])
        intended = generator.rule_mirror(copy.deepcopy(input_grid))
        rival = generator._tie_by_seed_rival(copy.deepcopy(input_grid))
        canonical_checks.append(
            {
                "pair_index": index,
                "intended_matches_expected": intended == expected,
                "rival_matches_expected": rival == expected,
            }
        )

    witness = _grid(list(WITNESS_ROWS))
    intended = generator.rule_mirror(copy.deepcopy(witness))
    rival = generator._tie_by_seed_rival(copy.deepcopy(witness))
    differences = [
        [r, c, intended[r][c], rival[r][c]]
        for r in range(len(witness))
        for c in range(len(witness[0]))
        if intended[r][c] != rival[r][c]
    ]
    observables = generator.semantic_observables(witness)
    witness_report: dict[str, Any] = {
        "input": witness,
        "intended_output": intended,
        "tie_by_seed_output": rival,
        "differences": differences,
        "self_check_errors": generator.self_check(witness),
        "profile": observables.get("profile"),
        "same_color_tie_cells": observables.get("same_color_tie_cells"),
    }
    if use_racket:
        racket = _racket_output(canonical["program_solution"], witness)
        witness_report["racket_output"] = racket
        witness_report["racket_matches_rule_mirror"] = racket == intended

    return {
        "task_id": TASK_ID,
        "rival": "tie_by_seed",
        "claim": (
            "Leave a cell at 0 whenever multiple nearest seed cells tie, "
            "without deduplicating tied seed colours."
        ),
        "canonical_checks": canonical_checks,
        "rival_fits_all_canonical_pairs": all(
            item["rival_matches_expected"] for item in canonical_checks
        ),
        "intended_fits_all_canonical_pairs": all(
            item["intended_matches_expected"] for item in canonical_checks
        ),
        "witness": witness_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--racket",
        action="store_true",
        help="also execute the canonical Racket rule on the witness",
    )
    parser.add_argument(
        "--compact", action="store_true", help="emit compact rather than indented JSON"
    )
    args = parser.parse_args()
    report = analyze(use_racket=args.racket)
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
