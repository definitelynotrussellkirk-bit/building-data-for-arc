from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "0bb8813a21dc"
HOME = Path(__file__).resolve().parents[1]
EXPECTED_RULE_HASH = "42a14ef4873c"
SCENE_PROFILES = ("identity_scope", "mixed_scope")
CANONICAL_PROFILES = {
    (5, 6, 9),
    (4, 7, 10),
    (4, 6, 8),
    (4, 7, 8),
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_0bb8813a21dc", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK, root=find_root(__file__))


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _labelled(seed, sample_index, difficulty="medium"):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exact():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    for pair in PAIRS:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_generation_is_deterministic_fresh_and_rule_mirror_is_input_pure():
    first = gen.generate(917, 11, difficulty="hard")
    second = gen.generate(917, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    before = copy.deepcopy(first)
    gen.rule_mirror(first)
    assert first == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_twenty_default_draws_hit_every_canonical_shape_palette_profile(difficulty):
    observed = {_profile(gen.generate(501, index, difficulty=difficulty)) for index in range(20)}
    assert CANONICAL_PROFILES <= observed


@pytest.mark.parametrize("profile", SCENE_PROFILES)
def test_every_exact_scene_profile_is_observable_and_honored(profile):
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            grid = gen.generate(seed, seed + 5, difficulty=difficulty, scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_unknown_override_and_invalid_profile_are_rejected():
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, typo_axis="mixed_scope")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, scene_profile="not-a-profile")


def test_every_default_instance_is_a_counterexample_to_each_declared_rival():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(300 + sample_index, sample_index, difficulty=difficulty)
            answer = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert rival(grid) != answer, (difficulty, sample_index, name)


def test_any_query_rotation_of_four_consecutive_pairs_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            labelled = [_labelled(800 + start, start + offset, difficulty) for offset in range(4)]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(labelled) if index != query_index]
                assert gen.lesson_identifiable(demos, labelled[query_index]) == []


def test_profiles_are_structurally_distinct_and_schedule_alternates():
    observed = [
        gen.observe_overrides(gen.generate(44, index))["scene_profile"]
        for index in range(8)
    ]
    assert observed == [SCENE_PROFILES[index % 2] for index in range(8)]


def test_self_check_rejects_shortcuts_outside_the_task_grammar():
    one_row = [[0] * 7 for _ in range(4)]
    one_row[1][1] = 2
    one_row[1][3] = 3
    one_row[1][5] = 3
    assert gen.self_check(one_row)

    no_visible_change = [[0] * 7 for _ in range(4)]
    for row, color in ((0, 2), (1, 3), (3, 4)):
        no_visible_change[row][1] = color
        no_visible_change[row][3] = color
        no_visible_change[row][5] = color
    assert gen.self_check(no_visible_change)

    contiguous_only = [[0] * 7 for _ in range(4)]
    for row, leader in ((0, 2), (1, 4), (3, 6)):
        contiguous_only[row][1:4] = [leader, leader + 1, leader + 1]
    assert gen.self_check(contiguous_only)


def test_every_semantic_witness_has_named_rival_disagreement():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    for witness, rivals in gen.WITNESS_RIVALS.items():
        assert rivals, witness
        assert set(rivals) <= set(gen.SEMANTIC_RIVALS)


def test_rarest_color_canonical_shortcut_is_declared_and_always_refuted_by_generation():
    assert "rarest_row_color" in gen.CANONICAL_SHORTCUTS
    assert "rarest_row_color" in gen.LESSON_COMPETITORS
    rival = gen.CANONICAL_SHORTCUTS["rarest_row_color"]
    for pair in PAIRS:
        assert rival(pair["input"]) == pair["output"]
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = gen.generate(1200, sample_index, difficulty=difficulty)
            assert rival(grid) != gen.rule_mirror(grid)
