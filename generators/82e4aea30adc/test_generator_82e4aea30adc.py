from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.82e4aea30adc.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_solved():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_axes_round_trip_and_invalid_combination_rejects():
    for profile in ("single_only", "mixed", "multi_only"):
        minimum = 2 if profile == "mixed" else 1
        for n_frames in range(minimum, 6):
            grid = gen.generate(
                9123,
                n_frames * 10,
                difficulty="hard",
                n_frames=n_frames,
                branch_profile=profile,
            )
            assert gen.observe_overrides(grid) == {
                "n_frames": n_frames,
                "branch_profile": profile,
            }
            assert gen.self_check(grid) == []
    with pytest.raises(ValueError):
        gen.generate(1, 0, n_frames=1, branch_profile="mixed")
    with pytest.raises(ValueError):
        gen.generate(1, 0, misspelled_axis=3)


def test_three_residue_schedule_identifies_every_lesson():
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            grids = [gen.generate(314159, start + offset, difficulty=band) for offset in range(4)]
            profiles = [gen.observe_overrides(grid)["branch_profile"] for grid in grids[:3]]
            assert set(profiles) == {"single_only", "mixed", "multi_only"}
            assert gen.lesson_identifiable([_pair(grid) for grid in grids[:3]], _pair(grids[3])) == []


def test_mixed_scene_reuses_one_color_across_opposite_branches():
    grid = gen.generate(77, 1, n_frames=5, branch_profile="mixed")
    profile = gen.semantic_profile(grid)
    assert profile["branch_profile"] == "mixed"
    assert profile["same_color_cross_branch"] is True


def test_mutation_fixtures_are_rejected():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_preservation():
    random.seed(20260727)
    before = random.getstate()
    first = gen.generate(1234, 56, difficulty="medium")
    after = random.getstate()
    second = gen.generate(1234, 56, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    mutated = copy.deepcopy(first)
    mutated[0][0] = (mutated[0][0] + 1) % 10
    assert gen.generate(1234, 56, difficulty="medium") == first
