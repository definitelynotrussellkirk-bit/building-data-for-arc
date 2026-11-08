"""Independent regression tests for separated one-cell bridge inputs.

Run from the repository root:
  python3 -m pytest -q generators/4a6d26e0b6ae/tests
No Racket is needed for these structural tests. Labels are checked separately.
"""
from collections import Counter, defaultdict
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
spec = importlib.util.spec_from_file_location("bridge_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def independent_spans(grid):
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                points[color].append((r, c))
    assert points, "missing motifs"
    spans = []
    for color, cells in points.items():
        assert len(cells) == 2, f"color {color}: not two endpoints"
        (r, c), (y, x) = cells
        assert (r == y or c == x) and abs(r-y) + abs(c-x) == 2
        middle = ((r+y)//2, (c+x)//2)
        assert grid[middle[0]][middle[1]] == 0, f"color {color}: overwritten gap"
        span = set(cells) | {middle}
        for other in spans:
            assert all(max(abs(a-u), abs(b-v)) > 1
                       for a, b in span for u, v in other), "motifs touch"
        spans.append(span)
    return spans


def test_seed10_previously_overwrote_a_reserved_gap():
    independent_spans(gen.generate(10, 0))


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_seed_and_sample_census_integrity(band):
    for seed in range(80):
        for index in (0, 7):
            grid = gen.generate(seed, index, difficulty=band)
            independent_spans(grid)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(seed, index, difficulty=band)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("axis", ["grid_h", "grid_w"])
@pytest.mark.parametrize("value", [5, 14])
def test_override_bounds_independent_of_difficulty(axis, value, band):
    grid = gen.generate(9, 0, difficulty=band, **{axis: value})
    assert (len(grid) if axis == "grid_h" else len(grid[0])) == value
    independent_spans(grid)


@pytest.mark.parametrize("count", [1, 3, 5, 8])
@pytest.mark.parametrize("texture", ["default", "horizontal", "vertical", "edge"])
def test_exact_requested_count_and_texture(count, texture):
    grid = gen.generate(17, 3, grid_h=14, grid_w=14,
                        gap_count=count, texture=texture)
    spans = independent_spans(grid)
    assert len(spans) == count
    assert gen.observe_overrides(grid)["gap_count"] == count
    if texture == "horizontal":
        assert all(len({r for r, _ in s}) == 1 for s in spans)
    elif texture == "vertical":
        assert all(len({c for _, c in s}) == 1 for s in spans)
    elif texture == "edge":
        assert any(r in (0, 13) or c in (0, 13) for s in spans for r, c in s)


@pytest.mark.parametrize("key", ["bogus", "palette_kind", "palette_size",
                                  "n_distinct_colors", "position_bias", "density"])
def test_ignored_legacy_or_unknown_axes_now_fail_loudly(key):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: 1})


@pytest.mark.parametrize("grid", [[], [[]], [[0, 1], [2]], [[0, 11]],
                                   [[0, 1.5]], [[False, 0]], [[1, 0, 1], [0, 0, 0], [0, 2, 0]]])
def test_selfcheck_rejects_malformed_and_incomplete_scenes(grid):
    assert gen.self_check(grid)


def test_selfcheck_rejects_overwritten_gap_even_when_another_gap_survives():
    grid = [[0]*9 for _ in range(7)]
    grid[1][1] = grid[1][3] = 4
    grid[4][5] = grid[6][5] = 7
    grid[5][5] = 2
    assert gen.self_check(grid)


def test_selfcheck_is_not_a_vacuous_rejector():
    grid = [[0]*9 for _ in range(7)]
    grid[1][1] = grid[1][3] = 4
    grid[4][5] = grid[6][5] = 7
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize("texture", ["no_gaps", "gap_already_filled", "mismatched_endpoints"])
def test_explicit_degenerate_honors_size_and_has_no_bridge(texture):
    grid = gen.generate(33, 4, texture=texture, grid_h=14, grid_w=5)
    assert (len(grid), len(grid[0])) == (14, 5)
    assert gen.self_check(grid, meta={"texture": texture}) == []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                continue
            assert not (0 < c < 4 and grid[r][c-1] and grid[r][c-1] == grid[r][c+1])
            assert not (0 < r < 13 and grid[r-1][c] and grid[r-1][c] == grid[r+1][c])


def test_impossible_count_is_structured_error_not_partial_return():
    with pytest.raises(ValueError) as caught:
        gen.generate(1, 0, grid_h=5, grid_w=5, gap_count=8)
    assert "gap_count" in caught.value.incompatible_axes


def test_blank_texture_cannot_silently_ignore_requested_gap_count():
    with pytest.raises(ValueError):
        gen.generate(1, 0, texture="no_gaps", gap_count=2)


@pytest.mark.parametrize("value", [True, 7.5, "8", 0, 15])
def test_bad_integer_parameters_rejected(value):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(0, 0, grid_h=value)


def test_difficulty_bands_do_not_clone_anchor_layouts():
    # Fixed census: an anchor is a shape/scale distribution, not a duplicate grid.
    grids = [repr(gen.generate(seed, 0, difficulty=band)) for seed in range(100)
             for band in (None, "easy", "medium", "hard")]
    assert len(set(grids)) >= 380


def test_negative_fixtures_not_advertised_as_ordinary_axis_values():
    assert not set(gen.DEGENERATE_TEXTURES) & set(gen.AXES["texture"]["valid"].split("|"))


@pytest.mark.parametrize("texture", ["default", "horizontal", "vertical", "edge"])
def test_dense_supported_capacity_across_every_size(texture):
    for h in range(5, 15):
        for w in range(5, 15):
            horizontal = ((h+1)//2) * ((w+1)//4)
            vertical = ((w+1)//2) * ((h+1)//4)
            capacity = horizontal if texture == "horizontal" else vertical if texture == "vertical" else max(horizontal, vertical)
            count = min(8, capacity)
            grid = gen.generate(31, 9, grid_h=h, grid_w=w, gap_count=count, texture=texture)
            assert len(independent_spans(grid)) == count
