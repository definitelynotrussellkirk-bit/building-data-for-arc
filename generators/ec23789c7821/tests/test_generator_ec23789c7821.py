"""Focused regressions for the horizontal-three to vertical-three generator."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest

GENERATOR = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_ec23789c7821", GENERATOR)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _target_cells(grid):
    used = set()
    h, w = len(grid), len(grid[0])
    starts = 0
    for r in range(1, h - 1):
        for c in range(w - 2):
            v = grid[r][c]
            if v and grid[r][c + 1] == v and grid[r][c + 2] == v:
                starts += 1
                used.update((r, cc) for cc in range(c, c + 3))
    return starts, used


def test_rule_hash_and_validator_are_pinned():
    assert GEN.RULE_HASH == "281bfb5a3049"
    grid = GEN.generate(0, 0)
    assert GEN.self_check(grid) == []


def test_exact_dimension_endpoints_work_in_every_difficulty_band():
    for difficulty in (None, "easy", "medium", "hard"):
        small_h = GEN.generate(7, 0, difficulty=difficulty, grid_h=5, n_runs=2)
        large_h = GEN.generate(7, 1, difficulty=difficulty, grid_h=14, n_runs=2)
        small_w = GEN.generate(7, 2, difficulty=difficulty, grid_w=5, n_runs=2)
        large_w = GEN.generate(7, 3, difficulty=difficulty, grid_w=16, n_runs=2)
        assert len(small_h) == 5 and len(large_h) == 14
        assert len(small_w[0]) == 5 and len(large_w[0]) == 16
        for grid in (small_h, large_h, small_w, large_w):
            assert GEN.self_check(grid) == []


def test_ordinary_draws_teach_preservation_of_non_target_cells():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(20):
            grid = GEN.generate(seed, seed * 17 + 5, difficulty=difficulty)
            _starts, used = _target_cells(grid)
            preserved = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                         if v != 0 and (r, c) not in used}
            assert preserved, (difficulty, seed, grid)
            output = GEN.rule_mirror(grid)
            assert all(output[r][c] == grid[r][c] for r, c in preserved)
            assert GEN.self_check(grid) == []


def test_count_and_palette_controls_are_exact_and_observable():
    grid = GEN.generate(
        13, 9, grid_h=10, grid_w=13, n_runs=6,
        palette_size=5, n_distinct_colors=5,
        palette_kind="varied_palette",
    )
    observed = GEN.observe_overrides(grid)
    assert observed["n_runs"] == 6
    assert observed["palette_size"] == 5
    assert observed["n_distinct_colors"] == 5
    assert observed["palette_kind"] == "varied_palette"
    assert GEN.self_check(grid) == []


def test_literal_rule_mirror_rotates_targets_and_preserves_distractors():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 8, 0],
        [4, 0, 0, 0, 0, 8, 0],
        [0, 0, 6, 6, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert GEN.rule_mirror(grid) == [
        [0, 0, 2, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 8, 0],
        [4, 0, 2, 0, 0, 8, 0],
        [0, 0, 6, 6, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261026)
    before = random.getstate()
    first = GEN.generate(91, 23, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(91, 23, difficulty="hard")
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_invalid_or_incompatible_requests_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="palette_size.*n_distinct_colors"):
        GEN.generate(0, 0, palette_size=2, n_distinct_colors=3)
    with pytest.raises(ValueError, match="n_runs.*grid_h.*grid_w"):
        GEN.generate(0, 0, grid_h=5, grid_w=5, n_runs=8)
