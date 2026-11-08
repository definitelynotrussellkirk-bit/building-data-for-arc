from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d48ec0001283 import generator as gen


ROOT = Path(__file__).resolve().parents[3]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _pair(index: int, seed: int = 20260726) -> dict:
    grid = gen.generate(seed, index, difficulty="medium")
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH
    pairs = row["train"] + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_four_sample_schedule_is_identifiable_and_contains_controls() -> None:
    demos = [_pair(index) for index in range(3)]
    query = _pair(3)
    assert gen.lesson_identifiable(demos, query) == []
    assert gen.observe_overrides(demos[1]["input"])["distractor_mode"] == "both_controls"
    assert gen.observe_overrides(demos[2]["input"])["distractor_mode"] == "both_controls"
    assert gen.strict_canonical_like(demos[0]["input"]) == []
    assert gen.strict_canonical_like(query["input"]) == []


def test_all_declared_overrides_are_exactly_observable() -> None:
    cases = [
        {"grid_h": 5, "grid_w": 6, "span_count": 2, "gap_profile": "compact",
         "edge_profile": "interior", "color_mode": "distinct", "distractor_mode": "none"},
        {"grid_h": 8, "grid_w": 10, "span_count": 3, "gap_profile": "mixed",
         "edge_profile": "both", "color_mode": "reused", "distractor_mode": "both_controls"},
        {"grid_h": 12, "grid_w": 14, "span_count": 3, "gap_profile": "wide",
         "edge_profile": "right", "color_mode": "distinct", "distractor_mode": "mixed_endpoints"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(99, index, difficulty="easy", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_self_check_rejects_rule_hiding_mutations() -> None:
    valid = gen.generate(
        123,
        5,
        grid_h=8,
        grid_w=10,
        span_count=3,
        gap_profile="mixed",
        edge_profile="both",
        color_mode="distinct",
        distractor_mode="both_controls",
    )
    assert gen.self_check(valid) == []

    one_span = [[0] * 8 for _ in range(5)]
    one_span[2][1] = one_span[2][6] = 4
    assert gen.self_check(one_span)

    adjacent = deepcopy(valid)
    info = gen._analyze(adjacent)
    span = info["active_spans"][0]
    adjacent[span["row"]] = [0] * len(adjacent[0])
    adjacent[span["row"]][2] = adjacent[span["row"]][3] = span["color"]
    assert gen.self_check(adjacent)

    third_distractor = deepcopy(valid)
    blank_row = next(row for row in range(len(valid)) if not any(valid[row]))
    third_distractor[blank_row][0] = 1
    third_distractor[blank_row][-1] = 2
    assert gen.self_check(third_distractor)

    malformed = deepcopy(valid)
    malformed[0][0] = 10
    assert gen.self_check(malformed)


def test_generation_is_deterministic_and_does_not_touch_global_rng() -> None:
    random.seed(314159)
    expected = random.getstate()
    first = gen.generate(77, 11, difficulty="hard")
    assert random.getstate() == expected
    second = gen.generate(77, 11, difficulty="hard")
    assert first == second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(77, 11, difficulty="hard") == second


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    with pytest.raises(TypeError):
        gen.generate(1, 0, typo_axis="x")
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h="5")
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="impossible")
