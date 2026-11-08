from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule


TASK_ID = "7ed6d6ae68f2"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_and_canonical_pairs_match_selected_authority():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_unknown_override_is_rejected_and_size_override_is_exact():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", typo_axis="10x13")
    for profile, (height, width) in GEN._SIZE_BY_PROFILE.items():
        grid = GEN.generate(17, 4, difficulty="hard", size_profile=profile)
        assert (len(grid), len(grid[0])) == (height, width)
        assert GEN.observe_overrides(grid) == {"size_profile": profile}


def test_every_three_demo_window_contains_all_semantic_scene_families():
    for difficulty in ("easy", "medium", "hard"):
        profiles = [GEN.schedule_profile(5, index, difficulty) for index in range(12)]
        for start in range(10):
            assert set(profiles[start : start + 3]) == set(GEN.SCHEDULE_PROFILES)


def test_generated_profiles_kill_the_named_shortcuts():
    for difficulty in ("easy", "medium", "hard"):
        generated = [GEN.generate(41, index, difficulty=difficulty) for index in range(3)]
        assert any(GEN._wall_sensitive_competition(grid) for grid in generated)
        assert any(GEN._disconnected_seed_regions(grid) for grid in generated)
        assert any(GEN._unreachable_region(grid) for grid in generated)
        assert any(GEN._equal_distance_tie(grid) for grid in generated)
        assert any(not GEN.strict_canonical_like(grid) for grid in generated)


def test_mutation_fixtures_are_all_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    state_before = random.getstate()
    first = GEN.generate(99, 8, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(99, 8, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert state_before == state_after


def test_negative_recombination_rejected_while_racket_oracle_executes():
    valid = GEN.generate(615001, 2, difficulty="hard")
    recombined = copy.deepcopy(valid)
    green = next((r, c) for r, row in enumerate(recombined) for c, value in enumerate(row) if value == 3)
    recombined[green[0]][green[1]] = 8  # foreign role/color: outside the teaching grammar
    assert GEN.self_check(recombined)

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    snapshot = copy.deepcopy(recombined)
    try:
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert recombined == snapshot
    assert output and len(output) == len(recombined) and len(output[0]) == len(recombined[0])
