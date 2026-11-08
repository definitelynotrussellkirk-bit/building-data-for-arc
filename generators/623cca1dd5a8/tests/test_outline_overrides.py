"""Portable, independent behavioral checks for the four exact outline axes.

The component census and geometry assertions below do not call the generator's
observer or component helpers. No retained baseline or packet-only path is needed
to collect these tests in the public task_tests staging runtime.
"""
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from itertools import combinations, product
import random

import numpy as np
import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "623cca1dd5a8"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DIFFICULTIES = [None, "easy", "medium", "hard"]
DIFFICULTY_IDS = ["default", "easy", "medium", "hard"]
LIMITS = {"grid_h": (8, 16), "grid_w": (8, 16),
          "n_blobs": (2, 4), "n_distinct_colors": (2, 5)}
FEASIBLE_COUNTS = [(n, colors) for n in range(2, 5)
                   for colors in range(2, 6) if colors <= n + 1]
IMPOSSIBLE_COUNTS = [(2, 4), (2, 5), (3, 5)]


def independent_components(grid):
    """Flood-fill nonzero equal-color cells using only four-neighbor edges."""
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color != 0}
    result = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        remaining.remove(first)
        pending, cells = [first], set()
        while pending:
            r, c = pending.pop()
            cells.add((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        result.append((color, cells))
    return result


def independent_bounds(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def independent_observation(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_blobs": len(independent_components(grid)),
            "n_distinct_colors": len({color for row in grid for color in row})}


def assert_production_geometry(grid, recipe):
    assert isinstance(grid, list) and grid, recipe
    width = len(grid[0])
    assert all(isinstance(row, list) and len(row) == width for row in grid), recipe
    assert all(type(color) is int and 0 <= color <= 9
               for row in grid for color in row), recipe
    assert any(color == 0 for row in grid for color in row), recipe
    boxes = []
    for _, cells in independent_components(grid):
        r0, c0, r1, c1 = independent_bounds(cells)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        assert height >= 2 and width >= 2, recipe
        assert len(cells) < height * width, recipe
        boxes.append((r0, c0, r1, c1))
    for a, b in combinations(boxes, 2):
        # At least one complete background row or column separates the bboxes.
        assert (a[2] + 1 < b[0] or b[2] + 1 < a[0]
                or a[3] + 1 < b[1] or b[3] + 1 < a[1]), recipe


def rich_witnesses(grid):
    groups = independent_components(grid)
    repeated = max(Counter(color for color, _ in groups).values(), default=0) > 1
    interior = any(r0 < r < r1 and c0 < c < c1
                   for _, cells in groups
                   for r0, c0, r1, c1 in [independent_bounds(cells)]
                   for r, c in cells)
    broad = any(r1 - r0 >= 2 and c1 - c0 >= 2
                for _, cells in groups
                for r0, c0, r1, c1 in [independent_bounds(cells)])
    return repeated, interior, broad


def has_thin_box(grid):
    return any(min(r1 - r0 + 1, c1 - c0 + 1) <= 2
               for _, cells in independent_components(grid)
               for r0, c0, r1, c1 in [independent_bounds(cells)])


def test_public_axes_and_incompatibilities_describe_exactly_the_supported_counts():
    assert set(GEN.AXES) == set(LIMITS)
    assert all(spec["type"] == "int" for spec in GEN.AXES.values())
    declared = set()
    for row in GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS:
        assert set(row) == {"n_blobs", "n_distinct_colors"}
        values = [value if isinstance(value, list) else [value]
                  for value in (row["n_blobs"], row["n_distinct_colors"])]
        declared.update(product(*values))
    assert declared == set(IMPOSSIBLE_COUNTS)


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("index", [0, 1], ids=["rich", "canonical"])
@pytest.mark.parametrize("n_blobs,n_colors", FEASIBLE_COUNTS)
def test_every_feasible_exact_count_and_canvas_is_realized(difficulty, index, n_blobs, n_colors):
    """72 collected cases exercise 81 canvases each: 5,832 exact joint draws."""
    for height, width in product(range(8, 17), repeat=2):
        expected = {"grid_h": height, "grid_w": width,
                    "n_blobs": n_blobs, "n_distinct_colors": n_colors}
        recipe = {"seed": 17, "sample_index": index, "difficulty": difficulty, **expected}
        grid = GEN.generate(17, index, difficulty=difficulty, **expected)
        observed = independent_observation(grid)
        assert observed == expected, (recipe, observed)
        assert_production_geometry(grid, recipe)
        assert GEN.observe_overrides(grid) == observed, recipe
        assert GEN.self_check(grid) == [], recipe


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("index", [0, 1], ids=["rich", "canonical"])
@pytest.mark.parametrize("n_blobs,n_colors", IMPOSSIBLE_COUNTS)
def test_only_impossible_color_component_pairs_are_refused(difficulty, index, n_blobs, n_colors):
    for height, width in product((8, 16), repeat=2):
        with pytest.raises(ValueError, match="n_distinct_colors.*n_blobs"):
            GEN.generate(17, index, difficulty=difficulty, grid_h=height, grid_w=width,
                         n_blobs=n_blobs, n_distinct_colors=n_colors)


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("index", [0, 1], ids=["rich", "canonical"])
def test_each_control_works_without_requiring_other_controls(difficulty, index):
    for axis, (lo, hi) in LIMITS.items():
        for value in range(lo, hi + 1):
            grid = GEN.generate(3, index, difficulty=difficulty, **{axis: value})
            observed = independent_observation(grid)
            assert observed[axis] == value, (axis, value, difficulty, index, observed)
            assert observed["n_distinct_colors"] <= observed["n_blobs"] + 1
            assert_production_geometry(grid, (axis, value, difficulty, index))


@pytest.mark.parametrize("overrides", [
    {"n_blobs": 4},
    {"n_distinct_colors": 5},
    {"n_distinct_colors": 2},
    {"grid_h": 16, "grid_w": 8},
], ids=["four-components", "five-colors", "two-colors-including-background", "full-canvas-range"])
def test_minimal_predecessor_override_regressions(overrides):
    grid = GEN.generate(0, 0, difficulty="easy", **overrides)
    observed = independent_observation(grid)
    assert all(observed[name] == value for name, value in overrides.items()), (overrides, observed)


@pytest.mark.parametrize("axis,value", [(axis, value)
    for axis, (lo, hi) in LIMITS.items() for value in (lo - 1, hi + 1)])
def test_integer_values_outside_advertised_ranges_are_rejected(axis, value):
    with pytest.raises(ValueError, match=axis):
        GEN.generate(0, 0, **{axis: value})


class IntegerSubclass(int):
    pass


INVALID_FACTORIES = [
    pytest.param(lambda value: True, id="true"),
    pytest.param(lambda value: False, id="false"),
    pytest.param(float, id="float"),
    pytest.param(str, id="string"),
    pytest.param(Decimal, id="decimal"),
    pytest.param(Fraction, id="fraction"),
    pytest.param(np.int64, id="numpy-integer"),
    pytest.param(IntegerSubclass, id="integer-subclass"),
    pytest.param(lambda value: [value], id="list"),
    pytest.param(lambda value: (value,), id="tuple"),
    pytest.param(lambda value: {"value": value}, id="mapping"),
]


@pytest.mark.parametrize("axis", list(LIMITS))
@pytest.mark.parametrize("factory", INVALID_FACTORIES)
def test_supplied_controls_reject_nonliteral_integers(axis, factory):
    # 9 and 10 also fit the predecessor's default draw ranges, so the float and
    # string cases detect coercion rather than merely an out-of-range value.
    valid = {"grid_h": 9, "grid_w": 10, "n_blobs": 2, "n_distinct_colors": 2}[axis]
    with pytest.raises(ValueError, match=axis):
        GEN.generate(0, 0, **{axis: factory(valid)})


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("index", [0, 1], ids=["rich", "canonical"])
def test_explicit_none_keeps_the_shared_unset_override_convention(difficulty, index):
    expected = GEN.generate(5, index, difficulty=difficulty)
    assert GEN.generate(5, index, difficulty=difficulty,
                        **dict.fromkeys(LIMITS)) == expected


@pytest.mark.parametrize("name,value", [
    ("palette_kind", "warm"), ("palette_size", 4),
    ("position_bias", "spaced_nonrect_blobs"), ("density", "sparse"),
    ("texture", "default"), ("texture", "no_blobs"),
    ("texture", "all_solid_rects"), ("texture", "single_cell_blobs"),
    ("canonical_side", 8), ("partition", 0), ("blob_0", 0),
    ("unknown_control", None),
])
@pytest.mark.parametrize("index", [0, 1], ids=["rich", "canonical"])
def test_retired_unknown_and_internal_controls_cannot_bypass_validation(name, value, index):
    with pytest.raises(ValueError, match="unknown override axes"):
        GEN.generate(0, index, **{name: value})


@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [
    pytest.param(-1, id="negative"), pytest.param(True, id="true"),
    pytest.param(False, id="false"), pytest.param(0.0, id="float"),
    pytest.param("0", id="string"), pytest.param(None, id="none"),
    pytest.param(np.int64(0), id="numpy-integer"),
    pytest.param(IntegerSubclass(0), id="integer-subclass"),
    pytest.param(float("inf"), id="infinity"), pytest.param(float("nan"), id="nan"),
])
def test_invalid_seed_and_index_are_rejected(argument, value):
    request = {"seed": 0, "sample_index": 0, argument: value}
    with pytest.raises(ValueError, match=argument):
        GEN.generate(**request)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "", "EASY", "unknown", [], {}])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("seed,index", [(0, 0), (17, 1), (2**129, 2**130 + 1)])
