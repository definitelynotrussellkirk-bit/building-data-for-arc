from __future__ import annotations

import copy
import random

from puzzle_generators.generic.concepts.dense_select import gen1
from puzzle_generators.generic.concepts.dense_select import py_objects


def _first_task():
    return gen1.generate_task(17, difficulty="medium")


def test_generated_lessons_are_structurally_clean_and_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            task = gen1.generate_task(seed, difficulty=band)
            assert gen1.self_check_task(task) == []
            for query in task["test"]:
                assert gen1.lesson_identifiable(task["train"], query) == []
            for pair in task["train"] + task["test"]:
                assert gen1.strict_canonical_like(pair["input"]) == []
                for witness in gen1.SEMANTIC_WITNESSES.values():
                    assert witness(pair["input"])
                for rival in gen1.LESSON_COMPETITORS.values():
                    assert rival(pair["input"]) != pair["output"]


def test_self_check_rejects_four_targeted_impostors():
    task = _first_task()

    missing_demo = copy.deepcopy(task)
    missing_demo["train"].pop()
    assert any("train pair count" in msg for msg in gen1.self_check_task(missing_demo))

    duplicate_query = copy.deepcopy(task)
    duplicate_query["test"][0]["input"] = copy.deepcopy(duplicate_query["train"][0]["input"])
    assert any("duplicate input grid" in msg for msg in gen1.self_check_task(duplicate_query))

    wrong_output = copy.deepcopy(task)
    wrong_output["train"][0]["output"] = copy.deepcopy(wrong_output["train"][0]["input"])
    assert any("output is not exact" in msg for msg in gen1.self_check_task(wrong_output))

    hidden_bbox_branch = copy.deepcopy(task)
    pair = hidden_bbox_branch["train"][0]
    bg = hidden_bbox_branch["meta"]["bg_color"]
    objs = py_objects(pair["input"], bg=bg)
    winner = max(objs, key=lambda obj: obj["size"])
    for obj in objs:
        if obj is winner:
            continue
        if gen1._bbox_area(obj) > gen1._bbox_area(winner):
            # Remove every bbox-area discriminator. Other aspects of the scene
            # remain plausible, so the checker must name the missing semantic
            # branch rather than merely accepting the recombination.
            for r, c in obj["cells"]:
                pair["input"][r][c] = bg
    pair["output"] = gen1._apply(pair["input"], bg=bg)
    assert any("larger bbox area" in msg for msg in gen1.self_check_task(hidden_bbox_branch))


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


def test_rule_hash_tracks_background_specialized_template():
    task = _first_task()
    bg = task["meta"]["bg_color"]
    assert task["program"] == gen1.RULE_TEMPLATE.format(bg=bg)
    assert task["meta"]["rule_hash"] == gen1.RULE_HASH
