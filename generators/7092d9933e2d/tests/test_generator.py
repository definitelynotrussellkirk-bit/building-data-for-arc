"""Focused regressions for the row-first-fill base generator."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]


def _load():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("row_first_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()
PAIRS = canonical_pairs("7092d9933e2d", root=find_root(__file__))


def oracle(grid):
    result = []
    for row in grid:
        colors = [value for value in row if value != 0]
        result.append(([colors[0]] * len(row)) if colors else ([0] * len(row)))
    return result


def active_rows(grid):
    return [row for row in grid if any(value != 0 for value in row)]


def test_declares_only_exact_observable_controls():
    assert set(gen.AXES) == {
        "grid_h", "grid_w", "palette_kind", "active_rows", "seeds_per_row"
    }
    assert tuple(gen.PALETTE_KINDS) == ("warm", "cool", "broad", "primary")


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_valid_and_match_row_first_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_and_deterministic(difficulty):
    kwargs = dict(grid_h=10, grid_w=12, palette_kind="warm", active_rows=5, seeds_per_row=3)
    grid = gen.generate(7092, 4, difficulty=difficulty, **kwargs)
    assert grid == gen.generate(7092, 4, difficulty=difficulty, **kwargs)
    assert (len(grid), len(grid[0])) == (10, 12)
    rows = active_rows(grid)
    assert len(rows) == 5
    assert all(sum(value != 0 for value in row) == 3 for row in rows)
    assert all(value in gen.PALETTES["warm"] for row in rows for value in row if value)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"grid_h": True},
        {"grid_h": 5},
        {"grid_w": 15},
        {"palette_kind": "infrared"},
        {"active_rows": 1},
        {"active_rows": 6},
        {"seeds_per_row": 0},
        {"seeds_per_row": 5},
    ],
)
def test_rejects_unknown_or_invalid_overrides(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_ordinary_draws_have_blank_rows_multiple_active_rows_and_content_spread():
    seen = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(1000 + index, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            rows = active_rows(grid)
            assert 2 <= len(rows) <= 5
            assert len(rows) < len(grid)
            assert 1 <= min(sum(v != 0 for v in row) for row in rows) <= 4
            assert oracle(grid)
            seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) > 140


def test_self_check_rejects_malformed_and_ruleless_inputs():
    bad = [None, [], [[]], [[0], [0, 0]], [[True] * 7 for _ in range(6)], [[0] * 7 for _ in range(6)]]
    for grid in bad:
        assert gen.self_check(grid)
