"""Canonical generator regressions for de6d50ef73a3."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parents[1]


def _rule_application(source, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return f"({wrap_rule(source)} {literal})"


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_generator_de6d50ef73a3_contract", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_row():
    from reviewer_support import canonical_path, find_root

    root = find_root(HOME)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    return next(row for row in rows if row["task_id"] == gen.TASK_ID)


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _bbox_crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _support(grid):
    crop = _bbox_crop(grid)
    return {(r, c) for r, row in enumerate(crop) for c, value in enumerate(row) if value}


def _colors(grid):
    return {value for row in grid for value in row if value}


def test_all_canonical_pairs_are_accepted_and_mirror_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]
        assert grid == snapshot


def test_components_join_adjacent_cells_across_colors():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 2, 0, 0],
        [0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    components = gen._components(grid)
    assert len(components) == 1
    assert set(components[0]) == {(1, 1), (1, 2), (2, 2)}
    assert gen.self_check(grid) == []


def test_unknown_invalid_and_unlabelable_controls_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="shape_choice"):
        gen.generate(1, 0, shape_choice=99)
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=4)
    with pytest.raises(ValueError, match="grid_w"):
        gen.generate(1, 0, grid_w=23)
    with pytest.raises(ValueError, match="palette_size"):
        gen.generate(1, 0, palette_size=4)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")
    assert "multi_object" not in gen.AXES["texture"]["valid"]
    with pytest.raises(ValueError, match="texture"):
        gen.generate(1, 0, texture="multi_object")


def test_self_check_is_total_and_rejects_malformed_or_trivial_inputs():
    assert gen.self_check([])
    assert gen.self_check([[0, 1], [0]])
    assert gen.self_check([[0, 0], [0, True]])
    assert gen.self_check([[0, 0], [0, 0]])
    assert gen.self_check([[5, 0], [0, 0]])
    assert gen.self_check([[1, 1], [0, 0]])


def test_shape_choice_controls_exact_normalized_support():
    expected = [
        {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)},
        {(0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 3)},
        {(0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)},
        {(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)},
    ]
    observed = []
    for shape_choice in range(4):
        grid = gen.generate(
            314159,
            7,
            difficulty="medium",
            grid_h=8,
            grid_w=10,
            shape_choice=shape_choice,
            palette_size=1,
        )
        assert gen.self_check(grid) == []
        observed.append(_support(grid))
    assert observed == expected


def test_palette_count_kind_and_aliases_are_observable():
    warm = gen.generate(
        2026, 4, grid_h=9, grid_w=11, shape_choice=2,
        palette_kind="warm", palette_size=3,
    )
    cool = gen.generate(
        2026, 4, grid_h=9, grid_w=11, shape_choice=2,
        palette_kind="cool", palette_size=3,
    )
    assert len(_colors(warm)) == len(_colors(cool)) == 3
    assert _colors(warm).isdisjoint(_colors(cool))
    assert gen.generate(
        2026, 4, grid_h=9, grid_w=11, shape_choice=2,
        texture="warm", n_distinct_colors=3,
    ) == warm
    with pytest.raises(ValueError, match="conflicting"):
        gen.generate(1, 0, palette_kind="cool", texture="warm")
    with pytest.raises(ValueError, match="conflicting"):
        gen.generate(1, 0, palette_size=2, n_distinct_colors=3)


def test_grid_overrides_are_exact_and_every_generated_grid_is_labelable():
    for height, width in ((5, 5), (18, 22), (7, 13)):
        grid = gen.generate(
            72, height + width, difficulty="hard", grid_h=height, grid_w=width,
            shape_choice=(height + width) % 4, palette_size=2,
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) != grid


def test_generation_is_deterministic_fresh_and_rng_isolated():
    random.seed(987654)
    state = random.getstate()
    first = gen.generate(
        88, 5, difficulty="hard", grid_h=18, grid_w=22,
        shape_choice=3, palette_kind="varied", palette_size=3,
    )
    assert random.getstate() == state
    second = gen.generate(
        88, 5, difficulty="hard", grid_h=18, grid_w=22,
        shape_choice=3, palette_kind="varied", palette_size=3,
    )
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_protected_racket_matches_mirror_on_generated_shapes():
    source = _canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for shape_choice in range(4):
            grid = gen.generate(
                404, shape_choice, grid_h=9, grid_w=12,
                shape_choice=shape_choice, palette_size=1 + shape_choice % 3,
            )
            assert bridge.eval_text(_rule_application(source, grid)) == gen.rule_mirror(grid)
    finally:
        bridge.shutdown()


def test_rule_mirror_preserves_canvas_on_empty_authority_edge_case():
    grid = [[0, 0, 0], [0, 0, 0]]
    assert gen.rule_mirror(grid) == grid
