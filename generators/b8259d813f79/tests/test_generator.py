"""Regression and semantic-contract tests for b8259d813f79."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "b8259d813f79"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for drow, dcolumn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + drow, cc + dcolumn
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(columns), max(rows), max(columns)),
                }
            )
    return sorted(result, key=lambda item: (item["bbox"][0], item["bbox"][1]))


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def independent_rule(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        r1, c1, r2, c2 = component["bbox"]
        output[(r1 + r2) // 2][(c1 + c2) // 2] = component["color"]
    return output


def color_group_shortcut(grid):
    output = _blank_like(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, column)
            for row, values in enumerate(grid)
            for column, value in enumerate(values)
            if value == color
        ]
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        output[(min(rows) + max(rows)) // 2][(min(columns) + max(columns)) // 2] = color
    return output


def nearest_centroid_shortcut(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        cells = component["cells"]
        count = len(cells)
        row = (2 * sum(r for r, _ in cells) + count) // (2 * count)
        column = (2 * sum(c for _, c in cells) + count) // (2 * count)
        output[row][column] = component["color"]
    return output


def ceil_bbox_center_shortcut(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        r1, c1, r2, c2 = component["bbox"]
        output[(r1 + r2 + 1) // 2][(c1 + c2 + 1) // 2] = component["color"]
    return output


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def _manual_shortcut_witness():
    grid = [[0] * 10 for _ in range(8)]
    # A 2x4 asymmetric color-4 object: intended center (0,1), rounded
    # centroid (0,2), and upper bbox midpoint (1,2).
    for row, column in ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)):
        grid[row][column] = 4
    # A second disconnected object of the same color makes per-color grouping wrong.
    for row, column in ((4, 0), (4, 1), (4, 2), (5, 0), (6, 0)):
        grid[row][column] = 4
    for row, column in ((4, 6), (4, 7), (4, 8), (5, 7), (6, 7)):
        grid[row][column] = 7
    return grid


def test_rule_pin_and_truthful_small_axis_contract():
    assert GEN.RULE_HASH == "60b82500e77c"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_blobs",
        "n_distinct_colors",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(8, 10), (9, 11), (14, 16)])
@pytest.mark.parametrize("n_blobs", [3, 4])
@pytest.mark.parametrize("n_distinct_colors", [2, 3])
def test_exact_overrides_are_constructive_and_observable(
    band, height, width, n_blobs, n_distinct_colors
):
    grid = GEN.generate(
        183,
        7,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        n_blobs=n_blobs,
        n_distinct_colors=n_distinct_colors,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "n_blobs": n_blobs,
        "n_distinct_colors": n_distinct_colors,
    }
    assert independent_rule(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 9},
        {"grid_w": 17},
        {"n_blobs": 2},
        {"n_blobs": 5},
        {"n_distinct_colors": 1},
        {"n_distinct_colors": 4},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"n_blobs": "3"},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    values = dict(kwargs)
    difficulty = values.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **values)


def test_canonical_inputs_are_accepted_and_rule_mirror_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_declared_shortcuts_really_fit_all_canonical_demonstrations():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    expected = {
        "one_center_per_color": color_group_shortcut,
        "nearest_cell_centroid": nearest_centroid_shortcut,
        "upper_bbox_midpoint": ceil_bbox_center_shortcut,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(expected)
    assert set(GEN.LESSON_COMPETITORS) == set(expected)
    for name, shortcut in expected.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name
        assert all(
            GEN.CANONICAL_SHORTCUTS[name](deepcopy(pair["input"])) == pair["output"]
            for pair in pairs
        ), name


def test_exact_manual_counterexample_refutes_all_declared_shortcuts():
    grid = _manual_shortcut_witness()
    expected = independent_rule(grid)
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert color_group_shortcut(grid) != expected
    assert nearest_centroid_shortcut(grid) != expected
    assert ceil_bbox_center_shortcut(grid) != expected
    assert GEN.SEMANTIC_WITNESSES["repeated_color_objects"](grid)
    assert GEN.SEMANTIC_WITNESSES["centroid_differs"](grid)
    assert GEN.SEMANTIC_WITNESSES["floor_midpoint_matters"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_profile_schedule_supplies_canonical_and_shortcut_witnesses(band):
    grids = [GEN.generate(911, index, difficulty=band) for index in range(12)]
    assert any(GEN.strict_canonical_like(grid) == [] for grid in grids)
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        firings = [witness(grid) for grid in grids]
        assert any(firings), (band, name)
        assert not all(firings), (band, name)
    for start in range(3):
        window = grids[start : start + 3]
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(grid) != independent_rule(grid) for grid in window), (
                band,
                start,
                name,
            )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_four_pair_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = [
            _pair(GEN.generate(1207 + start, start + offset, difficulty=band))
            for offset in range(4)
        ]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_generation_is_deterministic_fresh_and_helpers_are_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(15):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first) == []
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.LESSON_COMPETITORS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


def test_self_check_rejects_semantic_impostors():
    good = GEN.generate(202, 1, grid_h=8, grid_w=10, n_blobs=3, n_distinct_colors=2)
    assert GEN.self_check(good) == []

    impostors = [
        [[0] * 10 for _ in range(8)],
        [[4] * 10 for _ in range(8)],
        [[4 if (r, c) == (2, 2) else 0 for c in range(10)] for r in range(8)],
        [[4 if r == 2 and 2 <= c <= 4 else 0 for c in range(10)] for r in range(8)],
        [[4 if 2 <= r <= 3 and 2 <= c <= 3 else 0 for c in range(10)] for r in range(8)],
    ]
    for grid in impostors:
        assert GEN.self_check(grid), grid

    collision = _manual_shortcut_witness()
    # Move the third component so its bbox-center collides with the second.
    for row in range(8):
        for column in range(10):
            if collision[row][column] == 7:
                collision[row][column] = 0
    for row, column in ((4, 0), (4, 1), (4, 2), (5, 1), (6, 1)):
        collision[row][column] = 7
    assert GEN.self_check(collision)


def test_default_distribution_varies_all_public_controls_and_hits_profiles():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(314, index, difficulty=band) for index in range(90)]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert {item["n_blobs"] for item in observed} == {3, 4}
        assert {item["n_distinct_colors"] for item in observed} == {2, 3}
        assert len({item["grid_h"] for item in observed}) >= 5
        assert len({item["grid_w"] for item in observed}) >= 5
        assert any(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert any(GEN.SEMANTIC_WITNESSES["repeated_color_objects"](grid) for grid in grids)
        assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 86


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    canonical_profiles = {(9, 10, 4), (8, 11, 4), (10, 10, 4), (9, 11, 4)}
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact += profile in canonical_profiles
        assert exact >= 1, (band, exact)
