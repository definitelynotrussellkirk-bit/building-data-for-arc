"""Regression, override, and teaching-contract tests for 9d0a6f959321."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "9d0a6f959321"
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


def components(grid, *, include_background=False):
    """Independent same-color 4-connected component census."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if (not include_background and color == 0) or (r, c) in seen:
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
            sides = set()
            if any(rr == 0 for rr, _ in cells):
                sides.add("top")
            if any(rr == h - 1 for rr, _ in cells):
                sides.add("bottom")
            if any(cc == 0 for _, cc in cells):
                sides.add("left")
            if any(cc == w - 1 for _, cc in cells):
                sides.add("right")
            result.append(
                {"color": color, "cells": frozenset(cells), "sides": frozenset(sides)}
            )
    return result


def oracle(grid):
    out = deepcopy(grid)
    for obj in components(grid):
        if obj["color"] == 7 and obj["sides"]:
            for r, c in obj["cells"]:
                out[r][c] = 3
    return out


def observed(grid):
    objs = components(grid)
    orange = [obj for obj in objs if obj["color"] == 7]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_border_components": sum(bool(obj["sides"]) for obj in orange),
        "n_interior_components": sum(not obj["sides"] for obj in orange),
        "n_distractors": sum(obj["color"] != 7 for obj in objs),
    }


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_rule_mirror_matches(pair):
    assert gen.RULE_HASH == "7af38e7dbf07"
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_advertised_override_is_exact_and_observable(band):
    requested = {
        "grid_h": 7,
        "grid_w": 9,
        "n_border_components": 2,
        "n_interior_components": 2,
        "n_distractors": 2,
    }
    grid = gen.generate(41, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "options",
    [
        {"unknown_axis": 1},
        {"grid_h": 6},
        {"grid_h": 13},
        {"grid_w": 8},
        {"grid_w": 15},
        {"n_border_components": 0},
        {"n_border_components": 3},
        {"n_interior_components": 0},
        {"n_interior_components": 3},
        {"n_distractors": -1},
        {"n_distractors": 3},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"n_border_components": "2"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_diverse_and_counterexample_rich(band):
    shapes = set()
    palette_sizes = set()
    count_profiles = set()
    exact_profile_hits = 0
    strict_hits = 0
    witness_hits = Counter()
    rival_refutations = Counter()

    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in PAIRS
    }

    for index in range(48):
        seed = 10_000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == observed(grid)
        assert gen.rule_mirror(grid) == oracle(grid)
        assert oracle(grid) != grid

        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        exact_profile_hits += profile in canonical_profiles
        strict_hits += not gen.strict_canonical_like(grid)
        shapes.add((len(grid), len(grid[0])))
        palette_sizes.add(profile[2])
        stats = observed(grid)
        count_profiles.add(
            (stats["n_border_components"], stats["n_interior_components"], stats["n_distractors"])
        )

        intended = oracle(grid)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(witness(deepcopy(grid)))
        for name, rival in gen.SEMANTIC_RIVALS.items():
            rival_refutations[name] += rival(deepcopy(grid)) != intended

    assert exact_profile_hits >= 1
    assert strict_hits >= 4
    assert len(shapes) >= 6
    assert {2, 3} <= palette_sizes
    assert len(count_profiles) >= 4
    assert all(count > 0 for count in witness_hits.values()), witness_hits
    assert all(count > 0 for count in rival_refutations.values()), rival_refutations


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_consecutive_three_demo_lessons_are_identifiable(band):
    for start in range(12):
        pairs = []
        for offset in range(4):
            grid = gen.generate(777, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle(grid)})
        demos, query = pairs[:3], pairs[3]
        assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            fits = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
            assert not (fits and rival(deepcopy(query["input"])) != query["output"]), name


def test_self_check_rejects_structure_destroying_mutations():
    for grid in (None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)]):
        assert gen.self_check(grid)

    grid = gen.generate(
        55,
        9,
        grid_h=7,
        grid_w=9,
        n_border_components=1,
        n_interior_components=1,
        n_distractors=1,
    )
    assert gen.self_check(grid) == []

    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    no_interior = deepcopy(grid)
    for obj in components(no_interior):
        if obj["color"] == 7 and not obj["sides"]:
            for r, c in obj["cells"]:
                no_interior[r][c] = 0
    assert gen.self_check(no_interior)

    no_border = deepcopy(grid)
    for obj in components(no_border):
        if obj["color"] == 7 and obj["sides"]:
            for r, c in obj["cells"]:
                no_border[r][c] = 0
    assert gen.self_check(no_border)

    reserved_output_color = deepcopy(grid)
    reserved_output_color[3][3] = 3
    assert gen.self_check(reserved_output_color)


def test_generation_does_not_mutate_global_random_state():
    random.seed(418)
    before = random.getstate()
    gen.generate(77, 12, difficulty="hard")
    assert random.getstate() == before
