"""Task-local input contract regressions; portable to a staged runtime.

ARCPUZZLES_CONTRACT_GENERATOR_FILE selects a retained source snapshot for
replaying the baseline failures. Ordinary task tests exercise selected source.
"""
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "274345a1792c"


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    override = os.environ.get("ARCPUZZLES_CONTRACT_GENERATOR_FILE")
    candidates = ([Path(override)] if override else [
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ])
    source = next(path for path in candidates if path.is_file())
    spec = spec_from_file_location("contract_generator_274345a1792c", source)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene(*, anchors=((5, 7, 1), (5, 11, 2), (9, 7, 3))):
    """Hand-built 13x16 L prototype with independent control/anchor pairs."""
    grid = [[0] * 16 for _ in range(13)]
    for r, c in ((1, 1), (2, 1), (3, 1), (3, 2)):
        grid[r][c] = 9
    for r, c, code in anchors:
        grid[r - 1][c] = code
        grid[r][c] = 6
    return grid


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 13.5), ("grid_h", 13.0), ("grid_h", "13"),
    ("grid_w", 15.5), ("grid_w", 15.0), ("grid_w", "15"),
    ("n_anchors", 2.5), ("n_anchors", 2.0), ("n_anchors", "2"),
    ("n_anchors", True), ("n_anchors", False),
    ("palette_size", 5.5), ("palette_size", "5"), ("palette_size", True),
    ("n_distinct_colors", 5.5), ("n_distinct_colors", "5"),
    ("n_distinct_colors", True),
    ("prototype_cells", 4.5), ("prototype_cells", 4.0),
    ("prototype_cells", "4"), ("prototype_cells", True),
])
def test_integer_overrides_reject_coercion(generator, axis, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, difficulty="medium", **{axis: value})


def test_unknown_override_is_rejected(generator):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, difficulty="medium", grid_heigth=13)


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 8), ("grid_h", 25), ("grid_w", 11), ("grid_w", 25),
    ("n_anchors", 0), ("n_anchors", 6),
    ("prototype_cells", 1), ("prototype_cells", 9),
    ("palette_size", 3), ("palette_size", 8),
    ("n_distinct_colors", 3), ("n_distinct_colors", 8),
])
def test_integer_overrides_outside_declared_domain_are_rejected(generator, axis, value):
    with pytest.raises(ValueError):
        generator.generate(0, 0, difficulty="medium", **{axis: value})


@pytest.mark.parametrize("value", [-1, 10, True, False, 0.0, "0", None, [], {}])
def test_self_check_rejects_invalid_arc_cell_without_crashing(generator, value):
    grid = scene()
    grid[0][0] = value
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize("grid", [None, 17, "not a grid", {}, [None], [3], [[]], [[0], []]])
def test_self_check_rejects_malformed_grid_without_crashing(generator, grid):
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors


def test_self_check_accepts_hand_built_domain_witness(generator):
    assert generator.self_check(scene()) == []


def test_self_check_rejects_stamp_clipping_at_bottom_edge(generator):
    # Code 1 keeps the 3x2 L: (12,7) would also paint rows 13 and 14.
    grid = scene(anchors=((12, 7, 1), (5, 11, 2), (9, 2, 3)))
    assert generator.self_check(grid)


def test_self_check_rejects_stamp_overwriting_prototype(generator):
    # The code-1 stamp at (1,2) includes the existing maroon cell (3,2).
    grid = scene(anchors=((1, 2, 1), (5, 11, 2), (9, 7, 3)))
    assert generator.self_check(grid)


