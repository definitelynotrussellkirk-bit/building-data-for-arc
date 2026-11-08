"""Behavior regressions for complete cross-projection teaching lessons."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "e937c5b85cdd"
ROOT = find_root(__file__)
PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not PATH.is_file():
    PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location("cross_teaching_generator", PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _witnesses_from_pixels(grid):
    """Independent geometry check; no declared predicates or Python oracle."""
    h, w = len(grid), len(grid[0])
    colors = {v for row in grid[1:-1] for v in row[1:-1]} - {6, 7}
    length_three = nearer_facing = length_three_farther_facing = False
    for color in colors:
        points = {(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                  if grid[r][c] == color}
        center = next((r, c) for r, c in points
                      if {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} <= points)
        r, c = center
        arms = (r - min(y for y, x in points), max(y for y, x in points) - r,
                c - min(x for y, x in points), max(x for y, x in points) - c)
        length_three |= max(arms) == 3
        direction = arms.index(max(arms))
        distances = (r, h - 1 - r, c, w - 1 - c)
        nearer_facing |= distances[direction] < distances[direction ^ 1]
        length_three_farther_facing |= max(arms) == 3 and distances[direction] > distances[direction ^ 1]
    return length_three, nearer_facing, length_three_farther_facing


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_retains_all_witnesses_after_any_holdout(band):
    # Losing a witness on holding out one pair permits a plausible rival
    # to fit the demonstrations while changing that pair's answer.
    for seed in range(12):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(7)]
        observed = [_witnesses_from_pixels(grid) for grid in grids]
        for start in range(4):
            for held_out in range(4):
                remaining = [observed[start + i] for i in range(4) if i != held_out]
                assert all(any(item[k] for item in remaining) for k in range(3)), (
                    band, seed, start, held_out, observed[start:start + 4])


def test_declared_canonical_shortcuts_fit_every_labeled_occurrence():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


def test_lesson_hook_detects_a_real_ambiguity_and_its_refutation():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    # Length-three cross centered (4,5), extended toward the nearer top edge.
    grid = [[6 if r in (0, 10) or c in (0, 10) else 7 for c in range(11)]
            for r in range(11)]
    for r, c in [(4, 5), (3, 5), (2, 5), (1, 5), (5, 5), (4, 4), (4, 6)]:
        grid[r][c] = 2
    answer = [row[:] for row in grid]
    answer[0][5], answer[10][5] = 0, 2
    query = {"input": grid, "output": answer}
    assert gen.self_check(grid) == []
    reasons = gen.lesson_identifiable(pairs[:3], query)
    assert reasons and all(isinstance(reason, str) for reason in reasons)
    assert gen.lesson_identifiable([query, *pairs[:2]], query) == []


def test_strict_hook_excludes_a_lawful_extended_arm():
    pair = canonical_pairs(TASK_ID, root=ROOT)[0]
    assert gen.strict_canonical_like(pair["input"]) == []
    extended = gen.generate(17, 0, max_arm_len=3)
    assert gen.self_check(extended) == []
    assert gen.strict_canonical_like(extended)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_cycle_retains_the_full_canonical_proximity_relation(band):
    # Morphology alone missed the canonical relation: every painted side is
    # nearer its frame edge. Each cycle must retain at least one such scene.
    for seed in range(12):
        profiles = []
        for i in range(7):
            grid = gen.generate(seed, i, difficulty=band)
            colors = {v for row in grid[1:-1] for v in row[1:-1]} - {6, 7}
            linked = len(grid) == 11 and len(grid[0]) == 11 and colors == {2, 5, 8, 9}
            for color in colors:
                points = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                          if v == color}
                if len(points) != 6:
                    linked = False
                    continue
                r, c = next((r, c) for r, c in points
                            if {(r-1, c), (r+1, c), (r, c-1), (r, c+1)} <= points)
                tips = [(rr-r, cc-c) for rr, cc in points if abs(rr-r)+abs(cc-c) == 2]
                dr, dc = tips[0]
                linked &= ((dr < 0 and r > 10-r) or (dr > 0 and r < 10-r)
                           or (dc < 0 and c > 10-c) or (dc > 0 and c < 10-c))
            profiles.append(linked)
        for start in range(4):
            assert any(profiles[start:start+4]), (band, seed, start, profiles)


@pytest.mark.parametrize("outer", [list, tuple])
def test_accepted_tuple_rows_validate_without_mutating_the_input(outer):
    pair = canonical_pairs(TASK_ID, root=ROOT)[0]
    grid = outer(tuple(row) for row in pair["input"])
    assert gen.self_check(grid) == []
    assert gen._rule_output(grid) == pair["output"]
    assert grid == outer(tuple(row) for row in pair["input"])
