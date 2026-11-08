from __future__ import annotations

import importlib
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.778a00c38b8d.generator"
)
TASK_ID = "778a00c38b8d"


def _pair(seed: int, sample_index: int, band: str):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_rule_mirror_is_exact():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_and_unknown_rejection():
    requested = {
        "grid_h": 10,
        "grid_w": 10,
        "n_corner_components": 4,
        "n_interior_components": 3,
        "corner_size": 3,
        "interior_size": 2,
    }
    grid = GEN.generate(19, 7, difficulty="hard", **requested)
    assert GEN.observe_overrides(grid) == requested

    requested_low = {
        "grid_h": 8,
        "grid_w": 8,
        "n_corner_components": 2,
        "n_interior_components": 2,
        "corner_size": 2,
        "interior_size": 3,
    }
    grid_low = GEN.generate(23, 11, difficulty="easy", **requested_low)
    assert GEN.observe_overrides(grid_low) == requested_low

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, unknown_axis=1)
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="corner_size"):
        GEN.generate(0, 0, corner_size=True)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260729)
    state_before = random.getstate()
    first = GEN.generate(314159, 12, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(314159, 12, difficulty="medium")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    replay = GEN.generate(314159, 12, difficulty="medium")
    assert replay == second


def test_structural_mutations_are_rejected():
    grid = GEN.generate(41, 6, difficulty="hard")
    facts = GEN._analyze(grid)
    assert facts["errors"] == []

    no_distractor = deepcopy(grid)
    row, col = facts["distractors"][0]
    no_distractor[row][col] = 0
    assert GEN.self_check(no_distractor)

    no_noncorner_red = deepcopy(grid)
    for component in facts["noncorner_components"]:
        for row, col in component:
            no_noncorner_red[row][col] = 0
    assert any("avoid every grid corner" in reason for reason in GEN.self_check(no_noncorner_red))

    corner_cells_only = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    corners = set(GEN._corner_positions(height, width).values())
    for component in facts["corner_components"]:
        for row, col in component - corners:
            corner_cells_only[row][col] = 0
    assert any("extend beyond" in reason for reason in GEN.self_check(corner_cells_only))

    wrong_palette = deepcopy(grid)
    row, col = facts["distractors"][0]
    wrong_palette[row][col] = 7
    assert any("palette" in reason for reason in GEN.self_check(wrong_palette))

    duplicate_distractor = deepcopy(grid)
    placed = False
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            if duplicate_distractor[row][col] == 0:
                duplicate_distractor[row][col] = 5
                placed = True
                break
        if placed:
            break
    assert any("exactly one color-5" in reason for reason in GEN.self_check(duplicate_distractor))


def test_each_named_semantic_rival_is_killed_by_an_ordinary_draw():
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(73, 9, difficulty=band)
        expected = GEN.rule_mirror(grid)
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(deepcopy(grid)) != expected


def test_every_four_demo_sliding_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos = [_pair(101, start + offset, band) for offset in range(4)]
            query = _pair(101, start + 4, band)
            assert GEN.lesson_identifiable(demos, query) == []
