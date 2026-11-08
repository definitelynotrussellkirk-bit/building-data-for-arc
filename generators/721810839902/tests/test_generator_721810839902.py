from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

import importlib
gen = importlib.import_module("puzzle_generators.per_puzzle.721810839902.generator")
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from src.core.canonical_pairs import load_task_pairs

TASK_ID = "721810839902"
ROOT = Path(__file__).resolve().parents[1]


def _norm_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_authority_and_all_canonical_pairs() -> None:
    rows = [json.loads(line) for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()]
    row = next(row for row in rows if row.get("task_id") == TASK_ID)
    assert gen.RULE_HASH == _norm_hash(row["program_solution"]) == "e3401b50999e"
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.apply_rule(pair["input"]) == pair["output"]


def test_racket_exact_input_pure_and_a_b_a() -> None:
    pairs = load_task_pairs(TASK_ID)
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before
        a = gen.generate(701, 9, difficulty="easy")
        b = gen.generate(702, 10, difficulty="hard")
        a1 = _apply_rule(bridge, fn_name, a)
        bout = _apply_rule(bridge, fn_name, b)
        a2 = _apply_rule(bridge, fn_name, a)
        assert a1 == a2 == gen.apply_rule(a)
        assert bout == gen.apply_rule(b)
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_draws_have_both_semantic_branches_and_exact_observations(difficulty: str) -> None:
    for seed in range(80):
        grid = gen.generate(seed, seed * 17 + 3, difficulty=difficulty)
        observed = gen.observe_overrides(grid)
        assert gen.self_check(grid, difficulty=difficulty) == []
        assert 8 <= observed["grid_h"] <= 12
        assert 8 <= observed["grid_w"] <= 12
        assert 1 <= observed["n_border"] <= 3
        assert 1 <= observed["n_interior"] <= 3
        assert observed["n_border"] + observed["n_interior"] >= 2
        output = gen.apply_rule(grid)
        assert output != grid
        assert any(value for row in output for value in row)


def test_full_boundary_override_combination_is_exact() -> None:
    grid = gen.generate(
        1901,
        37,
        difficulty="hard",
        grid_h=12,
        grid_w=12,
        n_border=3,
        n_interior=3,
        border_side="top",
        shape_mix="varied",
        same_color_decoy=True,
    )
    observed = gen.observe_overrides(grid)
    assert observed == {
        "grid_h": 12,
        "grid_w": 12,
        "n_border": 3,
        "n_interior": 3,
        "border_side": "top",
        "shape_mix": "varied",
        "same_color_decoy": True,
    }
    assert gen.self_check(grid) == []


def test_same_color_decoy_requires_component_level_border_reasoning() -> None:
    grid = gen.generate(
        2201,
        41,
        difficulty="medium",
        grid_h=12,
        grid_w=12,
        n_border=2,
        n_interior=2,
        same_color_decoy=True,
        border_side="left",
        shape_mix="triominoes",
    )
    components = gen.components(grid)
    h, w = len(grid), len(grid[0])
    border_colors = {
        color
        for color, cells in components
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
    }
    interior_colors = {
        color
        for color, cells in components
        if not any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
    }
    shared = border_colors & interior_colors
    assert shared
    out = gen.apply_rule(grid)
    for color in shared:
        assert any(color in row for row in out)
        assert sum(row.count(color) for row in out) < sum(row.count(color) for row in grid)


def test_same_color_decoys_remain_distinct_under_eight_connectivity() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = gen.generate(8500 + sample_index, sample_index, difficulty=difficulty, same_color_decoy=True)
            assert not gen._same_color_diagonal_contact(grid)


def test_border_sides_are_exactly_observable_in_grid_effect() -> None:
    grids = {
        side: gen.generate(
            333,
            17,
            difficulty="medium",
            grid_h=12,
            grid_w=12,
            n_border=3,
            n_interior=2,
            border_side=side,
            shape_mix="dominoes",
            same_color_decoy=False,
        )
        for side in gen.BORDER_SIDES
    }
    assert len({tuple(map(tuple, grid)) for grid in grids.values()}) == len(gen.BORDER_SIDES)
    assert {side: gen.observe_overrides(grid)["border_side"] for side, grid in grids.items()} == {side: side for side in gen.BORDER_SIDES}


def test_self_check_rejects_targeted_impostors() -> None:
    blank = [[0] * 8 for _ in range(8)]
    all_border = copy.deepcopy(blank)
    all_border[0][1:3] = [2, 2]
    all_interior = copy.deepcopy(blank)
    all_interior[3][3:5] = [3, 3]
    singleton_mix = copy.deepcopy(blank)
    singleton_mix[0][1] = 2
    singleton_mix[4][4] = 3
    touching_colors = copy.deepcopy(blank)
    touching_colors[0][1:3] = [2, 2]
    touching_colors[3][3:5] = [3, 3]
    touching_colors[3][5] = 4
    for grid in (blank, all_border, all_interior, singleton_mix, touching_colors):
        assert gen.self_check(grid)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    state = random.getstate()
    first = gen.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(444, 19, difficulty="medium") == second


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 7},
        {"grid_w": 13},
        {"n_border": 0},
        {"n_interior": 4},
        {"border_side": "diagonal"},
        {"shape_mix": "solid"},
        {"same_color_decoy": "yes"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_overrides_reject_loudly(kwargs: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, difficulty="medium", **kwargs)
