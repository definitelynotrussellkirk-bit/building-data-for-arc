from __future__ import annotations

import copy
import random

import pytest

from src.core.canonical_pairs import load_task_pairs
from puzzle_generators.per_puzzle.f86f870eb9f2 import generator as gen

TASK_ID = "f86f870eb9f2"
EXPECTED_RULE_HASH = "1842ae0643b6"


def _generated(seed: int = 123, sample_index: int = 0, difficulty: str = "medium", **overrides):
    return gen.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_rule_hash_and_all_canonical_pairs_are_grounded():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_every_declared_override_is_exact_and_observable():
    cases = [
        {"scene_profile": "canonical_square", "wall_style": "canonical_1", "density_profile": "clear"},
        {"scene_profile": "canonical_wide", "wall_style": "mixed_1_9", "density_profile": "close"},
        {"scene_profile": "canonical_tall", "wall_style": "mixed_1_7_9", "density_profile": "clear"},
        {"scene_profile": "wide_matrix", "wall_style": "mixed_1_7_9", "density_profile": "close"},
        {"scene_profile": "tall_matrix", "wall_style": "mixed_1_9", "density_profile": "clear"},
        {"scene_profile": "large_matrix", "wall_style": "canonical_1", "density_profile": "close"},
    ]
    for index, requested in enumerate(cases):
        grid = _generated(900 + index, index, **requested)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested

    with pytest.raises((TypeError, ValueError)):
        _generated(1, 0, typo_axis="ignored")


def test_determinism_fresh_returns_and_global_rng_state():
    state = random.getstate()
    first = _generated(456, 7, difficulty="hard")
    assert random.getstate() == state
    second = _generated(456, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    assert second[0][0] != 99


def test_self_check_rejects_targeted_impostors():
    grid = _generated(777, 8, difficulty="medium", scene_profile="canonical_square")
    assert gen.self_check(grid) == []
    analysis = gen.analyze_scene(grid)

    mutations = {}

    broken_border = copy.deepcopy(grid)
    broken_border[0][1] = 0
    mutations["broken_outer_wall"] = broken_border

    stray_wall = copy.deepcopy(grid)
    room_cell = analysis["rooms"][0]["cells"][0]
    stray_wall[room_cell[0]][room_cell[1]] = 1
    mutations["stray_interior_wall"] = stray_wall

    tied_density = copy.deepcopy(grid)
    equal_pair = next(
        (i, j)
        for i, room in enumerate(analysis["rooms"])
        for j, other in enumerate(analysis["rooms"])
        if i < j and room["area"] == other["area"]
    )
    for room in analysis["rooms"]:
        for row, col in room["cells"]:
            tied_density[row][col] = 0
    for room_index in equal_pair:
        row, col = analysis["rooms"][room_index]["cells"][0]
        tied_density[row][col] = 3
    mutations["ambiguous_density_tie"] = tied_density

    no_markers = copy.deepcopy(grid)
    for row in range(len(no_markers)):
        for col in range(len(no_markers[0])):
            if no_markers[row][col] == 3:
                no_markers[row][col] = 0
    mutations["no_density_evidence"] = no_markers

    unexpected_color = copy.deepcopy(grid)
    unexpected_color[analysis["rooms"][0]["cells"][0][0]][analysis["rooms"][0]["cells"][0][1]] = 6
    mutations["unexpected_room_color"] = unexpected_color

    for name, mutated in mutations.items():
        assert gen.self_check(mutated), name


def test_ordinary_draws_refute_count_area_and_marker_only_shortcuts():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(24):
            grid = _generated(3000 + index, index, difficulty=difficulty)
            facts = gen.analyze_scene(grid)
            target = facts["target_index"]
            rooms = facts["rooms"]
            assert any(room["marker_count"] > rooms[target]["marker_count"] for i, room in enumerate(rooms) if i != target)
            assert any(room["area"] > rooms[target]["area"] for i, room in enumerate(rooms) if i != target)
            assert rooms[target]["marker_count"] < rooms[target]["area"]
            truth = gen.rule_mirror(grid)
            assert gen.SEMANTIC_RIVALS["most_markers"](grid) != truth
            assert gen.SEMANTIC_RIVALS["largest_room"](grid) != truth
            assert gen.SEMANTIC_RIVALS["marker_cells_only"](grid) != truth
