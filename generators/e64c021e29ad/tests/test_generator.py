"""Source-bound regressions for the arrow-driven sweep generator.

The geometry oracle and shortcut rules below are intentionally independent of
production helpers.  The selected Racket authority remains the label oracle in
battery/census runs; these tests pin the generator contract and catch the
source-bound marker-side shortcut found in the baseline.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "e64c021e29ad"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
TRAIN = PAIRS[:2]

DIRS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
COLOR_DIRECTION = {5: 4, 6: 1, 7: 3, 8: 2, 9: 1}


def _components(grid):
    """Independent row-major 4-connected components for object colors 5..9."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color < 5 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in DIRS.values():
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def _record(grid, component):
    color, cells = component
    h, w = len(grid), len(grid[0])
    markers = set()
    for r, c in cells:
        for dr, dc in DIRS.values():
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] in DIRS:
                markers.add((nr, nc))
    assert len(markers) == 1, (color, cells, markers)
    marker = next(iter(markers))
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    mr, mc = marker
    if mr < min_r:
        marker_side = 1
    elif mc > max_c:
        marker_side = 2
    elif mr > max_r:
        marker_side = 3
    elif mc < min_c:
        marker_side = 4
    else:
        # Generated markers are outside the bounding box.  This fallback keeps
        # the independent helper useful on a legal concavity attachment.
        neighbors = []
        for code, (dr, dc) in DIRS.items():
            if (mr - dr, mc - dc) in cells:
                neighbors.append(code)
        assert neighbors
        marker_side = neighbors[0]
    return {
        "color": color,
        "cells": cells,
        "marker": marker,
        "code": grid[mr][mc],
        "marker_side": marker_side,
    }


def records(grid):
    return [_record(grid, component) for component in _components(grid)]


