"""Regression tests for the top-row beam generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1198580cc354"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {(7, 8, 5), (8, 9, 5), (8, 10, 5), (9, 7, 4)}


def beam_output(grid):
    """Independent mirror of the canonical top-row beam rule."""
    out = deepcopy(grid)
    if not grid:
        return out
    for c, color in enumerate(grid[0]):
        if color in (0, 9):
            continue
        for r in range(1, len(grid)):
            if grid[r][c] == 9:
                break
            out[r][c] = color
    return out


def pair(grid):
    return {"input": deepcopy(grid), "output": beam_output(grid)}


def blocker_facts(grid):
    seeds = {c for c, value in enumerate(grid[0]) if value not in (0, 9)}
    blocked = {c for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value == 9}
    return seeds, blocked


def test_contract_is_pinned_and_axes_are_exact_observable_controls():
    assert GEN.RULE_HASH == "018c975f3e7f"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "seed_count"}


def test_all_canonical_pairs_are_accepted_and_match_independent_rule():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for item in pairs:
        original = deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert beam_output(item["input"]) == item["output"]
        assert item["input"] == original


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("grid_h", (7, 10))
@pytest.mark.parametrize("grid_w", (7, 12))
@pytest.mark.parametrize("seed_count", (2, 4))
def test_every_axis_boundary_combination_round_trips(difficulty, grid_h, grid_w, seed_count):
    requested = {"grid_h": grid_h, "grid_w": grid_w, "seed_count": seed_count}
    grid = GEN.generate(73, 11, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    seeds, blocked = blocker_facts(grid)
    assert len(seeds) == seed_count
    assert 1 in {grid[0][c] for c in seeds}
    assert blocked
    assert seeds - blocked
    assert beam_output(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 6},
        {"grid_h": 11},
        {"grid_w": 6},
        {"grid_w": 13},
        {"seed_count": 1},
        {"seed_count": 5},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"seed_count": "3"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_band_has_exact_canonical_profile_support_in_twenty_draws(difficulty):
    profiles = set()
    for index in range(20):
        grid = GEN.generate(1000 + index * 17, index, difficulty=difficulty)
        profiles.add((len(grid), len(grid[0]), len({value for row in grid for value in row})))
    assert profiles & CANONICAL_PROFILES


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_draws_are_decisive_mixed_beam_lessons(difficulty):
    for index in range(40):
        grid = GEN.generate(5000 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        seeds, blocked = blocker_facts(grid)
        assert blocked
        assert seeds - blocked
        assert 1 in {grid[0][c] for c in seeds}
        truth = beam_output(grid)
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(grid) != truth, (difficulty, index, name)


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_four_pair_window_and_query_rotation_is_identifiable(difficulty):
    for start in range(12):
        pairs = [
            pair(GEN.generate(9000 + start, start + offset, difficulty=difficulty))
            for offset in range(4)
        ]
        for query_index, query in enumerate(pairs):
            demos = [item for index, item in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []


def test_color_one_shortcut_fits_canonical_but_generated_witness_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    rival = GEN.CANONICAL_SHORTCUTS["ignore_color_1"]
    assert all(rival(item["input"]) == item["output"] for item in pairs)
    witness = GEN.generate(119, 3, grid_h=7, grid_w=8, seed_count=2)
    assert GEN.SEMANTIC_WITNESSES["color_1_is_a_seed"](witness)
    assert rival(witness) != beam_output(witness)


def test_self_check_rejects_malformed_or_semantically_empty_impostors():
    good = GEN.generate(17, 4, grid_h=8, grid_w=9, seed_count=3)
    assert GEN.self_check(good) == []

    cases = []
    cases.append([[0] * 9 for _ in range(8)])
    cases.append([[3] * 9 for _ in range(8)])
    cases.append([[3, 3], [3, 3]])

    top_blocker = deepcopy(good)
    top_blocker[0][0] = 9
    cases.append(top_blocker)

    stray_color = deepcopy(good)
    stray_color[2][0] = 4
    cases.append(stray_color)

    stray_blocker = deepcopy(good)
    empty_col = next(c for c, value in enumerate(good[0]) if value == 0)
    stray_blocker[2][empty_col] = 9
    cases.append(stray_blocker)

    duplicate_blocker = deepcopy(good)
    blocked_col = next(c for c in range(len(good[0])) if any(row[c] == 9 for row in good[1:]))
    free_row = next(r for r in range(2, len(good) - 1) if duplicate_blocker[r][blocked_col] == 0)
    duplicate_blocker[free_row][blocked_col] = 9
    cases.append(duplicate_blocker)

    no_blocker = deepcopy(good)
    for r in range(1, len(no_blocker)):
        for c in range(len(no_blocker[0])):
            if no_blocker[r][c] == 9:
                no_blocker[r][c] = 0
    cases.append(no_blocker)

    for grid in cases:
        assert GEN.self_check(grid), grid


def test_generation_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(777, 13, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 13, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(777, 13, difficulty="hard") == second


def test_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(808, 6)
    original = deepcopy(grid)
    GEN.observe_overrides(grid)
    GEN.strict_canonical_like(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(grid)
    assert grid == original


def test_public_schedule_contract_covers_declared_profiles():
    seen = {
        GEN.schedule_profile(123456, index, difficulty="hard")
        for index in range(len(GEN.SCHEDULE_PROFILES))
    }
    assert seen == set(GEN.SCHEDULE_PROFILES)
