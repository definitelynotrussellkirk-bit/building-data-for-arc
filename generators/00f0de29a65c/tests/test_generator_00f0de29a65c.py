"""Regression tests for the smallest-component curriculum of 00f0de29a65c."""
from __future__ import annotations

from collections import deque
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
TASK = "00f0de29a65c"
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
CANONICAL_PROFILES = {
    (12, 13, 5),
    (11, 12, 5),
    (10, 14, 5),
    (12, 12, 5),
    (11, 13, 5),
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_00f0de29a65c", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK:
                continue
            test = row.get("test", [])
            return row["train"] + (test if isinstance(test, list) else [test])
    raise AssertionError("canonical task row is missing")


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _scene(grid: list[list[int]]) -> dict[str, Any]:
    components = _components(grid)
    singles = [component for component in components if component["size"] == 1]
    shapes = [component for component in components if component["size"] > 1]
    assert len(singles) == 1
    sizes = [component["size"] for component in shapes]
    min_count = sizes.count(min(sizes))
    if len(set(sizes)) == 1:
        texture = "all_tied"
    elif min_count == 2:
        texture = "two_way_tie"
    elif min_count == 1:
        texture = "unique_min"
    else:
        texture = "unclassified"
    target = min(shapes, key=lambda component: (component["size"], *component["bbox"][:2]))
    return {
        "marker": singles[0],
        "shapes": shapes,
        "sizes": sizes,
        "texture": texture,
        "target": target,
    }


def _independent_output(grid: list[list[int]]) -> list[list[int]]:
    scene = _scene(grid)
    marker_color = scene["marker"]["color"]
    row1, col1, row2, col2 = scene["target"]["bbox"]
    crop = [row[col1 : col2 + 1] for row in grid[row1 : row2 + 1]]
    recolored = [
        [marker_color if value != 0 else 0 for value in row]
        for row in crop
    ]
    output: list[list[int]] = []
    for row in recolored:
        expanded = [value for value in row for _ in range(2)]
        output.extend([expanded[:], expanded[:]])
    return output


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_accepts_every_canonical_input_and_mirrors_output(pair):
    assert GEN.RULE_HASH == "708518128a6f"
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _independent_output(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("texture", "n_shapes"),
    [
        ("unique_min", 2),
        ("unique_min", 4),
        ("two_way_tie", 3),
        ("two_way_tie", 4),
        ("all_tied", 2),
        ("all_tied", 4),
    ],
)
def test_exact_overrides_are_realized_in_every_band(band, texture, n_shapes):
    grid = GEN.generate(
        1701,
        19,
        difficulty=band,
        grid_h=10,
        grid_w=11,
        n_shapes=n_shapes,
        texture=texture,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 10,
        "grid_w": 11,
        "n_shapes": n_shapes,
        "texture": texture,
    }
    scene = _scene(grid)
    assert len(scene["shapes"]) == n_shapes
    assert scene["texture"] == texture


def test_two_way_tie_requires_a_larger_third_shape():
    with pytest.raises(ValueError, match="two_way_tie"):
        GEN.generate(1, 2, n_shapes=2, texture="two_way_tie")


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 9},
        {"grid_h": 19},
        {"grid_w": 10},
        {"grid_w": 19},
        {"n_shapes": 1},
        {"n_shapes": 5},
        {"texture": "plain"},
        {"texture": "not_a_profile"},
        {"grid_h": True},
        {"n_shapes": 2.5},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


@pytest.mark.parametrize("start", range(12))
def test_every_four_example_window_teaches_selection_and_tie_break(start):
    profiles = {
        GEN.schedule_profile(9001, start + offset, "medium")
        for offset in range(GEN.EXAMPLES_NEEDED)
    }
    assert profiles == set(GEN.SCHEDULE_PROFILES)

    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(9001, start + offset, difficulty="medium")
        pairs.append({"input": grid, "output": _independent_output(grid)})
    assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []

    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:-1]), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_valid_diverse_and_semantically_complete(band):
    profiles: set[str] = set()
    inputs: set[str] = set()
    strict = 0
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    canonical_profile_hits = 0
    for index in range(96):
        seed = 5100 + index
        sample_index = index * 7 + 3
        grid = GEN.generate(seed, sample_index, difficulty=band)
        assert grid == GEN.generate(seed, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == _independent_output(grid)
        observed = GEN.observe_overrides(grid)
        profiles.add(observed["texture"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
        strict += GEN.strict_canonical_like(grid) == []
        profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        canonical_profile_hits += profile in CANONICAL_PROFILES
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(witness(grid))
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert strict >= 48
    assert canonical_profile_hits == 96
    assert min(witness_hits.values()) > 0
    assert len(inputs) >= 90


def _isolated_background_cell(grid: list[list[int]]) -> tuple[int, int]:
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if all(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] == 0
                for dr, dc in DIR4
            ):
                return row, col
    raise AssertionError("no isolated background cell")


def test_validator_rejects_multiple_markers_and_single_shape_curricula():
    grid = GEN.generate(77, 3, n_shapes=3, texture="two_way_tie")
    row, col = _isolated_background_cell(grid)
    used = {value for line in grid for value in line}
    grid[row][col] = next(color for color in range(1, 10) if color not in used)
    assert any("singleton" in finding or "marker" in finding for finding in GEN.self_check(grid))

    one_shape = GEN.generate(78, 4, n_shapes=2, texture="unique_min")
    scene = _scene(one_shape)
    erase = scene["shapes"][0]
    for row, col in erase["cells"]:
        one_shape[row][col] = 0
    assert any("shape" in finding for finding in GEN.self_check(one_shape))


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(10)]])
def test_malformed_grid_returns_diagnostics_instead_of_raising(grid):
    assert GEN.self_check(grid)


def test_canonical_shortcut_really_fits_canonical_and_is_refuted_by_schedule():
    shortcut = GEN.CANONICAL_SHORTCUTS["fixed_size_five"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    grid = GEN.generate(991, 0, texture="unique_min")
    assert GEN.SEMANTIC_WITNESSES["fixed_size_five_distractor"](grid)
    assert shortcut(grid) != GEN.rule_mirror(grid)


def test_difficulty_bands_change_pixels_without_changing_the_contract():
    by_band = {
        band: [GEN.generate(8100 + i, i * 5 + 1, difficulty=band) for i in range(24)]
        for band in ("easy", "medium", "hard")
    }
    assert by_band["easy"] != by_band["medium"]
    assert by_band["medium"] != by_band["hard"]
    assert by_band["easy"] != by_band["hard"]
