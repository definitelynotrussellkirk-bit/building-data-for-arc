from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.generic.concepts.dense_motion import gen1


def _task(difficulty="medium"):
    return gen1.generate_task(20260729, difficulty=difficulty)


def _messages(task):
    return "\n".join(gen1.self_check_task(task))


def test_generated_lessons_are_strict_identifiable_and_kill_all_rivals():
    expected_counts = {
        "easy": (3, 1, 5, 3),
        "medium": (4, 1, 6, 3),
        "hard": (4, 2, 7, 4),
    }
    for difficulty, (n_train, n_test, n_objects, n_colors) in expected_counts.items():
        for seed in range(20):
            task = gen1.generate_task(seed, difficulty=difficulty)
            assert gen1.self_check_task(task) == []
            assert len(task["train"]) == n_train
            assert len(task["test"]) == n_test
            assert task["meta"]["object_count"] == n_objects
            assert len(task["meta"]["palette"]) == n_colors
            for query in task["test"]:
                assert gen1.lesson_identifiable(task["train"], query) == []
            for pair in task["train"] + task["test"]:
                assert gen1.strict_canonical_like(pair["input"]) == []
                assert gen1._apply(pair["input"]) == pair["output"]
                for witness in gen1.SEMANTIC_WITNESSES.values():
                    assert witness(pair["input"])
                for rival in gen1.SEMANTIC_RIVALS.values():
                    assert rival(pair["input"]) != pair["output"]


def test_self_check_rejects_targeted_impostors():
    task = _task()

    missing_demo = copy.deepcopy(task)
    missing_demo["train"].pop()
    assert "train pair count disagrees" in _messages(missing_demo)

    duplicate_query = copy.deepcopy(task)
    duplicate_query["test"][0] = copy.deepcopy(duplicate_query["train"][0])
    assert "duplicate input grid" in _messages(duplicate_query)

    no_op = copy.deepcopy(task)
    no_op["train"][0]["output"] = copy.deepcopy(no_op["train"][0]["input"])
    assert "output is not rigid whole-object gravity" in _messages(no_op)

    per_cell = copy.deepcopy(task)
    gin = per_cell["train"][0]["input"]
    per_cell["train"][0]["output"] = gen1._rival_per_cell_gravity(gin)
    assert "output is not rigid whole-object gravity" in _messages(per_cell)

    invalid_shape = copy.deepcopy(task)
    pair = invalid_shape["train"][0]
    # Add a singleton in a guaranteed blank spacer column. The Racket authority
    # can execute this recombination, but it is outside the lesson grammar.
    pair["input"][0][2] = 9 if pair["input"][0][2] != 9 else 8
    pair["output"] = gen1._apply(pair["input"])
    assert "allowed uneven-bottom shapes" in _messages(invalid_shape)

    stale_rule = copy.deepcopy(task)
    stale_rule["meta"]["rule_hash"] = "0" * 64
    assert "meta.rule_hash does not match RULE_HASH" in _messages(stale_rule)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen1.generate_task(91, difficulty="hard")
    assert random.getstate() == state
    second = gen1.generate_task(91, difficulty="hard")
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert first != second
    assert random.getstate() == state


def test_difficulty_profiles_are_observable_and_disjoint():
    seen_dims = {}
    seen_object_counts = {}
    for difficulty in ("easy", "medium", "hard"):
        dims = set()
        counts = set()
        for seed in range(20):
            task = gen1.generate_task(seed, difficulty=difficulty)
            for pair in task["train"] + task["test"]:
                grid = pair["input"]
                dims.add((len(grid), len(grid[0])))
                counts.add(len(gen1.components(grid, bg=0)))
        seen_dims[difficulty] = dims
        seen_object_counts[difficulty] = counts
    assert seen_dims["easy"].isdisjoint(seen_dims["medium"])
    assert seen_dims["easy"].isdisjoint(seen_dims["hard"])
    assert seen_dims["medium"].isdisjoint(seen_dims["hard"])
    assert seen_object_counts == {"easy": {5}, "medium": {6}, "hard": {7}}


def test_rule_hash_tracks_literal_program_and_bad_difficulty_is_rejected():
    task = _task()
    assert task["program"] == gen1.PROGRAM
    assert task["meta"]["rule_hash"] == gen1.RULE_HASH
    assert len(gen1.RULE_HASH) == 64
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen1.generate_task(0, difficulty="unsupported")
