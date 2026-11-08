"""Focused regression tests for the even-area component generator."""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.bbb0f21653d8 import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        return [pair["input"] for pair in row["train"] + row["test"]]
    raise AssertionError("canonical task not found")


def _pair(grid):
    return {"input": grid, "output": gen._official_output(grid)}


def test_rule_hash_and_canonical_inputs_are_owned():
    assert gen.RULE_HASH == "42e06f7977db"
    canonical = _canonical_inputs()
    assert len(canonical) == 5
    for grid in canonical:
        original = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == original


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7},
        {"grid_h": 14},
        {"grid_w": 8},
        {"grid_w": 14},
        {"n_blobs": 4},
        {"n_blobs": 6},
        {"palette_kind": "canonical"},
        {"palette_kind": "warm"},
        {"palette_kind": "cool"},
        {"palette_kind": "varied"},
        {"diagonal_touch": False},
        {"diagonal_touch": True},
    ],
)
def test_every_declared_axis_is_observable_at_boundaries(overrides):
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(12345, 3, difficulty=band, **overrides)
        observed = gen.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value
        assert gen.self_check(grid) == []


def test_four_sample_schedule_contains_semantic_counterexamples():
    grids = [gen.generate(777, index, difficulty="medium") for index in range(4)]
    features = [gen.analyze_grid(grid)[1] for grid in grids]
    assert any(gen.strict_canonical_like(grid) == [] for grid in grids)
    assert {feature["n_blobs"] for feature in features} == {4, 5, 6}
    assert {feature["diagonal_touch"] for feature in features} == {False, True}
    assert {feature["palette_kind"] for feature in features} == set(gen.PALETTE_KINDS)
    assert any(feature["cross_parity_colors"] for feature in features)
    assert any(feature["bbox_parity_conflict"] for feature in features)
    assert any(gen._witness_decisive_diagonal(grid) for grid in grids)


def test_lesson_is_identifiable_against_shortcuts():
    grids = [gen.generate(918273, index, difficulty="medium") for index in range(5)]
    demos = [_pair(grid) for grid in grids[:4]]
    query = _pair(grids[4])
    assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors():
    impostors = {
        "all_background": [[0] * 10 for _ in range(9)],
        "singleton": [[1] + [0] * 9] + [[0] * 10 for _ in range(8)],
        "solid_2x2": [[1, 1] + [0] * 8, [1, 1] + [0] * 8]
        + [[0] * 10 for _ in range(7)],
        "short_line": [[1, 1, 1] + [0] * 7] + [[0] * 10 for _ in range(8)],
        "all_even": [
            [1, 1, 0, 2, 2, 0, 3, 3, 0, 4, 4],
            [0] * 11,
            [0] * 11,
            [0] * 11,
            [0] * 11,
            [0] * 11,
            [0] * 11,
            [0] * 11,
            [0] * 11,
        ],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_are_preserved():
    random.seed(24680)
    state_before = random.getstate()
    first = gen.generate(13579, 2, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(13579, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert state_before == state_after


def test_explicit_incompatibility_rejects_loudly():
    with pytest.raises(ValueError, match="requires at least"):
        gen.generate(
            1,
            1,
            difficulty="easy",
            grid_h=7,
            grid_w=8,
            n_blobs=6,
            diagonal_touch=False,
        )