def realized_axes(grid):
    colors = {cell for row in grid for cell in row}
    prototype = [(r, c) for r, row in enumerate(grid)
                 for c, cell in enumerate(row) if cell == 9]
    min_r, max_r = min(r for r, _ in prototype), max(r for r, _ in prototype)
    min_c, max_c = min(c for _, c in prototype), max(c for _, c in prototype)
    vertical = "top" if min_r + max_r < len(grid) - 1 else "bottom"
    horizontal = "left" if min_c + max_c < len(grid[0]) - 1 else "right"
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_anchors": sum(cell == 6 for row in grid for cell in row),
            "prototype_cells": len(prototype), "palette_size": len(colors),
            "n_distinct_colors": len(colors),
            "position_bias": f"{vertical}_{horizontal}"}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("sample_index", [0, 1])
@pytest.mark.parametrize("axis,value", [
    ("grid_h", 9), ("grid_h", 24), ("grid_w", 12), ("grid_w", 24),
    ("n_anchors", 1), ("n_anchors", 5),
    ("prototype_cells", 2), ("prototype_cells", 8),
    ("palette_size", 4), ("palette_size", 7),
    ("n_distinct_colors", 4), ("n_distinct_colors", 7),
])
def test_single_axis_endpoints_are_realized_in_every_band(
        generator, difficulty, sample_index, axis, value):
    grid = generator.generate(23, sample_index, difficulty=difficulty, **{axis: value})
    assert realized_axes(grid)[axis] == value
    assert generator.self_check(grid, difficulty=difficulty) == []
    assert generator.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,anchors,cells,palette", [
    (9, 12, 5, 8, 7), (24, 24, 1, 2, 4),
    (9, 24, 4, 7, 7), (24, 12, 5, 2, 4),
])
def test_joint_feasible_extremes_preserve_every_exact_control(
        generator, difficulty, height, width, anchors, cells, palette):
    requested = {"grid_h": height, "grid_w": width, "n_anchors": anchors,
                 "prototype_cells": cells, "palette_size": palette,
                 "n_distinct_colors": palette}
    grid = generator.generate(23, 2, difficulty=difficulty, **requested)
    actual = realized_axes(grid)
    observed = generator.observe_overrides(grid)
    for axis, value in requested.items():
        assert actual[axis] == value, (axis, value, actual)
        assert observed[axis] == value, (axis, value, observed)
    assert generator.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("position", ["top_left", "top_right", "bottom_left", "bottom_right"])
@pytest.mark.parametrize("height,width", [(9, 12), (24, 24)])
def test_position_names_locate_the_prototype_in_the_requested_quadrant(
        generator, position, height, width):
    grid = generator.generate(23, 3, difficulty="hard", grid_h=height,
                              grid_w=width, n_anchors=5, prototype_cells=8,
                              position_bias=position)
    assert realized_axes(grid)["position_bias"] == position
    assert generator.observe_overrides(grid)["position_bias"] == position
    assert generator.self_check(grid, difficulty="hard") == []


@pytest.mark.parametrize("overrides", [
    {"palette_size": 4, "n_distinct_colors": 5, "n_anchors": 3},
    {"palette_size": 5, "n_distinct_colors": 6, "n_anchors": 3},
    {"n_anchors": 1, "palette_size": 5},
    {"n_anchors": 2, "n_distinct_colors": 6},
    {"n_anchors": 3, "palette_size": 7},
])
def test_conflicting_exact_palette_constraints_are_rejected(generator, overrides):
    with pytest.raises(ValueError):
        generator.generate(23, 0, difficulty="medium", **overrides)


