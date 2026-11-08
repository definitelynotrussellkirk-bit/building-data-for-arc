from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "8d45a1d4a531"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _project(grid):
    out = [[0 for _ in row] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0:
                continue
            for cc in range(len(values)):
                out[row][cc] = value
            for rr in range(len(grid)):
                out[rr][col] = value
    return out


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def test_rule_hash_and_canonical_inputs_are_accepted():
    assert MODULE.RULE_HASH == "04b45d1c8bbd"
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert _project(pair["input"]) == pair["output"]


def test_boundary_overrides_are_exact_and_non_degenerate():
    cases = (
        {"grid_h": 7, "grid_w": 7, "markers": 2, "marker_color": 1},
        {"grid_h": 14, "grid_w": 16, "markers": 4, "marker_color": 9},
    )
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(101, index, difficulty="hard", **overrides)
        assert len(grid) == overrides["grid_h"]
        assert len(grid[0]) == overrides["grid_w"]
        assert MODULE.observe_overrides(grid) == {
            "markers": overrides["markers"],
            "marker_color": overrides["marker_color"],
        }
        assert MODULE.self_check(grid) == []
        output = _project(grid)
        assert output != grid
        assert any(value == 0 for row in output for value in row)


def test_self_check_rejects_targeted_impostors():
    valid = MODULE.generate(
        7,
        11,
        grid_h=9,
        grid_w=10,
        markers=3,
        marker_color=6,
    )
    assert MODULE.self_check(valid) == []

    no_markers = [[0] * 10 for _ in range(9)]
    assert MODULE.self_check(no_markers)

    mixed = copy.deepcopy(valid)
    first = next((r, c) for r, row in enumerate(mixed) for c, v in enumerate(row) if v)
    mixed[first[0]][first[1]] = 2
    assert any("one nonzero color" in error for error in MODULE.self_check(mixed))

    same_row = [[0] * 10 for _ in range(9)]
    same_row[2][1] = same_row[2][7] = 6
    assert any("distinct rows" in error for error in MODULE.self_check(same_row))

    same_col = [[0] * 10 for _ in range(9)]
    same_col[1][4] = same_col[7][4] = 6
    assert any("distinct columns" in error for error in MODULE.self_check(same_col))

    too_many = [[0] * 10 for _ in range(9)]
    for index in range(5):
        too_many[index][index] = 6
    assert any("2..4 markers" in error for error in MODULE.self_check(too_many))


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(982451653)
    before = random.getstate()
    first = MODULE.generate(123, 456, difficulty="medium")
    after = random.getstate()
    second = MODULE.generate(123, 456, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(123, 456, difficulty="medium") == second


def test_invalid_controls_reject_loudly():
    with pytest.raises(TypeError):
        MODULE.generate(1, 0, unknown_axis=1)
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, marker_color=0)
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, difficulty="extreme")
