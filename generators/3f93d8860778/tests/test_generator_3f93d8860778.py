from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "3f93d8860778"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.extend(pair["input"] for pair in row["train"] + row["test"])
    return rows


def _pairs(grid):
    return GEN._analysis(grid)["pairs"]


def test_rule_hash_and_canonical_inputs_are_owned():
    assert GEN.RULE_HASH == "abdf780ecbe7"
    canonical = _canonical_inputs()
    assert len(canonical) == 5
    for grid in canonical:
        assert GEN.self_check(copy.deepcopy(grid)) == []
        assert GEN.strict_canonical_like(copy.deepcopy(grid)) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7},
        {"grid_h": 12},
        {"grid_w": 8},
        {"grid_w": 11},
        {"spans": 2},
        {"spans": 5},
        {"grid_h": 7, "grid_w": 8, "spans": 2},
        {"grid_h": 12, "grid_w": 11, "spans": 5},
    ],
)
def test_exact_override_boundaries_are_observable(difficulty, overrides):
    grid = GEN.generate(918273, 5, difficulty=difficulty, **overrides)
    observed = GEN.observe_overrides(grid)
    assert GEN.self_check(grid, meta={"overrides": overrides}) == []
    for key, expected in overrides.items():
        assert observed[key] == expected


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(24680)
    before = random.getstate()
    first = GEN.generate(12345, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(12345, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(333, 0, difficulty="medium")
    pair0, pair1 = _pairs(base)[:2]

    singleton = copy.deepcopy(base)
    singleton[pair0["bottom"]][pair0["column"]] = 0
    assert GEN.self_check(singleton)

    mismatch = copy.deepcopy(base)
    mismatch[pair0["bottom"]][pair0["column"]] = (
        pair0["colour"] % 9
    ) + 1
    assert GEN.self_check(mismatch)

    occupied_gap = copy.deepcopy(base)
    occupied_gap[pair0["top"] + 1][pair0["column"]] = pair0["colour"]
    assert GEN.self_check(occupied_gap)

    duplicate_colour = copy.deepcopy(base)
    duplicate_colour[pair1["top"]][pair1["column"]] = pair0["colour"]
    duplicate_colour[pair1["bottom"]][pair1["column"]] = pair0["colour"]
    assert GEN.self_check(duplicate_colour)

    no_border = copy.deepcopy(base)
    for pair in _pairs(no_border):
        if pair["top"] == 0:
            no_border[0][pair["column"]] = 0
            no_border[1][pair["column"]] = pair["colour"]
        if pair["bottom"] == len(no_border) - 1:
            no_border[-1][pair["column"]] = 0
            no_border[-2][pair["column"]] = pair["colour"]
    assert any("border-anchored" in msg for msg in GEN.self_check(no_border))


def test_semantic_witnesses_fire_in_every_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for sample_index in range(60):
            grid = GEN.generate(700000 + sample_index, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                hits[name] += int(predicate(grid))
        assert all(count > 0 for count in hits.values()), (band, hits)


def test_materialized_lesson_rebuts_declared_shortcuts():
    pairs = []
    for sample_index in range(4):
        grid = GEN.generate(8080, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
