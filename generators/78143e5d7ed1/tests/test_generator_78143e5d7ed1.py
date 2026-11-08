"""Focused regression tests for generator 78143e5d7ed1."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.78143e5d7ed1.generator"
)
ROOT = find_root(__file__)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def test_rule_hash_and_python_mirror_match_all_canonical_pairs() -> None:
    assert MODULE.RULE_HASH == "d87cff5947e7"
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            assert MODULE.self_check(pair["input"]) == []
            assert MODULE.strict_canonical_like(pair["input"]) == []
            assert MODULE._solve_grid(pair["input"]) == pair["output"]


def test_four_step_schedule_covers_every_sort_key_in_each_band() -> None:
    expected = list(MODULE.TIE_PROFILES)
    for band in ("easy", "medium", "hard"):
        observed = []
        for sample_index in range(4):
            grid = MODULE.generate(4100, sample_index, difficulty=band)
            assert MODULE.self_check(grid) == []
            observed.append(MODULE.observe_overrides(grid)["tie_profile"])
        assert observed == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 9,
            "grid_w": 12,
            "n_objs": 3,
            "palette_kind": "low",
            "tie_profile": "area",
        },
        {
            "grid_h": 14,
            "grid_w": 20,
            "n_objs": 4,
            "palette_kind": "high",
            "tie_profile": "height",
        },
        {
            "grid_h": 9,
            "grid_w": 20,
            "n_objs": 4,
            "palette_kind": "mixed",
            "tie_profile": "width",
        },
        {
            "grid_h": 14,
            "grid_w": 12,
            "n_objs": 3,
            "palette_kind": "mixed",
            "tie_profile": "color",
        },
    ],
)
def test_exact_override_boundaries_are_realized(overrides: dict) -> None:
    for band in ("easy", "medium", "hard"):
        grid = MODULE.generate(7331, 17, difficulty=band, **overrides)
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        assert {name: observed[name] for name in overrides} == overrides


def test_self_check_rejects_targeted_impostors() -> None:
    valid = MODULE.generate(991, 2, difficulty="medium")
    assert MODULE.self_check(valid) == []

    assert MODULE.self_check([])

    one_object = [row[:] for row in valid]
    kept = next(value for row in one_object for value in row if value)
    for row_index, row in enumerate(one_object):
        for column_index, value in enumerate(row):
            if value != kept:
                one_object[row_index][column_index] = 0
    assert any("3..4 components" in error for error in MODULE.self_check(one_object))

    duplicate_color = [row[:] for row in valid]
    objects = MODULE._extract_components(duplicate_color)
    old_color = objects[1].color
    new_color = objects[0].color
    for row, column in objects[1].cells:
        assert duplicate_color[row][column] == old_color
        duplicate_color[row][column] = new_color
    assert any("distinct colors" in error for error in MODULE.self_check(duplicate_color))

    touching = [[0] * 12 for _ in range(9)]
    for row, column in ((1, 1), (1, 2), (2, 1)):
        touching[row][column] = 2
    for row, column in ((3, 2), (3, 3), (4, 3)):
        touching[row][column] = 4
    for row, column in ((6, 8), (6, 9), (7, 9)):
        touching[row][column] = 7
    assert any("moat" in error for error in MODULE.self_check(touching))

    all_rectangles = [[0] * 12 for _ in range(9)]
    for color, row0, column0 in ((2, 1, 1), (4, 1, 7), (7, 6, 4)):
        for dr in range(2):
            for dc in range(2):
                all_rectangles[row0 + dr][column0 + dc] = color
    assert any(
        "all components are filled rectangles" in error
        for error in MODULE.self_check(all_rectangles)
    )


def test_materialized_lesson_refutes_named_rivals() -> None:
    pairs = []
    for sample_index in range(5):
        grid = MODULE.generate(20260725, sample_index, difficulty="hard")
        pairs.append({"input": grid, "output": MODULE._solve_grid(grid)})
    assert MODULE.lesson_identifiable(pairs[:4], pairs[4]) == []
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == [
        "need at least 4 demonstrations"
    ]
