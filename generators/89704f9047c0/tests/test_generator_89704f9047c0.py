"""Focused regression tests for the nearest-corner generator repair."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.89704f9047c0.generator")
from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "89704f9047c0"


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_match_python_mirror():
    assert gen.RULE_HASH == "83dc1de09d53"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_four_step_schedule_reaches_every_profile_in_every_band():
    for band in ("easy", "medium", "hard"):
        observed = {
            gen.observe_overrides(gen.generate(31, index, difficulty=band))["scene_profile"]
            for index in range(4)
        }
        assert observed == set(gen.SCENE_PROFILES)


def test_exact_profile_overrides_and_unknown_keys_are_falsifiable():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(41, 9, difficulty="hard", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(41, 9, typo_profile="canonical_5x7")
    with pytest.raises(ValueError):
        gen.generate(41, 9, scene_profile="not_a_profile")


def test_self_check_rejects_four_targeted_impostors():
    grid = gen.generate(7, 0)

    missing_corner = copy.deepcopy(grid)
    missing_corner[0][0] = 0
    assert gen.self_check(missing_corner)

    duplicate_corner = copy.deepcopy(grid)
    duplicate_corner[0][-1] = duplicate_corner[0][0]
    assert gen.self_check(duplicate_corner)

    interior_leak = copy.deepcopy(grid)
    interior_leak[1][1] = 9
    assert gen.self_check(interior_leak)

    ragged = copy.deepcopy(grid)
    ragged[-1] = ragged[-1][:-1]
    assert gen.self_check(ragged)


def test_every_sliding_four_demo_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(gen.generate(101, index, difficulty=band))
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            query = _pair(gen.generate(101, start + gen.EXAMPLES_NEEDED, difficulty=band))
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_memorizer_fits_official_pairs_but_loses_on_generated_input():
    for pair in canonical_pairs(TASK_ID):
        assert gen.SEMANTIC_RIVALS["canonical_palette_memorizer"](pair["input"]) == pair["output"]
    grid = gen.generate(55, 3)
    assert gen._witness_novel_palette_profile(grid)
    assert gen.SEMANTIC_RIVALS["canonical_palette_memorizer"](grid) != gen.rule_mirror(grid)


def test_replay_returns_fresh_objects_without_touching_global_rng():
    random.seed(90210)
    before = random.getstate()
    first = gen.generate(123, 8, difficulty="medium")
    middle = gen.generate(999, 5, difficulty="hard")
    second = gen.generate(123, 8, difficulty="medium")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert middle != first
    assert before == after


def test_repeated_scene_profiles_do_not_lock_palette_rank_order():
    repeated_profile_orders = {
        gen._analysis(gen.generate(271, sample_index, difficulty="medium"))["rank_order"]
        for sample_index in range(0, 20, len(gen.SCENE_PROFILES))
    }
    assert len(repeated_profile_orders) == 5


def test_profile_palette_rank_shortcut_is_named_and_refuted_by_each_lesson():
    rival_name = "profile_palette_rank_shortcut"
    assert rival_name in gen.SEMANTIC_RIVALS
    rival = gen.SEMANTIC_RIVALS[rival_name]
    for start in range(12):
        demos = [
            _pair(gen.generate(313, index, difficulty="medium"))
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        assert any(rival(demo["input"]) != demo["output"] for demo in demos)


def test_lesson_identifiable_reports_outside_profile_without_competitor_crash():
    outside = [[0 for _ in range(10)] for _ in range(9)]
    outside[0][0], outside[0][-1], outside[-1][0], outside[-1][-1] = (1, 2, 3, 4)
    demos = [_pair(outside)] + [
        _pair(gen.generate(419, index, difficulty="medium"))
        for index in range(1, gen.EXAMPLES_NEEDED)
    ]
    query = _pair(gen.generate(419, gen.EXAMPLES_NEEDED, difficulty="medium"))

    reasons = gen.lesson_identifiable(demos, query)

    assert any("outside the linked canonical profile set" in reason for reason in reasons)