def test_inputs_are_deterministic_without_global_rng_or_override_order_dependence(difficulty, seed, index):
    overrides = {"grid_h": 8, "grid_w": 8, "n_blobs": 4, "n_distinct_colors": 2}
    before = random.getstate()
    first = GEN.generate(seed, index, difficulty=difficulty, **overrides)
    GEN.generate(seed + 1, index + 1, difficulty=difficulty)
    repeated = GEN.generate(seed, index, difficulty=difficulty,
                            **dict(reversed(list(overrides.items()))))
    assert repeated == first
    assert random.getstate() == before
    assert independent_observation(first) == overrides


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("seed", [0, 1, 17])
def test_default_period_two_profiles_have_their_observable_witnesses(difficulty, seed):
    assert GEN.LESSON_SCHEDULE_PERIOD == 2
    assert GEN.EXAMPLES_NEEDED == 3
    for index in range(12):
        grid = GEN.generate(seed, index, difficulty=difficulty)
        observed = independent_observation(grid)
        if index % 2 == 0:
            assert GEN.schedule_profile(seed, index, difficulty) == "rich"
            assert all(rich_witnesses(grid)), (seed, index, difficulty)
        else:
            assert GEN.schedule_profile(seed, index, difficulty) == "canonical_scale"
            assert observed["grid_h"] == observed["grid_w"]
            assert 8 <= observed["grid_h"] <= 10
            assert observed["n_blobs"] == 2 and observed["n_distinct_colors"] == 3
            assert has_thin_box(grid), (seed, index, difficulty)


