from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.516502422f5c.generator"
)


def _canonical_inputs():
    path = Path(__file__).parents[1] / "data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == MODULE.TASK_ID:
            return [pair["input"] for pair in row["train"] + row["test"]]
    raise AssertionError("canonical task missing")


def test_canonical_inputs_pass_structural_check():
    assert all(MODULE.self_check(grid) == [] for grid in _canonical_inputs())


def test_exact_axes_are_observable_at_boundaries():
    for side in MODULE.MARKER_SIDES:
        grid = MODULE.generate(
            123,
            7,
            difficulty="hard",
            grid_h=10,
            grid_w=22,
            diag_color=9,
            n_markers=15,
            marker_sides=side,
        )
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == {
            "grid_h": 10,
            "grid_w": 22,
            "diag_color": 9,
            "n_markers": 15,
            "marker_sides": side,
        }


def test_self_check_rejects_four_structural_impostors():
    base = MODULE.generate(91, 3, difficulty="medium", marker_sides="both")
    assert MODULE.self_check(base) == []

    missing_diagonal = copy.deepcopy(base)
    diag_color = MODULE.observe_overrides(base)["diag_color"]
    for r, row in enumerate(missing_diagonal):
        for c, value in enumerate(row):
            if value == diag_color:
                missing_diagonal[r][c] = 0
                break
        else:
            continue
        break

    off_diagonal_color = copy.deepcopy(base)
    for r, row in enumerate(off_diagonal_color):
        for c, value in enumerate(row):
            if value == 0:
                off_diagonal_color[r][c] = diag_color
                break
        else:
            continue
        break

    no_markers = [[0 if value == 5 else value for value in row] for row in base]
    second_color = copy.deepcopy(base)
    for r, row in enumerate(second_color):
        for c, value in enumerate(row):
            if value == 5:
                second_color[r][c] = 4 if diag_color != 4 else 3
                break
        else:
            continue
        break

    impostors = [missing_diagonal, off_diagonal_color, no_markers, second_color]
    assert all(MODULE.self_check(grid) for grid in impostors)


def test_self_check_rejects_single_marker_shortcut_scene():
    grid = MODULE.generate(303, 0, n_markers=2)
    removed = False
    for row in grid:
        for c, value in enumerate(row):
            if value == 5:
                if removed:
                    row[c] = 0
                    assert MODULE.self_check(grid)
                    return
                removed = True
    raise AssertionError("expected two markers")


def test_degenerate_textures_are_rejected():
    for texture in MODULE.DEGENERATE_TEXTURES:
        grid = MODULE.generate(5, 0, texture=texture)
        assert MODULE.self_check(grid)


def test_sequential_lesson_slots_cover_all_side_branches():
    grids = [MODULE.generate(8080, slot) for slot in range(3)]
    analyses = [MODULE._analyze(grid)[0] for grid in grids]
    assert [analysis["marker_sides"] for analysis in analyses] == [
        "left",
        "right",
        "both",
    ]
    extents = []
    for analysis in analyses:
        offsets = [
            value
            for value in (analysis["left_extreme"], analysis["right_extreme"])
            if value is not None
        ]
        extents.append(max(abs(value) for value in offsets))
    assert extents == [2, 3, 4]


def test_canonical_size_anchor_is_regular_and_overrideable():
    anchored = MODULE.generate(404, 0)
    assert (len(anchored), len(anchored[0])) == (10, 10)
    overridden = MODULE.generate(404, 0, grid_h=20, grid_w=22)
    assert (len(overridden), len(overridden[0])) == (20, 22)
