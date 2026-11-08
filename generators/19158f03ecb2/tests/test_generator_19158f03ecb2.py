from __future__ import annotations

import copy
import importlib
import random


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.19158f03ecb2.generator"
)


def test_default_lesson_schedules_disambiguate_duplication():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(9101, i, difficulty=difficulty) for i in range(5)]
        observed = [MODULE.observe_overrides(grid)["lr_asymmetric"] for grid in grids]
        assert observed == [True, True, True, False, False]
        for grid in grids[:3]:
            mirrored = [row + list(reversed(row)) for row in grid]
            duplicated = [row + row for row in grid]
            assert mirrored != duplicated
        # Both supported episode shapes end with a symmetric query.
        for query in (grids[3], grids[4]):
            assert [row + list(reversed(row)) for row in query] == [row + row for row in query]


def test_exact_axis_overrides_are_observed():
    cases = [
        dict(grid_h=3, grid_w=3, palette_size=2, lr_asymmetric=True),
        dict(grid_h=15, grid_w=15, palette_size=10, lr_asymmetric=True),
        dict(grid_h=5, grid_w=5, palette_size=10, lr_asymmetric=False),
    ]
    for i, overrides in enumerate(cases):
        grid = MODULE.generate(9200 + i, i, difficulty="easy", **overrides)
        observed = MODULE.observe_overrides(grid)
        for key, value in overrides.items():
            assert observed[key] == value


def test_incompatible_symmetric_palette_rejects_loudly():
    try:
        MODULE.generate(
            9300,
            0,
            grid_h=3,
            grid_w=4,
            palette_size=10,
            lr_asymmetric=False,
        )
    except ValueError as exc:
        assert "palette" in str(exc) or "dimensions" in str(exc)
    else:
        raise AssertionError("incompatible exact overrides must reject")


def test_determinism_fresh_returns_and_global_rng_purity():
    state = random.getstate()
    first = MODULE.generate(9400, 4, difficulty="medium")
    second = MODULE.generate(9400, 4, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == MODULE.generate(9400, 4, difficulty="medium")
    assert random.getstate() == state


def test_self_check_accepts_canonical_and_rejects_shortcuts():
    canonical = [
        [[1, 1, 1], [8, 1, 6], [6, 8, 8]],
        [[6, 8, 6], [8, 6, 8], [1, 6, 1]],
    ]
    assert all(not MODULE.self_check(copy.deepcopy(grid)) for grid in canonical)
    for _, grid in MODULE.mutation_fixtures():
        assert MODULE.self_check(grid)
