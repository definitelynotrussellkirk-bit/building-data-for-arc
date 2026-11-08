"""Constructive sampling and exact-override regressions for 22398bb29643."""
from __future__ import annotations

import importlib
import random

import pytest


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.22398bb29643.generator"
)
BANDS = ("easy", "medium", "hard")
CANONICAL_PROFILES = {
    (10, 10, 6),
    (9, 9, 4),
    (9, 10, 4),
    (9, 12, 6),
    (9, 11, 4),
}


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def test_only_observable_exact_axes_are_advertised():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "components"}
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_default_schedule_covers_every_canonical_profile_in_every_band():
    for band in BANDS:
        seen = set()
        for sample_index in range(10):
            grid = GEN.generate(0, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            seen.add(_profile(grid))
            facts = GEN.observe_overrides(grid)
            assert facts["grid_h"] == len(grid)
            assert facts["grid_w"] == len(grid[0])
            assert facts["components"] == len(GEN._components(grid))
            assert 3 <= facts["components"] <= 6
            assert all(3 <= len(component) <= 5 for component in GEN._components(grid))
        assert CANONICAL_PROFILES <= seen


@pytest.mark.parametrize(
    "height,width,components",
    [(9, 9, 6), (9, 14, 3), (12, 9, 6), (12, 14, 3), (11, 13, 5)],
)
def test_override_boundaries_are_exact_and_band_independent(height, width, components):
    for band in BANDS:
        grid = GEN.generate(
            19,
            7,
            difficulty=band,
            grid_h=height,
            grid_w=width,
            components=components,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": height,
            "grid_w": width,
            "components": components,
        }


def test_unknown_and_invalid_scalar_controls_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)

    for bad in (True, 9.0, "9"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, grid_h=bad)
    for bad in (8, 13):
        with pytest.raises(ValueError):
            GEN.generate(0, 0, grid_h=bad)
    for bad in (2, 7):
        with pytest.raises(ValueError):
            GEN.generate(0, 0, components=bad)

    for bad_seed in (None, True, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(bad_seed, 0)
    for bad_index in (-1, True, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, bad_index)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="expert")


def test_replay_is_fresh_and_does_not_touch_global_rng():
    random.seed(99173)
    before = random.getstate()
    first = GEN.generate(3, 8, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(3, 8, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
