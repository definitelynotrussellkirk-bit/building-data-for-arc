from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.dd09ba465298.generator")
TASK_ID = "dd09ba465298"


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_match_the_python_mirror() -> None:
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "6dce763a142e"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        observed = gen.observe_overrides(pair["input"])
        assert observed == {
            "grid_h": 9,
            "grid_w": 9,
            "n_objects": 4,
            "scene_kind": "columns",
            "palette_mode": "same_color",
            "rank_order": "scrambled",
        }


def test_every_two_example_schedule_window_refutes_every_named_competitor() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [
                _pair(gen.generate(80123 + start, start + offset, difficulty=difficulty))
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                gen.generate(
                    80123 + start,
                    start + gen.EXAMPLES_NEEDED,
                    difficulty=difficulty,
                )
            )
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert not all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                ), (difficulty, start, name)


def test_schedule_and_witnesses_cover_all_declared_semantic_branches() -> None:
    grids = [gen.generate(1776, index, difficulty="medium") for index in range(8)]
    assert [gen.schedule_profile(1776, index) for index in range(8)] == list(
        gen.SCHEDULE_PROFILES
    )
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        grid = next(
            candidate
            for candidate in grids
            if gen.SEMANTIC_WITNESSES[witness_name](candidate)
        )
        answer = gen.rule_mirror(grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != answer


def test_full_boundary_override_cartesian_product_is_exact_and_observable() -> None:
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (9, 17):
            for grid_w in (9, 17):
                for n_objects in (3, 4, 5):
                    for scene_kind in gen.SCENE_KINDS:
                        for palette_mode in gen.PALETTE_MODES:
                            for rank_order in gen.RANK_ORDERS:
                                requested = {
                                    "grid_h": grid_h,
                                    "grid_w": grid_w,
                                    "n_objects": n_objects,
                                    "scene_kind": scene_kind,
                                    "palette_mode": palette_mode,
                                    "rank_order": rank_order,
                                }
                                grid = gen.generate(
                                    910000 + case,
                                    case % 19,
                                    difficulty=difficulty,
                                    **requested,
                                )
                                assert gen.self_check(grid, difficulty=difficulty) == []
                                assert gen.observe_overrides(grid) == requested
                                case += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, misspelled_axis="accepted-is-a-bug")


def test_replay_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(20260728)
    before = random.getstate()
    first = gen.generate(123456, 789, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(123456, 789, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_mutation_fixtures_are_structurally_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name
