"""Independent geometry and protected-Racket tests for the proposed family.

The exact fixture expectations below list hand-checked cell additions.  They
are not a Python implementation of the label rule.  Generated teaching checks
compare executed Racket programs using demonstrations alone.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ROOT = HOME.parents[3]


@pytest.fixture(scope="module")
def prototype():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("frame_parametric_semantics", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket():
    from arcpuzzles.parametric_worker import _real_evaluator

    apply, identity, bridge = _real_evaluator(ROOT / "shared" / "runtime")
    assert identity["backend"] == "racket" and identity["protected"] is True
    try:
        yield apply
    finally:
        bridge.close()


def _frames(grid):
    """Extract monochrome four-connected components without prototype helpers."""
    todo = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color}
    frames = []
    while todo:
        start = min(todo)
        color = grid[start[0]][start[1]]
        todo.remove(start)
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in todo and grid[point[0]][point[1]] == color:
                    todo.remove(point)
                    cells.add(point)
                    stack.append(point)
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {(r, c) for r in range(top, bottom + 1)
                  for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        if cells == border:
            frames.append({"top": top, "left": left, "bottom": bottom,
                           "right": right, "height": bottom - top + 1,
                           "width": right - left + 1, "color": color,
                           "perimeter": len(cells),
                           "area": (bottom - top + 1) * (right - left + 1)})
    return sorted(frames, key=lambda frame: frame["perimeter"], reverse=True)


def _hand_fixture():
    """Tall 23x7 target (perimeter 56, area 161), wide 11x15 decoy (48,165)."""
    grid = [[0] * 30 for _ in range(30)]
    for top, left, bottom, right, color in ((3, 2, 25, 8, 6), (2, 13, 12, 27, 4)):
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r in (top, bottom) or c in (left, right):
                    grid[r][c] = color
    for r, c, color in ((4, 3, 2), (8, 6, 3), (13, 4, 2),
                        (18, 7, 7), (23, 3, 3), (24, 6, 7),
                        (3, 14, 2), (5, 25, 3), (1, 4, 2)):
        grid[r][c] = color
    return grid


def _with_edits(grid, edits):
    result = deepcopy(grid)
    for row, column, color in edits:
        assert result[row][column] == 0
        result[row][column] = color
    return result


VERTICAL_ADDITIONS = ((4, 7, 2), (8, 4, 3), (13, 6, 2),
                      (18, 3, 7), (23, 7, 3), (24, 4, 7))
HORIZONTAL_ADDITIONS = ((24, 3, 2), (20, 6, 3), (15, 4, 2),
                        (10, 7, 7), (5, 3, 3), (4, 6, 7))


@pytest.mark.parametrize("axis,edits", [
    ("vertical", VERTICAL_ADDITIONS),
    ("horizontal", HORIZONTAL_ADDITIONS),
    ("long_axis", VERTICAL_ADDITIONS),
])
def test_exact_fixture_labels_select_perimeter_and_preserve_exterior(prototype, racket, axis, edits):
    grid = _hand_fixture()
    before = deepcopy(grid)
    actual = racket(prototype.program({"axis": axis}), grid)
    assert actual == _with_edits(grid, edits)
    assert grid == before


def test_transposed_fixture_changes_derived_long_axis(prototype, racket):
    grid = [list(row) for row in zip(*_hand_fixture())]
    expected = [list(row) for row in zip(*_with_edits(_hand_fixture(), VERTICAL_ADDITIONS))]
    actual = racket(prototype.program({"axis": "long_axis"}), grid)
    assert actual == expected
    assert actual != racket(prototype.program({"axis": "vertical"}), grid)


def test_wrong_selected_frame_changes_the_consumed_axis_and_output(prototype, racket):
    grid = _hand_fixture()
    expected_wrong = _with_edits(grid, ((11, 14, 2), (9, 25, 3)))
    correct = racket(prototype.program({"axis": "long_axis"}), grid)
    for selection in ("smallest", "largest_area", "first"):
        wrong = racket(prototype.diagnostic_rule("long_axis", selection=selection), grid)
        assert wrong == expected_wrong
        assert wrong != correct


@pytest.mark.parametrize("seed", [0, 14, 17])
def test_generated_selection_cues_and_stress_are_structural(prototype, seed):
    train, queries = prototype.inputs(seed, demos=2, queries=4)
    for index, grid in enumerate(train + queries):
        frames = _frames(grid)
        assert len(frames) == 2, (seed, index, frames)
        main, decoy = frames
        assert main["perimeter"] > decoy["perimeter"]
        assert main["height"] != main["width"]
        assert all(frame["height"] % 2 == frame["width"] % 2 == 1 for frame in frames)
        for frame in frames:
            center_r = (frame["top"] + frame["bottom"]) // 2
            center_c = (frame["left"] + frame["right"]) // 2
            quadrants = {(r > center_r, c > center_c)
                         for r in range(frame["top"] + 1, frame["bottom"])
                         for c in range(frame["left"] + 1, frame["right"])
                         if grid[r][c] and r != center_r and c != center_c}
            assert quadrants, "Each frame needs unfinished off-axis content"
            if frame is main:
                assert quadrants == {(False, False), (False, True), (True, False), (True, True)}
        if index < 2:
            assert decoy["area"] > main["area"], "Area and perimeter need opposite rankings"
            assert (main["height"] > main["width"]) != (decoy["height"] > decoy["width"])
            target_first = (main["top"], main["left"]) < (decoy["top"], decoy["left"])
            assert target_first is bool(index % 2), "Transpose must preserve the teaching order"
        if len(grid) == len(grid[0]) == 30:
            top = min(frame["top"] for frame in frames)
            bottom = max(frame["bottom"] for frame in frames)
            left = min(frame["left"] for frame in frames)
            right = max(frame["right"] for frame in frames)
            assert bottom - top + 1 >= 27 and right - left + 1 >= 27
            assert 27 in (main["height"], main["width"])
            assert main["top"] == 0 or main["left"] == 0 or main["bottom"] == 29 or main["right"] == 29


@pytest.mark.parametrize("seed", [0, 14, 17])
@pytest.mark.parametrize("axis", ["vertical", "horizontal", "long_axis"])
def test_two_demos_rule_out_query_disagreeing_shortcuts(prototype, racket, seed, axis):
    train, queries = prototype.inputs(seed, demos=2, queries=4)
    rule = prototype.program({"axis": axis})
    demo_labels = [racket(rule, grid) for grid in train]
    query_labels = [racket(rule, grid) for grid in queries]
    names = ("setting_vertical", "setting_horizontal", "setting_long_axis",
             "select_largest_area", "select_first", "select_last", "canvas_axis",
             "source_half", "exterior", "all_frames")
    rivals = prototype.rivals(axis)
    for name in names:
        rival = rivals[name]
        if all(racket(rival, grid) == output for grid, output in zip(train, demo_labels)):
            bad_queries = [index for index, (grid, output) in enumerate(zip(queries, query_labels))
                           if racket(rival, grid) != output]
            assert not bad_queries, (seed, axis, name, bad_queries)


def test_seed14_scope_regression_refutes_exterior_rival_in_demos(prototype, racket):
    """Before repair, both demos fit the rival and all four queries disagreed."""
    train, _ = prototype.inputs(14, demos=2, queries=4)
    correct = prototype.program({"axis": "long_axis"})
    rival = prototype.diagnostic_rule("long_axis", mode="exterior")
    assert any(racket(correct, grid) != racket(rival, grid) for grid in train)
