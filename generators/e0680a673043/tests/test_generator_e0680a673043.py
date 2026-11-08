"""Focused regressions for the e0680a673043 ordinary generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root
import hashlib
import json


gen = importlib.import_module("puzzle_generators.per_puzzle.e0680a673043.generator")
ROOT = find_root(__file__)


def _canonical_rule_hash() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        row = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == gen.TASK_ID)
    return hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]


def test_rule_hash_and_canonical_pairs_match_independent_mirror():
    assert gen.RULE_HASH == _canonical_rule_hash() == "2a70169611d2"
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) >= 2
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_ordinary_draws_are_lawful_deterministic_fresh_and_rng_pure():
    random.seed(20261026)
    global_state = random.getstate()
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(40):
            grid = gen.generate(9000 + sample_index, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid)
            again = gen.generate(9000 + sample_index, sample_index, difficulty=difficulty)
            assert again == grid
            assert again is not grid
            assert all(a is not b for a, b in zip(again, grid))
    assert random.getstate() == global_state


def test_exact_override_surface_round_trips_at_boundaries():
    for requested in (
        {"grid_h": 9, "grid_w": 12, "k": 1, "cmd": 1},
        {"grid_h": 9, "grid_w": 18, "k": 3, "cmd": 4},
        {"grid_h": 14, "grid_w": 12, "k": 2, "cmd": 3},
        {"grid_h": 14, "grid_w": 18, "k": 3, "cmd": 2},
    ):
        grid = gen.generate(111, 7, difficulty="hard", **requested)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested


def test_invalid_calls_and_overrides_fail_loudly():
    for args, message in (
        ((True, 0), "seed must be a nonnegative exact integer"),
        ((0, -1), "sample_index must be a nonnegative exact integer"),
        ((0, "1"), "sample_index must be a nonnegative exact integer"),
    ):
        with pytest.raises(ValueError, match=message):
            gen.generate(*args)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="grid_h must be an integer"):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="k must be an integer"):
        gen.generate(0, 0, k="2")
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, cmd=5)