@pytest.mark.parametrize("difficulty", DIFFICULTIES, ids=DIFFICULTY_IDS)
@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("start", [0, 1, 4, 5])
def test_each_query_holdout_retains_rich_and_thin_demo_witnesses(difficulty, seed, start):
    """32 four-pair lessons exercise every holdout, for 128 rotations."""
    inputs = [GEN.generate(seed, index, difficulty=difficulty)
              for index in range(start, start + 4)]
    for query_index in range(4):
        demos = [grid for index, grid in enumerate(inputs) if index != query_index]
        assert len(demos) == 3
        assert any(all(rich_witnesses(grid)) for grid in demos), (difficulty, seed, start, query_index)
        assert any(has_thin_box(grid) for grid in demos), (difficulty, seed, start, query_index)


@pytest.mark.parametrize("height,width", [(30, 8), (8, 30), (30, 30)])
def test_self_check_accepts_legal_full_extent_canvases_beyond_production(height, width):
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = 7
    for row, col in [(height - 2, width - 2), (height - 1, width - 2),
                     (height - 1, width - 1)]:
        grid[row][col] = 4
    assert independent_observation(grid) == {"grid_h": height, "grid_w": width,
                                             "n_blobs": 2, "n_distinct_colors": 3}
    assert GEN.self_check(grid) == []
