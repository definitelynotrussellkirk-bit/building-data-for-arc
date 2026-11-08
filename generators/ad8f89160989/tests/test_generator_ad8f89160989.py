"""Focused regressions for the canonical distance-one halo generator."""
from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root


def _load_generator():
    try:
        return importlib.import_module("puzzle_generators.per_puzzle.ad8f89160989.generator")
    except ModuleNotFoundError:
        path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location("_test_ad8f89160989_generator", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


gen = _load_generator()
TASK_ID = "ad8f89160989"
PALETTE = {2, 3, 4, 6, 7, 9}


def _seeds(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def test_canonical_pairs_match_independent_python_mirror() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) >= 3
    for pair in pairs:
        assert gen._solve_official(pair["input"]) == pair["output"]


def test_strict_controls_realize_each_position_profile() -> None:
    for profile in ("interior", "edge", "corner", "mixed"):
        grid = gen.generate(
            8102,
            77,
            difficulty="medium",
            grid_h=10,
            grid_w=11,
            n_seeds=4,
            position_bias=profile,
        )
        assert len(grid) == 10 and len(grid[0]) == 11
        assert len(_seeds(grid)) == 4
        assert gen.self_check(grid, difficulty="medium", meta={"position_bias": profile}) == []
        assert gen.observe_profile(grid) == profile


def test_seed_domain_is_distinct_spaced_and_color_eight_free() -> None:
    for seed in range(30):
        for difficulty in (None, "easy", "medium", "hard"):
            grid = gen.generate(seed, seed + 300, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == []
            seeds = _seeds(grid)
            assert {value for _, _, value in seeds} <= PALETTE
            assert len({value for _, _, value in seeds}) == len(seeds)
            assert all(value != 8 for _, _, value in seeds)
            for i, (r, c, _) in enumerate(seeds):
                for rr, cc, _ in seeds[:i]:
                    assert abs(r - rr) + abs(c - cc) >= 3


def test_declared_global_override_ranges_are_honored() -> None:
    for difficulty in (None, "easy", "medium", "hard"):
        small = gen.generate(9001, 1, difficulty=difficulty, grid_h=5, grid_w=6, n_seeds=1, position_bias="corner")
        large = gen.generate(9002, 2, difficulty=difficulty, grid_h=14, grid_w=13, n_seeds=1, position_bias="interior")
        assert (len(small), len(small[0]), len(_seeds(small))) == (5, 6, 1)
        assert (len(large), len(large[0]), len(_seeds(large))) == (14, 13, 1)
        assert gen.observe_profile(small) == "corner"
        assert gen.observe_profile(large) == "interior"


def test_unknown_and_coercing_overrides_are_rejected() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, typo_count=3)
    for value in (True, 8.0, "8"):
        with pytest.raises((TypeError, ValueError), match="grid_h"):
            gen.generate(1, 2, grid_h=value)
    with pytest.raises(ValueError, match="position_bias"):
        gen.generate(1, 2, position_bias="centerish")


def test_self_check_rejects_structural_impostors() -> None:
    valid = gen.generate(42, 9, grid_h=9, grid_w=9, n_seeds=3, position_bias="interior")

    with_eight = copy.deepcopy(valid)
    with_eight[0][0] = 8
    assert any("color 8" in error for error in gen.self_check(with_eight))

    repeated = copy.deepcopy(valid)
    seeds = _seeds(repeated)
    repeated[seeds[1][0]][seeds[1][1]] = seeds[0][2]
    assert any("distinct" in error for error in gen.self_check(repeated))

    too_close = [[0] * 7 for _ in range(7)]
    too_close[3][2] = 2
    too_close[3][4] = 3
    assert any("distance" in error for error in gen.self_check(too_close))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert any("rectangular" in error for error in gen.self_check(ragged))


def test_self_check_enforces_declared_dimension_limits() -> None:
    too_tall = [[0] * 14 for _ in range(15)]
    too_tall[7][7] = 2
    too_wide = [[0] * 15 for _ in range(14)]
    too_wide[7][7] = 2
    assert any("5..14" in error for error in gen.self_check(too_tall))
    assert any("5..14" in error for error in gen.self_check(too_wide))


def test_generation_is_deterministic_fresh_and_rng_pure() -> None:
    before = random.getstate()
    first = gen.generate(123456, 51, difficulty="medium")
    after = random.getstate()
    second = gen.generate(123456, 51, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
