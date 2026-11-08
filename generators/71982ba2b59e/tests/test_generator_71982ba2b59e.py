"""Focused semantic regressions for ARC generator 71982ba2b59e."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import shutil

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import set_ctx_observer
from scripts.rule_smoke import purity_body, rule_application


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "71982ba2b59e"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/529ce7614691"
    / "hard_40_shape_color_relation_matrix__71982ba2b59e.json"
)


def canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def normalized_shape(cells):
    cells = tuple(cells)
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def rotate(shape):
    bottom = max(row for row, _col in shape)
    return normalized_shape((col, bottom - row) for row, col in shape)


def rotations(shape):
    result = set()
    current = normalized_shape(shape)
    for _ in range(4):
        result.add(current)
        current = rotate(current)
    return result


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (cr + dr, cc + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(cells)
    result.sort(
        key=lambda cells: (
            min(row for row, _col in cells),
            min(col for _row, col in cells),
        )
    )
    return result


def independent_analysis(grid):
    records = []
    for cells in components(grid):
        colors = {grid[row][col] for row, col in cells}
        records.append(
            {
                "cells": cells,
                "color": next(iter(colors)) if len(colors) == 1 else None,
                "shape": normalized_shape(cells),
            }
        )
    counts = Counter()
    output = []
    for i, left in enumerate(records):
        row = []
        for j, right in enumerate(records):
            if i == j:
                counts["diag"] += 1
                row.append(left["color"])
                continue
            shape_match = right["shape"] in rotations(left["shape"])
            color_match = left["color"] == right["color"]
            if shape_match:
                counts["both" if color_match else "shape_only"] += 1
                row.append(8)
            elif color_match:
                counts["color_only"] += 1
                row.append(6)
            else:
                counts["neither"] += 1
                row.append(0)
        output.append(row)
    return records, counts, output


def core_grid(seed=73001):
    return MODULE.generate(
        seed,
        seed * 13 + 7,
        difficulty="easy",
        n_components=3,
        n_colors=2,
        relation_profile="core",
    )


def shape_only_pair(grid):
    records, _counts, _output = independent_analysis(grid)
    for i, left in enumerate(records):
        for j, right in enumerate(records):
            if i >= j:
                continue
            if (
                right["shape"] in rotations(left["shape"])
                and left["color"] != right["color"]
            ):
                return left, right
    raise AssertionError("missing shape-only pair")


def color_only_pair(grid):
    records, _counts, _output = independent_analysis(grid)
    for i, left in enumerate(records):
        for j, right in enumerate(records):
            if i >= j:
                continue
            if (
                left["color"] == right["color"]
                and right["shape"] not in rotations(left["shape"])
            ):
                return left, right
    raise AssertionError("missing color-only pair")


def recolor(grid, cells, color):
    result = copy.deepcopy(grid)
    for row, col in cells:
        result[row][col] = color
    return result


def remove_component(grid, cells):
    return recolor(grid, cells, 0)


def bridge_components(grid, left, right):
    result = copy.deepcopy(grid)
    start = min(left["cells"])
    end = min(right["cells"])
    row, col = start
    end_row, end_col = end
    color = left["color"]
    while col != end_col:
        col += 1 if end_col > col else -1
        result[row][col] = color
    while row != end_row:
        row += 1 if end_row > row else -1
        result[row][col] = color
    return result


def test_authorities_and_rule_hash_are_synchronized():
    row = canonical_row()
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]["target_code"]
    assert row["program_solution"] == target
    assert MODULE.RULE_HASH == normalized_hash(target)
    assert MODULE.RULE_HASH == "65d92f91150b"
    assert base["racket_target"]["raw_code"] != target


def test_all_five_canonical_pairs_are_accepted_and_exact():
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        records, counts, expected = independent_analysis(source)
        assert len(records) == 4
        assert counts["shape_only"] == 2
        assert counts["color_only"] == 2
        assert counts["neither"] == 8
        assert MODULE.self_check(source) == []
        assert MODULE.observe_overrides(source) == {
            "n_components": 4,
            "n_colors": 3,
            "relation_profile": "core",
        }
        assert expected == pair["output"]
        assert MODULE.semantic_output(source) == pair["output"]
        assert source == snapshot


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 9),
        ("grid_h", 18),
        ("grid_w", 11),
        ("grid_w", 22),
        ("n_components", 3),
        ("n_components", 6),
        ("n_colors", 2),
        ("n_colors", 4),
        ("relation_profile", "core"),
        ("relation_profile", "precedence"),
    ],
)
def test_every_declared_axis_boundary_is_realizable_and_observable(band, axis, value):
    override = {axis: value}
    grid = MODULE.generate(811, 977, difficulty=band, **override)
    assert MODULE.self_check(
        grid,
        difficulty=band,
        meta={"overrides": override},
    ) == []
    observed = MODULE.observe_overrides(grid)
    if axis == "grid_h":
        assert len(grid) == value
    elif axis == "grid_w":
        assert len(grid[0]) == value
    else:
        assert observed[axis] == value


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_tight_and_maximal_compatible_override_combinations(band):
    cases = (
        {
            "grid_h": 9,
            "grid_w": 11,
            "n_components": 6,
            "n_colors": 4,
            "relation_profile": "precedence",
        },
        {
            "grid_h": 18,
            "grid_w": 22,
            "n_components": 5,
            "n_colors": 4,
            "relation_profile": "core",
        },
    )
    for overrides in cases:
        grid = MODULE.generate(1321, 1717, difficulty=band, **overrides)
        assert len(grid) == overrides["grid_h"]
        assert len(grid[0]) == overrides["grid_w"]
        assert MODULE.observe_overrides(grid) == {
            key: overrides[key]
            for key in ("n_components", "n_colors", "relation_profile")
        }
        assert MODULE.self_check(
            grid,
            difficulty=band,
            meta={"overrides": overrides},
        ) == []


def test_invalid_or_incompatible_requests_fail_loudly():
    invalid = (
        {"n_components": 2},
        {"n_colors": 5},
        {"relation_profile": "unknown"},
        {"grid_h": 8},
        {"grid_w": 23},
        {"n_components": 3, "relation_profile": "precedence"},
        {"n_components": 4, "n_colors": 4},
        {"n_components": 5, "n_colors": 4, "relation_profile": "precedence"},
        {"not_an_axis": 1},
    )
    for overrides in invalid:
        with pytest.raises((ValueError, KeyError)):
            MODULE.generate(19, 23, difficulty="medium", **overrides)
    with pytest.raises(ValueError):
        MODULE.generate(19, 23, difficulty="mystery")


def test_normal_draws_preserve_keyed_semantic_requests_and_all_core_branches():
    profiles = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(80):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = MODULE.generate(
                    90_000 + band_index * 10_000 + index,
                    50_000 + index * 31,
                    difficulty=band,
                )
            finally:
                set_ctx_observer(None)
            assert MODULE.self_check(grid) == []
            records, counts, expected = independent_analysis(grid)
            assert expected == MODULE.semantic_output(grid)
            assert counts["shape_only"] > 0
            assert counts["color_only"] > 0
            assert counts["neither"] > 0
            observed = {
                "grid_h": len(grid),
                "grid_w": len(grid[0]),
                **MODULE.observe_overrides(grid),
            }
            assert captured
            for axis, requested in captured[-1]._drawn.items():
                if axis in observed:
                    assert observed[axis] == requested
            profiles.add(observed["relation_profile"])
            assert len(records) == observed["n_components"]
    assert profiles == {"core", "precedence"}


def test_replay_is_deterministic_fresh_and_global_rng_neutral():
    args = (778899, 112233)
    kwargs = {
        "difficulty": "hard",
        "n_components": 6,
        "n_colors": 4,
        "relation_profile": "precedence",
    }
    random.seed(20260723)
    before = random.getstate()
    first = MODULE.generate(*args, **kwargs)
    after = random.getstate()
    second = MODULE.generate(*args, **kwargs)
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_targeted_impostors_are_rejected_and_novel_feature_is_absent_elsewhere():
    grid = core_grid()
    records, _counts, _output = independent_analysis(grid)
    left_shape, right_shape = shape_only_pair(grid)
    left_color, right_color = color_only_pair(grid)

    removed = remove_component(grid, records[0]["cells"])

    # Recolor the shape-only mate to the anchor color: the only shape match is
    # now same-color, so the required shape-only witness disappears.
    no_shape_only = recolor(grid, right_shape["cells"], left_shape["color"])

    # Replace one member of the only color-only pair with a wholly novel color.
    # The replacement color is absent from every remaining scene part.
    used = {record["color"] for record in records}
    novel = next(color for color in range(1, 10) if color not in used)
    no_color_only = recolor(grid, right_color["cells"], novel)
    remaining_colors = {
        grid[row][col]
        for record in records
        if record is not right_color
        for row, col in record["cells"]
    }
    assert novel not in remaining_colors

    bridged = bridge_components(grid, left_shape, right_shape)

    for name, impostor in {
        "component_removed": removed,
        "shape_only_eliminated": no_shape_only,
        "color_only_eliminated_by_novel_feature": no_color_only,
        "components_bridged": bridged,
    }.items():
        errors = MODULE.self_check(impostor)
        assert errors, name

    assert independent_analysis(no_shape_only)[1]["shape_only"] == 0
    assert independent_analysis(no_color_only)[1]["color_only"] == 0


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_shape_matching_is_rotation_only_not_reflection():
    # S and its mirror Z are not equivalent under rotation.  This executable
    # near-miss falsifies the plausible reflection-inclusive interpretation.
    grid = [[0 for _ in range(12)] for _ in range(7)]
    for row, col in ((0, 0), (0, 1), (1, 1), (1, 2)):
        grid[1 + row][1 + col] = 2
    for row, col in ((0, 1), (0, 2), (1, 0), (1, 1)):
        grid[4 + row][7 + col] = 3
    _records, counts, expected = independent_analysis(grid)
    assert counts["shape_only"] == 0
    assert counts["neither"] == 2
    assert expected == [[2, 0], [0, 3]]

    source = canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=None)
    try:
        assert bridge.eval_text(rule_application(source, grid)) == expected
    finally:
        bridge.shutdown()


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_is_exact_pure_atomic_and_executes_rejected_recombination():
    row = canonical_row()
    source = row["program_solution"]
    pairs = row["train"] + row["test"]
    generated = [
        MODULE.generate(
            600_000 + index,
            700_000 + index * 17,
            difficulty=("easy", "medium", "hard")[index % 3],
        )
        for index in range(12)
    ]
    bridge = RacketBridge(max_calls_before_restart=None)
    try:
        for grid, expected in [
            *((pair["input"], pair["output"]) for pair in pairs),
            *((grid, independent_analysis(grid)[2]) for grid in generated),
        ]:
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == expected
            assert grid == snapshot

        probe = bridge.eval_text(
            purity_body(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe == [pairs[0]["output"], pairs[0]["output"], pairs[0]["input"]]

        malformed = core_grid(73009)
        _left, right = color_only_pair(malformed)
        used = {record["color"] for record in independent_analysis(malformed)[0]}
        novel = next(color for color in range(1, 10) if color not in used)
        malformed = recolor(malformed, right["cells"], novel)
        assert MODULE.self_check(malformed)
        oracle_output = bridge.eval_text(rule_application(source, malformed))
        assert oracle_output == independent_analysis(malformed)[2]
    finally:
        bridge.shutdown()
