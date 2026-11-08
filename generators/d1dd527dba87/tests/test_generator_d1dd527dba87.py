from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d1dd527dba87 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        for split in ("train", "test"):
            pairs = row.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for pair in pairs:
                yield pair["input"]


def _axis_values(name):
    spec = gen.AXES[name]
    valid = spec["valid"]
    if spec["type"] == "int":
        lo, hi = map(int, valid.split(".."))
        return [lo, hi]
    if spec["type"] == "color":
        return [int(value) for value in valid.split("|")]
    return valid.split("|")


def test_rule_hash_and_canonical_inputs_are_pinned():
    assert gen.RULE_HASH == "a9d6dd158d01"
    canonical = list(_canonical_inputs())
    assert len(canonical) == 5
    for grid in canonical:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_generation_is_deterministic_fresh_rng_pure_and_structural():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(40):
            state = random.getstate()
            first = gen.generate(9127, sample_index, difficulty=band)
            assert random.getstate() == state
            second = gen.generate(9127, sample_index, difficulty=band)
            assert first == second
            assert first is not second
            assert first[0] is not second[0]
            assert gen.self_check(first, difficulty=band) == []
            first[0][0] = 9 if first[0][0] != 9 else 0
            assert gen.generate(9127, sample_index, difficulty=band) == second


def test_every_declared_axis_is_exactly_observable_at_boundaries():
    for name in gen.AXES:
        for value in _axis_values(name):
            grid = gen.generate(44, 17, difficulty="hard", **{name: value})
            assert gen.observe_overrides(grid)[name] == value
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, misspelled_axis=1)


def test_scheduled_three_demo_lessons_are_identifiable():
    for start in range(24):
        demos = []
        for sample_index in range(start, start + 3):
            grid = gen.generate(1000 + start, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen._truth_xor(grid)})
        query_grid = gen.generate(1000 + start, start + 3, difficulty="medium")
        query = {"input": query_grid, "output": gen._truth_xor(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(207, 3, difficulty="medium", decoy_mode="both")
    analysis = gen._analysis(valid)
    assert analysis["errors"] == []

    missing_distractor = copy.deepcopy(valid)
    distractor = analysis["distractor_color"]
    for r, row in enumerate(missing_distractor):
        for c, value in enumerate(row):
            if value == distractor:
                missing_distractor[r][c] = 0
    assert any("distractor" in reason for reason in gen.self_check(missing_distractor))

    second_distractor = copy.deepcopy(valid)
    for r, row in enumerate(second_distractor):
        for c, value in enumerate(row):
            if value == 0:
                second_distractor[r][c] = 3
                break
        else:
            continue
        break
    assert any("distractor" in reason for reason in gen.self_check(second_distractor))

    identical = [[0] * 11 for _ in range(9)]
    shape = {(0, 0), (0, 1), (1, 0), (1, 1)}
    for r, c in shape:
        identical[1 + r][1 + c] = 1
        identical[5 + r][7 + c] = 2
    identical[8][10] = 5
    reasons = gen.self_check(identical)
    assert any("exclusive" in reason for reason in reasons)

    tied_blue = copy.deepcopy(valid)
    blue_main = analysis["blue_main"]
    blue_size = len(blue_main)
    free = [
        (r, c)
        for r, row in enumerate(tied_blue)
        for c, value in enumerate(row)
        if value == 0
    ]
    # A disconnected same-color component with main-sized cardinal chain is a
    # malformed largest-object tie, not a lawful teaching scene.
    placed = []
    for r, c in free:
        if all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in placed):
            placed.append((r, c))
        if len(placed) == blue_size:
            break
    for r, c in placed:
        tied_blue[r][c] = 1
    assert gen.self_check(tied_blue)


def test_declared_rival_witnesses_are_real_counterexamples():
    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for sample_index in range(120):
        grid = gen.generate(8080 + sample_index, sample_index, difficulty="hard")
        truth = gen._truth_xor(grid)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            hits[name] += 1
            for rival_name in gen.WITNESS_RIVALS[name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(count > 0 for count in hits.values()), hits
