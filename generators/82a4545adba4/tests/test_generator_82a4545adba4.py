"""Focused regression and semantic tests for generator 82a4545adba4."""
from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "82a4545adba4"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def _marker_columns(grid):
    return [c for c, value in enumerate(grid[0]) if value]


def test_rule_hash_and_canonical_pairs_match_python_mirror():
    assert GEN.RULE_HASH == "be4eaba83110"
    row = _canonical_row()
    pairs = [*row["train"], row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_declared_boundary_overrides_are_exact_or_loud():
    cases = [
        ({"grid_h": 4}, 4, None, None),
        ({"grid_h": 10}, 10, None, None),
        ({"grid_w": 5}, None, 5, None),
        ({"grid_w": 12}, None, 12, None),
        ({"n_markers": 2}, None, None, 2),
        ({"n_markers": 5}, None, None, 5),
    ]
    for overrides, expected_h, expected_w, expected_n in cases:
        grid = GEN.generate(17, 9, difficulty="hard", **overrides)
        assert GEN.self_check(grid) == []
        if expected_h is not None:
            assert len(grid) == expected_h
        if expected_w is not None:
            assert len(grid[0]) == expected_w
        if expected_n is not None:
            assert GEN.observe_overrides(grid)["n_markers"] == expected_n

    with pytest.raises(ValueError, match="grid_w must be >= grid_h"):
        GEN.generate(0, 0, grid_h=10, grid_w=5)
    with pytest.raises(ValueError, match="n_markers must fit"):
        GEN.generate(0, 0, grid_w=5, n_markers=5)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, n_distinct_colors=1)


def test_helpful_textures_are_live_and_rule_valid():
    outputs = {}
    for texture in GEN.HELPFUL_TEXTURES:
        grid = GEN.generate(
            41,
            7,
            difficulty="medium",
            grid_h=6,
            grid_w=9,
            n_markers=3,
            texture=texture,
        )
        assert GEN.self_check(grid) == []
        outputs[texture] = tuple(tuple(row) for row in grid)
    assert len(set(outputs.values())) == len(GEN.HELPFUL_TEXTURES)


def test_every_ordinary_draw_witnesses_both_edge_branches():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = GEN.generate(seed, seed * 13 + 5, difficulty=band)
            assert GEN.self_check(grid) == []
            h, w = len(grid), len(grid[0])
            columns = _marker_columns(grid)
            assert any(c + h - 1 <= w - 1 for c in columns)
            assert any(c + h - 1 > w - 1 for c in columns)


def test_self_check_rejects_targeted_impostors():
    valid = GEN.generate(
        3,
        5,
        difficulty="medium",
        grid_h=6,
        grid_w=9,
        n_markers=3,
        texture="sparse",
    )
    assert GEN.self_check(valid) == []

    no_markers = [[0 for _ in row] for row in valid]
    assert GEN.self_check(no_markers)

    body_cell = [row[:] for row in valid]
    body_cell[2][2] = 8
    assert any("below row 0" in error for error in GEN.self_check(body_cell))

    final_column = [row[:] for row in valid]
    marker_col = _marker_columns(final_column)[0]
    final_column[0][-1] = final_column[0][marker_col]
    final_column[0][marker_col] = 0
    assert any("final column" in error for error in GEN.self_check(final_column))

    duplicate_colour = [row[:] for row in valid]
    columns = _marker_columns(duplicate_colour)
    duplicate_colour[0][columns[1]] = duplicate_colour[0][columns[0]]
    assert any("distinct" in error for error in GEN.self_check(duplicate_colour))

    only_right_clipped = [row[:] for row in valid]
    for c in _marker_columns(only_right_clipped):
        only_right_clipped[0][c] = 0
    only_right_clipped[0][-2] = 2
    only_right_clipped[0][-3] = 4
    assert any("bottom" in error for error in GEN.self_check(only_right_clipped))

    no_strict_right_clip = [[0] * 7 for _ in range(5)]
    no_strict_right_clip[0][0] = 2
    no_strict_right_clip[0][2] = 4  # reaches the bottom-right corner exactly
    errors = GEN.self_check(no_strict_right_clip)
    assert any("strictly clipped" in error for error in errors)


def test_replay_fresh_returns_and_global_rng_state():
    random.seed(9281)
    state = random.getstate()
    first = GEN.generate(9, 11, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(9, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_two_demo_lessons_reject_simple_competing_rules():
    demos = []
    for sample_index in (0, 1):
        input_grid = GEN.generate(77, sample_index, difficulty="medium")
        demos.append({"input": input_grid, "output": GEN.rule_mirror(input_grid)})
    query_input = GEN.generate(77, 2, difficulty="medium")
    query = {"input": query_input, "output": GEN.rule_mirror(query_input)}
    assert GEN.lesson_identifiable(demos, query) == []
