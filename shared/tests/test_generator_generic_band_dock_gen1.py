from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.generic.concepts.band_dock import gen1


def _task(difficulty="medium"):
    return gen1.generate_task(20260727, difficulty=difficulty)


def _messages(task):
    return "\n".join(gen1.self_check_task(task))


def test_generated_lessons_are_structural_identifiable_and_rival_killing():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(15):
            task = gen1.generate_task(seed, difficulty=difficulty)
            assert gen1.self_check_task(task) == []
            for query in task["test"]:
                assert gen1.lesson_identifiable(task["train"], query) == []
            for pair in task["train"] + task["test"]:
                assert gen1.strict_canonical_like(pair["input"]) == []
                for witness in gen1.SEMANTIC_WITNESSES.values():
                    assert witness(pair["input"])
                for rival in gen1.SEMANTIC_RIVALS.values():
                    assert rival(pair["input"]) != pair["output"]


def test_self_check_rejects_targeted_impostors():
    task = _task()

    missing_demo = copy.deepcopy(task)
    missing_demo["train"].pop()
    assert "task must contain exactly 3 training pairs" in _messages(missing_demo)

    duplicate_input = copy.deepcopy(task)
    duplicate_input["test"][0] = copy.deepcopy(duplicate_input["train"][0])
    assert "duplicates an earlier input" in _messages(duplicate_input)

    filled_decoys = copy.deepcopy(task)
    pair = filled_decoys["train"][0]
    desc = gen1._band_descriptor(pair["input"])
    output = gen1._apply(pair["input"])
    r1, c1, r2, c2 = desc["bbox"]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if output[r][c] == 0:
                pair["input"][r][c] = desc["band_color"]
    pair["output"] = gen1._apply(pair["input"])
    assert "expected 1..2 surviving decoy notches, found 0" in _messages(filled_decoys)

    one_loose_piece = copy.deepcopy(task)
    pair = one_loose_piece["train"][0]
    desc = gen1._band_descriptor(pair["input"])
    loose = [
        comp for index, comp in enumerate(desc["components"])
        if index != desc["band_index"]
    ]
    for comp in loose[1:]:
        for r, c in comp:
            pair["input"][r][c] = 0
    pair["output"] = gen1._apply(pair["input"])
    assert "expected 2..6 loose pieces, found 1" in _messages(one_loose_piece)

    wrong_output = copy.deepcopy(task)
    pair = wrong_output["train"][0]
    pair["output"][0][0] = (pair["output"][0][0] + 1) % 10
    assert "output disagrees with the selected rule" in _messages(wrong_output)

    stale_rule = copy.deepcopy(task)
    stale_rule["meta"]["rule_hash"] = "0" * 64
    assert "task meta.rule_hash is stale" in _messages(stale_rule)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen1.generate_task(91, difficulty="hard")
    assert random.getstate() == state
    second = gen1.generate_task(91, difficulty="hard")
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = (
        first["train"][0]["input"][0][0] + 1
    ) % 10
    assert first != second
    assert random.getstate() == state


def test_difficulty_bands_are_arc_legal_observable_and_disjoint():
    expected = {
        "easy": (24, 25),
        "medium": (26, 27),
        "hard": (28, 30),
    }
    seen_sizes = {}
    for difficulty, (lo, hi) in expected.items():
        sizes = set()
        for seed in range(20):
            task = gen1.generate_task(seed, difficulty=difficulty)
            for pair in task["train"] + task["test"]:
                h, w = len(pair["input"]), len(pair["input"][0])
                assert lo <= h <= hi <= 30
                assert lo <= w <= hi <= 30
                sizes.add((h, w))
        seen_sizes[difficulty] = sizes
    assert seen_sizes["easy"].isdisjoint(seen_sizes["medium"])
    assert seen_sizes["easy"].isdisjoint(seen_sizes["hard"])
    assert seen_sizes["medium"].isdisjoint(seen_sizes["hard"])


def test_rule_hash_is_normalized_program_content_and_bad_difficulty_rejected():
    task = _task()
    assert task["program"] == gen1.PROGRAM
    assert task["meta"]["rule_hash"] == gen1.RULE_HASH
    assert len(gen1.RULE_HASH) == 64
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen1.generate_task(0, difficulty="unsupported")