def sweep(grid, direction_for, *, bounding_box=False, skip_color=None):
    """Independent rule family used for intended and rival predictions."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for rec in records(grid):
        if rec["color"] == skip_color:
            continue
        cells = set(rec["cells"])
        if bounding_box:
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            cells = {
                (r, c)
                for r in range(min(rs), max(rs) + 1)
                for c in range(min(cs), max(cs) + 1)
            }
        code = direction_for(rec)
        dr, dc = DIRS[code]
        for r, c in sorted(cells):
            rr, cc = r, c
            while 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = rec["color"]
                rr += dr
                cc += dc
    return out


def intended(grid):
    return sweep(grid, lambda rec: rec["code"])


def color_direction_rival(grid):
    return sweep(grid, lambda rec: COLOR_DIRECTION[rec["color"]])


def marker_side_rival(grid):
    return sweep(grid, lambda rec: rec["marker_side"])


def bounding_box_rival(grid):
    return sweep(grid, lambda rec: rec["code"], bounding_box=True)


def palette_profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    assert gen.RULE_HASH == "69a4bb5ee756"
    assert len(PAIRS) == 3
    for pair in PAIRS:
        assert gen.self_check(pair["input"]) == []
        assert intended(pair["input"]) == pair["output"]
        assert gen._python_apply(pair["input"]) == pair["output"]
        assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 9, "grid_w": 10, "n_objects": 3},
        {"grid_h": 16, "grid_w": 20, "n_objects": 1},
        {"grid_h": 9, "grid_w": 20, "n_objects": 2},
        {"grid_h": 16, "grid_w": 10, "n_objects": 3},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, overrides):
    grid = gen.generate(6101, 17, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert (len(grid), len(grid[0]), len(records(grid))) == (
        overrides["grid_h"],
        overrides["grid_w"],
        overrides["n_objects"],
    )


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 1},
        {"grid_h": True},
        {"grid_h": 9.0},
        {"grid_h": "9"},
        {"grid_w": False},
        {"grid_w": 10.5},
        {"n_objects": True},
        {"n_objects": 2.0},
        {"n_objects": "2"},
        {"grid_h": 8},
        {"grid_w": 21},
        {"n_objects": 0},
        {"n_objects": 4},
    ],
)
def test_invalid_or_unknown_overrides_fail_explicitly(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("bad_difficulty", ["expert", 0.5, True])
def test_unknown_difficulty_fails_explicitly(bad_difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=bad_difficulty)


def test_marker_attachment_is_not_a_direction_shortcut():
    combinations = set()
    mismatches = 0
    for index in range(64):
        grid = gen.generate(7200, index, difficulty="medium")
        assert gen.self_check(grid) == []
        for rec in records(grid):
            combinations.add((rec["code"], rec["marker_side"]))
            mismatches += rec["code"] != rec["marker_side"]
        assert intended(grid) != marker_side_rival(grid)
    assert combinations == {(code, side) for code in DIRS for side in DIRS}
    assert mismatches > 0


def test_object_color_direction_is_a_real_canonical_shortcut_and_is_refuted():
    # Canonical colors are perfectly confounded with directions: 5=left,
    # 6=up, 7=down, 8=right.  The repaired generator must break that cue.
    assert all(color_direction_rival(pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(20):
        grid = gen.generate(7300, index, difficulty="medium")
        assert intended(grid) != color_direction_rival(grid)
        assert gen.SEMANTIC_WITNESSES["color_does_not_encode_direction"](grid)


def test_bounding_box_sweep_fits_training_demos_but_generated_notches_refute_it():
    assert all(bounding_box_rival(pair["input"]) == pair["output"] for pair in TRAIN)
    assert bounding_box_rival(PAIRS[2]["input"]) != PAIRS[2]["output"]
    for index in range(20):
        grid = gen.generate(7400, index, difficulty="medium")
        assert intended(grid) != bounding_box_rival(grid)
        assert gen.SEMANTIC_WITNESSES["cellwise_not_bounding_box"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_canonical_profile_support_and_default_witnesses(band):
    canonical_profiles = {(9, 10, 5), (10, 11, 5), (12, 12, 7)}
    grids = [gen.generate(7500, index, difficulty=band) for index in range(20)]
    assert sum(palette_profile(grid) in canonical_profiles for grid in grids) >= 5
    for grid in grids:
        assert gen.self_check(grid) == []
        assert len(records(grid)) >= 2
        assert any(rec["color"] == 9 for rec in records(grid))
        assert gen._python_apply(grid) == intended(grid)
        for rival in gen.LESSON_COMPETITORS.values():
            assert rival(grid) != intended(grid)


def test_every_cyclic_lesson_start_and_query_rotation_refutes_declared_rivals():
    # Five consecutive pairs: four demonstrations plus one query.  Every
    # single pair is a witness, so every held-out rotation remains identifiable.
    for band in ("easy", "medium", "hard"):
        for start in range(48):
            pairs = []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(7600, index, difficulty=band)
                pairs.append({"input": grid, "output": intended(grid)})
            for query_index in range(len(pairs)):
                demos = [deepcopy(pair) for i, pair in enumerate(pairs) if i != query_index]
                query = deepcopy(pairs[query_index])
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(9)],
        [[1.5] * 10 for _ in range(9)],
    ],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_stray_shared_and_missing_markers():
    grid = gen.generate(7700, 3, difficulty="medium")
    assert gen.self_check(grid) == []

    stray = deepcopy(grid)
    empty = next(
        (r, c)
        for r, row in enumerate(stray)
        for c, value in enumerate(row)
        if value == 0
        and all(
            not (0 <= r + dr < len(stray) and 0 <= c + dc < len(stray[0]))
            or stray[r + dr][c + dc] < 5
            for dr, dc in DIRS.values()
        )
    )
    stray[empty[0]][empty[1]] = 1
    assert gen.self_check(stray)

    missing = deepcopy(grid)
    marker = records(missing)[0]["marker"]
    missing[marker[0]][marker[1]] = 0
    assert gen.self_check(missing)


def test_generation_is_deterministic_and_does_not_mutate_outputs():
    for band in (None, "easy", "medium", "hard"):
        for index in range(20):
            first = gen.generate(7800 + index, index, difficulty=band)
            before = deepcopy(first)
            output = gen._python_apply(first)
            assert first == before
            assert output == intended(first)
            assert first == gen.generate(7800 + index, index, difficulty=band)


def test_single_object_override_refutes_marker_side_shortcut():
    grid = gen.generate(2, 37, difficulty="easy", n_objects=1)
    assert intended(grid) != marker_side_rival(grid)
