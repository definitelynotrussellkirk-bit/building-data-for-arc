from __future__ import annotations

import copy
import importlib
import json
import random

gen = importlib.import_module("puzzle_generators.per_puzzle.1e74f9aa9324.generator")


def _canonical_record():
    with open("data/canonical/puzzles.jsonl", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical record not found")


def test_canonical_inputs_are_accepted_and_match_rule_mirror():
    record = _canonical_record()
    pairs = record["train"] + record["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_override_boundaries_are_exact_and_observable():
    for difficulty in ("easy", "medium", "hard"):
        for height in (5, 30):
            for width in (5, 30):
                for texture in gen.HELPFUL_TEXTURES:
                    grid = gen.generate(
                        11,
                        7,
                        difficulty=difficulty,
                        grid_h=height,
                        grid_w=width,
                        texture=texture,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "texture": texture,
                    }


def test_four_slot_schedule_anchors_canonical_and_covers_distractors():
    textures = []
    for sample_index in range(4):
        grid = gen.generate(1234, sample_index, difficulty="hard")
        facts = gen.observe_overrides(grid)
        textures.append(facts["texture"])
        assert set(row[0] for row in grid) == {0, 2, 3, 4, 8}
        assert gen.self_check(grid) == []
    assert textures == ["no_decoys", "one_per_row", "two_per_row", "one_per_row"]
    canonical = gen.generate(1234, 0, difficulty="hard")
    assert (len(canonical), len(canonical[0])) == (10, 10)
    assert gen.strict_canonical_like(canonical) == []


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(5, 1, difficulty="medium", texture="one_per_row")

    missing_branch = copy.deepcopy(base)
    for row in missing_branch:
        if row[0] == 8:
            row[0] = 2
    assert any("omits required" in error for error in gen.self_check(missing_branch))

    unsupported_code = copy.deepcopy(base)
    unsupported_code[0][0] = 1
    assert any("unsupported code" in error for error in gen.self_check(unsupported_code))

    answer_leakage = copy.deepcopy(base)
    row_index = next(index for index, row in enumerate(answer_leakage) if row[0] == 3)
    answer_leakage[row_index][4] = 3
    assert any("destination cells must be blank" in error for error in gen.self_check(answer_leakage))

    mixed_texture = copy.deepcopy(base)
    row = mixed_texture[0]
    occupied = {index for index, value in enumerate(row[1:], 1) if value}
    target = gen._target_column(row[0])
    extra = next(index for index in range(1, len(row)) if index not in occupied and index != target)
    row[extra] = 9
    assert any("shared distractor count" in error for error in gen.self_check(mixed_texture))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(98765)
    before = random.getstate()
    first = gen.generate(77, 2, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(77, 2, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert gen.generate(77, 2, difficulty="hard") == second


def test_lesson_schedule_is_identifiable_against_named_rivals():
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(2026, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_rule_hash_matches_canonical_authority():
    assert gen.RULE_HASH == "d37150574f6e"
