"""Task-local regression tests for the canonical six-code transform table."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "dd6724624b9f"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
sys.path.insert(0, str(WORKSPACE))
from reference_probe import legacy_transform, oracle_output, transform  # noqa: E402


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))
def test_independent_oracle_matches_every_canonical_pair(pair):
    assert oracle_output(pair["input"]) == pair["output"]
    assert GEN.self_check(pair["input"]) == []


def test_rule_pin_and_exact_six_code_table():
    assert GEN.RULE_HASH == "8dd08a5ab5cb"
    shape = ((0, 0), (1, 0), (2, 0), (2, 1))
    for code in range(1, 7):
        assert GEN._transform(shape, code) == list(transform(shape, code))


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_declared_override_is_exact_in_every_band(band):
    requested = {
        "grid_h": 8,
        "grid_w": 9,
        "transform_code": 6,
        "body_cells": 8,
        "color_pair": 7,
    }
    grid = GEN.generate(173, 11, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert oracle_output(grid) != oracle_output(grid, legacy=True)


@pytest.mark.parametrize("start", range(12))
def test_every_six_demo_window_covers_all_transform_codes(start):
    observed = [
        GEN.observe_overrides(GEN.generate(991, start + offset))["transform_code"]
        for offset in range(GEN.EXAMPLES_NEEDED)
    ]
    assert GEN.EXAMPLES_NEEDED == 6
    assert set(observed) == set(range(1, 7))


def test_generated_inputs_kill_the_stale_transform_table_and_recolor_shortcut():
    for code in range(2, 7):
        grid = GEN.generate(812, code, transform_code=code, body_cells=8)
        expected = oracle_output(grid)
        assert GEN.self_check(grid) == []
        assert expected != oracle_output(grid, legacy=True)
        assert expected != oracle_output(grid, preserve_body_color=True)
        assert GEN.SEMANTIC_WITNESSES["legacy_transform_table"](grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_w": 8},
        {"transform_code": 0},
        {"transform_code": 7},
        {"body_cells": 2},
        {"body_cells": 9},
        {"color_pair": -1},
        {"color_pair": 8},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_indices_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_deterministic_and_global_rng_independent():
    first = GEN.generate(412, 73, difficulty="hard")
    for index in range(100):
        GEN.generate(index, index * 7)
    assert GEN.generate(412, 73, difficulty="hard") == first


def test_lesson_hook_accepts_a_normal_six_demo_window():
    demos = []
    for index in range(6):
        grid = GEN.generate(55, index)
        demos.append({"input": grid, "output": oracle_output(grid)})
    query_grid = GEN.generate(55, 6)
    assert GEN.lesson_identifiable(demos, {"input": query_grid, "output": oracle_output(query_grid)}) == []


def test_difficulty_bands_are_live_and_each_keep_a_canonical_profile_anchor():
    grids = [
        GEN.generate(314, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    ]
    keys = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(keys) == 3
    canonical_profiles = {(8, 9, 4), (8, 10, 4), (9, 10, 4), (9, 11, 4), (10, 10, 4)}
    assert {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    } <= canonical_profiles
    body_counts = [GEN.observe_overrides(grid)["body_cells"] for grid in grids]
    assert 3 <= body_counts[0] <= 4
    assert 5 <= body_counts[1] <= 6
    assert 7 <= body_counts[2] <= 8


def test_even_curriculum_slots_cover_every_declared_grid_dimension():
    grids = [
        GEN.generate(314, sample_index, difficulty="medium")
        for sample_index in range(0, 18, 2)
    ]
    assert {len(grid) for grid in grids} == set(range(8, 17))
    assert {len(grid[0]) for grid in grids} == set(range(9, 18))
