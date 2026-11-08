from __future__ import annotations

import copy
import importlib
import random

import pytest

from src.core.canonical_pairs import load_task_pairs
gen = importlib.import_module("puzzle_generators.per_puzzle.1484fc8ec47b.generator")

TASK_ID = "1484fc8ec47b"
EXPECTED_RULE_HASH = "33d8fa4b8fcd"


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
        {"scene_profile": "canonical_matrix_2x3", "wall_style": "canonical_1", "count_profile": "close"},
        {"scene_profile": "canonical_row_1x3", "wall_style": "mixed_1_9", "count_profile": "clear"},
        {"scene_profile": "canonical_matrix_2x2", "wall_style": "mixed_1_7_9", "count_profile": "close"},
        {"scene_profile": "control_matrix_2x3", "wall_style": "mixed_1_7_9", "count_profile": "clear"},
        {"scene_profile": "control_tall_3x2", "wall_style": "mixed_1_9", "count_profile": "close"},
        {"scene_profile": "control_wide_2x4", "wall_style": "canonical_1", "count_profile": "clear"},
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
    grid = _generated(
        777,
        8,
        difficulty="medium",
        scene_profile="control_matrix_2x3",
        wall_style="canonical_1",
        count_profile="close",
    )
    assert gen.self_check(grid) == []
    facts = gen.analyze_scene(grid)
    target = facts["target_index"]
    assert target is not None

    mutations = {}

    broken_border = copy.deepcopy(grid)
    broken_border[0][1] = 0
    mutations["broken_outer_wall"] = broken_border

    stray_wall = copy.deepcopy(grid)
    row, col = facts["rooms"][0]["cells"][0]
    stray_wall[row][col] = 1
    mutations["stray_interior_wall"] = stray_wall

    tied_maximum = copy.deepcopy(grid)
    target_count = facts["rooms"][target]["marker_count"]
    losing = next(i for i, room in enumerate(facts["rooms"]) if i != target and room["area"] > target_count)
    for row, col in facts["rooms"][losing]["cells"]:
        tied_maximum[row][col] = 0
    for row, col in facts["rooms"][losing]["cells"][:target_count]:
        tied_maximum[row][col] = 3
    mutations["ambiguous_maximum_tie"] = tied_maximum

    target_full = copy.deepcopy(grid)
    for row, col in facts["rooms"][target]["cells"]:
        target_full[row][col] = 3
    mutations["target_completely_marked"] = target_full

    no_losing_evidence = copy.deepcopy(grid)
    for index, room in enumerate(facts["rooms"]):
        if index == target:
            continue
        for row, col in room["cells"]:
            if no_losing_evidence[row][col] == 3:
                no_losing_evidence[row][col] = 0
    mutations["no_losing_marker_evidence"] = no_losing_evidence

    unexpected_color = copy.deepcopy(grid)
    row, col = facts["rooms"][0]["cells"][0]
    unexpected_color[row][col] = 6
    mutations["unexpected_room_color"] = unexpected_color

    for name, mutated in mutations.items():
        assert gen.self_check(mutated), name


def test_every_draw_refutes_density_position_and_marker_only_shortcuts():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(36):
            grid = _generated(3000 + index, index, difficulty=difficulty)
            truth = gen.rule_mirror(grid)
            assert gen.SEMANTIC_RIVALS["densest_room"](grid) != truth
            assert gen.SEMANTIC_RIVALS["first_room"](grid) != truth
            assert gen.SEMANTIC_RIVALS["last_room"](grid) != truth
            assert gen.SEMANTIC_RIVALS["marker_cells_only"](grid) != truth


def test_every_three_demo_window_kills_all_named_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = _generated(6100 + start, start + offset, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = _generated(7100 + start, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            assert any(
                gen.SEMANTIC_RIVALS["largest_room"](demo["input"]) != demo["output"]
                for demo in demos
            )
