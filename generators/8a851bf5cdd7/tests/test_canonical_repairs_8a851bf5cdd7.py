"""Regressions for canonical 8a851bf5cdd7 source-review findings."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_canonical_8a851bf5cdd7", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load_generator()


def _panels(grid):
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    assert len(separators) == 2
    pw = separators[0]
    assert separators == [pw, 2 * pw + 1]
    return [
        [[grid[r][panel * (pw + 1) + c] for c in range(pw)] for r in range(h)]
        for panel in range(3)
    ]


def _visible_branches(grid):
    before, after, query = _panels(grid)
    visible_add = False
    visible_delete = False
    for r in range(len(before)):
        for c in range(len(before[0])):
            if before[r][c] == 0 and after[r][c] != 0 and query[r][c] == 0:
                visible_add = True
            if before[r][c] != 0 and after[r][c] == 0 and query[r][c] != 0:
                visible_delete = True
    return visible_add, visible_delete


def test_rule_hash_is_pinned(generator):
    assert generator.RULE_HASH == "d2ea4a091d55"


def test_ragged_self_check_returns_a_finding_instead_of_raising(generator):
    assert generator.self_check([[8, 0, 8], [8]]) == ["ragged grid"]


def test_invalid_no_separator_and_unknown_overrides_are_rejected(generator):
    with pytest.raises(ValueError, match="no_separator|unsupported|unknown"):
        generator.generate(0, 0, difficulty="easy", texture="no_separator")
    with pytest.raises(ValueError, match="unknown|unsupported"):
        generator.generate(0, 0, difficulty="easy", bogus_axis=1)


def test_variant_is_a_real_axis(generator):
    grids = [generator.generate(11, 4, difficulty="medium", variant=value)
             for value in (0, 1, 2)]
    assert len({repr(grid) for grid in grids}) == 3


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_ordinary_draw_visibly_exercises_addition_and_deletion(generator, difficulty):
    for seed in range(12):
        grid = generator.generate(seed, seed % 3, difficulty=difficulty)
        assert generator.self_check(grid) == []
        assert _visible_branches(grid) == (True, True)
