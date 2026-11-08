#!/usr/bin/env python3
"""Retained exact probe for the canonical-compatible fixed-column shortcut.

Run from any directory after creating ``shortcut_episode.jsonl`` with the
command recorded in QUESTION_ANSWER.md. The episode's output is produced by
the canonical Racket authority; this script independently compares that output
to the generator's Python rule mirror and the named shortcut.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
EPISODE_PATH = HERE / "shortcut_episode.jsonl"
RESULT_PATH = HERE / "shortcut_probe_result.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("shortcut_probe_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_nonzero_difference(left: list[list[int]], right: list[list[int]]) -> dict[str, int] | None:
    for row, (left_row, right_row) in enumerate(zip(left, right)):
        for column, (left_value, right_value) in enumerate(zip(left_row, right_row)):
            if left_value != right_value:
                return {
                    "row": row,
                    "column": column,
                    "intended": left_value,
                    "shortcut": right_value,
                }
    return None


def main() -> int:
    generator = load_generator()
    episode = json.loads(EPISODE_PATH.read_text(encoding="utf-8").splitlines()[0])
    pair = episode["test"][0]
    grid = pair["input"]
    racket_output = pair["output"]
    mirror_output = generator.rule_mirror(grid)
    shortcut_output = generator.CANONICAL_SHORTCUTS["first_three_columns_only"](grid)

    if mirror_output != racket_output:
        raise AssertionError("Python mirror disagrees with canonical Racket output")
    if shortcut_output == racket_output:
        raise AssertionError("probe does not separate the shortcut from the intended rule")

    differences = sum(
        intended != shortcut
        for intended_row, shortcut_row in zip(racket_output, shortcut_output)
        for intended, shortcut in zip(intended_row, shortcut_row)
    )
    result = {
        "schema": "arcpuzzles-shortcut-probe-v1",
        "task_id": episode["task_id"],
        "seed": episode["seed"],
        "sample_index": episode["sample_indices"][1],
        "executed_rule_hash": episode["executed_rule_hash"],
        "shortcut": "first_three_columns_only",
        "input": grid,
        "intended_output": racket_output,
        "shortcut_output": shortcut_output,
        "different_cells": differences,
        "first_difference": first_nonzero_difference(racket_output, shortcut_output),
        "generator_emits_case": True,
        "checks": {
            "racket_equals_python_mirror": True,
            "shortcut_disagrees": True,
            "legend_columns": generator._legend(grid)[0],
        },
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
