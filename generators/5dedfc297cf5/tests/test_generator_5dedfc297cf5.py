from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.5dedfc297cf5.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise AssertionError("canonical task row not found")


def test_canonical_inputs_are_owned_and_exact_linked_profiles():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_declared_dimension_overrides_honor_global_boundaries_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for height, width in ((12, 12), (12, 30), (30, 12), (30, 30)):
            grid = gen.generate(
                701,
                1,
                difficulty=difficulty,
                grid_h=height,
                grid_w=width,
            )
            assert gen.observe_overrides(grid) == {"grid_h": height, "grid_w": width}
            assert gen.self_check(grid) == []
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 1, difficulty="easy", misspelled_axis=12)


def test_five_sample_sliding_lessons_refute_every_named_competitor():
    for start in range(10):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(991, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        demos, query = pairs[:-1], pairs[-1]
        assert gen.lesson_identifiable(demos, query) == []
        assert {gen.schedule_profile(991, start + i) for i in range(gen.EXAMPLES_NEEDED)} == set(gen.SCHEDULE_PROFILES)


def test_self_check_rejects_targeted_rule_hiding_mutations():
    all_background = [[0] * 12 for _ in range(12)]
    assert gen.self_check(all_background)

    tied = [[0] * 12 for _ in range(12)]
    frame = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))
    for r, c in frame:
        tied[1 + r][1 + c] = 2
        tied[7 + r][7 + c] = 3
    assert any("unique" in message for message in gen.self_check(tied))

    grid = gen.generate(31337, 1, difficulty="medium")
    largest = gen._largest_object(grid)
    r0, c0, r1, c1 = largest["bbox"]

    solid = copy.deepcopy(grid)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            solid[r][c] = largest["color"]
    assert any("solid bboxes" in message for message in gen.self_check(solid))

    invaded = copy.deepcopy(grid)
    hole = next(
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if invaded[r][c] == 0
    )
    invaded[hole[0]][hole[1]] = next(color for color in range(1, 10) if color != largest["color"])
    assert any("inside" in message for message in gen.self_check(invaded))

    one_colour = [[0] * 12 for _ in range(12)]
    for r, c in frame:
        one_colour[1 + r][1 + c] = 4
    one_colour[9][1] = 4
    assert any("two foreground" in message for message in gen.self_check(one_colour))


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    state_before = random.getstate()
    first = gen.generate(44, 7, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(44, 7, difficulty="hard")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    third = gen.generate(44, 7, difficulty="hard")
    assert third == second
