from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.generic.concepts.dense_field import gen3
from scripts.canonical_profile_gate import normalized_rule_hash


def _task(difficulty="medium", seed=20260815):
    return gen3.generate_task(seed, difficulty=difficulty)


def _messages(task):
    return "\n".join(gen3.self_check_task(task))


def _cyclic_windows(items, width):
    return [
        [items[(start + offset) % len(items)] for offset in range(width)]
        for start in range(len(items))
    ]


def test_generated_lessons_are_strict_identifiable_and_kill_all_rivals():
    expected_counts = {"easy": (3, 1), "medium": (3, 1), "hard": (4, 2)}
    for difficulty, (n_train, n_test) in expected_counts.items():
        for seed in range(24):
            task = gen3.generate_task(seed, difficulty=difficulty)
            assert gen3.self_check_task(task) == []
            assert len(task["train"]) == n_train
            assert len(task["test"]) == n_test

            # The contract's EXAMPLES_NEEDED is meaningful only if every
            # residue-class window of that size still identifies the query.
            for demos in _cyclic_windows(task["train"], gen3.EXAMPLES_NEEDED):
                assert len({len(pair["output"][0]) for pair in demos}) == 2
                assert len({len(pair["input"]) for pair in demos}) == 2
                for query in task["test"]:
                    assert gen3.lesson_identifiable(demos, query) == []

            for pair in task["train"] + task["test"]:
                assert gen3.strict_canonical_like(pair["input"]) == []
                assert gen3._apply(pair["input"]) == pair["output"]
                for witness in gen3.SEMANTIC_WITNESSES.values():
                    assert witness(pair["input"])
                for rival in gen3.SEMANTIC_RIVALS.values():
                    assert rival(pair["input"]) != pair["output"]


def test_self_check_rejects_targeted_impostors():
    task = _task()

    wrong_output = copy.deepcopy(task)
    wrong_output["train"][0]["output"] = copy.deepcopy(
        gen3._right_half(wrong_output["train"][0]["input"])
    )
    assert "output is not exact left-half crop" in _messages(wrong_output)

    background_hole = copy.deepcopy(task)
    background_hole["train"][0]["input"][0][0] = 0
    background_hole["train"][0]["output"] = gen3._apply(
        background_hole["train"][0]["input"]
    )
    assert "dense-field input must not contain background 0" in _messages(background_hole)

    right_echoes_left = copy.deepcopy(task)
    gin = right_echoes_left["train"][0]["input"]
    half = len(gin[0]) // 2
    for row in gin:
        row[half:] = row[:half]
    right_echoes_left["train"][0]["output"] = gen3._apply(gin)
    assert "right-half crop must disagree" in _messages(right_echoes_left)

    duplicate_query = copy.deepcopy(task)
    duplicate_query["test"][0] = copy.deepcopy(duplicate_query["train"][0])
    assert "duplicates an earlier input grid" in _messages(duplicate_query)

    stale_rule = copy.deepcopy(task)
    stale_rule["meta"]["rule_hash"] = "0" * len(gen3.RULE_HASH)
    assert "meta.rule_hash does not match RULE_HASH" in _messages(stale_rule)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen3.generate_task(91, difficulty="hard")
    assert random.getstate() == state
    second = gen3.generate_task(91, difficulty="hard")
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] % 9) + 1
    assert first != second
    assert random.getstate() == state


def test_difficulty_profiles_are_observable_disjoint_and_fully_reached():
    observed = {}
    for difficulty in ("easy", "medium", "hard"):
        dims = set()
        palettes = set()
        for seed in range(32):
            task = gen3.generate_task(seed, difficulty=difficulty)
            palettes.add(len(task["meta"]["palette"]))
            for pair in task["train"] + task["test"]:
                dims.add((len(pair["input"]), len(pair["input"][0])))
        observed[difficulty] = dims
        assert dims == set(gen3._BAND_CONFIG[difficulty]["dims"])
        assert palettes == {gen3._BAND_CONFIG[difficulty]["palette"]}

    assert observed["easy"].isdisjoint(observed["medium"])
    assert observed["easy"].isdisjoint(observed["hard"])
    assert observed["medium"].isdisjoint(observed["hard"])


def test_rule_hash_tracks_literal_program_and_bad_difficulty_is_rejected():
    task = _task()
    assert task["program"] == gen3.PROGRAM
    assert task["meta"]["rule_hash"] == gen3.RULE_HASH
    assert gen3.RULE_HASH == normalized_rule_hash(gen3.PROGRAM)
    assert len(gen3.RULE_HASH) == 12
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen3.generate_task(0, difficulty="unsupported")
