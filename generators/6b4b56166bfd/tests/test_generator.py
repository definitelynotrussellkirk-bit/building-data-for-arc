"""Focused regressions for the fourfold pivot-orbit input sampler."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "6b4b56166bfd"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pivot_and_seeds(grid):
    pivot = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    seeds = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 5)]
    assert len(pivot) == 1
    return pivot[0], seeds


def _orbit(pivot, row, col):
    pr, pc = pivot
    dr, dc = row - pr, col - pc
    return frozenset(
        (pr + rr, pc + cc)
        for rr, cc in ((dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr))
    )


def _pinned_profile_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_rule_hash_canonical_acceptance_and_python_mirror_are_exact():
    assert gen.RULE_HASH == "f2aaf100dc45"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        source = deepcopy(pair["input"])
        snapshot = deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == snapshot


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 5, "grid_w": 14, "n_cells": 1},
        {"grid_h": 14, "grid_w": 5, "n_cells": 3},
        {"grid_h": 9, "grid_w": 9, "n_cells": 2},
    ],
)
def test_every_exact_override_is_honored_and_observable_in_every_band(band, requested):
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"n_cells": "2"},
        {"n_cells": 2.75},
        {"grid_h": 4},
        {"grid_w": 15},
        {"n_cells": 0},
        {"n_cells": 4},
    ],
)
def test_invalid_or_unknown_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (0, True, None),
        (0, -1, None),
        (0, 0, "extreme"),
    ],
)
def test_invalid_call_scalars_fail_closed(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


def test_self_check_rejects_non_arc_cells_and_malformed_grids_without_crashing():
    for malformed in (None, [], [[]], [[0], [0, 1]], "not a grid"):
        assert gen.self_check(malformed)

    base = gen.generate(91, 7, grid_h=9, grid_w=9, n_cells=2)
    _, seeds = _pivot_and_seeds(base)
    row, col, _ = seeds[0]
    for invalid in (True, 10, -1, 2.5, "2"):
        changed = deepcopy(base)
        changed[row][col] = invalid
        assert gen.self_check(changed), invalid


def test_generated_seeds_have_distinct_colors_and_disjoint_in_bounds_orbits():
    for band in (None, "easy", "medium", "hard"):
        for index in range(120):
            grid = gen.generate(1000 + index, index * 17 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            pivot, seeds = _pivot_and_seeds(grid)
            assert len({value for _, _, value in seeds}) == len(seeds)
            orbits = [_orbit(pivot, row, col) for row, col, _ in seeds]
            assert len(set(orbits)) == len(orbits)
            assert all(
                0 <= row < len(grid) and 0 <= col < len(grid[0])
                for orbit in orbits
                for row, col in orbit
            )
            assert gen.rule_mirror(grid) != grid


def test_nine_by_nine_sampling_reaches_canonical_radius_three_orbits():
    seen_radius_three = False
    for index in range(80):
        grid = gen.generate(2000 + index, index, grid_h=9, grid_w=9, n_cells=3)
        pivot, seeds = _pivot_and_seeds(grid)
        pr, pc = pivot
        if any(max(abs(row - pr), abs(col - pc)) >= 3 for row, col, _ in seeds):
            seen_radius_three = True
            break
    assert seen_radius_three


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_profile_floor_pinned_census_has_a_canonical_profile_in_each_band(band):
    canonical_profiles = {_profile(pair["input"]) for pair in PAIRS}
    generated_profiles = set()
    for index in range(20):
        seed = _pinned_profile_seed(band, index)
        grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
        generated_profiles.add(_profile(grid))
    assert canonical_profiles & generated_profiles


def test_semantic_witness_refutes_half_turn_only_and_lessons_report_survivors():
    grid = gen.generate(712, 11, grid_h=9, grid_w=9, n_cells=3)
    intended = gen.rule_mirror(grid)
    rival = gen.SEMANTIC_RIVALS["half_turn_only"](grid)
    assert gen.SEMANTIC_WITNESSES["quarter_turn_completion"](grid)
    assert intended != rival
    assert gen.WITNESS_RIVALS["quarter_turn_completion"] == ["half_turn_only"]

    demos = [{"input": grid, "output": intended}]
    query = {"input": grid, "output": intended}
    assert gen.lesson_identifiable(demos, query) == []
    assert gen.lesson_identifiable(
        [{"input": grid, "output": rival}], query
    )
