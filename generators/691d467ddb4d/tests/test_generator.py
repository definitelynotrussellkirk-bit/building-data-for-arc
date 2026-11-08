"""Focused regression suite for the repaired leftmost-object sampler."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    border_touch_output,
    canonical_output,
    canonical_pairs,
    components,
    load_generator,
    observed,
    topmost_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_authority_is_pinned():
    assert gen.RULE_HASH == "cbcf1f4c6292"


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert canonical_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w,n_right", [(8, 10, 3), (14, 18, 1), (10, 12, 2)])
def test_exact_observable_overrides_work_in_every_band(band, grid_h, grid_w, n_right):
    grid = gen.generate(17, 9, difficulty=band, grid_h=grid_h, grid_w=grid_w, n_right=n_right)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_right": n_right,
    }
    assert observed(grid)["n_right"] == n_right


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 9},
        {"grid_w": 19},
        {"n_right": 0},
        {"n_right": 4},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"n_right": "2"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_default_distribution_refutes_border_touch_shortcut():
    target_columns = []
    for index in range(30):
        grid = gen.generate(500 + index, index, difficulty="medium")
        assert gen.self_check(grid) == []
        target_columns.append(observed(grid)["target_min_col"])
    assert min(target_columns) <= 1
    assert max(target_columns) >= 5
    assert sum(column >= 2 for column in target_columns) >= 18


@pytest.mark.parametrize("start", range(12))
def test_every_three_pair_schedule_is_identifiable_under_any_query_rotation(start):
    pairs = []
    for sample_index in range(start, start + 3):
        grid = gen.generate(901, sample_index, difficulty="hard")
        pairs.append({"input": grid, "output": canonical_output(grid)})
    assert sum(observed(pair["input"])["target_min_col"] >= 2 for pair in pairs) >= 2
    for query_index in range(3):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_semantic_witness_refutes_declared_rivals():
    grid = gen.generate(712, 0, difficulty="easy")
    assert gen.SEMANTIC_WITNESSES["interior_leftmost"](grid)
    assert gen.SEMANTIC_WITNESSES["leftmost_not_topmost"](grid)
    expected = canonical_output(grid)
    assert gen.SEMANTIC_RIVALS["border_touch_first_two_columns"](grid) == border_touch_output(grid)
    assert gen.SEMANTIC_RIVALS["topmost_object"](grid) == topmost_output(grid)
    assert border_touch_output(grid) != expected
    assert topmost_output(grid) != expected


def test_component_count_is_exact_and_objects_do_not_merge():
    for n_right in (1, 2, 3):
        for sample_index in range(18):
            grid = gen.generate(1200 + sample_index, sample_index, grid_h=8, grid_w=10, n_right=n_right)
            assert gen.self_check(grid) == []
            assert len(components(grid)) == n_right + 1


def test_generation_is_deterministic_and_returns_fresh_grids():
    first = gen.generate(31, 8, difficulty="hard")
    second = gen.generate(31, 8, difficulty="hard")
    assert first == second
    second[0][0] = 9
    assert gen.generate(31, 8, difficulty="hard") == first


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 0]], [[9] * 10 for _ in range(8)]])
def test_malformed_grids_return_diagnostics(bad):
    assert gen.self_check(bad)


def test_validator_rejects_tied_leftmost_components():
    grid = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 2), (1, 3), (4, 2), (5, 2), (4, 7), (5, 7)):
        grid[r][c] = 4
    assert any("tied" in reason for reason in gen.self_check(deepcopy(grid)))
