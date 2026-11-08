from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "423fca3dc076"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "675cabbc5188"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_declared_axes_round_trip_at_boundaries_and_unknown_keys_reject():
    cases = [
        {"grid_h": 8, "grid_w": 9, "layout": "vertical_2", "texture": "top_left_seeds"},
        {"grid_h": 10, "grid_w": 12, "layout": "horizontal_2", "texture": "off_corner_seeds"},
        {"grid_h": 8, "grid_w": 12, "layout": "cross_4", "texture": "off_corner_seeds"},
        {"grid_h": 10, "grid_w": 9, "layout": "t_right_3", "texture": "top_left_seeds"},
    ]
    for i, overrides in enumerate(cases):
        grid = gen.generate(9000 + i, 50 + i, difficulty="hard", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, misspelled_axis=3)


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(700, 0, layout="vertical_2", texture="off_corner_seeds")

    border_hole = copy.deepcopy(base)
    border_hole[0][1] = 0
    assert gen.self_check(border_hole)

    dangling_wall = copy.deepcopy(base)
    dangling_wall[2][2] = 5
    assert gen.self_check(dangling_wall)

    two_seeds = gen.generate(1, 0, texture="two_seeds_one_room")
    assert gen.self_check(two_seeds)

    duplicate_colors = gen.generate(1, 0, texture="duplicate_seed_colors")
    assert gen.self_check(duplicate_colors)

    no_seeds = gen.generate(1, 0, texture="no_seeds")
    assert gen.self_check(no_seeds)


def test_every_four_demo_window_contains_decisive_controls_and_kills_rivals():
    for start in range(16):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(12345, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(54321, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, competitor in gen.LESSON_COMPETITORS.items():
            assert any(
                competitor(demo["input"]) != demo["output"]
                for demo in demos
            ), name
