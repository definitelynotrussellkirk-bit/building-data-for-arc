"""Focused behavioral regression coverage for the projection generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


_spec = importlib.util.spec_from_file_location("projection_contract_support", Path(__file__).with_name("contract_support.py"))
support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(support)
GEN, SOURCE, ROOT = support.load_generator(__file__)


@pytest.mark.parametrize("name,band,overrides", support.valid_cases(), ids=lambda item: item if isinstance(item, str) else None)
def test_exact_override_realization(name, band, overrides):
    # Several draws in the old valid range exercise formerly partial placement.
    seeds = range(8) if name.startswith(("in-band", "small-", "high-count")) else range(2)
    for seed in seeds:
        grid = GEN.generate(seed, seed + 7, difficulty=band, **overrides)
        support.assert_realization(GEN, grid, overrides, band)


@pytest.mark.parametrize("name,bad", support.invalid_cases(), ids=lambda item: item if isinstance(item, str) else None)
def test_invalid_overrides_reject(name, bad):
    overrides = dict(grid_h=9, grid_w=10, n_dots=2, shape_kind="rect", texture="plain")
    overrides.update(bad)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 7, **overrides)


@pytest.mark.parametrize("name,overrides,context", support.incompatible_cases(), ids=lambda item: item if isinstance(item, str) else None)
def test_structured_incompatibility(name, overrides, context):
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 7, **overrides)
    support.assert_incompatibility(caught.value, context)


def _valid_grid():
    grid = [[0] * 5 for _ in range(5)]
    for row in (1, 2, 3):
        grid[row][2] = 8
    grid[1][0] = 2
    grid[3][4] = 2
    return grid


@pytest.mark.parametrize("grid", [[], [[]], [[8, 0], [1]], [[0, 0], [0, 0]], [[8] * 5 for _ in range(5)]],
                         ids=("empty", "empty-width", "ragged", "no-region", "full-grid-negative"))
def test_self_check_rejects_invalid_or_identity_fixtures(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize("value", (True, False, -1, 10, 1.0, "1", None))
def test_self_check_rejects_invalid_cell_types_and_palette(value):
    grid = _valid_grid()
    grid[0][0] = value
    assert GEN.self_check(grid)


def test_self_check_rejects_non_solid_bbox():
    grid = _valid_grid()
    grid[2][2] = 0
    assert GEN.self_check(grid)


@pytest.mark.parametrize("same_color", (False, True))
def test_self_check_rejects_colliding_projection_targets(same_color):
    grid = _valid_grid()
    grid[1][4] = 2 if same_color else 3
    assert GEN.self_check(grid)


def test_self_check_accepts_repeated_colors_without_collision():
    assert GEN.self_check(_valid_grid()) == []


def test_no_dots_is_a_negative_fixture():
    grid = _valid_grid()
    grid[1][0] = grid[3][4] = 0
    assert GEN.self_check(grid)


def test_normal_texture_axis_excludes_identity_fixtures():
    valid = GEN.AXES["texture"]["valid"]
    assert "no_dots" not in valid and "full_grid" not in valid
    assert all(texture in valid for texture in support.TEXTURES)


def test_all_canonical_inputs_are_accepted_including_repeated_colors():
    pairs = support.canonical_pairs(support.TASK_ID, root=support.find_root(__file__))
    assert pairs
    repeated = False
    for pair in pairs:
        grid = pair["input"]
        assert GEN.self_check(grid) == [], (pair["variant"], pair["split"], pair["pair_index"])
        colors = [cell for row in grid for cell in row if cell not in (0, 8)]
        repeated |= len(colors) != len(set(colors))
    assert repeated, "canonical repeated-color acceptance was not exercised"


def test_generation_is_deterministic_and_self_check_does_not_mutate():
    overrides = dict(grid_h=9, grid_w=10, n_dots=2, shape_kind="rect", texture="diag_decoy")
    first = GEN.generate(123, 456, **overrides)
    assert first == GEN.generate(123, 456, **overrides)
    original = deepcopy(first)
    assert GEN.self_check(first) == []
    assert first == original


def test_single_dot_does_not_require_an_implicit_opposite_pair():
    for seed in range(12):
        grid = GEN.generate(seed, 19, grid_h=9, grid_w=10, n_dots=1)
        actual = support.observe(grid)
        assert actual["aligned_count"] == 1
        assert actual["unique_target_count"] == 1
        assert actual["diagonal_count"] in (0, 1)
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("axis", ("grid_h", "grid_w", "n_dots", "shape_kind", "texture"))
def test_none_has_the_shared_unspecified_override_convention(axis):
    for seed in range(4):
        assert GEN.generate(seed, 17, **{axis: None}) == GEN.generate(seed, 17)
