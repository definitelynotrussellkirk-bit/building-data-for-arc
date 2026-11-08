"""Regression and semantic-contract tests for 82b36c453029."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "82b36c453029"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
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


def blank_like(grid):
    return [[0 for _ in row] for row in grid]


def independent_rule(grid):
    output = blank_like(grid)
    for component in components(grid):
        r1, c1, r2, c2 = component["bbox"]
        output[(r1 + r2) // 2][(c1 + c2) // 2] = component["color"]
    return output


def one_center_per_color(grid):
    output = blank_like(grid)
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


def nearest_centroid(grid):
    output = blank_like(grid)
    for component in components(grid):
        cells = component["cells"]
        count = len(cells)
        row = (2 * sum(r for r, _ in cells) + count) // (2 * count)
        column = (2 * sum(c for _, c in cells) + count) // (2 * count)
        output[row][column] = component["color"]
    return output


def upper_bbox_midpoint(grid):
    output = blank_like(grid)
    for component in components(grid):
        r1, c1, r2, c2 = component["bbox"]
        output[(r1 + r2 + 1) // 2][(c1 + c2 + 1) // 2] = component["color"]
    return output


def occupied_center_only(grid):
    output = blank_like(grid)
    for component in components(grid):
        r1, c1, r2, c2 = component["bbox"]
        row, column = (r1 + r2) // 2, (c1 + c2) // 2
        if grid[row][column] == component["color"]:
            output[row][column] = component["color"]
    return output


def pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def manual_shortcut_witness():
    grid = [[0] * 11 for _ in range(9)]
    # Asymmetric 2x4 color-4 component. Intended=(0,1), centroid=(0,2),
    # upper midpoint=(1,2).
    for row, column in ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)):
        grid[row][column] = 4
    # A second disconnected color-4 component is a 3x3 ring. Its intended
    # bbox center (5,1) is initially background, defeating "keep the center".
    for row, column in (
        (4, 0), (4, 1), (4, 2), (5, 0), (5, 2), (6, 0), (6, 1), (6, 2)
    ):
        grid[row][column] = 4
    # A third ordinary component keeps the scene within the declared grammar.
    for row, column in ((4, 7), (5, 6), (5, 7), (5, 8), (6, 7)):
        grid[row][column] = 7
    return grid


def test_rule_pin_and_truthful_axis_contract():
    assert GEN.RULE_HASH == "b5f364e5c32b"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "components",
        "n_distinct_colors",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "sample_index,height,width,count,distinct",
    [
        (0, 7, 9, 3, 3),
        (1, 7, 9, 4, 2),
        (2, 10, 12, 3, 2),
        (3, 14, 16, 4, 3),
    ],
)
def test_exact_overrides_are_constructive_and_observable(
    band, sample_index, height, width, count, distinct
):
    grid = GEN.generate(
        183,
        sample_index,
        difficulty=band,
        grid_h=height,
        grid_w=width,
        components=count,
        n_distinct_colors=distinct,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "components": count,
        "n_distinct_colors": distinct,
    }
    assert independent_rule(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,overrides",
    [
        (True, 0, None, {}),
        (0, True, None, {}),
        (0, -1, None, {}),
        (0, 0, "impossible", {}),
        (0, 0, None, {"grid_h": 6}),
        (0, 0, None, {"grid_h": 15}),
        (0, 0, None, {"grid_w": 8}),
        (0, 0, None, {"grid_w": 17}),
        (0, 0, None, {"components": 2}),
        (0, 0, None, {"components": 5}),
        (0, 0, None, {"n_distinct_colors": 1}),
        (0, 0, None, {"n_distinct_colors": 4}),
        (0, 0, None, {"components": "3"}),
        (0, 0, None, {"unknown_axis": 1}),
    ],
)
def test_invalid_controls_are_rejected(seed, sample_index, difficulty, overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_canonical_inputs_are_accepted_and_rule_mirror_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for item in pairs:
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert independent_rule(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]


def test_declared_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    expected = {
        "one_center_per_color": one_center_per_color,
        "nearest_cell_centroid": nearest_centroid,
        "upper_bbox_midpoint": upper_bbox_midpoint,
        "occupied_center_only": occupied_center_only,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(expected)
    assert set(GEN.LESSON_COMPETITORS) == set(expected)
    for name, shortcut in expected.items():
        assert all(shortcut(item["input"]) == item["output"] for item in pairs), name
        assert all(
            GEN.CANONICAL_SHORTCUTS[name](deepcopy(item["input"])) == item["output"]
            for item in pairs
        ), name


def test_exact_manual_counterexample_refutes_all_declared_shortcuts():
    grid = manual_shortcut_witness()
    expected = independent_rule(grid)
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert one_center_per_color(grid) != expected
    assert nearest_centroid(grid) != expected
    assert upper_bbox_midpoint(grid) != expected
    assert occupied_center_only(grid) != expected
    assert GEN.SEMANTIC_WITNESSES["repeated_color_objects"](grid)
    assert GEN.SEMANTIC_WITNESSES["centroid_differs"](grid)
    assert GEN.SEMANTIC_WITNESSES["floor_midpoint_matters"](grid)
    assert GEN.SEMANTIC_WITNESSES["bbox_center_is_background"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_profile_schedule_supplies_all_shortcut_witnesses(band):
    grids = [GEN.generate(911, index, difficulty=band) for index in range(15)]
    assert any(GEN.strict_canonical_like(grid) == [] for grid in grids)
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        firings = [witness(grid) for grid in grids]
        assert any(firings), (band, name)
        assert not all(firings), (band, name)
    for start in range(12):
        lesson = [pair(grid) for grid in grids[start : start + 4]]
        for query_index, query in enumerate(lesson):
            demos = [item for index, item in enumerate(lesson) if index != query_index]
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


def test_self_check_rejects_structural_impostors_and_malformed_grids():
    impostors = [
        None,
        [],
        [[]],
        [[0] * 11 for _ in range(9)],
        [[4] * 11 for _ in range(9)],
        [[4 if (r, c) == (2, 2) else 0 for c in range(11)] for r in range(9)],
        [[4 if r == 2 and 2 <= c <= 4 else 0 for c in range(11)] for r in range(9)],
        [[4 if 2 <= r <= 3 and 2 <= c <= 3 else 0 for c in range(11)] for r in range(9)],
        [[True] * 11 for _ in range(9)],
    ]
    for grid in impostors:
        assert GEN.self_check(grid), grid


def test_default_distribution_varies_controls_and_hits_every_profile():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(314, index, difficulty=band) for index in range(90)]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert {item["components"] for item in observed} == {3, 4}
        assert {item["n_distinct_colors"] for item in observed} == {2, 3}
        assert len({item["grid_h"] for item in observed}) >= 5
        assert len({item["grid_w"] for item in observed}) >= 5
        assert any(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert any(GEN.SEMANTIC_WITNESSES["repeated_color_objects"](grid) for grid in grids)
        assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 86


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    canonical_profiles = {(9, 11, 4), (8, 10, 4), (10, 12, 4), (7, 9, 4), (9, 10, 4)}
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
