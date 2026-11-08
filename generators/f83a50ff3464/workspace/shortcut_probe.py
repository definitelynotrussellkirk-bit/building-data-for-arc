#!/usr/bin/env python3
"""Emit machine-readable shortcut evidence for generator f83a50ff3464.

This is a reviewer aid, not part of generation.  It answers three questions:

1. Which named rival rules fit every canonical demonstration?
2. Which generated scene first falsifies each rival, and where do outputs differ?
3. Does every scheduled four-demonstration window identify the selected rule?

Run from anywhere with Python 3.12+::

    python3 repo/generators/f83a50ff3464/workspace/shortcut_probe.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable


TASK_ID = "f83a50ff3464"
HERE = Path(__file__).resolve()
GENERATOR_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
CANONICAL = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    path = GENERATOR_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value:
        raise ValueError("expected non-empty ARC grid")
    if all(isinstance(row, str) for row in value):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def _canonical_row() -> dict[str, Any]:
    with CANONICAL.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row {TASK_ID} not found")


def _pairs(row: dict[str, Any]) -> list[dict[str, list[list[int]]]]:
    result: list[dict[str, list[list[int]]]] = []
    for split in ("train", "test"):
        value = row.get(split, [])
        items = [value] if isinstance(value, dict) else value
        for pair in items:
            result.append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    return result


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row, values in enumerate(left)
        for col, value in enumerate(values)
        if right[row][col] != value
    ]


def _first_counterexample(
    gen,
    witness_name: str,
    witness: Callable[[Any], bool],
) -> dict[str, Any]:
    claimed = gen.WITNESS_RIVALS[witness_name]
    rival_names = [claimed] if isinstance(claimed, str) else list(claimed)
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(
            seed=9100 + index,
            sample_index=index,
            difficulty="medium",
            scene_profile=profile,
        )
        if not witness(grid):
            continue
        official = gen.rule_mirror(grid)
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name](grid)
            if rival != official:
                return {
                    "witness": witness_name,
                    "profile": profile,
                    "seed": 9100 + index,
                    "rival": rival_name,
                    "input": grid,
                    "official_output": official,
                    "rival_output": rival,
                    "differing_output_cells": _diff_cells(official, rival),
                }
    raise RuntimeError(f"no generated counterexample for witness {witness_name!r}")


def _schedule_failures(gen) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [
                gen.generate(12000 + start, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids[: gen.EXAMPLES_NEEDED]
            ]
            query_grid = grids[-1]
            reasons = gen.lesson_identifiable(
                demos,
                {"input": query_grid, "output": gen.rule_mirror(query_grid)},
            )
            if reasons:
                failures.append({"band": band, "start": start, "reasons": reasons})
    return failures


def main() -> int:
    gen = _load_generator()
    canonical_pairs = _pairs(_canonical_row())
    canonical_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    counterexamples = [
        _first_counterexample(gen, name, witness)
        for name, witness in gen.SEMANTIC_WITNESSES.items()
    ]

    # Compact exact counterexample used in QUESTION_ANSWER.md.  Three cardinal
    # arms are color 2 and the fourth is color 3.  The selected rule leaves the
    # zero center unchanged; the 3-of-4 majority rival fills it with 2.
    question_input = [
        [0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0],
        [0, 2, 0, 3, 0],
        [0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    question_official = gen.rule_mirror(question_input)
    question_rival = gen.SEMANTIC_RIVALS["majority_three_nonzero"](question_input)

    report = {
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "canonical_pair_count": len(canonical_pairs),
        "canonical_shortcuts_fit_all_pairs": canonical_fit,
        "generated_counterexamples": counterexamples,
        "schedule_window_failures": _schedule_failures(gen),
        "question_counterexample": {
            "rival": "majority_three_nonzero",
            "input": question_input,
            "official_output": question_official,
            "rival_output": question_rival,
            "differing_output_cells": _diff_cells(question_official, question_rival),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(canonical_fit.values()) and not report["schedule_window_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
