from __future__ import annotations

import copy
import random
from itertools import product

import pytest

from src.core.canonical_pairs import load_task_pairs
from puzzle_generators.per_puzzle.e46763527c42 import generator as gen

TASK_ID = "e46763527c42"
EXPECTED_RULE_HASH = "3aba9759872c"


def test_rule_hash_and_all_canonical_pairs_are_grounded() -> None:
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_exact_override_combination_is_observable_in_every_band() -> None:
    for difficulty, profile, relation, overlap in product(
        ("easy", "medium", "hard"),
        gen._CANVAS_PROFILES,
        gen._CONNECTOR_RELATIONS,
        (1, 2, 3),
    ):
        requested = {
            "canvas_profile": profile,
            "connector_relation": relation,
            "overlap_cells": overlap,
        }
        for seed in (0, 17, 29):
            grid = gen.generate(
                seed,
                seed + 11,
                difficulty=difficulty,
                **requested,
            )
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis="silently ignored")


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(20260815)
    global_state = random.getstate()
    first = gen.generate(456, 7, difficulty="hard")
    assert random.getstate() == global_state
    second = gen.generate(456, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_ordinary_draws_are_strict_and_refute_every_named_rival() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = gen.generate(3000 + sample_index, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            truth = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (difficulty, sample_index, name)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, (difficulty, sample_index, name)


def test_self_check_rejects_targeted_structural_impostors() -> None:
    fixtures = gen.mutation_fixtures()
    assert {name for name, _ in fixtures} == {
        "missing_connector",
        "duplicate_connector",
        "single_component",
        "third_component",
        "clipped_overlay",
    }
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_lesson_identifiability_checks_outputs_and_shortcuts() -> None:
    grids = [gen.generate(8001, index, difficulty="medium") for index in range(3)]
    pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    assert gen.lesson_identifiable(pairs[:2], pairs[2]) == []
    assert gen.lesson_identifiable(pairs[:1], pairs[2]) == [
        "at least 2 demonstrations are required"
    ]

    wrong_query = copy.deepcopy(pairs[2])
    wrong_query["output"] = gen.SEMANTIC_RIVALS["use only the first fragment"](
        wrong_query["input"]
    )
    assert any(
        "output disagrees" in reason
        for reason in gen.lesson_identifiable(pairs[:2], wrong_query)
    )
