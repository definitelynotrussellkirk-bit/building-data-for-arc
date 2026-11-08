from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.64bd7bc767bb.generator"
)
ROOT = find_root(__file__)


def _canonical_rows():
    with canonical_path(ROOT).open() as handle:
        return [
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == "64bd7bc767bb"
        ]


def test_rule_hash_and_active_rule_contract():
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == "47689caca367"
    assert "Count colors 1..4 independently" in gen.SUMMARY
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "count_distribution",
        "count_max_kind",
        "distractor_count",
    }


def test_canonical_inputs_are_owned_and_mirror_all_official_outputs():
    rows = _canonical_rows()
    assert len(rows) == 2
    pairs = [pair for row in rows for split in ("train", "test") for pair in row[split]]
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_are_observable():
    cases = [
        dict(
            grid_h=5,
            grid_w=4,
            count_distribution="ascending",
            count_max_kind="full",
            distractor_count=3,
        ),
        dict(
            grid_h=14,
            grid_w=18,
            count_distribution="wide_spread",
            count_max_kind="capped",
            distractor_count=0,
        ),
        dict(
            grid_h=18,
            grid_w=4,
            count_distribution="shuffled",
            count_max_kind="full",
            distractor_count=2,
        ),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, 70 + index, difficulty="hard", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_incompatible_override_combination_rejects_loudly():
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(
            1,
            1,
            grid_h=5,
            count_distribution="wide_spread",
            count_max_kind="capped",
        )


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(44, 1, difficulty="medium")
    assert gen.self_check(base) == []

    missing = copy.deepcopy(base)
    for row in missing:
        for c, value in enumerate(row):
            if value == 1:
                row[c] = 0
    assert any("missing counted color 1" in error for error in gen.self_check(missing))

    overflowing = [[0 for _ in row] for row in base]
    for color in (1, 2, 3, 4):
        for r in range(len(overflowing)):
            overflowing[r][color - 1] = color
    assert any("must be below height" in error for error in gen.self_check(overflowing))

    equal = [[0 for _ in row] for row in base]
    for color in (1, 2, 3, 4):
        equal[color - 1][color - 1] = color
    assert any("equal totals" in error for error in gen.self_check(equal))

    too_many_distractors = copy.deepcopy(base)
    zeros = [(r, c) for r, row in enumerate(too_many_distractors) for c, value in enumerate(row) if value == 0]
    for index, (r, c) in enumerate(zeros[:4]):
        too_many_distractors[r][c] = 5 + index
    assert any("exceeds the teaching limit" in error for error in gen.self_check(too_many_distractors))

    bad_palette = copy.deepcopy(base)
    bad_palette[0][0] = 10
    assert any("out-of-palette" in error for error in gen.self_check(bad_palette))


def test_default_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(1837)
    state = random.getstate()
    first = gen.generate(123456, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123456, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    third = gen.generate(123456, 7, difficulty="hard")
    assert third == second


def test_sequential_lesson_refutes_named_competitors():
    seed = 777
    pairs = []
    for sample_index in range(5):
        inp = gen.generate(seed, sample_index)
        pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
    assert any(
        any(5 <= value <= 9 for row in demo["input"] for value in row)
        for demo in pairs[:4]
    )
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
