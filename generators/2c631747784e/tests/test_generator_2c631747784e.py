from __future__ import annotations

import copy
import random

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.2c631747784e.generator")
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_inputs_are_accepted() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_are_observable() -> None:
    cases = [
        {"grid_h": 8, "grid_w": 8, "path_length": 32, "n_distinct_colors": 7, "anchor_corner": True},
        {"grid_h": 16, "grid_w": 16, "path_length": 8, "n_distinct_colors": 2, "anchor_corner": False},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(100 + index, index, difficulty="easy", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        observed = gen.observe_overrides(grid)
        assert observed == overrides


def test_unknown_override_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


def test_generated_draws_refute_all_declared_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            grid = gen.generate(1000 + index, index, difficulty=band)
            expected = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            for rival in gen.SEMANTIC_RIVALS.values():
                assert rival(grid) != expected
            for witness in gen.SEMANTIC_WITNESSES.values():
                assert witness(grid)


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(77, 3, difficulty="medium")

    no_path = [[8 for _ in row] for row in valid]
    assert gen.self_check(no_path)

    disconnected = copy.deepcopy(valid)
    info = gen._analyze(disconnected)
    r, c = info["path"][len(info["path"]) // 2]
    disconnected[r][c] = 8
    assert gen.self_check(disconnected)

    branched = copy.deepcopy(valid)
    info = gen._analyze(branched)
    branch_added = False
    occupied = set(info["path"])
    for r, c in info["path"][2:-2]:
        for dr, dc in gen._DIRS:
            cell = (r + dr, c + dc)
            if not (0 <= cell[0] < len(branched) and 0 <= cell[1] < len(branched[0])):
                continue
            if cell in occupied:
                continue
            branched[cell[0]][cell[1]] = 3
            if gen.self_check(branched):
                branch_added = True
                break
            branched[cell[0]][cell[1]] = 8
        if branch_added:
            break
    assert branch_added

    palindromic = copy.deepcopy(valid)
    info = gen._analyze(palindromic)
    half = [1 + (i % 3) for i in range((len(info["path"]) + 1) // 2)]
    sequence = half + list(reversed(half[: len(info["path"]) // 2]))
    for (r, c), color in zip(info["path"], sequence):
        palindromic[r][c] = color
    assert any("palindromic" in message for message in gen.self_check(palindromic))


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(987654321)
    before = random.getstate()
    first = gen.generate(91, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(91, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 99
    assert second[0][0] != 99
