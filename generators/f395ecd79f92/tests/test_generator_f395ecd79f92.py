from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.f395ecd79f92 import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return [*row["train"], *row["test"]]
    raise AssertionError("canonical task not found")


def _valid_fixture():
    grid = [[0] * 10 for _ in range(8)]
    grid[1][1] = 1
    grid[1][4] = grid[1][5] = 2
    grid[4][7] = grid[5][7] = grid[5][8] = 3
    assert gen.self_check(grid) == []
    return grid


def test_rule_hash_and_version_changed_for_distribution_repair():
    assert gen.RULE_HASH == "77202e38a056"
    assert gen.VERSION == "3.0.0"


def test_all_canonical_pairs_are_accepted_and_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.expected_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_replay_is_deterministic_fresh_and_global_rng_pure(band):
    state = random.getstate()
    first = gen.generate(911, 37, difficulty=band)
    assert random.getstate() == state
    untouched = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = gen.generate(911, 37, difficulty=band)
    assert second == untouched
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8},
        {"grid_h": 16},
        {"grid_w": 8},
        {"grid_w": 18},
        {"n_blobs": 3},
        {"n_blobs": 7},
        {"shape_style": "rectangles"},
        {"shape_style": "mixed"},
        {"shape_style": "organic"},
        {"size_order": "ascending_reading"},
        {"size_order": "descending_reading"},
        {"size_order": "shuffled"},
        {"palette_kind": "mixed"},
        {"palette_kind": "warm"},
        {"palette_kind": "cool"},
        {"grid_h": 8, "grid_w": 8, "n_blobs": 3},
        {"grid_h": 16, "grid_w": 18, "n_blobs": 7, "shape_style": "organic"},
    ],
)
def test_declared_override_boundaries_are_consumed_and_observable(overrides):
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(17, 3, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for key in ("grid_h", "grid_w", "n_blobs"):
            if key in overrides:
                assert observed[key] == overrides[key]


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, made_up_axis=1)


def test_three_demo_schedule_identifies_the_rule_without_query_output():
    demos = []
    for index in range(3):
        inp = gen.generate(1234, index, difficulty="medium")
        demos.append({"input": inp, "output": gen.expected_output(inp)})
    query_input = gen.generate(1234, 3, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_input}) == []


def test_self_check_rejects_even_object_count():
    grid = _valid_fixture()
    for r, c in ((4, 7), (5, 7), (5, 8)):
        grid[r][c] = 0
    assert any("3, 5, or 7" in item for item in gen.self_check(grid))


def test_self_check_rejects_duplicate_cell_areas():
    grid = _valid_fixture()
    grid[5][8] = 0
    assert any("cell-areas must be distinct" in item for item in gen.self_check(grid))


def test_self_check_rejects_reused_color_across_disconnected_objects():
    grid = _valid_fixture()
    grid[6][1] = 1
    errors = gen.self_check(grid)
    assert any("colors must be distinct" in item for item in errors)


def test_self_check_rejects_orthogonally_touching_objects():
    grid = _valid_fixture()
    grid[1][2] = 2
    grid[1][4] = 0
    errors = gen.self_check(grid)
    assert "different objects touch orthogonally" in errors


def test_self_check_rejects_nonzero_majority_background():
    grid = _valid_fixture()
    for r in range(8):
        for c in range(10):
            if grid[r][c] == 0:
                grid[r][c] = 9
    assert any("majority background" in item for item in gen.self_check(grid))
