"""Focused regression tests for generator 552c2402dce3."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.552c2402dce3.generator")
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "552c2402dce3"


def _pair(grid):
    return {"input": grid, "output": gen._solve_true_local_rule(grid)}


def test_rule_hash_and_canonical_inputs_are_pinned() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._solve_true_local_rule(pair["input"]) == pair["output"]


def test_exact_axes_round_trip_and_unknown_keys_reject() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for grid_size in gen._GRID_SIZES:
            for block_count in (2, 4):
                grid = gen.generate(
                    seed=17,
                    sample_index=5,
                    difficulty=difficulty,
                    grid_size=grid_size,
                    block_count=block_count,
                )
                assert gen.observe_overrides(grid) == {
                    "grid_size": grid_size,
                    "block_count": block_count,
                }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(seed=0, sample_index=0, typo_axis=1)


def test_every_sliding_window_covers_corners_and_profiles() -> None:
    for seed in range(8):
        for start in range(12):
            grids = [gen.generate(seed, index) for index in range(start, start + 4)]
            infos = [gen._analyze(grid)[0] for grid in grids]
            assert all(info is not None for info in infos)
            assert {info["profile"] for info in infos} == set(gen.SCHEDULE_PROFILES)
            assert {
                corner
                for info in infos
                for corner in info["missing_corners"]
            } == set(gen._CORNER_NAMES)


def test_structural_self_check_rejects_targeted_impostors() -> None:
    grid = gen.generate(seed=9, sample_index=0, grid_size="8x10", block_count=3)
    h, w = len(grid), len(grid[0])

    blank = [[0] * w for _ in range(h)]
    assert gen.self_check(blank)

    contaminated = copy.deepcopy(grid)
    first = next((r, c) for r in range(h) for c in range(w) if contaminated[r][c] == 8)
    contaminated[first[0]][first[1]] = 1
    assert gen.self_check(contaminated)

    solid_only = [[0] * w for _ in range(h)]
    for r in (1, 2):
        for c in (1, 2):
            solid_only[r][c] = 8
    assert gen.self_check(solid_only)

    transformed_output = gen._solve_true_local_rule(grid)
    assert transformed_output != grid
    assert gen.self_check(transformed_output)


def test_canonical_shortcuts_need_generated_counterexamples() -> None:
    pairs = canonical_pairs(TASK_ID)
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    grids = [gen.generate(seed=3, sample_index=index) for index in range(4)]
    official = [gen._solve_true_local_rule(grid) for grid in grids]
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert any(shortcut(grid) != answer for grid, answer in zip(grids, official)), name


def test_four_demo_lessons_refute_named_query_changing_rivals() -> None:
    for seed in range(6):
        for start in range(8):
            demos = [_pair(gen.generate(seed, index)) for index in range(start, start + 4)]
            query = _pair(gen.generate(seed, start + 4))
            assert gen.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(11, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(11, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
