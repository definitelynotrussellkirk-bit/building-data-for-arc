"""Regression tests for the d250e5455b23 domino-growth generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest


TASK_ID = "d250e5455b23"
HERE = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_contract_is_source_bound_and_unknown_overrides_fail_closed():
    assert gen.RULE_HASH == "9af05fcaf1f5"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(7, 7), (9, 9)])
@pytest.mark.parametrize("count", [2, 3])
@pytest.mark.parametrize("orientation", ["horizontal", "vertical", "mixed"])
def test_boundary_overrides_are_constructive_and_observable(
    band, height, width, count, orientation
):
    requested = {
        "grid_h": height,
        "grid_w": width,
        "domino_count": count,
        "orientation_mode": orientation,
    }
    grid = gen.generate(417, 23, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(417, 23, difficulty=band, **requested)


@pytest.mark.parametrize("bad", [
    {"grid_h": 6},
    {"grid_w": 10},
    {"domino_count": 1},
    {"domino_count": 4},
    {"orientation_mode": "diagonal"},
    {"grid_h": True},
    {"domino_count": 2.5},
])
def test_invalid_overrides_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **bad)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_hits_canonical_profiles_in_every_band(band):
    canonical_profiles = {(7, 7, 3), (8, 8, 4), (8, 9, 4), (9, 9, 4)}
    profiles = set()
    for sample_index in range(20):
        grid = gen.generate(8128, sample_index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        profiles.add(_profile(grid))
    assert profiles & canonical_profiles


def test_canonical_pairs_are_strict_and_match_python_rule_mirror():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert pairs
    for pair in pairs:
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_semantic_rivals_are_real_and_lesson_hook_accepts_taught_lesson():
    horizontal = gen.generate(
        3, 0, grid_h=7, grid_w=7, domino_count=2,
        orientation_mode="horizontal",
    )
    vertical = gen.generate(
        3, 1, grid_h=8, grid_w=8, domino_count=3,
        orientation_mode="vertical",
    )
    mixed = gen.generate(
        3, 2, grid_h=9, grid_w=9, domino_count=3,
        orientation_mode="mixed",
    )

    assert gen.SEMANTIC_WITNESSES["horizontal_domino"](horizontal)
    assert gen.SEMANTIC_WITNESSES["vertical_domino"](vertical)
    assert gen.SEMANTIC_WITNESSES["multiple_dominos"](mixed)

    assert gen.SEMANTIC_RIVALS["vertical_only"](horizontal) != gen.rule_mirror(horizontal)
    assert gen.SEMANTIC_RIVALS["horizontal_only"](vertical) != gen.rule_mirror(vertical)
    assert gen.SEMANTIC_RIVALS["first_domino_only"](mixed) != gen.rule_mirror(mixed)

    demos = [
        {"input": horizontal, "output": gen.rule_mirror(horizontal)},
        {"input": vertical, "output": gen.rule_mirror(vertical)},
        {"input": mixed, "output": gen.rule_mirror(mixed)},
        {"input": deepcopy(horizontal), "output": gen.rule_mirror(horizontal)},
    ]
    query = {"input": deepcopy(mixed), "output": gen.rule_mirror(mixed)}
    assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_a_singleton_nearest_impostor():
    grid = gen.generate(
        91, 4, grid_h=7, grid_w=7, domino_count=2,
        orientation_mode="mixed",
    )
    changed = deepcopy(grid)
    for r, row in enumerate(changed):
        for c, value in enumerate(row):
            if value:
                changed[r][c] = 0
                assert gen.self_check(changed)
                return
    raise AssertionError("generated grid unexpectedly had no domino")
