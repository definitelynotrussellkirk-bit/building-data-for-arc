"""Focused regression coverage for chamber plurality fill (d7b84df5a06a)."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "d7b84df5a06a"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _pairs():
    return canonical_pairs(TASK_ID)


def test_rule_pin_and_every_canonical_pair():
    pairs = _pairs()
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "8ba1dc91d063"
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_one_generated_pair_teaches_every_decisive_branch_and_rejects_rivals():
    for sample_index in range(6):
        grid = gen.generate(1701, sample_index, difficulty="medium")
        output = gen.rule_mirror(grid)
        for name in (
            "mapped_winner_2",
            "mapped_winner_3",
            "mapped_winner_4",
            "top_count_tie",
            "plurality_without_majority",
            "lower_count_tie",
            "independent_chamber_outcomes",
        ):
            assert gen.SEMANTIC_WITNESSES[name](grid), name
        for rival_name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != output, rival_name
        pair = {"input": grid, "output": output}
        assert gen.lesson_identifiable([pair], pair) == []


def test_override_boundaries_are_exact_observable_and_unknown_keys_reject():
    boundary_cases = (
        {"grid_h": 11, "grid_w": 13},
        {"grid_h": 19, "grid_w": 21},
        {"grid_h": 11, "grid_w": 21},
        {"grid_h": 19, "grid_w": 13},
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(boundary_cases):
            grid = gen.generate(900 + index, 40 + index, difficulty=difficulty, **requested)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == requested
    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260727)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    middle = gen.generate(124, 457, difficulty="easy")
    second = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first != middle
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(123, 456, difficulty="hard") == second


def test_structural_mutations_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(copy.deepcopy(grid)), name


def test_rule_preserves_walls_and_markers_and_fills_only_zeroes():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = gen.generate(8000, sample_index, difficulty=difficulty)
            output = gen.rule_mirror(grid)
            for row in range(len(grid)):
                for col in range(len(grid[0])):
                    if grid[row][col] != 0:
                        assert output[row][col] == grid[row][col]
                    else:
                        assert output[row][col] in {6, 7, 8, 9}
