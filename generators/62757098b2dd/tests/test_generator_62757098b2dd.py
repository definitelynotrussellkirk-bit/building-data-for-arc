"""Focused regression tests for the 62757098b2dd generator repair."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.62757098b2dd.generator")
TASK_ID = "62757098b2dd"


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_owned_exactly():
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "6d0daea2c755"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_exact_override_combination_is_consumed_and_observable():
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for scene_profile in GEN.SCENE_PROFILES:
            for palette_profile in GEN.PALETTE_PROFILES:
                requested = {
                    "scene_profile": scene_profile,
                    "palette_profile": palette_profile,
                }
                grid = GEN.generate(
                    10_000 + case_index,
                    case_index,
                    difficulty=difficulty,
                    **requested,
                )
                assert GEN.self_check(
                    grid, difficulty=difficulty, meta={"overrides": requested}
                ) == []
                assert GEN.observe_overrides(grid) == requested
                case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis=True)
    with pytest.raises(ValueError, match="unknown scene_profile"):
        GEN.generate(1, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="unknown palette_profile"):
        GEN.generate(1, 0, palette_profile="not-a-palette")


def test_schedule_windows_cover_odd_multi_and_refute_all_named_rivals():
    period = len(GEN.SCHEDULE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(period):
            grids = [
                GEN.generate(2707, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            assert any(GEN._has_odd_dimension(grid) for grid in grids)
            assert any(GEN._has_multiple_rectangles(grid) for grid in grids)
            demos = [_pair(grid) for grid in grids]
            query = _pair(GEN.generate(2707, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty))
            assert GEN.lesson_identifiable(demos, query) == []
            for rival_name, rival in GEN.SEMANTIC_RIVALS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    difficulty,
                    start,
                    rival_name,
                )


def test_targeted_structural_mutations_are_rejected():
    grid = GEN.generate(
        31337,
        2,
        difficulty="medium",
        scene_profile="canonical_multi",
        palette_profile="broad",
    )
    fixtures = GEN.mutation_impostors(grid)
    assert len(fixtures) >= 5
    for name, malformed in fixtures:
        assert GEN.self_check(malformed), name


def test_replay_returns_fresh_objects_and_preserves_global_random_state():
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_rule_mirror_is_input_pure_and_rivals_have_specific_witnesses():
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness = GEN.SEMANTIC_WITNESSES[witness_name]
        grid = next(
            GEN.generate(8181, index, difficulty="medium")
            for index in range(len(GEN.SCHEDULE_PROFILES))
            if witness(GEN.generate(8181, index, difficulty="medium"))
        )
        before = copy.deepcopy(grid)
        expected = GEN.rule_mirror(grid)
        assert grid == before
        for rival_name in rival_names:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != expected
