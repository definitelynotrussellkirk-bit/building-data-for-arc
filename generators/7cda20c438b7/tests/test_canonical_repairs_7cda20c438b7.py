"""Regressions for canonical 7cda20c438b7 source-review findings."""
from __future__ import annotations

import importlib.util
from itertools import combinations
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_canonical_7cda20c438b7", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load_generator()


def test_rule_hash_is_pinned(generator):
    assert generator.RULE_HASH == "ac623b9aa2f6"


def test_invalid_degenerate_and_unknown_overrides_are_rejected(generator):
    with pytest.raises(ValueError, match="no_xs|unsupported|unknown"):
        generator.generate(0, 0, difficulty="medium", texture="no_xs")
    with pytest.raises(ValueError, match="unknown|unsupported"):
        generator.generate(0, 0, difficulty="medium", bogus_axis=1)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_ordinary_draw_contains_a_shared_arm_pair(generator, difficulty):
    for seed in range(12):
        grid = generator.generate(seed, seed % 3, difficulty=difficulty)
        centers = generator._x_centers(grid)
        assert generator.self_check(grid) == []
        assert any(max(abs(r1 - r2), abs(c1 - c2)) == 2
                   for (r1, c1), (r2, c2) in combinations(centers, 2))


def test_declared_dimension_and_count_overrides_are_observable(generator):
    grid = generator.generate(31, 2, difficulty="easy", grid_h=9, grid_w=10, centers=3)
    assert generator.observe_overrides(grid) == {"grid_h": 9, "grid_w": 10, "centers": 3}
