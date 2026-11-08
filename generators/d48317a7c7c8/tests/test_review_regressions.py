"""Source-bound regressions for exact yellow three-bar cap generation.

Run from the packet with ``python3 run_with_racket.py python3 -m pytest
generators/d48317a7c7c8/tests/test_review_regressions.py``.  The tests also work
in a copied runtime: canonical data and the implementation are located from
this file, without private checker imports or another checkout.
"""
from __future__ import annotations

from collections import deque
import importlib.util
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "d48317a7c7c8"
ROOT = find_root(__file__)
_SOURCE_CANDIDATES = (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
)
SOURCE = next(path for path in _SOURCE_CANDIDATES if path.is_file())
_SPEC = importlib.util.spec_from_file_location("reviewed_d48317a7c7c8", SOURCE)
assert _SPEC is not None and _SPEC.loader is not None
gen = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = gen
_SPEC.loader.exec_module(gen)


def _components(grid):
    """Observe nonzero, monochrome, four-connected objects independently."""
    height, width = len(grid), len(grid[0])
    unvisited = {(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] != 0}
    found = []
    while unvisited:
        start = min(unvisited)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unvisited.remove(start)
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for next_cell in ((row - 1, col), (row + 1, col),
                              (row, col - 1), (row, col + 1)):
                if next_cell not in unvisited:
                    continue
                if grid[next_cell[0]][next_cell[1]] != color:
                    continue
                unvisited.remove(next_cell)
                cells.add(next_cell)
                queue.append(next_cell)
        found.append((color, frozenset(cells)))
    return found


def _straight(cells):
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    return len(rows) == 1 or len(cols) == 1


def _targets(grid):
    return [cells for color, cells in _components(grid)
            if color == 4 and len(cells) == 3 and _straight(cells)]


def _caps(cells):
    rows = sorted({row for row, _ in cells})
    cols = sorted({col for _, col in cells})
    if len(rows) == 1:
        return ((rows[0], cols[0] - 1), (rows[0], cols[-1] + 1))
    return ((rows[0] - 1, cols[0]), (rows[-1] + 1, cols[0]))


def _expected_output(grid):
    """Apply the task rule to observed objects, never generator internals."""
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for cells in _targets(grid):
        for row, col in _caps(cells):
            if 0 <= row < height and 0 <= col < width and grid[row][col] == 0:
                out[row][col] = 8
    return out


def _scene(cells, color=4):
    grid = [[0] * 8 for _ in range(6)]
    for row, col in cells:
        grid[row][col] = color
    return grid


def _assert_grid(grid, height, width):
    assert len(grid) == height
    assert all(len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9
               for row in grid for value in row)


def test_canonical_inputs_are_accepted_and_observer_matches_labels():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    for pair in pairs:
        identity = (pair["variant"], pair["split"], pair["pair_index"])
        assert gen.self_check(pair["input"]) == [], identity
        assert _expected_output(pair["input"]) == pair["output"], identity


@pytest.mark.parametrize("cells,color", [
    ([(2, 2), (2, 3), (2, 4), (2, 5)], 4),
    ([(2, 2), (2, 3), (2, 4), (3, 4)], 4),
    ([(2, 2), (2, 3), (3, 3)], 4),
    ([(2, 2), (2, 3), (2, 4)], 6),
    ([], 4),
], ids=["length-four", "L-with-three-cell-arm", "L-three", "nonyellow", "empty-scene"])
def test_self_check_requires_an_exact_straight_yellow_component(cells, color):
    grid = _scene(cells, color)
    assert not _targets(grid)
    assert _expected_output(grid) == grid
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors, "A no-target scene was certified"


def test_self_check_rejects_a_target_with_both_cap_cells_occupied():
    grid = _scene([(2, 2), (2, 3), (2, 4)])
    grid[2][1], grid[2][5] = 6, 1
    assert len(_targets(grid)) == 1
    assert _expected_output(grid) == grid
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors, "A scene with no paintable cap was certified"


@pytest.mark.parametrize("kind", ["boundary", "occupied"])
def test_self_check_accepts_a_target_with_one_available_cap(kind):
    if kind == "boundary":
        grid = _scene([(2, 0), (2, 1), (2, 2)])
    else:
        grid = _scene([(2, 2), (2, 3), (2, 4)])
        grid[2][1] = 6
    expected = _expected_output(grid)
    assert sum(left != right for a, b in zip(grid, expected)
               for left, right in zip(a, b)) == 1
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("invalid", [-1, 10, False, 4.0, "4", None])
@pytest.mark.parametrize("meta", [None, {"texture": "no_bars"}])
def test_self_check_rejects_invalid_cell_data_even_with_degenerate_metadata(invalid, meta):
    grid = _scene([(2, 2), (2, 3), (2, 4)])
    grid[0][0] = invalid
    errors = gen.self_check(grid, meta=meta)
    assert isinstance(errors, list) and errors, "Invalid ARC cells were certified"


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_bars", [1, 10])
def test_exact_target_count_and_size_are_independent_of_difficulty(difficulty, n_bars):
    grid = gen.generate(2718, 3, difficulty=difficulty,
                        grid_h=24, grid_w=24, n_bars=n_bars)
    _assert_grid(grid, 24, 24)
    assert len(_targets(grid)) == n_bars
    assert gen.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("difficulty", ["medium", "hard"])
