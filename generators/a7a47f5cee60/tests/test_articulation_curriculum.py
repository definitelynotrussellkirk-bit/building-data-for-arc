"""Task-local regression contract for the component-articulation curriculum.

The graph oracle in this file is intentionally independent of generator.py so
these tests catch a return to pixel-cut-vertex logic.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(
    p for p in HOME.parents
    if (p / "shared/runtime").is_dir() or (p / "arc_repl").is_dir()
)
if (ROOT / "shared/runtime").is_dir():
    sys.path.insert(0, str(ROOT / "shared/runtime"))
else:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("articulation_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    path = ROOT / (
        "shared/data/canonical/puzzles.jsonl"
        if (ROOT / "shared").is_dir()
        else "data/canonical/puzzles.jsonl"
    )
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    task = next(row for row in rows if row.get("task_id") == gen.TASK_ID)
    test = task["test"] if isinstance(task["test"], list) else [task["test"]]
    return list(task["train"]) + test


def objects(grid):
    """Independent monochromatic four-connected component extraction."""
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        cells, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in MOVES:
                point = (r + dr, c + dc)
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    cells.add(point)
                    queue.append(point)
        result.append({"color": color, "cells": frozenset(cells)})
    return result


def graph(grid):
    objs = objects(grid)
    owner = {cell: i for i, obj in enumerate(objs) for cell in obj["cells"]}
    edges = [set() for _ in objs]
    for cell, i in owner.items():
        r, c = cell
        for dr, dc in MOVES:
            j = owner.get((r + dr, c + dc))
            if j is not None and j != i:
                edges[i].add(j)
                edges[j].add(i)
    return objs, edges


def component_count(edges, skip=None):
    remaining = set(range(len(edges)))
    if skip is not None:
        remaining.discard(skip)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            i = stack.pop()
            for j in edges[i]:
                if j in remaining:
                    remaining.remove(j)
                    stack.append(j)
    return count


def articulation_indices(grid):
    _, edges = graph(grid)
    base = component_count(edges)
    return [i for i in range(len(edges)) if component_count(edges, i) > base]


def oracle_output(grid):
    objs, _ = graph(grid)
    out = [[0 for _ in row] for row in grid]
    for i in articulation_indices(grid):
        for r, c in objs[i]["cells"]:
            out[r][c] = 8
    return out


def largest_graph_component_size(edges):
    remaining = set(range(len(edges)))
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            size += 1
            i = stack.pop()
            for j in edges[i]:
                if j in remaining:
                    remaining.remove(j)
                    stack.append(j)
        sizes.append(size)
    return max(sizes, default=0)


def test_rule_hash_and_all_canonical_examples_match_an_independent_oracle():
    assert gen.RULE_HASH == "2c1f4bbab8e6"
    for pair in canonical_pairs():
        assert oracle_output(pair["input"]) == pair["output"]
        assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_draws_are_deterministic_component_graph_instances(difficulty):
    for seed in range(18):
        index = seed % 9
        grid = gen.generate(seed, index, difficulty=difficulty)
        assert grid == gen.generate(seed, index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        objs, edges = graph(grid)
        arts = articulation_indices(grid)
        assert len(arts) == 1
        assert len(objs[arts[0]]["cells"]) >= 2
        assert largest_graph_component_size(edges) < len(objs), "need a disconnected distractor"
        assert len({obj["color"] for obj in objs}) == len(objs)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(9, 11), (9, 22), (18, 11), (18, 22)])
def test_dimension_overrides_work_at_declared_corners(difficulty, shape):
    h, w = shape
    grid = gen.generate(7, 2, difficulty=difficulty, grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == shape
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("name", ["grid_h", "grid_w"])
@pytest.mark.parametrize("bad", [True, 12.0, "12"])
def test_dimension_overrides_reject_non_integer_values(name, bad):
    with pytest.raises(ValueError, match=name):
        gen.generate(0, 0, **{name: bad})


def test_unknown_override_and_bad_difficulty_are_rejected():
    with pytest.raises(ValueError, match="[Uu]nknown"):
        gen.generate(0, 0, definitely_a_typo=1)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("bad", [
    [], [[]], [[0, 1], [2]], [[-1]], [[10]], [["x"]], [[True]], None,
])
def test_malformed_grids_return_diagnostics_instead_of_raising(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize("profile", ["star", "triangle", "cycle"])
def test_each_explicit_profile_is_valid_and_recolors_the_component_oracle(profile):
    for seed in range(12):
        grid = gen.generate(seed, 1, texture=profile)
        assert gen.self_check(grid) == []
        assert gen._rule_mirror(grid) == oracle_output(grid)


def test_four_slot_schedule_survives_every_single_query_rotation():
    assert set(gen.SCHEDULE_PROFILES) == {"star", "triangle", "cycle"}
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    rivals = ("max_degree", "largest_in_main_cluster")
    for start in range(8):
        grids = [gen.generate(17, start + offset, difficulty="hard") for offset in range(4)]
        profiles = [gen.schedule_profile(17, start + offset, difficulty="hard") for offset in range(4)]
        assert profiles.count("cycle") == 2
        for query_index in range(4):
            demonstrations = [grid for i, grid in enumerate(grids) if i != query_index]
            for name in rivals:
                assert any(
                    gen.SEMANTIC_RIVALS[name](grid) != oracle_output(grid)
                    for grid in demonstrations
                ), (start, query_index, name, profiles)

    cycle = gen.generate(11, 1, texture="cycle")
    truth = oracle_output(cycle)
    assert gen.SEMANTIC_RIVALS["max_degree"](cycle) != truth
    assert gen.SEMANTIC_RIVALS["largest_in_main_cluster"](cycle) != truth


def test_declared_canonical_shortcuts_really_fit_canonical_and_are_refuted():
    expected = {"input_color_two", "max_degree", "largest_in_main_cluster"}
    assert expected <= set(gen.CANONICAL_SHORTCUTS)
    pairs = canonical_pairs()
    for name in expected:
        rival = gen.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    fired = {name: 0 for name in expected}
    for seed in range(30):
        for index in range(3):
            grid = gen.generate(seed, index)
            truth = oracle_output(grid)
            for name in expected:
                fired[name] += gen.CANONICAL_SHORTCUTS[name](grid) != truth
    assert fired["input_color_two"] == 90
    assert fired["max_degree"] >= 30
    assert fired["largest_in_main_cluster"] >= 30


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_canonical_scale_and_input_color_eight_remain_represented(difficulty):
    canonical_shapes = {(9, 11), (10, 12), (10, 13)}
    corpus = [gen.generate(seed, seed % 3, difficulty=difficulty) for seed in range(100)]
    assert sum((len(g), len(g[0])) in canonical_shapes for g in corpus) >= 25
    input_eight = sum(any(8 in row for row in g) for g in corpus)
    assert 5 <= input_eight <= 20, input_eight


@pytest.mark.parametrize("mode", ["no_articulation", "multiple_articulations", "empty"])
def test_degenerates_are_explicit_only_and_honor_dimensions(mode):
    grid = gen.generate(3, 0, texture=mode, grid_h=9, grid_w=11)
    assert (len(grid), len(grid[0])) == (9, 11)
    assert gen.self_check(grid)
    assert mode not in gen.AXES["texture"]["valid"].split("|")


def test_reusable_probe_agrees_with_independent_graph_oracle():
    probe_path = HOME / "workspace/review_probe.py"
    probe_spec = importlib.util.spec_from_file_location("articulation_probe", probe_path)
    probe = importlib.util.module_from_spec(probe_spec)
    assert probe_spec.loader is not None
    probe_spec.loader.exec_module(probe)
    grid = gen.generate(19, 2, texture="cycle")
    report = probe.analyze(grid)
    objs, edges = graph(grid)
    assert report["object_count"] == len(objs)
    assert report["articulation_indices"] == articulation_indices(grid)
    assert report["graph_component_count"] == component_count(edges)
