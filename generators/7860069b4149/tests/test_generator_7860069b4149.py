from __future__ import annotations

import copy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "7860069b4149"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK, root=ROOT)


def _facts(grid):
    height, width = len(grid), len(grid[0])
    anchor = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 9]
    cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] not in (0, 9)]
    assert len(anchor) == 1 and cells
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    ar, ac = anchor[0]
    if ac < c0:
        direction = (0, 1)
        steps = width - 1 - c1
    elif ac > c1:
        direction = (0, -1)
        steps = c0
    elif ar < r0:
        direction = (1, 0)
        steps = height - 1 - r1
    else:
        direction = (-1, 0)
        steps = r0
    return cells, anchor[0], direction, steps


def _oracle(grid):
    output = copy.deepcopy(grid)
    cells, _, (dr, dc), steps = _facts(grid)
    color = grid[cells[0][0]][cells[0][1]]
    for distance in range(1, steps + 1):
        for row, col in cells:
            output[row + dr * distance][col + dc * distance] = color
    return output


def _scanline_envelope(grid):
    output = copy.deepcopy(grid)
    cells, _, (dr, dc), steps = _facts(grid)
    color = grid[cells[0][0]][cells[0][1]]
    shifted = [(r + dr * steps, c + dc * steps) for r, c in cells]
    if dc:
        by_row = {}
        for r, c in cells + shifted:
            by_row.setdefault(r, []).append(c)
        for r, cols in by_row.items():
            for c in range(min(cols), max(cols) + 1):
                output[r][c] = color
    else:
        by_col = {}
        for r, c in cells + shifted:
            by_col.setdefault(c, []).append(r)
        for c, rows in by_col.items():
            for r in range(min(rows), max(rows) + 1):
                output[r][c] = color
    return output


def test_every_labeled_canonical_input_is_in_domain_and_matches_independent_oracle():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("side,expected", [
    ("left", (0, 1)),
    ("right", (0, -1)),
    ("top", (1, 0)),
    ("bottom", (-1, 0)),
])
def test_each_anchor_side_is_generated_and_has_positive_sweep(side, expected):
    grid = GEN.generate(
        101,
        3,
        grid_h=11,
        grid_w=13,
        anchor_side=side,
        shape_kind="l3",
        foreground_color=6,
    )
    assert GEN.self_check(grid) == []
    cells, _, direction, steps = _facts(grid)
    assert direction == expected
    assert steps >= 1
    assert {grid[r][c] for r, c in cells} == {6}
    assert GEN.rule_mirror(grid) == _oracle(grid)


@pytest.mark.parametrize("height,width", [(5, 5), (5, 30), (30, 5), (30, 30)])
def test_declared_dimension_boundaries_execute(height, width):
    grid = GEN.generate(202, 0, grid_h=height, grid_w=width, shape_kind="l3")
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.self_check(grid) == []


def test_concave_shape_refutes_scanline_envelope_shortcut():
    grid = GEN.generate(
        303,
        0,
        grid_h=9,
        grid_w=12,
        anchor_side="left",
        shape_kind="wide_u",
        foreground_color=4,
        sweep_steps=1,
    )
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == _oracle(grid)
    assert GEN.rule_mirror(grid) != _scanline_envelope(grid)


def test_exactly_one_available_translation_step_is_valid_in_every_direction():
    cases = []
    # right
    g = [[0] * 8 for _ in range(6)]
    for r, c in ((2, 5), (2, 6), (3, 5), (3, 6)):
        g[r][c] = 4
    g[2][4] = 9
    cases.append(g)
    # left
    g = [[0] * 8 for _ in range(6)]
    for r, c in ((2, 1), (2, 2), (3, 1), (3, 2)):
        g[r][c] = 4
    g[2][3] = 9
    cases.append(g)
    # down
    g = [[0] * 6 for _ in range(8)]
    for r, c in ((5, 2), (5, 3), (6, 2), (6, 3)):
        g[r][c] = 4
    g[4][2] = 9
    cases.append(g)
    # up
    g = [[0] * 6 for _ in range(8)]
    for r, c in ((1, 2), (1, 3), (2, 2), (2, 3)):
        g[r][c] = 4
    g[3][2] = 9
    cases.append(g)

    for grid in cases:
        assert _facts(grid)[3] == 1
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == _oracle(grid)


def test_zero_step_disconnected_and_multicolor_inputs_fail_closed():
    zero_step = [[0] * 6 for _ in range(6)]
    for r, c in ((0, 2), (0, 3), (1, 2)):
        zero_step[r][c] = 5
    zero_step[2][2] = 9
    assert GEN.self_check(zero_step)

    disconnected = [[0] * 8 for _ in range(6)]
    disconnected[2][2] = disconnected[2][4] = 3
    disconnected[2][1] = 9
    assert GEN.self_check(disconnected)

    multicolor = [[0] * 8 for _ in range(6)]
    multicolor[2][2] = 3
    multicolor[2][3] = 4
    multicolor[2][1] = 9
    assert GEN.self_check(multicolor)


def test_deterministic_fresh_returns_and_unknown_controls_fail_closed():
    first = GEN.generate(404, 7, anchor_side="bottom", shape_kind="t4")
    second = GEN.generate(404, 7, anchor_side="bottom", shape_kind="t4")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 8
    assert GEN.generate(404, 7, anchor_side="bottom", shape_kind="t4") == second
    with pytest.raises(ValueError):
        GEN.generate(1, 0, anchor_side="diagonal")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, shape_kind="unknown")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, palette_kind="warm")
