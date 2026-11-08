from __future__ import annotations

import copy
import importlib
import random

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.628b4a2c24c1.generator"
)


def _canonical_pairs():
    return canonical_pairs(MODULE.TASK_ID, root=ROOT, labeled_only=True)


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    signatures = set()
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original
        signatures.add(MODULE.profile_signature(pair["input"]))
    assert signatures == set(MODULE.CANONICAL_PROFILE_SIGNATURES)


def test_profile_schedule_is_exact_and_reaches_every_official_profile():
    for band in ("easy", "medium", "hard"):
        matches = 0
        signatures = set()
        for sample_index in range(200):
            grid = MODULE.generate(811, sample_index, difficulty=band)
            if MODULE.is_canonical_profile(grid):
                matches += 1
                signatures.add(MODULE.profile_signature(grid))
        assert matches == 50
        assert signatures == set(MODULE.CANONICAL_PROFILE_SIGNATURES)


def test_exact_axes_are_observable_at_boundary_combination():
    overrides = {
        "grid_h": 5,
        "grid_w": 8,
        "active_rows": 4,
        "seed_color": 9,
        "seed_mode": "separated",
        "wall_mode": "staggered",
        "wide_seed_row": True,
        "extra_walls": True,
    }
    grid = MODULE.generate(924, 17, difficulty="easy", **overrides)
    assert MODULE.observe_overrides(grid) == overrides
    assert MODULE.self_check(grid) == []


def test_self_check_rejects_targeted_structural_impostors():
    grid = MODULE.generate(
        101,
        3,
        difficulty="medium",
        grid_h=6,
        grid_w=10,
        active_rows=3,
        seed_color=4,
        seed_mode="separated",
        wall_mode="staggered",
        wide_seed_row=False,
        extra_walls=False,
    )

    no_walls = [[0 if value == 8 else value for value in row] for row in grid]
    assert "scene must contain at least one color-8 wall" in MODULE.self_check(no_walls)

    no_seeds = [[0 if value not in (0, 8) else value for value in row] for row in grid]
    assert any("seed" in error for error in MODULE.self_check(no_seeds))

    adjacent_wall = copy.deepcopy(grid)
    seed_row = next(r for r, row in enumerate(grid) if any(v not in (0, 8) for v in row))
    seed_end = max(c for c, value in enumerate(grid[seed_row]) if value not in (0, 8))
    old_wall = next(c for c, value in enumerate(grid[seed_row]) if value == 8)
    adjacent_wall[seed_row][old_wall] = 0
    adjacent_wall[seed_row][seed_end + 1] = 8
    assert any("blank corridor" in error for error in MODULE.self_check(adjacent_wall))

    two_colors = copy.deepcopy(grid)
    r, c = next(
        (r, c)
        for r, row in enumerate(two_colors)
        for c, value in enumerate(row)
        if value not in (0, 8)
    )
    two_colors[r][c] = 5
    assert "scene must contain exactly one non-wall seed color" in MODULE.self_check(two_colors)


def test_negative_recombination_is_lawful_but_not_an_official_profile():
    grid = [[0] * 10 for _ in range(6)]
    for r, c in ((1, 1), (2, 2), (3, 1)):
        grid[r][c] = 6
    # Canonical train[1] uses walls 4/6/8; replacing only the middle wall by 7
    # creates a plausible linked recombination that is not any official input.
    for r, c in ((1, 4), (2, 7), (3, 8)):
        grid[r][c] = 8
    assert MODULE.self_check(grid) == []
    assert not MODULE.is_canonical_profile(grid)
    assert MODULE.rule_mirror(grid)[2][6] == 6


def test_generation_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(9917)
    before = random.getstate()
    first = MODULE.generate(42, 19, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(42, 19, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
