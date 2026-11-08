"""Focused regressions for the odd-run midpoint base generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "generator.py"


def _load():
    spec = importlib.util.spec_from_file_location("base_2fc4ca4ea6c4", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_lengths(grid):
    lengths = []
    for row in grid:
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            color = row[c]
            start = c
            while c < len(row) and row[c] == color:
                c += 1
            lengths.append(c - start)
    return lengths


def test_declared_dimension_overrides_work_and_unknown_axes_are_rejected():
    module = _load()
    small = module.generate(42, 0, grid_h=3, grid_w=7, run_rows=1)
    large = module.generate(42, 0, grid_h=12, grid_w=16, run_rows=8)
    assert (len(small), len(small[0])) == (3, 7)
    assert (len(large), len(large[0])) == (12, 16)
    assert module.self_check(small) == []
    assert module.self_check(large) == []
    with pytest.raises(ValueError, match="unknown override"):
        module.generate(42, 0, unknown_axis=1)


def test_regular_generation_teaches_singleton_identity_and_longer_collapse():
    module = _load()
    for seed in range(16):
        grid = module.generate(seed, 0, difficulty="medium")
        lengths = _run_lengths(grid)
        assert module.self_check(grid, difficulty="medium") == []
        assert 1 in lengths, (seed, lengths)
        assert any(length > 1 for length in lengths), (seed, lengths)
        assert all(length % 2 == 1 for length in lengths)


def test_texture_and_color_count_are_real_controls():
    module = _load()
    one = module.generate(11, 2, texture="cool", n_distinct_colors=1)
    five = module.generate(11, 2, texture="warm", n_distinct_colors=5)
    one_colors = {value for row in one for value in row if value}
    five_colors = {value for row in five for value in row if value}
    assert len(one_colors) == 1
    assert len(five_colors) >= 2
    assert one != five
