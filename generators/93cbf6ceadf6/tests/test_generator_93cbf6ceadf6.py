"""Semantic and regression tests for generator 93cbf6ceadf6."""
from __future__ import annotations

import copy
import importlib
import json
import random
from collections import Counter

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import set_ctx_observer
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "93cbf6ceadf6"
ROOT = find_root(__file__)
GEN = importlib.import_module("puzzle_generators.per_puzzle.93cbf6ceadf6.generator")


def _canonical_source() -> str:
    sources = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.append(row["program_solution"])
    assert len(set(sources)) == 1
    return sources[0]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _literal(grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _stamp(grid, shape, row, col, color):
    for dr, dc in shape:
        grid[row + dr][col + dc] = color


def _manual_scene(shapes):
    grid = [[0] * 12 for _ in range(10)]
    anchors = ((0, 0), (0, 6), (6, 3))
    for index, (shape, anchor) in enumerate(zip(shapes, anchors), start=2):
        _stamp(grid, shape, *anchor, index)
    return grid


def test_metadata_and_all_canonical_pairs_match_python_mirror() -> None:
    assert GEN.VERSION == "2.0.0"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN._odd_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_ordinary_generation_has_exact_two_plus_one_shape_grammar() -> None:
    shapes = set()
    odd_colors = set()
    odd_positions = set()
    color_multiplicities = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(60):
            grid = GEN.generate(1000 + seed, seed * 19 + 7, difficulty=band)
            assert GEN.self_check(grid) == []
            items = GEN._component_items(grid)
            frequencies = Counter(item["shape"] for item in items)
            assert sorted(frequencies.values()) == [1, 2]
            odd = next(item for item in items if frequencies[item["shape"]] == 1)
            shapes.add(odd["shape"])
            odd_colors.add(odd["color"])
            odd_positions.add((odd["r0"] * 3 // len(grid), odd["c0"] * 3 // len(grid[0])))
            color_multiplicities.add(tuple(sorted(Counter(item["color"] for item in items).values())))
            assert GEN._odd_output(grid)
    assert len(shapes) >= 8
    assert len(odd_colors) >= 7
    assert len(odd_positions) >= 6
    assert color_multiplicities >= {(3,), (1, 2), (1, 1, 1)}


def test_observable_boundary_overrides_are_exact() -> None:
    for overrides in (
        {"grid_h": 9},
        {"grid_h": 22},
        {"grid_w": 9},
        {"grid_w": 22},
        {"grid_h": 9, "grid_w": 9},
        {"grid_h": 22, "grid_w": 22},
    ):
        for seed in range(5):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(seed, seed + 5, difficulty="medium", **overrides)
            finally:
                set_ctx_observer(None)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            assert observed | overrides == observed
            for name, value in overrides.items():
                assert observed[name] == value
            assert captured
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="gallery")


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20261026)
    state = random.getstate()
    first = GEN.generate(77, 91, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    second[0][0] = (second[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_wrong_object_and_shape_multiplicities() -> None:
    a = ((0, 0), (0, 1), (1, 1))
    b = ((0, 0), (1, 0), (1, 1))
    c = ((0, 0), (0, 1), (0, 2))
    valid = _manual_scene((a, a, b))
    assert GEN.self_check(valid) == []
    impostors = {
        "blank": [[0] * 12 for _ in range(10)],
        "two_objects": _manual_scene((a, a)),
        "three_same": _manual_scene((a, a, a)),
        "three_distinct": _manual_scene((a, b, c)),
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_generated_python_labels_match_protected_racket() -> None:
    program = _canonical_source()
    wrapped = wrap_rule(program)
    grids = [GEN.generate(900 + seed, seed, difficulty="medium") for seed in range(6)]
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity.get("protected") is True
        for grid in grids:
            actual = bridge.eval_text(f"({wrapped} {_literal(grid)})")
            assert actual == GEN._odd_output(grid)
    finally:
        bridge.close()
