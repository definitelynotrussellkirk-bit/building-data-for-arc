#!/usr/bin/env python3
"""Findings-only audit probe for cf60523d1603; never edits the target."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "cf60523d1603"
ROOT = find_root(__file__)
GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_cf60523d1603", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def intended(grid):
    """Independent implementation of the documented exactly-two same-color rule."""
    out = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for col in range(width):
        colors = sorted({grid[row][col] for row in range(height)} - {0})
        for color in colors:
            rows = [row for row in range(height) if grid[row][col] == color]
            if len(rows) != 2:
                continue
            top, bottom = rows
            if all(grid[row][col] == 0 for row in range(top + 1, bottom)):
                for row in range(top, bottom + 1):
                    out[row][col] = color
    return out


def any_two_nonzero_rival(grid):
    """Shortcut: ignores endpoint color equality and fills from the top endpoint."""
    out = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for col in range(width):
        rows = [row for row in range(height) if grid[row][col] != 0]
        if len(rows) != 2:
            continue
        top, bottom = rows
        if all(grid[row][col] == 0 for row in range(top + 1, bottom)):
            color = grid[top][col]
            for row in range(top, bottom + 1):
                out[row][col] = color
    return out


def stats(grid):
    height, width = len(grid), len(grid[0])
    return {
        "height": height,
        "width": width,
        "nonzero_columns": sum(
            any(grid[row][col] != 0 for row in range(height))
            for col in range(width)
        ),
        "nonzero_colors": sorted({value for row in grid for value in row if value}),
    }


def main():
    gen = load_generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    canonical = []
    for pair in pairs:
        expected = pair["output"]
        canonical.append({
            "split": pair.get("split"),
            "pair_index": pair.get("pair_index"),
            "intended_matches_label": intended(pair["input"]) == expected,
            "rival_matches_label": any_two_nonzero_rival(pair["input"]) == expected,
        })

    generated = []
    rival_failures = []
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(100):
            grid = gen.generate(918273 + sample_index, sample_index, difficulty=difficulty)
            expected = intended(grid)
            if any_two_nonzero_rival(grid) != expected:
                rival_failures.append({
                    "difficulty": difficulty,
                    "sample_index": sample_index,
                    "input": grid,
                })
            generated.append({
                "difficulty": "default" if difficulty is None else difficulty,
                "sample_index": sample_index,
                "self_check": gen.self_check(grid),
            })

    counterexample = [[0] * 4 for _ in range(5)]
    counterexample[0][0] = counterexample[4][0] = 4  # valid positive column
    counterexample[0][2] = 2
    counterexample[4][2] = 3  # mixed-color endpoints: canonical rule must not fill
    intended_output = intended(counterexample)
    rival_output = any_two_nonzero_rival(counterexample)

    ignored_axis_pairs = {
        "n_columns": (1, 5),
        "palette_size": (1, 5),
        "n_distinct_colors": (1, 5),
        "palette_kind": ("warm", "cool"),
        "position_bias": ("col_endpoints", "bogus"),
        "density": ("sparse", "dense"),
        "texture": ("default", "varied"),
    }
    axis_results = {}
    for name, values in ignored_axis_pairs.items():
        first = gen.generate(123, 4, **{name: values[0]})
        second = gen.generate(123, 4, **{name: values[1]})
        axis_results[name] = {
            "values": list(values),
            "outputs_identical": first == second,
            "first_stats": stats(first),
            "second_stats": stats(second),
        }

    accepted_invalid = []
    for kwargs in (
        {"not_an_axis": 1},
        {"n_columns": "not-an-int"},
        {"position_bias": "bogus"},
        {"density": "dense"},
    ):
        try:
            grid = gen.generate(1, 0, **kwargs)
        except Exception as exc:  # pragma: no cover - retained if fixed later
            accepted_invalid.append({"kwargs": kwargs, "accepted": False, "error": repr(exc)})
        else:
            accepted_invalid.append({
                "kwargs": kwargs,
                "accepted": True,
                "self_check": gen.self_check(grid),
                "stats": stats(grid),
            })

    report = {
        "schema": "arc-audit-cf60523d1603-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "canonical": canonical,
        "canonical_all_intended": all(row["intended_matches_label"] for row in canonical),
        "canonical_all_rival": all(row["rival_matches_label"] for row in canonical),
        "generated_draws": len(generated),
        "generated_self_check_failures": [row for row in generated if row["self_check"]],
        "generated_rival_failures": rival_failures,
        "counterexample": {
            "input": counterexample,
            "self_check": gen.self_check(counterexample),
            "intended_output": intended_output,
            "rival_output": rival_output,
            "outputs_differ": intended_output != rival_output,
        },
        "ignored_axis_results": axis_results,
        "all_tested_axes_ignored": all(row["outputs_identical"] for row in axis_results.values()),
        "accepted_invalid_overrides": accepted_invalid,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
