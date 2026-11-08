from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("_b9ada70e7181_generator_test", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _nonpalindromic_stacks(grid):
    stacks = []
    for column in range(len(grid[0])):
        values = [row[column] for row in grid if row[column] not in (0, 8)]
        if len(values) >= 2 and values != list(reversed(values)):
            stacks.append((column, values))
    return stacks


def test_repaired_old_ambiguous_lesson_has_order_witness_in_every_demo():
    generator = _load_generator()
    for sample_index in (36, 37, 38):
        grid = generator.generate(222, sample_index, difficulty="medium")
        assert _nonpalindromic_stacks(grid), sample_index


def test_ordinary_draws_always_expose_stable_within_column_order():
    generator = _load_generator()
    for seed in range(16):
        for sample_index in range(8):
            grid = generator.generate(seed, sample_index, difficulty=None)
            assert generator.self_check(grid) == []
            assert _nonpalindromic_stacks(grid), (seed, sample_index)


def test_self_check_rejects_palindromic_only_order_evidence():
    generator = _load_generator()
    grid = [[0] * 10 for _ in range(7)]
    for row in range(7):
        grid[row][2] = 8
        grid[row][6] = 8
    # Three legal chambers, but every repeated stack is palindromic.
    grid[0][0] = grid[2][0] = 4
    grid[1][4] = grid[3][4] = 5
    grid[0][8] = grid[4][8] = 6
    errors = generator.self_check(grid)
    assert any("non-palindromic" in error for error in errors)


def test_dimension_overrides_remain_exact_after_order_repair():
    generator = _load_generator()
    for height, width in ((6, 9), (12, 16)):
        grid = generator.generate(7, height * 100 + width, grid_h=height, grid_w=width)
        assert (len(grid), len(grid[0])) == (height, width)
        assert generator.self_check(grid) == []
