"""Regression probes for semantic omissions found after the standard battery passed."""
from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.53ffc8bc9584.generator")


def perpendicular_rival(grid):
    """Deliberately wrong: the diagonal yellow requirement is absent."""
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            directions = [
                0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 4
                for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1))
            ]
            if any(directions[k] and directions[(k + 1) % 4] for k in range(4)):
                out[r][c] = 9
    return out


def test_omitted_diagonal_rival_really_fits_every_canonical_pair():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    assert all(perpendicular_rival(p["input"]) == p["output"] for p in pairs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_ordinary_sandwich_refutes_the_omitted_diagonal(band):
    for cycle in range(12):
        seed = 53_000 + cycle
        index = next(i for i in range(4 * cycle, 4 * cycle + 4)
                     if gen.schedule_profile(seed, i, difficulty=band) == "sandwich")
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert perpendicular_rival(grid) != gen.rule_mirror(grid), cycle
        assert gen.CANONICAL_SHORTCUTS["two_cardinal_yellows"](grid) != gen.rule_mirror(grid)


def test_ordinary_linked_scenes_cover_all_four_actual_motif_orientations():
    signatures = set()
    for cycle in range(12):
        grid = gen.generate(70_000, 4 * cycle + 1, difficulty="medium")
        for component in gen._components(grid, 4):
            if len(component) == 5:
                signatures.add(gen._component_signature(component))
    assert signatures == gen._LINKED_SIGNATURES


@pytest.mark.parametrize("value", ["4", None, [], {}, True, 4.0])
def test_malformed_cell_returns_diagnostics_instead_of_raising(value):
    grid = gen.generate(1, 0)
    grid[0][0] = value
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("overrides", [
    {"grid_h": 7.9}, {"grid_w": "8"}, {"grid_h": None},
    {"n_targets": 2.9}, {"n_targets": "2"}, {"n_targets": True},
])
def test_exact_integer_controls_do_not_silently_coerce(overrides):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **overrides)


def test_perpendicular_rival_is_in_the_executable_lesson_contract():
    assert "perpendicular_yellows" in gen.CANONICAL_SHORTCUTS
    assert "perpendicular_yellows" in gen.LESSON_COMPETITORS
    grid = gen.generate(56, 2)
    assert gen.CANONICAL_SHORTCUTS["perpendicular_yellows"](grid) == perpendicular_rival(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_four_demo_query_position_covers_every_family_across_seeds(band):
    # Public generation starts at index0 for each episode and increments seed
    # across the batch.  A seed-independent family schedule always queries the
    # isolated family even though the demonstrations contain all four.
    counts = {family: 0 for family in gen.SCENE_FAMILIES}
    for seed in range(16):
        grid = gen.generate(seed, 4, difficulty=band)
        counts[gen.observe_overrides(grid)["scene_family"]] += 1
    assert set(counts.values()) == {4}, counts
