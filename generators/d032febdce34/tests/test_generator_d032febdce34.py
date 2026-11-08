"""Focused regression tests for generator d032febdce34."""
from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "d032febdce34"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_matches_canonical_authority():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)


def test_self_check_accepts_every_canonical_pair_and_mirror_matches():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_boundary_overrides_round_trip_and_unknown_keys_reject():
    cases = [
        dict(grid_h=5, grid_w=5, border_objects=1, interior_objects=1),
        dict(grid_h=5, grid_w=5, border_objects=2, interior_objects=2),
        dict(grid_h=12, grid_w=12, border_objects=2, interior_objects=2),
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(701 + index, index, difficulty="hard", **overrides)
        assert GEN.self_check(grid, meta={"overrides": overrides}) == []
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)


def test_ordinary_draws_always_exercise_keep_and_erase_branches():
    for band in ("easy", "medium", "hard"):
        for seed in range(32):
            grid = GEN.generate(seed, seed * 13 + 5, difficulty=band)
            output = GEN.rule_mirror(grid)
            assert output != grid
            assert any(value != 0 for row in output for value in row)
            profile = GEN.semantic_profile(grid)
            assert profile["valid"]
            assert profile["border_objects"] >= 1
            assert profile["interior_objects"] >= 1
            assert profile["changed_cell_count"] >= 1
            assert GEN.strict_canonical_like(grid) == []


def test_four_sample_schedule_kills_every_named_competitor_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(9001, sample_index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(
                9001, start + GEN.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []

            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), name


def test_schedule_contains_color_size_side_count_and_full_component_witnesses():
    expected = {
        "edge_only_border_component",
        "multiple_kept_components",
        "shared_color_opposite_fate",
        "border_components_smaller_than_interior",
        "border_components_larger_than_interior",
        "border_component_extends_inward",
    }
    for band in ("easy", "medium", "hard"):
        demos = [
            GEN.generate(1212, sample_index, difficulty=band)
            for sample_index in range(GEN.EXAMPLES_NEEDED)
        ]
        fired = {
            name
            for name, predicate in GEN.SEMANTIC_WITNESSES.items()
            if any(predicate(grid) for grid in demos)
        }
        assert expected <= fired


def test_global_border_color_shortcut_fits_canonical_but_generated_witness_kills():
    shortcut = GEN.CANONICAL_SHORTCUTS[
        "keep_every_component_of_a_border_color"
    ]
    for pair in canonical_pairs(TASK_ID):
        assert shortcut(pair["input"]) == pair["output"]

    found = False
    for sample_index in range(16):
        grid = GEN.generate(2222, sample_index, difficulty="medium")
        if GEN.SEMANTIC_WITNESSES["shared_color_opposite_fate"](grid):
            found = True
            assert shortcut(grid) != GEN.rule_mirror(grid)
    assert found


def test_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_untouched():
    random.seed(424242)
    before = random.getstate()
    first = GEN.generate(77, 31, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(77, 31, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
