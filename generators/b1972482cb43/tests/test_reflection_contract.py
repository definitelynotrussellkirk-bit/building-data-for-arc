"""Source-local contracts for the single-anchor point-reflection generator.

Run in a review packet with:
    python3 review.py run python3 -m pytest -q \
        generators/b1972482cb43/tests/test_reflection_contract.py

The geometry below is independent of the generator's placement implementation.
Canonical labels bind that geometry to this selected task.
"""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "b1972482cb43"
ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def _grid(shape=((1, 1), (1, 2)), *, anchor=(2, 3), h=5, w=7, color=3):
    grid = [[0] * w for _ in range(h)]
    for r, c in shape:
        grid[r][c] = color
    if anchor is not None:
        grid[anchor[0]][anchor[1]] = 9
    return grid


def _cells(grid, predicate):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if predicate(value)
    }


def _reflection(grid):
    (ar, ac), = _cells(grid, lambda value: value == 9)
    h, w = len(grid), len(grid[0])
    return {
        (2 * ar - r, 2 * ac - c)
        for r, c in _cells(grid, lambda value: value not in (0, 9))
        if 0 <= 2 * ar - r < h and 0 <= 2 * ac - c < w
    }


def _point_reflection_output(grid):
    output = [row[:] for row in grid]
    (ar, ac), = _cells(grid, lambda value: value == 9)
    h, w = len(grid), len(grid[0])
    for r, c in _cells(grid, lambda value: value not in (0, 9)):
        rr, cc = 2 * ar - r, 2 * ac - c
        if 0 <= rr < h and 0 <= cc < w:
            output[rr][cc] = grid[r][c]
    return output


def _assert_lawful(grid):
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert grid[0]
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    assert len(_cells(grid, lambda value: value == 9)) == 1
    shape = _cells(grid, lambda value: value not in (0, 9))
    assert 2 <= len(shape) <= 5
    assert len({grid[r][c] for r, c in shape}) == 1
    reached = {next(iter(shape))}
    pending = list(reached)
    while pending:
        r, c = pending.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in shape and neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    assert reached == shape, "shape must be connected through shared edges"
    reflected = _reflection(grid)
    assert reflected, "at least one reflected cell must be visible"
    assert not (shape & reflected), "shape must not overlap its point reflection"
    assert _point_reflection_output(grid) != grid


@pytest.mark.parametrize(
    "pair", CANONICAL,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_canonical_inputs_satisfy_contract_and_reflection_matches_labels(pair):
    _assert_lawful(pair["input"])
    assert GENERATOR.self_check(pair["input"]) == []
    assert _point_reflection_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        7,
        "not a grid",
        [None],
        [[0, 9], [3]],
        [[0, 9], [3, 3, 0]],
        [[0, 9], None],
    ],
    ids=[
        "none", "empty", "empty-row", "scalar", "text", "non-row",
        "short-row", "long-row", "mixed-row-types",
    ],
)
def test_malformed_inputs_return_diagnostics_instead_of_crashing(grid):
    errors = GENERATOR.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) and error for error in errors)


@pytest.mark.parametrize(
    "value", [False, True, 0.0, 3.0, "0", None, -1, 10],
    ids=["false", "true", "float-background", "float-color", "text", "none", "negative", "too-large"],
)
def test_non_arc_integer_cells_are_rejected(value):
    grid = _grid()
    grid[0][0] = value
    assert GENERATOR.self_check(grid)


def _invalid_semantic_grids():
    multiple_anchors = _grid()
    multiple_anchors[3][3] = 9
    multiple_colors = _grid()
    multiple_colors[1][2] = 4
    return [
        pytest.param(_grid(anchor=None), id="no-anchor"),
        pytest.param(multiple_anchors, id="multiple-anchors"),
        pytest.param(_grid(shape=()), id="no-shape"),
        pytest.param(_grid(shape=((1, 1),)), id="one-cell-shape"),
        pytest.param(multiple_colors, id="multiple-shape-colors"),
        pytest.param(_grid(shape=((1, 1), (1, 3))), id="disconnected-shape"),
        pytest.param(_grid(shape=((1, 1), (2, 2))), id="diagonal-only-shape"),
        pytest.param(
            _grid(shape=((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))),
            id="six-cell-shape",
        ),
        pytest.param(
            _grid(shape=((1, 2), (1, 3), (1, 4), (2, 4), (3, 4))),
            id="overlapping-reflection",
        ),
        pytest.param(
            _grid(shape=((2, 2), (2, 3)), anchor=(0, 0)),
            id="fully-clipped-reflection",
        ),
    ]


