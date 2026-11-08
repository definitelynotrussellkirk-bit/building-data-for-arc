"""Portable behavioral regressions for the pairwise-intersection gallery.

The oracle below follows the four literal windows of the selected Racket rule.
It imports no generator helpers, source notes, or private review scripts.
Run in a catalog checkout with PYTHONPATH=src:shared/runtime, or through the
public task_tests stage, which supplies the copied runtime's import path.
"""
from __future__ import annotations

import copy
import importlib.util
import sys

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "0db54f549d0e"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("reviewed_pairwise_gallery", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

PAIRS = canonical_pairs(TASK, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")
WINDOWS = ((0, 0), (4, 0), (0, 4), (0, 8))
AXES = ("row0_cells", "row1_cells", "col0_cells", "col1_cells")
CANONICAL_PALETTE = {0, 2, 3, 4, 5}


def masks(grid):
    return tuple(
        frozenset((r, c) for r in range(3) for c in range(3)
                  if grid[top + r][left + c] != 0)
        for top, left in WINDOWS
    )


def observed_counts(grid):
    return dict(zip(AXES, (len(shape) for shape in masks(grid))))


def gallery_output(grid):
    """Independent truth-table oracle: four Boolean ANDs, no color equality."""
    shapes = masks(grid)
    out = [[0] * 7 for _ in range(7)]
    for i in range(2):
        for j in range(2):
            for r, c in shapes[i] & shapes[j + 2]:
                out[4 * i + r][4 * j + c] = 8
    return out


def fixture(height=7, width=11):
    """Four differently shaped windows; background includes blank separators."""
    grid = [[0] * width for _ in range(height)]
    patterns = (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0), (2, 1)),
        ((0, 0), (0, 2), (1, 1), (2, 1)),
        ((0, 1), (1, 0), (1, 2), (2, 0), (2, 2)),
    )
    for (top, left), color, cells in zip(WINDOWS, (2, 3, 4, 5), patterns):
        for r, c in cells:
            grid[top + r][left + c] = color
    return grid


def require_callable(name):
    function = getattr(GEN, name, None)
    assert callable(function), f"missing public callable {name}"
    return function


def findings(check, grid):
    result = check(grid)
    assert isinstance(result, list), "validators must return list[str]"
    assert all(isinstance(message, str) for message in result)
    return result


def freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_identity_is_pinned_to_the_unchanged_authority():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK
    assert getattr(GEN, "RULE_HASH", None) == "2a9df9793155"


def test_independent_oracle_matches_every_canonical_label():
    assert PAIRS, "Canonical coverage may not silently be empty"
    for pair in PAIRS:
        assert gallery_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_every_count_value_is_exact_in_each_window_and_difficulty(band):
    # Removing any public count override or silently clamping its boundary must fail.
    for index, axis in enumerate(AXES):
        for target in range(10):
            request = dict(zip(AXES, (3, 4, 5, 6)))
            request[axis] = target
            grid = GEN.generate(431, 10 * index + target, difficulty=band, **request)
            assert observed_counts(grid) == request, (band, axis, target)
            assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
