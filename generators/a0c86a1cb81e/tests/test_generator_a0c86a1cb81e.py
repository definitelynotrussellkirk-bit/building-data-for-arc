from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.a0c86a1cb81e.generator")


def test_canonical_inputs_are_accepted_and_mirrored():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_structural_checker_rejects_targeted_impostors():
    impostors = {
        "solid_2x2": [[0, 0, 0, 0], [0, 3, 3, 0], [0, 3, 3, 0], [0, 0, 0, 0]],
        "straight_line": [[0, 0, 0, 0, 0], [0, 3, 3, 3, 0], [0, 0, 0, 0, 0]],
        "t_junction": [[0, 3, 0], [3, 3, 3], [0, 0, 0]],
        "isolated_singleton": [[0, 0, 0], [0, 3, 0], [0, 0, 0]],
        "wrong_palette": [[0, 0, 0], [0, 2, 2], [0, 2, 0]],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_exact_overrides_are_observable_across_bands():
    for band in ("easy", "medium", "hard"):
        for overrides in (
            {"grid_h": 8, "grid_w": 8, "n_paths": 1},
            {"grid_h": 14, "grid_w": 14, "n_paths": 4},
            {"grid_h": 8, "grid_w": 14, "n_paths": 4},
        ):
            grid = gen.generate(91, 7, difficulty=band, **overrides)
            assert gen.observe_overrides(grid) == overrides
            assert gen.self_check(grid) == []


def test_unknown_override_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, mystery_axis=3)


def test_ordinary_draws_refute_degree_two_and_fixed_corner_shortcuts():
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(1000 + index, index, difficulty=band)
            obs = gen.semantic_observables(grid)
            assert obs["straight_degree2_count"] >= 1
            assert obs["multi_turn_paths"] >= 1
            truth = gen.rule_mirror(grid)
            assert gen.SEMANTIC_RIVALS["recolor every degree-two green cell"](grid) != truth
            assert gen.SEMANTIC_RIVALS["recolor a fixed top-left component cell"](grid) != truth


def test_every_three_demo_sliding_window_identifies_rule():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(16):
            grid = gen.generate(4400 + index, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(12):
            assert gen.lesson_identifiable(pairs[start:start + 3], pairs[start + 3]) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(2026)
    before = random.getstate()
    first = gen.generate(123, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(123, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9
