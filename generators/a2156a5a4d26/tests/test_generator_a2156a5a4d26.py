"""Task-linked regressions for generator a2156a5a4d26."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "a2156a5a4d26"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
BANDS = ("easy", "medium", "hard")


def test_rule_pin_and_every_canonical_pair_match_python_mirror():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "c60ea943a128"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_exact_override_boundaries_are_observable_in_every_band():
    cases = (
        {"grid_h": 9, "grid_w": 10, "n_pairs": 2, "pair_height": 2, "pair_width": 2, "n_distractors": 0},
        {"grid_h": 14, "grid_w": 14, "n_pairs": 3, "pair_height": 3, "pair_width": 4, "n_distractors": 2},
        {"grid_h": 9, "grid_w": 14, "n_pairs": 3, "pair_height": 3, "pair_width": 2, "n_distractors": 2},
        {"grid_h": 14, "grid_w": 10, "n_pairs": 2, "pair_height": 2, "pair_width": 4, "n_distractors": 0},
    )
    for band in BANDS:
        for index, requested in enumerate(cases):
            grid = GEN.generate(71000 + index, 20 + index, difficulty=band, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested


def test_unknown_invalid_overrides_and_difficulty_fail_closed():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_pairs=3)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, pair_height=9)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, grid_w=9)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_canonical_shortcuts_fit_public_pairs_but_counterexample_profile_kills_them():
    pairs = canonical_pairs(TASK_ID)
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    # Force the odd counterexample slot; it carries anti-diagonal pairs,
    # triplet distractors, and height-2 rectangles simultaneously.
    grid = GEN.generate(72001, 1, difficulty="medium")
    truth = GEN.rule_mirror(grid)
    profile = GEN.semantic_profile(grid)
    assert profile["anti_pairs"] > 0
    assert profile["triplet_distractors"] > 0
    assert 2 in profile["pair_heights"]
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert shortcut(grid) != truth, name


def test_every_two_demo_sliding_window_identifies_the_rule():
    for start in range(8):
        demos = []
        for offset in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(73000 + start, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(74000 + start, start + GEN.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        profiles = [GEN.schedule_profile(0, start + i) for i in range(GEN.EXAMPLES_NEEDED)]
        assert "shortcut_counterexample" in profiles
        assert GEN.lesson_identifiable(demos, query) == []


def test_mutation_impostors_are_all_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_triplet_distractor_is_not_transformed_by_true_rule():
    grid = GEN.generate(75001, 1, difficulty="hard")
    counts = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                counts.setdefault(value, []).append((r, c))
    triplets = {color: cells for color, cells in counts.items() if len(cells) == 3}
    assert triplets
    out = GEN.rule_mirror(grid)
    for color, cells in triplets.items():
        assert {(r, c) for r, c in cells} == {
            (r, c)
            for r, row in enumerate(out)
            for c, value in enumerate(row)
            if value == color
        }


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20260815)
    before = random.getstate()
    first = GEN.generate(987654, 77, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(987654, 77, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    third = GEN.generate(987654, 77, difficulty="hard")
    assert second == third
