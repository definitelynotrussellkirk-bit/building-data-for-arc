"""Focused canonical regressions for c6a422753abe."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "c6a422753abe"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def signature(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_every_canonical_pair_is_owned_and_mirrored_exactly():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generated_census_uses_one_separator_axis_two_colors_and_both_sides():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(20261024, i, difficulty=band) for i in range(36)]
        assert all(GEN.self_check(grid, difficulty=band) == [] for grid in grids)
        scenes = [GEN._analyze_grid(grid) for grid in grids]
        assert {scene["axis"] for scene in scenes} == {"row", "col"}
        assert {scene["side"] for scene in scenes} == {"before", "after"}
        assert all(len(scene["colors"]) == 2 for scene in scenes)
        assert len({signature(grid) for grid in grids}) >= 34
        for start in range(0, 28, 4):
            demos = [{"input": g, "output": GEN.rule_mirror(g)} for g in grids[start : start + 3]]
            query_grid = grids[start + 3]
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_exact_overrides_and_substantive_30_by_30_case():
    grid = GEN.generate(
        17,
        5,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        separator_axis="col",
        source_side="before",
        separator_index=15,
        n_cells=18,
        palette_pair="2,8",
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    scene = GEN._analyze_grid(grid)
    assert scene["axis"] == "col" and scene["side"] == "before"
    assert scene["separator"] == 15 and set(scene["colors"]) == {2, 8}
    assert len(scene["source_cells"]) == 18
    output = GEN.rule_mirror(grid)
    occupied = {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value not in (0, 1)}
    assert len(occupied) == 36
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 20
    assert GEN.observe_overrides(grid) == {
        "grid_h": 30,
        "grid_w": 30,
        "separator_axis": "col",
        "separator_index": 15,
        "source_side": "before",
        "n_cells": 18,
        "palette_pair": "2,8",
    }


@pytest.mark.parametrize("mutation", [
    "remove_separator", "add_second_separator", "one_color", "shape_both_sides", "bad_cell"
])
def test_self_check_rejects_targeted_impostors(mutation):
    grid = GEN.generate(44, 3, separator_axis="row", source_side="before")
    broken = deepcopy(grid)
    scene = GEN._analyze_grid(grid)
    if mutation == "remove_separator":
        r = scene["separator"]
        broken[r][0] = 0
    elif mutation == "add_second_separator":
        r = 0 if scene["separator"] != 0 else len(grid) - 1
        broken[r] = [1] * len(grid[0])
    elif mutation == "one_color":
        a, b = scene["colors"]
        broken = [[a if value == b else value for value in row] for row in broken]
    elif mutation == "shape_both_sides":
        r, c = scene["source_cells"][0]
        rr, cc = GEN._reflect(scene, r, c)
        broken[rr][cc] = scene["colors"][0]
    else:
        broken[0][0] = True
    assert GEN.self_check(broken)


def test_invalid_controls_fail_explicitly():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, separator_axis="diag")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, source_side="left")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, palette_pair="2,2")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, n_cells=True)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, mystery_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="impossible")
