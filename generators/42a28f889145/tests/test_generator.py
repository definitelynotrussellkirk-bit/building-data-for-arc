"""Portable regression and teaching-contract tests for 42a28f889145."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "42a28f889145"
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
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _components(grid):
    """Independent same-color 4-connected component extraction."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": frozenset(cells)})
    return sorted(result, key=lambda obj: min(c for _, c in obj["cells"]))


def _oracle(grid):
    objects = _components(grid)
    if len(objects) != 2:
        raise ValueError("oracle requires exactly two objects")
    out = deepcopy(grid)
    for (r, c) in objects[0]["cells"]:
        out[r][c] = objects[1]["color"]
    for (r, c) in objects[1]["cells"]:
        out[r][c] = objects[0]["color"]
    return out


def _left_color_is_greater(grid):
    objects = _components(grid)
    return objects[0]["color"] > objects[1]["color"]


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_oracle_matches(pair):
    assert gen.RULE_HASH == "57cc84264d9e"
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_advertised_override_is_exact_and_observable(band):
    requested = {
        "grid_h": 7,
        "grid_w": 9,
        "shape_pair": 35,
        "color_pair": 35,
    }
    grid = gen.generate(41, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1, -1), {}),
        ((1, 0), {"difficulty": "expert"}),
        ((1, 0), {"unknown_axis": 1}),
        ((1, 0), {"grid_h": 6}),
        ((1, 0), {"grid_h": 13}),
        ((1, 0), {"grid_w": 8}),
        ((1, 0), {"grid_w": 17}),
        ((1, 0), {"shape_pair": -1}),
        ((1, 0), {"shape_pair": 36}),
        ((1, 0), {"color_pair": -1}),
        ((1, 0), {"color_pair": 36}),
        ((1, 0), {"grid_h": True}),
        ((1, 0), {"grid_w": 9.0}),
        ((1, 0), {"shape_pair": "3"}),
    ],
)
def test_invalid_calls_and_overrides_fail_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(*args, **kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_canonical_rich_and_order_balanced(band):
    profiles = []
    observed = []
    grids = []
    for index in range(24):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert grid == gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        facts = gen.observe_overrides(grid)
        assert set(facts) == {"grid_h", "grid_w", "shape_pair", "color_pair"}
        profiles.append((len(grid), len(grid[0]), len({v for row in grid for v in row if v})))
        observed.append((facts["shape_pair"], facts["color_pair"]))
        grids.append(grid)

    exact = sum(h == 7 and w in (9, 10) and colors == 2 for h, w, colors in profiles)
    assert exact >= 8
    assert len(set(observed)) >= 12
    for start in range(0, 24, 4):
        assert {_left_color_is_greater(grid) for grid in grids[start : start + 4]} == {False, True}


def test_boundary_override_combinations_are_constructive():
    for grid_h in (7, 12):
        for grid_w in (9, 16):
            for shape_pair in (0, 35):
                for color_pair in (0, 35):
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "shape_pair": shape_pair,
                        "color_pair": color_pair,
                    }
                    grid = gen.generate(88, 5, difficulty="hard", **requested)
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested


def test_declared_canonical_shortcut_fits_canonicals_and_is_refuted_by_generation():
    rival = gen.CANONICAL_SHORTCUTS["sort_colors_descending"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)

    witness = gen.generate(9, 1, grid_h=7, grid_w=9, shape_pair=0, color_pair=0)
    assert _left_color_is_greater(witness)
    assert gen.SEMANTIC_WITNESSES["left_color_greater"](witness)
    assert rival(witness) != _oracle(witness)


def test_every_four_pair_lesson_and_rotation_refutes_the_shortcut():
    pairs = []
    for index in range(4):
        grid = gen.generate(123, index, difficulty="medium")
        pairs.append({"input": grid, "output": _oracle(grid)})

    assert {_left_color_is_greater(pair["input"]) for pair in pairs} == {False, True}
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []

    one_sided = [pair for pair in pairs if not _left_color_is_greater(pair["input"])]
    assert gen.lesson_identifiable(one_sided, pairs[1])


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)]])
def test_malformed_grids_are_rejected_without_crashing(grid):
    assert gen.self_check(grid)
