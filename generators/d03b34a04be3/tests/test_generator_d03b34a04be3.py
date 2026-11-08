"""Focused regression tests for the d03b34a04be3 selector-crop generator."""
from __future__ import annotations

import copy
import random
import pytest

from puzzle_generators.per_puzzle.d03b34a04be3 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_pairs_match_rule_and_selfcheck():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_profiles_are_exactly_observable_and_general_profiles_kill_rivals():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                91000 + index,
                index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.self_check(
                grid, meta={"overrides": {"scene_profile": profile}}
            ) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            if profile in gen.GENERAL_PROFILES:
                official = gen.rule_mirror(grid)
                for rival in gen.SEMANTIC_RIVALS.values():
                    assert rival(grid) != official


def test_sliding_lesson_windows_refute_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            seed = 77000 + start
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(seed, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="wide_adversary")
    with pytest.raises(ValueError, match="scene_profile must be one of"):
        gen.generate(1, 0, scene_profile="not_a_profile")


def test_selfcheck_rejects_targeted_rule_hiding_impostors():
    impostors = {}

    no_body = [[0] * 8 for _ in range(7)]
    no_body[0][0] = 4
    no_body[3][5] = 7
    impostors["no_body_target"] = no_body

    solid_bbox = [[0] * 8 for _ in range(7)]
    solid_bbox[0][0] = 4
    for row in (2, 3):
        for col in (3, 4):
            solid_bbox[row][col] = 4
    solid_bbox[5][6] = 7
    impostors["solid_target_bbox"] = solid_bbox

    key_in_bbox = [[0] * 8 for _ in range(7)]
    key_in_bbox[0][0] = 4
    key_in_bbox[0][4] = key_in_bbox[3][0] = key_in_bbox[3][4] = 4
    key_in_bbox[5][6] = 7
    impostors["key_spanning_bbox"] = key_in_bbox

    no_exterior_distractor = [[0] * 8 for _ in range(7)]
    no_exterior_distractor[0][0] = 4
    no_exterior_distractor[2][2] = 4
    no_exterior_distractor[2][5] = 4
    no_exterior_distractor[4][2] = 4
    no_exterior_distractor[4][5] = 4
    no_exterior_distractor[3][3] = 7
    impostors["no_exterior_distractor"] = no_exterior_distractor

    dense_body = [[0] * 8 for _ in range(7)]
    dense_body[0][0] = 4
    for row in range(1, 6):
        for col in range(1, 7):
            dense_body[row][col] = 4
    dense_body[6][7] = 7
    impostors["dense_target_body"] = dense_body

    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_state():
    state = random.getstate()
    first = gen.generate(8821, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8821, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    snapshot = copy.deepcopy(second)
    first[0][0] = (first[0][0] % 9) + 1
    assert second == snapshot


def test_rule_hash_and_version_pin_current_authority():
    assert gen.RULE_HASH == "e7aaedd41057"
    assert gen.VERSION == "2.0.0"
