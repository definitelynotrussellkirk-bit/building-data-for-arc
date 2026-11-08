"""Observable input and override contracts for the cyan-count generator.

These tests run both beside the library source and in the public task-tests
runtime.  Expected counts and cell types are measured directly from each grid.
"""
from __future__ import annotations

import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "5dc10de63325"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path
    for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    if path.is_file()
)
SPEC = importlib.util.spec_from_file_location("cyan_count_controls_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)

DIFFICULTIES = (None, "easy", "medium", "hard")
TEXTURES = ("clustered", "row_aligned", "block", "snake", "scattered")
SEEDS = (0, 7, 997)


class IntSubclass(int):
    """Distinguish the exact Python-int contract from coercible integers."""


def cyan_count(grid):
    return sum(cell == 8 for row in grid for cell in row)


def lawful_grid(height=5, width=5, count=4):
    return [
        [8 if r * width + c < count else 0 for c in range(width)]
        for r in range(height)
    ]


def assert_lawful(grid):
    assert type(grid) is list
    assert 5 <= len(grid) <= 18
    assert all(type(row) is list for row in grid)
    width = len(grid[0])
    assert 5 <= width <= 18
    assert all(len(row) == width for row in grid)
    assert all(type(cell) is int and cell in (0, 8) for row in grid for cell in row)
    assert 4 <= cyan_count(grid) <= 19
    assert any(cell == 0 for row in grid for cell in row)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("height,width", ((5, 5), (5, 18), (18, 5), (18, 18), (9, 13), (13, 9)))
def test_explicit_dimensions_are_exact_in_every_difficulty(difficulty, height, width):
    for seed in SEEDS:
        grid = GENERATOR.generate(
            seed, 3, difficulty=difficulty, grid_h=height, grid_w=width,
            n_cyans=12, distribution="scattered",
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert cyan_count(grid) == 12
        assert_lawful(grid)


@pytest.mark.parametrize("count", range(4, 20))
@pytest.mark.parametrize("texture", TEXTURES)
def test_every_supported_count_is_exact_without_clamping(count, texture):
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            grid = GENERATOR.generate(
                seed, 6, difficulty=difficulty, n_cyans=count, distribution=texture,
            )
            assert cyan_count(grid) == count
            assert_lawful(grid)


INVALID_TYPES = (True, False, None, 8.0, 8.5, "8", [], {}, IntSubclass(8))


@pytest.mark.parametrize("axis", ("grid_h", "grid_w", "n_cyans"))
@pytest.mark.parametrize("value", INVALID_TYPES)
def test_numeric_controls_reject_non_exact_python_ints(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, **{axis: value})


@pytest.mark.parametrize("axis", ("grid_h", "grid_w"))
@pytest.mark.parametrize("value", (-10, 0, 4, 19, 1000))
def test_dimensions_reject_values_outside_supported_bounds(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, **{axis: value})


@pytest.mark.parametrize("count", (-10, 0, 1, 3, 20, 1000))
def test_counts_outside_supported_bounds_are_rejected(count):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, n_cyans=count)


@pytest.mark.parametrize("axis", ("anchor_corner", "asymmetry_force", "include_decoy", "force_div_4"))
@pytest.mark.parametrize("value", (True, False))
def test_removed_controls_cannot_be_silently_ignored(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, n_cyans=13, **{axis: value})


@pytest.mark.parametrize("axis,value", (("n_cyan", 12), ("grid_height", 8), ("position_bias", "corner"), ("palette_size", 2)))
def test_unknown_controls_are_rejected(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, **{axis: value})


@pytest.mark.parametrize("texture", TEXTURES)
def test_distribution_and_texture_are_equivalent_and_may_agree(texture):
    for seed in SEEDS:
        arguments = dict(grid_h=9, grid_w=11, n_cyans=13)
        by_distribution = GENERATOR.generate(seed, 2, distribution=texture, **arguments)
        by_texture = GENERATOR.generate(seed, 2, texture=texture, **arguments)
        by_both = GENERATOR.generate(seed, 2, distribution=texture, texture=texture, **arguments)
        assert by_distribution == by_texture == by_both
        assert cyan_count(by_both) == 13
        assert_lawful(by_both)


@pytest.mark.parametrize("distribution,texture", [(a, b) for a in TEXTURES for b in TEXTURES if a != b])
def test_conflicting_aliases_are_rejected(distribution, texture):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, distribution=distribution, texture=texture)


@pytest.mark.parametrize("axis", ("distribution", "texture"))
@pytest.mark.parametrize("value", (None, "", "diagonal_typo", 8, True, [], {}))
def test_invalid_texture_values_are_rejected(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(7, 0, **{axis: value})


def test_advertised_controls_only_offer_supported_ordinary_textures():
    assert set(GENERATOR.HELPFUL_TEXTURES) == set(TEXTURES)
    for axis in ("distribution", "texture"):
        assert set(GENERATOR.AXES[axis]["valid"].split("|")) == set(TEXTURES)
    assert {"anchor_corner", "asymmetry_force", "include_decoy", "force_div_4"}.isdisjoint(GENERATOR.AXES)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("texture", (None, *TEXTURES))
def test_helpful_draws_have_valid_dimensions_palette_count_and_background(difficulty, texture):
    overrides = {} if texture is None else {"texture": texture}
    for seed in SEEDS:
        for sample_index in range(12):
            grid = GENERATOR.generate(seed, sample_index, difficulty=difficulty, **overrides)
            assert_lawful(grid)
            assert GENERATOR.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("cell", (1, 9, -1, 10, True, False, 0.0, 8.0, "0", None, [], {}, (0,)))
def test_self_check_reports_invalid_cell_types_and_colors(cell):
    grid = lawful_grid()
    grid[4][4] = cell
    errors = GENERATOR.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("grid", (None, [], [[]], 8, "00000", [0] * 5, [[0] * 5, None], [[8] * 4] + [[0] * 5 for _ in range(4)]))
def test_self_check_reports_invalid_grid_structure(grid):
    errors = GENERATOR.self_check(grid)
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize("height,width", ((4, 5), (5, 4), (19, 5), (5, 19)))
def test_self_check_rejects_out_of_domain_dimensions(height, width):
    grid = lawful_grid(height, width)
    assert cyan_count(grid) == 4
    assert GENERATOR.self_check(grid)


@pytest.mark.parametrize("count", (0, 1, 2, 3, 20, 25, 36))
def test_self_check_rejects_out_of_domain_cyan_counts(count):
    grid = lawful_grid(6, 6, count)
    assert cyan_count(grid) == count
    assert GENERATOR.self_check(grid)


@pytest.mark.parametrize("count", range(4, 20))
def test_self_check_accepts_the_entire_lawful_count_range(count):
    grid = lawful_grid(count=count)
    assert GENERATOR.self_check(grid) == []


@pytest.mark.parametrize("positions", (((1, 1), (1, 2), (2, 1), (2, 2)), ((2, 1), (2, 2), (2, 3), (2, 4))), ids=("solid_four", "line_four"))
def test_self_check_accepts_lawful_solid_and_line_four(positions):
    grid = [[0] * 6 for _ in range(6)]
    for r, c in positions:
        grid[r][c] = 8
    assert cyan_count(grid) == 4
    assert GENERATOR.self_check(grid) == []


def test_self_check_accepts_every_canonical_input():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        identity = (pair["variant"], pair["split"], pair["pair_index"])
        assert GENERATOR.self_check(pair["input"]) == [], identity
