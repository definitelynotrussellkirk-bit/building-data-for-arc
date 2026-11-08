"""Focused generator contract for 69927005ac25."""
from __future__ import annotations

from collections import Counter
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_69927005ac25", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)


def _oracle(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dc in (2, -2):
                nr, nc = r + 2, c + dc
                mr, mc = r + 1, c + dc // 2
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == value and out[mr][mc] == 0:
                    out[mr][mc] = value
    return out


def _ordinary_facts(grid):
    counts = Counter(value for row in grid for value in row if value)
    return len(grid), len(grid[0]), len(counts), tuple(sorted(counts.values()))


@pytest.mark.parametrize("pair", _pairs(), ids=lambda pair: pair.get("split", "canonical"))
def test_canonical_examples_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_size_and_pair_controls_are_honored(difficulty):
    overrides = {
        "grid_h": 12,
        "grid_w": 14,
        "n_pairs": 4,
        "palette_size": 4,
        "n_distinct_colors": 4,
        "palette_kind": "warm",
        "position_bias": "diagonal_distance_2_pairs",
        "density": "sparse",
    }
    grid = gen.generate(17, 5, difficulty=difficulty, **overrides)
    assert _ordinary_facts(grid) == (12, 14, 4, (2, 2, 2, 2))
    assert gen.observe_overrides(grid)["n_pairs"] == 4
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("n_pairs", [1, 2, 3, 4])
def test_requested_pair_count_is_never_silently_dropped(n_pairs):
    for seed in range(25):
        grid = gen.generate(seed, 7, grid_h=5, grid_w=6, n_pairs=n_pairs,
                            palette_size=n_pairs, n_distinct_colors=n_pairs)
        facts = _ordinary_facts(grid)
        assert facts[2:] == (n_pairs, (2,) * n_pairs)
        assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"grid_h": 4},
        {"grid_w": 15},
        {"n_pairs": 0},
        {"n_pairs": True},
        {"palette_kind": "unknown"},
        {"position_bias": "random"},
        {"density": "dense"},
        {"n_pairs": 3, "palette_size": 2},
        {"n_pairs": 2, "n_distinct_colors": 3},
        {"palette_size": 2, "n_distinct_colors": 3},
    ],
)
def test_invalid_or_incompatible_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_generation_is_deterministic_and_medium_is_supported():
    kwargs = dict(grid_h=10, grid_w=11, n_pairs=3, palette_size=3,
                  n_distinct_colors=3, palette_kind="cool")
    left = gen.generate(812, 19, difficulty="medium", **kwargs)
    right = gen.generate(812, 19, difficulty="medium", **kwargs)
    assert left == right
    assert gen.self_check(left) == []


@pytest.mark.parametrize("texture", ["no_pairs", "midpoint_filled", "axis_aligned"])
def test_declared_degenerate_textures_remain_valid(texture):
    grid = gen.generate(0, 0, texture=texture)
    assert gen.self_check(grid) == []
