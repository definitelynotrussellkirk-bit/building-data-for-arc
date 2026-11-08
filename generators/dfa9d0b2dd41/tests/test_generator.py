"""Focused regressions for the rectangle-sort generator repair.

The Racket source is the label authority.  These tests independently reproduce
its observable sort-and-pack behavior and the strongest canonical-fitting rival:
sort by bounding-box area rather than occupied-cell count.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "dfa9d0b2dd41"
TASK_DIR = Path(__file__).resolve().parents[1]
for candidate in (TASK_DIR, *TASK_DIR.parents):
    if (candidate / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(candidate / "shared/runtime"))
        break
    if (candidate / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:  # pragma: no cover - a broken test snapshot should fail loudly
    raise RuntimeError("no independent puzzle_generators runtime found")

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {(10, 12, 4), (11, 13, 4), (9, 14, 4), (12, 15, 5)}


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _components(grid):
    """Independent same-color 4-connected components in scan order."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            found.append(cells)
    return found


def _item(grid, cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    crop = [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]
    return {
        "cells": cells,
        "r1": r1,
        "c1": c1,
        "height": r2 - r1 + 1,
        "width": c2 - c1 + 1,
        "crop": crop,
    }


def _pack(grid, *, bbox_area=False):
    items = [_item(grid, cells) for cells in _components(grid)]
    primary = (
        (lambda item: item["height"] * item["width"])
        if bbox_area
        else (lambda item: len(item["cells"]))
    )
    items.sort(key=lambda item: (primary(item), item["r1"], item["c1"]))
    out_h = max(item["height"] for item in items)
    out_w = sum(item["width"] for item in items) + len(items) - 1
    out = [[0 for _ in range(out_w)] for _ in range(out_h)]
    left = 0
    for item in items:
        for row, values in enumerate(item["crop"]):
            for col, value in enumerate(values):
                if value != 0:
                    out[row][left + col] = value
        left += item["width"] + 1
    return out


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_canonical_acceptance_and_independent_outputs():
    assert gen.RULE_HASH == "76c3cefee423"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _pack(pair["input"]) == pair["output"]
        assert _pack(pair["input"], bbox_area=True) == pair["output"]
        assert pair["input"] == original


def test_retained_bbox_area_counterexample_matches_both_rules():
    path = TASK_DIR / "counterexamples" / "bbox_area_sort.json"
    case = json.loads(path.read_text())
    assert case["task_id"] == TASK_ID
    assert case["generator_sha256"] == case["checked_generator_sha256"]
    assert gen.self_check(case["input"]) == []
    assert _pack(case["input"]) == case["authority_output"]
    assert _pack(case["input"], bbox_area=True) == case["rival_output"]
    assert case["authority_output"] != case["rival_output"]


def test_bbox_area_shortcut_has_an_ordinary_generated_counterexample():
    assert set(gen.CANONICAL_SHORTCUTS) == {"bbox_area_sort"}
    rival = gen.CANONICAL_SHORTCUTS["bbox_area_sort"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())

    witness = gen.generate(31415, 1, grid_h=8, grid_w=10, n_objs=4)
    assert gen.self_check(witness) == []
    assert gen.SEMANTIC_WITNESSES["cell_count_not_bbox_area"](witness)
    assert rival(witness) == _pack(witness, bbox_area=True)
    assert rival(witness) != _pack(witness)


@pytest.mark.parametrize("band", BANDS)
def test_exact_overrides_are_visible_in_every_band(band):
    requested = {"grid_h": 8, "grid_w": 10, "n_objs": 4}
    grid = gen.generate(1701, 1, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == requested
    assert (len(grid), len(grid[0]), len(_components(grid))) == (8, 10, 4)


@pytest.mark.parametrize(
    "sample_index,difficulty,overrides",
    [
        (0, None, {"typo": 1}),
        (0, None, {"grid_h": 7}),
        (0, None, {"grid_h": 15}),
        (0, None, {"grid_w": 9}),
        (0, None, {"grid_w": 19}),
        (0, None, {"n_objs": 1}),
        (0, None, {"n_objs": 5}),
        (0, None, {"n_objs": 2.5}),
        (0, None, {"grid_h": True}),
        (0, None, {"grid_w": "12"}),
        (-1, None, {}),
        (True, None, {}),
        (0, "expert", {}),
    ],
)
def test_invalid_calls_are_rejected(sample_index, difficulty, overrides):
    with pytest.raises(ValueError):
        gen.generate(0, sample_index, difficulty=difficulty, **overrides)


@pytest.mark.parametrize("band", BANDS)
def test_three_draw_schedule_contains_canonical_and_two_counterexamples(band):
    grids = [gen.generate(81, index, difficulty=band) for index in range(3)]
    assert gen.schedule_profile(81, 0, band) == "solid_rectangles"
    assert [gen.schedule_profile(81, index, band) for index in (1, 2)] == [
        "bbox_area_witness",
        "bbox_area_witness",
    ]
    assert gen.strict_canonical_like(grids[0]) == []
    assert not gen.SEMANTIC_WITNESSES["cell_count_not_bbox_area"](grids[0])
    for grid in grids[1:]:
        assert gen.self_check(grid, difficulty=band) == []
        assert gen.SEMANTIC_WITNESSES["cell_count_not_bbox_area"](grid)
        assert _pack(grid) != _pack(grid, bbox_area=True)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_defaults_are_deterministic_valid_and_anchor_canonical_profiles(band):
    random.seed(9917)
    state = random.getstate()
    grids = [gen.generate(4000 + i, i, difficulty=band) for i in range(36)]
    assert random.getstate() == state
    assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)
    assert all(grid == gen.generate(4000 + i, i, difficulty=band) for i, grid in enumerate(grids))
    assert {_profile(grid) for grid in grids[:20]} & CANONICAL_PROFILES
    assert {len(_components(grid)) for grid in grids} >= {3, 4}
    assert sum(gen.strict_canonical_like(grid) == [] for grid in grids) >= 12
    assert sum(gen.SEMANTIC_WITNESSES["cell_count_not_bbox_area"](grid) for grid in grids) >= 24


def test_every_query_rotation_is_identifiable_from_three_demonstrations():
    pairs = [
        {"input": grid, "output": _pack(grid)}
        for grid in [gen.generate(777, index) for index in range(4)]
    ]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_default_component_scale_reaches_the_canonical_large_object_band():
    maxima = {
        max(len(cells) for cells in _components(gen.generate(9000 + index, index, difficulty=band)))
        for band in ("easy", "medium", "hard")
        for index in range(12)
    }
    # Canonical examples have largest objects of 6, 8, 9, and 10 cells.  A
    # generator capped at six cells teaches a visibly smaller task family.
    assert maxima & {8, 9, 10}
