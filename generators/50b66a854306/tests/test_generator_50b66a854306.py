"""Focused regressions for the 50b66a854306 generator repair."""
from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.50b66a854306.generator"
)
TASK_ID = "50b66a854306"


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_match():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "0b773d88a636"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_three_example_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(18):
            lesson = [
                _pair(gen.generate(2701, index, difficulty=difficulty))
                for index in range(start, start + 4)
            ]
            assert gen.lesson_identifiable(lesson[:3], lesson[3]) == []
            assert any(
                gen.strict_canonical_like(pair["input"]) == []
                for pair in lesson[:3]
            )
            assert len({len(pair["output"]) for pair in lesson[:3]}) >= 2


def test_all_profile_overrides_are_exact_observable_and_band_safe():
    for difficulty in ("easy", "medium", "hard"):
        for profile_index, profile in enumerate(gen.PROFILE_NAMES):
            for seed in (0, 9, 77):
                grid = gen.generate(
                    seed,
                    profile_index + 13,
                    difficulty=difficulty,
                    profile=profile,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {"profile": profile}

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis="ignored")


def test_regression_seed_preserves_different_color_equivalent_pair():
    grid = gen.generate(
        9,
        0,
        difficulty="medium",
        profile=gen.PROFILE_N6_PAIR_PAIR_SINGLES,
    )
    assert gen.self_check(grid) == []
    components = gen._components(grid)
    assert any(
        gen._canon(components[left]["shape"]) == gen._canon(components[right]["shape"])
        and components[left]["color"] != components[right]["color"]
        for left in range(len(components))
        for right in range(left + 1, len(components))
    )


def test_structural_mutations_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, malformed in fixtures:
        assert gen.self_check(malformed), name


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20260726)
    state = random.getstate()
    first = gen.generate(314159, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second
