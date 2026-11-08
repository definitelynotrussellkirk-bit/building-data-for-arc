"""Portable regressions for the advertised controls and validation boundary.

Grouped sweeps cover the finite domains without creating thousands of pytest
cases. These tests exercise the selected live source in their own tree.
"""
from copy import deepcopy
from pathlib import Path
import sys

import pytest


# Support is at a copied runtime root or in a library's shared/runtime. Resolve
# from this test, never cwd or a neighboring checkout.
for ancestor in Path(__file__).resolve().parents:
    candidates = (ancestor, ancestor / "shared" / "runtime")
    support = next((p for p in candidates if (p / "reviewer_support.py").is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support))
        break
else:
    raise ImportError("No local public reviewer_support module")

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "03909f3e98e7"
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")


@pytest.fixture(scope="module")
def generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}


def assert_ordinary(module, grid, *, height=None, width=None, size=None, texture=None):
    assert isinstance(grid, list) and grid and isinstance(grid[0], list) and grid[0]
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    if height is not None:
        assert len(grid) == height
    if width is not None:
        assert len(grid[0]) == width
    occupied = cells(grid)
    assert 3 <= len(occupied) <= 8
    if size is not None:
        assert len(occupied) == size
    assert 2 <= len({grid[r][c] for r, c in occupied}) <= 3
    top, left = min(r for r, _ in occupied), min(c for _, c in occupied)
    crop_h = max(r for r, _ in occupied) - top + 1
    crop_w = max(c for _, c in occupied) - left + 1
    assert (top, left) != ((len(grid) - crop_h) // 2, (len(grid[0]) - crop_w) // 2)
    assert module.self_check(grid) == []
    if texture == "blob":
        reached = {next(iter(occupied))}
        pending = list(reached)
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in occupied and neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        assert reached == occupied


def test_all_finite_ordinary_controls_in_every_band(generator):
    # Each of 9 heights, 9 widths, 6 counts and 2 textures is tested together
    # in every difficulty band. A clipped count or narrower band fails here.
    for band in BANDS:
        for height in range(6, 15):
            for width in range(6, 15):
                for size in range(3, 9):
                    for texture in ("blob", "scatter"):
                        grid = generator.generate(17, 3, difficulty=band,
                                                  grid_h=height, grid_w=width,
                                                  shape_size=size, texture=texture)
                        assert_ordinary(generator, grid, height=height, width=width,
                                        size=size, texture=texture)


def test_observer_reports_realized_exact_values(generator):
    for seed, index in ((0, 0), (17, 3), (301, 27)):
        for texture in ("blob", "scatter"):
            grid = generator.generate(seed, index, grid_h=6, grid_w=14,
                                      shape_size=8, texture=texture)
            actual = generator.observe_overrides(grid)
            assert actual["grid_h"] == 6 and type(actual["grid_h"]) is int
            assert actual["grid_w"] == 14 and type(actual["grid_w"]) is int
            assert actual["shape_size"] == 8 and type(actual["shape_size"]) is int
            assert actual["shape_size"] == len(cells(grid))
            assert "texture" not in actual  # Sampling style is not uniquely observable.


def test_numeric_controls_reject_coercion_and_out_of_domain_values(generator):
    for axis in ("grid_h", "grid_w", "shape_size"):
        for value in (True, False, 3.0, 6.9, "8", [], {}):
            with pytest.raises((TypeError, ValueError)):
                generator.generate(0, 3, **{axis: value})
    for axis, values in (("grid_h", (5, 15)), ("grid_w", (5, 15)),
                         ("shape_size", (2, 9))):
        for value in values:
            with pytest.raises(ValueError):
                generator.generate(0, 3, **{axis: value})


def test_unknown_controls_and_textures_are_rejected(generator):
    for value in (1, None):
        with pytest.raises((TypeError, ValueError, KeyError)):
            generator.generate(0, 3, unknown_knob=value)
    for texture in ("misspelled", "", 1, True, [], {}):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(0, 3, texture=texture)


def test_seed_index_and_difficulty_are_strict_request_scalars(generator):
    for seed in (True, False, 17.0, "17", None, [], {}):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(seed, 3)
    for index in (True, False, 3.0, "3", None, -1, [], {}):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(17, index)
    for band in (True, False, 0, 0.5, "unknown", "", [], {}):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(17, 3, difficulty=band)


def test_none_controls_keep_the_no_override_convention(generator):
    for band in BANDS:
        expected = generator.generate(17, 3, difficulty=band)
        assert generator.generate(17, 3, difficulty=band, grid_h=None,
                                  grid_w=None, shape_size=None, texture=None) == expected


def test_diagnostic_textures_honor_dimensions_and_reject_as_lessons(generator):
    for band in BANDS:
        for height, width in ((6, 14), (14, 6), (9, 10)):
            for size in range(3, 9):
                grid = generator.generate(17, 3, difficulty=band, texture="already_centered",
                                          grid_h=height, grid_w=width, shape_size=size)
                assert (len(grid), len(grid[0]), len(cells(grid))) == (height, width, size)
                assert generator.self_check(grid)
            grid = generator.generate(17, 3, difficulty=band, texture="shape_fills_grid",
                                      grid_h=height, grid_w=width, shape_size=None)
            assert (len(grid), len(grid[0])) == (height, width)
            assert len(cells(grid)) == height * width
            assert generator.self_check(grid)
            with pytest.raises(ValueError) as rejected:
                generator.generate(17, 3, difficulty=band, texture="shape_fills_grid",
                                   grid_h=height, grid_w=width, shape_size=3)
            assert "shape_size" in str(rejected.value)
            assert "shape_fills_grid" in str(rejected.value)


def test_diagnostic_textures_are_outside_the_ordinary_axis_domain(generator):
    valid = generator.AXES["texture"]["valid"]
    ordinary = {value.strip() for value in valid.split("|")} if isinstance(valid, str) else set(valid)
    assert ordinary == {"blob", "scatter"}
    assert set(generator.DEGENERATE_TEXTURES) == {"already_centered", "shape_fills_grid"}
    assert ordinary.isdisjoint(generator.DEGENERATE_TEXTURES)


def test_diagnostic_selection_is_recorded_in_draw_provenance(generator):
    from puzzle_generators.base import set_ctx_observer
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for texture in generator.DEGENERATE_TEXTURES:
            generator.generate(17, 3, grid_h=6, grid_w=14, texture=texture)
            assert contexts[-1].overrides_used().get("texture") == texture
            assert contexts[-1].recorded_draws().get("texture") == texture
    finally:
        set_ctx_observer(None)


def test_validator_rejects_malformed_grids_without_mutating_them(generator):
    malformed = (None, 3, "01", [], [[]], [[0], [0, 1]], [[False, True]],
                 [[0, 10]], [[-1, 0]], [[1.0, 0]], [["1", 0]], [None],
                 [[0, 0], [0, 0]])
    for grid in malformed:
        original = deepcopy(grid)
        reasons = generator.self_check(grid)
        assert isinstance(reasons, list) and reasons, repr(grid)
        assert all(isinstance(reason, str) and reason for reason in reasons)
        assert grid == original


def test_validator_rejects_grid_count_and_palette_outside_the_lesson_domain(generator):
    examples = []
    for height, width in ((5, 8), (15, 8), (8, 5), (8, 15)):
        grid = [[0] * width for _ in range(height)]
        grid[0][:2], grid[1][:2] = [1, 2], [2, 1]
        examples.append(grid)
    for count in (1, 2, 9):
        grid = [[0] * 10 for _ in range(10)]
        for position in range(count):
            grid[position // 3][position % 3] = 1 + position % 2
        examples.append(grid)
    for palette in ((1, 1, 1, 1), (1, 2, 3, 4)):
        grid = [[0] * 8 for _ in range(8)]
        grid[0][:2], grid[1][:2] = list(palette[:2]), list(palette[2:])
        examples.append(grid)
    for grid in examples:
        original = deepcopy(grid)
        assert generator.self_check(grid), grid
        assert grid == original


def test_canonical_inputs_remain_accepted_and_validation_is_pure(generator):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert generator.self_check(pair["input"]) == [], (pair["variant"], pair["split"], pair["pair_index"])
        assert pair["input"] == original


def test_default_draws_and_replays_stay_in_the_declared_domain(generator):
    observed = set()
    signatures = set()
    for band in BANDS:
        for seed in range(30):
            index = seed * 17 + 3
            grid = generator.generate(seed, index, difficulty=band)
            assert_ordinary(generator, grid)
            assert generator.generate(seed, index, difficulty=band) == grid
            observed.add(len(cells(grid)))
            signatures.add(tuple(map(tuple, grid)))
    assert observed == set(range(3, 9))
    assert len(signatures) >= 30