@pytest.mark.parametrize("grid", _invalid_semantic_grids())
def test_declared_semantic_violations_are_rejected(grid):
    assert GENERATOR.self_check(grid)


@pytest.mark.parametrize("texture", ["no_anchor", "no_shape", "reflection_oob"])
def test_degenerate_texture_names_are_truthful_and_rejected(texture):
    grid = GENERATOR.generate(17, 0, texture=texture)
    anchors = _cells(grid, lambda value: value == 9)
    shape = _cells(grid, lambda value: value not in (0, 9))
    if texture == "no_anchor":
        assert not anchors and shape
    elif texture == "no_shape":
        assert len(anchors) == 1 and not shape
    else:
        assert len(anchors) == 1 and 2 <= len(shape) <= 5
        assert not _reflection(grid), "reflection_oob must put every reflected cell outside the grid"
    assert GENERATOR.self_check(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(4, 5), (5, 7), (5, 8), (12, 14)])
def test_exact_boundary_and_canonical_dimensions_work_in_every_band(difficulty, height, width):
    overrides = {"grid_h": height, "grid_w": width}
    for seed, sample_index in ((0, 0), (17, 3), (91, 11)):
        grid = GENERATOR.generate(seed, sample_index, difficulty=difficulty, **overrides)
        assert len(grid) == height
        assert all(len(row) == width for row in grid)
        _assert_lawful(grid)
        assert GENERATOR.self_check(grid, difficulty=difficulty) == []
        assert grid == GENERATOR.generate(seed, sample_index, difficulty=difficulty, **overrides)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_are_lawful_and_deterministic(difficulty):
    for sample_index in range(12):
        grid = GENERATOR.generate(231, sample_index, difficulty=difficulty)
        _assert_lawful(grid)
        assert GENERATOR.self_check(grid, difficulty=difficulty) == []
        assert grid == GENERATOR.generate(231, sample_index, difficulty=difficulty)


@pytest.mark.parametrize(
    "palette_kind,allowed",
    [
        ("default", set(range(1, 9))),
        ("warm", {2, 4, 7}),
        ("cool", {1, 3, 8}),
        ("varied", {5, 6}),
    ],
)
def test_palette_kind_selects_the_declared_shape_color_family(palette_kind, allowed):
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(4):
            grid = GENERATOR.generate(41, sample_index, difficulty=difficulty, palette_kind=palette_kind)
            shape_colors = {value for row in grid for value in row if value not in (0, 9)}
            assert len(shape_colors) == 1 and shape_colors <= allowed
            _assert_lawful(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": True},
        {"grid_w": 7.0},
        {"grid_h": "5"},
        {"grid_h": 3},
        {"grid_w": 15},
        {"palette_size": 3},
        {"palette_size": True},
        {"n_distinct_colors": 2},
        {"n_distinct_colors": 3.0},
        {"palette_kind": "unknown"},
        {"position_bias": "center"},
        {"density": "dense"},
        {"texture": "unknown"},
        {"unexpected_axis": "ignored"},
    ],
    ids=[
        "boolean-height", "float-width", "text-height", "short-height", "wide-width",
        "wrong-palette-size", "boolean-palette-size", "wrong-distinct-count", "float-distinct-count",
        "unknown-palette", "unknown-position", "unknown-density", "unknown-texture", "unknown-key",
    ],
)
def test_invalid_controls_are_rejected_instead_of_ignored_or_coerced(overrides):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(0, 0, difficulty="easy", **overrides)


def test_fixed_color_count_controls_describe_the_generated_grid():
    grid = GENERATOR.generate(17, 0, palette_size=2, n_distinct_colors=3)
    colors = {value for row in grid for value in row}
    assert len(colors - {0}) == 2
    assert len(colors) == 3
    _assert_lawful(grid)