@pytest.mark.parametrize("anchors", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("palette", [4, 5, 6, 7])
@pytest.mark.parametrize("axis", ["palette_size", "n_distinct_colors"])
def test_every_palette_and_anchor_count_combination(generator, anchors, palette, axis):
    requested = {"n_anchors": anchors, axis: palette}
    # Background, prototype and anchors account for three fixed colors;
    # each remaining distinct color requires its own anchor's control.
    if palette - 3 > anchors:
        with pytest.raises(ValueError) as caught:
            generator.generate(31, 2, difficulty="medium", **requested)
        assert {"n_anchors", axis} <= set(caught.value.incompatible_axes)
        return
    grid = generator.generate(31, 2, difficulty="medium", **requested)
    actual = realized_axes(grid)
    assert actual["n_anchors"] == anchors and actual[axis] == palette
    assert generator.observe_overrides(grid)[axis] == palette
    assert generator.self_check(grid, difficulty="medium") == []


@pytest.mark.parametrize("anchors", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("palette", [4, 5, 6, 7])
@pytest.mark.parametrize("distinct", [4, 5, 6, 7])
def test_every_simultaneous_palette_alias_combination(generator, anchors, palette, distinct):
    requested = {"n_anchors": anchors, "palette_size": palette,
                 "n_distinct_colors": distinct}
    if palette != distinct or palette - 3 > anchors:
        with pytest.raises(ValueError) as caught:
            generator.generate(31, 2, difficulty="medium", **requested)
        axes = set(caught.value.incompatible_axes)
        if palette != distinct:
            assert {"palette_size", "n_distinct_colors"} <= axes
        else:
            assert "n_anchors" in axes and axes & {"palette_size", "n_distinct_colors"}
        return
    grid = generator.generate(31, 2, difficulty="medium", **requested)
    actual = realized_axes(grid)
    observed = generator.observe_overrides(grid)
    for axis, value in requested.items():
        assert actual[axis] == value
        assert observed[axis] == value
    assert generator.self_check(grid, difficulty="medium") == []


@pytest.mark.parametrize("overrides", [
    {"palette_kind": "default"}, {"density": "sparse"},
    {"texture": "default"}, {"texture": "no_prototype"},
    {"texture": "no_anchors"}, {"texture": "missing_control"},
    {"position_bias": "prototype_with_anchors_and_codes"},
])
def test_retired_inert_and_malformed_controls_are_rejected(generator, overrides):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(23, 0, difficulty="medium", **overrides)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_self_check_accepts_all_canonical_inputs_in_every_band(generator, difficulty):
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert generator.self_check(pair["input"], difficulty=difficulty) == [], (
            pair["variant"], pair["split"], pair["pair_index"], difficulty)


def test_self_check_allows_anchor_outside_transformed_occupied_cells(generator):
    grid = scene(anchors=((5, 7, 2), (5, 11, 1), (9, 7, 4)))
    for r, c in ((1, 1), (2, 1), (3, 1), (3, 2)):
        grid[r][c] = 0
    for r, c in ((1, 1), (1, 2), (1, 3), (2, 2)):
        grid[r][c] = 9
    # Rotating this T gives offsets (0,1), (1,0), (1,1), (2,1),
    # so the bbox-origin anchor stays magenta under codes 2 and 4.
    assert generator.self_check(grid) == []


def test_self_check_rejects_multiple_maroon_components(generator):
    grid = scene()
    grid[1][4] = grid[1][5] = 9
    assert generator.self_check(grid)


def test_self_check_rejects_unbound_control_code(generator):
    grid = scene()
    grid[0][0] = 4
    assert generator.self_check(grid)


def test_self_check_rejects_stamp_overwriting_another_control(generator):
    # The first identity stamp occupies (7,7), the second anchor's control.
    grid = scene(anchors=((5, 7, 1), (8, 7, 2), (9, 11, 3)))
    assert generator.self_check(grid)


def test_self_check_rejects_stamp_overwriting_another_anchor(generator):
    # The first identity stamp includes (7,8); its control at (6,8) is clear.
    grid = scene(anchors=((5, 7, 1), (7, 8, 1), (9, 11, 3)))
    assert generator.self_check(grid)


def test_self_check_rejects_overlapping_stamps_outside_supported_domain(generator):
    # The Racket rule lawfully unions these two L stamps at (7,6). The
    # documented production domain is narrower: distinct stamps are disjoint.
    # Retained public-reference evidence is under checks/contracts/overlap*.
    grid = scene(anchors=((5, 5, 1), (5, 6, 1)))
    assert generator.self_check(grid)
