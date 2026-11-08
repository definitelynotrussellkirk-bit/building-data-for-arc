from __future__ import annotations

import copy
import random

from puzzle_generators.generic.concepts.hole_count_key import gen1


def _task():
    return gen1.generate_task(20260727, difficulty="medium")


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
    assert "task must contain 3..4 training pairs" in _messages(missing_demo)

    duplicate_input = copy.deepcopy(task)
    duplicate_input["test"][0] = copy.deepcopy(duplicate_input["train"][0])
    assert "duplicates an earlier input grid" in _messages(duplicate_input)

    wrong_output = copy.deepcopy(task)
    wrong_output["train"][0]["output"] = copy.deepcopy(
        wrong_output["train"][0]["input"]
    )
    assert "output is not exact hole-count-key recoloring" in _messages(wrong_output)

    no_unmatched = copy.deepcopy(task)
    pair = no_unmatched["train"][0]
    scene = gen1._scene_parts(pair["input"])
    keymap = gen1._keymap(scene)
    removed = 0
    for blob in scene["blobs"]:
        if blob["holes"] not in keymap:
            for r, c in blob["cells"]:
                pair["input"][r][c] = 0
            removed += 1
    assert removed
    pair["output"] = gen1._apply(pair["input"])
    assert "field is missing gray hole-count branch" in _messages(no_unmatched)

    stale_rule = copy.deepcopy(task)
    stale_rule["meta"]["rule_hash"] = "0" * 64
    assert "meta.rule_hash does not match normalized PROGRAM" in _messages(stale_rule)


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


def test_rule_hash_is_normalized_program_content():
    task = _task()
    assert task["program"] == gen1.PROGRAM
    assert task["meta"]["rule_hash"] == gen1.RULE_HASH
    assert len(gen1.RULE_HASH) == 64


def test_regression_seed_with_repeated_random_legend_order_is_now_planned():
    task = gen1.generate_task(210036, difficulty="hard")
    assert gen1.self_check_task(task) == []
    orders = [gen1._key_order_signature(p["input"]) for p in task["train"]]
    mappings = [gen1._mapping_signature(p["input"]) for p in task["train"]]
    assert len(set(orders)) >= 2
    assert len(set(mappings)) >= 2
