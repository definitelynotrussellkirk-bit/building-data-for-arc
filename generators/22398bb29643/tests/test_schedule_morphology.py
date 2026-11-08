"""Schedule-level morphology and band-variation regressions."""
from __future__ import annotations

import importlib


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.22398bb29643.generator"
)
BANDS = ("easy", "medium", "hard")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_default_object_counts_stay_on_the_canonical_three_or_five_support():
    for band in BANDS:
        for sample_index in range(20):
            grid = GEN.generate(77, sample_index, difficulty=band)
            assert len(GEN._components(grid)) in {3, 5}


def test_difficulty_band_enters_keyed_draws_without_changing_the_rule_contract():
    for sample_index in range(10):
        grids = [GEN.generate(31337, sample_index, difficulty=band) for band in BANDS]
        assert len({_freeze(grid) for grid in grids}) == len(BANDS)
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(len(GEN.rule_mirror(grid)) == 1 for grid in grids)