def test_one_bar_override_is_observed_on_default_sized_boards(difficulty):
    grid = gen.generate(2718, 3, difficulty=difficulty, n_bars=1)
    assert len(_targets(grid)) == 1


@pytest.mark.parametrize("axis,value", [
    ("grid_h", True), ("grid_h", 9.0), ("grid_h", "9"),
    ("grid_w", True), ("grid_w", 9.0), ("grid_w", "9"),
    ("n_bars", True), ("n_bars", 1.0), ("n_bars", "1"),
    ("distractor_color", False), ("distractor_color", 6.0),
    ("distractor_color", "6"),
    ("grid_h", 7), ("grid_w", 25), ("n_bars", 0), ("n_bars", 11),
    ("distractor_color", 0), ("distractor_color", 4), ("distractor_color", 10),
])
def test_invalid_exact_overrides_raise_instead_of_coercing_or_ignoring(axis, value):
    overrides = {"grid_h": 9, "grid_w": 9, "n_bars": 1, axis: value}
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty="easy", **overrides)


@pytest.mark.parametrize("axis,value", [
    ("review_unknown_axis", True),
    ("palette_kind", "varied"), ("palette_size", 1),
    ("position_bias", "scattered_length3_bars"),
    ("n_distinct_colors", 1), ("density", "sparse"),
    ("texture", "default"),
])
def test_unknown_and_retired_descriptive_overrides_are_rejected(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty="easy", **{axis: value})


@pytest.mark.parametrize("color", [1, 6, 8, 9])
def test_exact_distractor_color_changes_observed_nonyellow_three_bar(color):
    grid = gen.generate(9, 1, difficulty="medium", grid_h=13, grid_w=13,
                        n_bars=2, distractor_color=color)
    _assert_grid(grid, 13, 13)
    colored_bars = [cells for observed, cells in _components(grid)
                    if observed == color and len(cells) == 3 and _straight(cells)]
    assert colored_bars, f"No length-three distractor in exact requested color {color}"
    assert len(_targets(grid)) == 2


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_ordinary_sampling_teaches_color_length_and_straightness_filters(difficulty):
    observed = set()
    for index in range(24):
        grid = gen.generate(314159, index, difficulty=difficulty)
        _assert_grid(grid, len(grid), len(grid[0]))
        assert gen.self_check(grid, difficulty=difficulty) == [], index
        targets = _targets(grid)
        assert targets, index
        height, width = len(grid), len(grid[0])
        for cells in targets:
            for row, col in _caps(cells):
                if not (0 <= row < height and 0 <= col < width):
                    observed.add("boundary_cap")
                elif grid[row][col] != 0:
                    observed.add("occupied_cap")
        for color, cells in _components(grid):
            if color != 4 and len(cells) == 3 and _straight(cells):
                observed.add("nonyellow_three")
            elif color == 4 and _straight(cells) and len(cells) in (2, 4, 5):
                observed.add("yellow_wrong_length")
            elif color == 4 and len(cells) == 3 and not _straight(cells):
                observed.add("yellow_L_three")
            elif color == 4 and len(cells) == 3:
                observed.add("horizontal" if len({row for row, _ in cells}) == 1
                             else "vertical")
    required = {"nonyellow_three", "yellow_wrong_length", "yellow_L_three",
                "horizontal", "vertical", "boundary_cap", "occupied_cap"}
    assert required <= observed, f"Missing ordinary {difficulty} support: {required - observed}"


@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_fixed_small_dimensions_adapt_the_unpinned_target_count(difficulty):
    grid = gen.generate(0, 1, difficulty=difficulty, grid_h=8, grid_w=8)
    _assert_grid(grid, 8, 8)
    assert len(_targets(grid)) >= 2


def test_ordinary_scene_keeps_both_cap_teaching_roles():
    # This actual initial-repair draw had one bar, dropping the occupied-cap
    # and monochrome-connectivity witnesses from ordinary training support.
    grid = gen.generate(0, 75, difficulty='hard')
    assert len(_targets(grid)) >= 2
    assert all(rival(grid) != _expected_output(grid)
               for rival in gen.LESSON_COMPETITORS.values())


def test_impossible_rich_packing_reports_the_requested_axes():
    with pytest.raises(ValueError) as error:
        gen.generate(0, 0, grid_h=8, grid_w=8, n_bars=10)
    assert set(error.value.incompatible_axes) == {'grid_h', 'grid_w', 'n_bars'}
    assert '2' in str(error.value)
