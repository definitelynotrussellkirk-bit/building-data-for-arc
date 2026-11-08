"""Focused regressions for generator f98b43c1996b."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "f98b43c1996b"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.f98b43c1996b.generator"
)
BANDS = ("easy", "medium", "hard")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN._solve_grid(grid)}


def test_rule_hash_and_every_canonical_pair_are_pinned_and_accepted():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "cbbce0964240"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._solve_grid(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_override_boundaries_round_trip_in_every_band():
    cases = (
        {"grid_h": 6, "grid_w": 7, "n_blocks": 2, "n_distractors": 1},
        {"grid_h": 9, "grid_w": 9, "n_blocks": 4, "n_distractors": 2},
        {"grid_h": 6, "grid_w": 9, "n_blocks": 4, "n_distractors": 1},
        {"grid_h": 9, "grid_w": 7, "n_blocks": 2, "n_distractors": 2},
    )
    for band_index, band in enumerate(BANDS):
        for index, requested in enumerate(cases):
            grid = GEN.generate(
                10_000 + 100 * band_index + index,
                index,
                difficulty=band,
                **requested,
            )
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []


def test_unknown_override_and_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20260815)
    state = random.getstate()
    first = GEN.generate(424242, 17, difficulty="hard")
    second = GEN.generate(424242, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert GEN.generate(424242, 17, difficulty="hard") == second


def test_every_ordinary_draw_carries_all_shortcut_killing_witnesses():
    for band_index, band in enumerate(BANDS):
        for index in range(60):
            grid = GEN.generate(20_000 + 1000 * band_index + index, index, difficulty=band)
            expected = GEN._solve_grid(grid)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert all(witness(grid) for witness in GEN.SEMANTIC_WITNESSES.values())
            for rival in GEN.SEMANTIC_RIVALS.values():
                assert rival(grid) != expected


def test_every_two_demo_sliding_window_is_identifiable():
    for band_index, band in enumerate(BANDS):
        for start in range(16):
            seed = 30_000 + 1000 * band_index + start
            grids = [
                GEN.generate(seed, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos = [_pair(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
            query = _pair(grids[GEN.EXAMPLES_NEEDED])
            assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_four_declared_structural_impostors():
    fixtures = list(GEN.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), f"declared impostor {name!r} unexpectedly passed"


def test_negative_recombination_is_distribution_invalid_but_oracle_defined():
    # A larger same-color region has overlapping 2x2 windows.  The selected
    # Racket rule can execute it in scan order, but the written ARC task never
    # specifies overlap conflict resolution, so the teaching grammar excludes it.
    grid = [[0] * 7 for _ in range(6)]
    for r in range(1, 4):
        for c in range(1, 4):
            grid[r][c] = 2
    for r in (4, 5):
        for c in (5, 6):
            grid[r][c] = 3
    errors = GEN.self_check(grid)
    assert any("conflict semantics" in error for error in errors)
    solved = GEN._solve_grid(grid)
    assert len(solved) == len(grid)
    assert all(len(row) == len(grid[0]) for row in solved)