def test_joint_counts_include_opposite_extremes_and_intermediate_values(band):
    cases = [(0, 9, 0, 9), (9, 0, 9, 0), (0, 0, 0, 0), (9, 9, 9, 9)]
    cases += [(n, (n + 3) % 10, 9 - n, (n + 7) % 10) for n in range(10)]
    for index, values in enumerate(cases):
        request = dict(zip(AXES, values))
        grid = GEN.generate(902, index, difficulty=band, **request)
        assert observed_counts(grid) == request
        assert GEN.self_check(grid, difficulty=band, meta={"overrides": request}) == []


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("value", [-1, 10, True, False, 1.0, 2.5, "3", "", [], {}])
def test_invalid_cell_count_values_are_rejected(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(13, 6, **{axis: value})


@pytest.mark.parametrize("overrides", [{"typo_axis": 2}, {"row0_cell": 3}, {"unknown": None}])
def test_unknown_override_names_are_rejected_even_when_none(overrides):
    with pytest.raises(ValueError):
        GEN.generate(13, 6, **overrides)


@pytest.mark.parametrize("value", ["bogus", "", 3, True, [], {}])
def test_invalid_texture_values_are_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(13, 6, texture=value)


@pytest.mark.parametrize("band", BANDS)
def test_none_overrides_have_the_same_meaning_as_absence(band):
    for index in range(4):
        expected = GEN.generate(167, index, difficulty=band)
        supplied = {axis: None for axis in AXES}
        supplied["texture"] = None
        assert GEN.generate(167, index, difficulty=band, **supplied) == expected


@pytest.mark.parametrize("texture,count,output_ink", [
    ("empty_shapes", 0, 0), ("full_shapes", 9, 36), ("single_overlap", 1, 4),
])
def test_declared_textures_are_lawful_and_have_exact_semantics(texture, count, output_ink):
    assert texture in GEN.DEGENERATE_TEXTURES
    for index in range(4):
        request = dict.fromkeys(AXES, count)
        grid = GEN.generate(337, index, texture=texture, **request)
        assert observed_counts(grid) == request
        assert findings(GEN.self_check, grid) == []
        assert sum(cell == 8 for row in gallery_output(grid) for cell in row) == output_ink
        if texture == "single_overlap":
            assert len(set(masks(grid))) == 1, "All four singleton masks must coincide"


@pytest.mark.parametrize("texture,conflict", [
    ("empty_shapes", 1), ("full_shapes", 8), ("single_overlap", 2),
])
@pytest.mark.parametrize("axis", AXES)
def test_incompatible_texture_counts_raise_instead_of_overriding_the_request(texture, conflict, axis):
    with pytest.raises(ValueError):
        GEN.generate(219, 3, texture=texture, **{axis: conflict})


@pytest.mark.parametrize("grid", [
    None, 17, True, "junk", {}, [], [[]], [0] * 7, [None] * 7,
    [[0] * 11 for _ in range(6)] + [[0] * 2],
    [[0] * 11, None] + [[0] * 11 for _ in range(5)],
    [[0] * 11 for _ in range(6)], [[0] * 10 for _ in range(7)],
])
def test_self_check_handles_malformed_grids_without_crashing(grid):
    assert findings(GEN.self_check, grid)


@pytest.mark.parametrize("bad_cell", [-1, 10, True, 2.0, "2", None, float("nan"), float("inf")])
def test_self_check_rejects_non_arc_cells_inside_an_occupied_window(bad_cell):
    grid = fixture()
    grid[0][0] = bad_cell
    assert findings(GEN.self_check, grid)


def test_self_check_accepts_lawful_empty_windows_and_maximum_padding():
    cases = [fixture(), fixture(11, 15), [[0] * 11 for _ in range(7)]]
    one_empty = fixture()
    for row in range(3):
        one_empty[row][:3] = [0, 0, 0]
    cases.append(one_empty)
    for grid in cases:
        original = copy.deepcopy(grid)
        assert findings(GEN.self_check, grid) == []
        assert grid == original


@pytest.mark.parametrize("height,width", [(12, 11), (7, 16)])
def test_self_check_rejects_grids_outside_the_declared_finite_support(height, width):
    assert findings(GEN.self_check, fixture(height, width))


@pytest.mark.parametrize("position", [(3, 0), (0, 3), (3, 3), (6, 10), (10, 14)])
def test_self_check_rejects_ink_outside_the_fixed_windows(position):
    grid = fixture(11, 15)
    grid[position[0]][position[1]] = 7
    assert findings(GEN.self_check, grid)


def test_self_check_rejects_multiple_nonzero_colors_in_one_window():
    grid = fixture()
    grid[0][0] = 9
    assert findings(GEN.self_check, grid)


def test_canonical_examples_are_accepted_and_match_the_independent_oracle():
    strict = require_callable("strict_canonical_like")
    assert PAIRS, "Canonical coverage may not silently be empty"
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert findings(GEN.self_check, pair["input"]) == []
        assert findings(strict, pair["input"]) == []
        assert gallery_output(pair["input"]) == pair["output"]
        assert pair["input"] == original
    assert findings(strict, [[0] * 11 for _ in range(6)] + [[0]])


def test_observer_reads_window_pixels_in_handmade_and_modified_inputs():
    observe = require_callable("observe_overrides")
    grid = fixture(11, 15)
    original = copy.deepcopy(grid)
    assert {axis: observe(grid)[axis] for axis in AXES} == observed_counts(grid)
    assert grid == original
    grid[0][0] = 0
    result = observe(grid)
    assert isinstance(result, dict)
    assert {axis: result[axis] for axis in AXES} == observed_counts(grid)
    assert result["row0_cells"] == 1


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_are_deterministic_varied_and_retain_canonical_profiles(band):
    grids = [GEN.generate(101, index, difficulty=band) for index in range(20)]
    assert grids == [GEN.generate(101, index, difficulty=band) for index in range(20)]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert len({freeze(grid) for grid in grids}) >= 10
    assert len({freeze(gallery_output(grid)) for grid in grids}) >= 4
    exact = [grid for grid in grids if len(grid) == 7 and len(grid[0]) == 11
             and {cell for row in grid for cell in row} == CANONICAL_PALETTE]
    assert exact, f"No exact canonical dimension/palette profile in {band} 20-draw window"
    assert any(len(grid) > 7 or len(grid[0]) > 11 for grid in grids)
    assert any({cell for row in grid for cell in row} - CANONICAL_PALETTE for grid in grids)
    canonical_inputs = {freeze(pair["input"]) for pair in PAIRS}
    assert all(freeze(grid) not in canonical_inputs for grid in grids)


def test_rule_mirror_obeys_intersection_placement_and_ignores_nonzero_color_identity():
    mirror = require_callable("rule_mirror")
    inputs = [fixture(), fixture(11, 15)]
    inputs += [GEN.generate(783, index) for index in range(8)]
    inputs += [GEN.generate(783, 0, texture=name) for name in GEN.DEGENERATE_TEXTURES]
    for grid in inputs:
        original = copy.deepcopy(grid)
        expected = gallery_output(grid)
        assert mirror(grid) == expected
        assert grid == original
        # All shapes share one arbitrary color; no output may depend on equality
        # between the original window colors or on an input color being 8.
        for color in (1, 8, 9):
            recolored = [[color if cell else 0 for cell in row] for row in grid]
            assert GEN.self_check(recolored) == []
            assert mirror(recolored) == gallery_output(recolored) == expected


def test_public_keyed_draw_provenance_matches_realized_default_and_requested_counts():
    from puzzle_generators.base import set_ctx_observer

    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for index, request in enumerate(({}, dict(zip(AXES, (0, 9, 2, 7))))):
            grid = GEN.generate(173, index, **request)
            assert contexts, "generate must use the public deterministic context"
            context = contexts[-1]
            drawn = context.recorded_draws()
            assert all(axis in drawn for axis in AXES), "Counts need keyed draw provenance"
            assert {axis: drawn[axis] for axis in AXES} == observed_counts(grid)
            if request:
                used = context.overrides_used()
                assert {axis: used[axis] for axis in AXES} == request
    finally:
        set_ctx_observer(None)
