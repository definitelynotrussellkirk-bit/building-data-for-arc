"""Focused regressions for the normalized-shape intersection base generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "generator.py"


def _load():
    spec = importlib.util.spec_from_file_location("base_c878420172c2", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _connected(cells):
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if p in cells and p not in seen:
                seen.add(p)
                stack.append(p)
    return seen == cells


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def test_declared_dimension_and_shape_size_overrides_work():
    module = _load()
    small = module.generate(7, 0, grid_h=7, grid_w=8, n_shape=2)
    large = module.generate(7, 0, grid_h=14, grid_w=16, n_shape=6)
    assert (len(small), len(small[0])) == (7, 8)
    assert (len(large), len(large[0])) == (14, 16)
    assert len(_cells(small, 2)) == len(_cells(small, 3)) == 2
    assert len(_cells(large, 2)) == len(_cells(large, 3)) == 6
    assert module.self_check(small) == []
    assert module.self_check(large) == []
    with pytest.raises(ValueError, match="unknown override"):
        module.generate(7, 0, unknown_axis=1)


def test_regular_shapes_are_connected_distinct_and_overlap_after_normalization():
    module = _load()
    for seed in range(32):
        grid = module.generate(seed, 0, difficulty="medium")
        twos, threes = _cells(grid, 2), _cells(grid, 3)
        assert module.self_check(grid, difficulty="medium") == []
        assert _connected(twos) and _connected(threes)
        n2, n3 = _normalize(twos), _normalize(threes)
        assert n2 != n3
        assert n2 & n3


def test_self_check_rejects_disconnected_color_blob():
    module = _load()
    grid = [[0] * 8 for _ in range(7)]
    grid[0][0] = grid[2][0] = 2
    grid[4][4] = grid[4][5] = 3
    messages = module.self_check(grid)
    assert any("color-2" in message and "connected" in message for message in messages)


def test_self_check_rejects_identical_normalized_shapes():
    module = _load()
    grid = [[0] * 10 for _ in range(9)]
    for row, column in ((0, 0), (0, 1), (1, 0), (1, 1)):
        grid[1 + row][1 + column] = 2
        grid[5 + row][6 + column] = 3
    messages = module.self_check(grid)
    assert any("identical" in message for message in messages)
