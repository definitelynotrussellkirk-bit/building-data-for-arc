from __future__ import annotations

import copy
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs
from puzzle_generators.per_puzzle.b7c3b8bc9805 import generator as gen


def _pair(seed: int, sample_index: int, difficulty: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_owned_and_rule_mirror_matches() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_four_slot_schedule_is_lesson_identifiable_from_every_start() -> None:
    for start in range(12):
        demos = [_pair(901, start + offset) for offset in range(gen.EXAMPLES_NEEDED)]
        query = _pair(901, start + gen.EXAMPLES_NEEDED)
        assert gen.lesson_identifiable(demos, query) == []


def test_same_phase_scene_kills_canonical_compatible_symmetric_shortcut() -> None:
    canonical = canonical_pairs(gen.TASK_ID)
    shortcut = gen.CANONICAL_SHORTCUTS["marker_position_symmetric"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical)
    witness = gen.generate(77, 1, difficulty="easy")
    assert gen.semantic_signature(witness)["marker_phase_relation"] == "same"
    assert shortcut(witness) != gen.rule_mirror(witness)


def test_exact_overrides_are_observable_and_boundaries_work() -> None:
    cases = (
        {"grid_h": 10}, {"grid_h": 22}, {"grid_w": 10}, {"grid_w": 24},
        {"frame_h": 5}, {"frame_h": 6}, {"frame_w": 5}, {"frame_w": 6},
        {"m1_quadrant": "UL"}, {"m1_quadrant": "UR"},
        {"m1_quadrant": "LL"}, {"m1_quadrant": "LR"},
    )
    for index, override in enumerate(cases):
        grid = gen.generate(1000 + index, index, difficulty="hard", **override)
        observed = gen.observe_overrides(grid)
        key, value = next(iter(override.items()))
        assert observed[key] == value
        assert gen.self_check(grid) == []


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=9)
    with pytest.raises(ValueError):
        gen.generate(1, 0, m1_quadrant="CENTER")


def test_self_check_rejects_targeted_impostors() -> None:
    for _, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), grid


def test_deterministic_fresh_and_global_rng_neutral() -> None:
    random.seed(12345)
    state = random.getstate()
    first = gen.generate(42, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(42, 3, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(42, 3, difficulty="hard")


def test_canonical_profile_is_scheduled_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(123, 0, difficulty=band)
        assert gen.strict_canonical_like(grid) == []
