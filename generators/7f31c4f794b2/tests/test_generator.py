"""Regression and teaching-contract tests for 7f31c4f794b2."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "7f31c4f794b2"
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


def components(grid):
    """Independent same-color 4-connected component census."""
    if not grid or not grid[0]:
        return []
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
            sides = set()
            if any(rr == 0 for rr, _ in cells):
                sides.add("top")
            if any(rr == h - 1 for rr, _ in cells):
                sides.add("bottom")
            if any(cc == 0 for _, cc in cells):
                sides.add("left")
            if any(cc == w - 1 for _, cc in cells):
                sides.add("right")
            result.append({"color": color, "cells": set(cells), "sides": sides})
    return result


def oracle(grid):
    out = deepcopy(grid)
    for obj in components(grid):
        if obj["sides"]:
            for r, c in obj["cells"]:
                out[r][c] = 7
    return out


def border_color_shortcut(grid):
    h, w = len(grid), len(grid[0])
    colors = {
        grid[r][c]
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r in (0, h - 1) or c in (0, w - 1))
    }
    return [[7 if value in colors else value for value in row] for row in grid]


def observed(grid):
    objs = components(grid)
    border = [obj for obj in objs if obj["sides"]]
    interior = [obj for obj in objs if not obj["sides"]]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_border_components": len(border),
        "n_interior_components": len(interior),
    }


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_python_oracle_matches(pair):
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert oracle(pair["input"]) == pair["output"]


def test_selected_rule_hash_is_pinned():
    assert gen.RULE_HASH == "187a145d27eb"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_advertised_override_is_exact_and_observable(band):
    requested = {
        "grid_h": 8,
        "grid_w": 8,
        "n_border_components": 3,
        "n_interior_components": 2,
    }
    grid = gen.generate(41, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "options",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 7},
        {"grid_w": 15},
        {"n_border_components": 1},
        {"n_border_components": 4},
        {"n_interior_components": 1},
        {"n_interior_components": 4},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"n_border_components": "2"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(options):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_diverse_and_shortcut_resistant(band):
    shapes = set()
    component_counts = set()
    object_sizes = set()
    exact_profile_hits = 0
    for index in range(72):
        seed = 10_000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == observed(grid)
        assert oracle(grid) != grid

        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        component_counts.add(stats["n_border_components"] + stats["n_interior_components"])
        object_sizes.update(len(obj["cells"]) for obj in components(grid))
        exact_profile_hits += (
            (len(grid), len(grid[0])) in {(8, 8), (10, 10)}
            and len({value for row in grid for value in row}) == 5
        )

        border = [obj for obj in components(grid) if obj["sides"]]
        assert any(obj["sides"] <= {"top", "bottom"} for obj in border)
        assert any(obj["sides"] <= {"left", "right"} for obj in border)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), name
        intended = oracle(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(deepcopy(grid)) != intended, name

    assert exact_profile_hits >= 12
    assert len(shapes) >= 8
    assert component_counts == {4, 5, 6}
    assert {3, 4, 5} <= object_sizes


def test_canonical_border_color_shortcut_is_refuted_by_generated_components():
    shortcut = gen.CANONICAL_SHORTCUTS["global_border_colors"]
    assert all(shortcut(deepcopy(pair["input"])) == pair["output"] for pair in PAIRS)
    for index in range(24):
        grid = gen.generate(700 + index, index, difficulty="medium")
        assert shortcut(deepcopy(grid)) == border_color_shortcut(grid)
        assert shortcut(deepcopy(grid)) != oracle(grid)


def test_three_demo_lesson_refutes_every_declared_competitor():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(123, index, difficulty="medium")
        demos.append({"input": grid, "output": oracle(grid)})
    query_grid = gen.generate(123, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": oracle(query_grid)}
    assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


def test_self_check_rejects_malformed_and_structure_destroying_mutations():
    for grid in (None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]):
        assert gen.self_check(grid)

    grid = gen.generate(55, 9, grid_h=8, grid_w=8, n_border_components=2, n_interior_components=2)
    assert gen.self_check(grid) == []

    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    singleton = [[0] * 8 for _ in range(8)]
    singleton[3][3] = 4
    assert gen.self_check(singleton)

    solid_square = [[0] * 8 for _ in range(8)]
    for r in (3, 4):
        for c in (3, 4):
            solid_square[r][c] = 4
    assert gen.self_check(solid_square)

    reserved = deepcopy(grid)
    r, c = next(iter(components(reserved)[0]["cells"]))
    reserved[r][c] = 7
    assert gen.self_check(reserved)


def test_generation_does_not_mutate_global_random_state():
    random.seed(418)
    before = random.getstate()
    gen.generate(77, 12, difficulty="hard")
    assert random.getstate() == before


def test_workspace_component_contract_probe_covers_cyclic_lessons(tmp_path):
    probe_path = TASK_HOME / "workspace" / "component_contract_probe.py"
    assert probe_path.exists(), "workspace probe has not been implemented"
    spec = importlib.util.spec_from_file_location("component_contract_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(
        gen,
        draws_per_band=8,
        schedule_period=12,
        seed=20261005,
    )
    assert report["status"] == "pass"
    assert report["summary"]["draws"] == 24
    assert report["summary"]["cyclic_lessons"] == 36
    assert report["summary"]["ambiguous_lessons"] == 0
    assert set(report["rivals"]) == set(gen.LESSON_COMPETITORS)
    assert all(count == 24 for count in report["rival_refutations"].values())

    out = tmp_path / "probe.json"
    probe.write_report(report, out)
    assert out.exists()
    assert out.read_text().endswith("\n")
