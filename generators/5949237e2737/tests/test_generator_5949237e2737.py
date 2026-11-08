from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.5949237e2737.generator")


def test_canonical_inputs_are_accepted_and_python_mirror_matches_all_outputs():
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        input_grid = pair["input"]
        expected = pair["output"]
        before = copy.deepcopy(input_grid)
        assert GEN.self_check(input_grid) == []
        assert GEN.strict_canonical_like(input_grid) == []
        assert GEN.rule_mirror(input_grid) == expected
        assert input_grid == before


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(20260726)
    state = random.getstate()
    first = GEN.generate(17, 3, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(17, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(17, 3, difficulty="hard") == second


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
def test_exact_overrides_are_observable_across_bands_and_profiles(band, profile):
    requested = {
        "grid_h": 5 if band == "easy" else 14,
        "half_w": 2 if band == "easy" else 7,
        "left_cells": 9,
        "match_count": 1,
        "palette_size": 4,
        "scene_profile": profile,
    }
    grid = GEN.generate(91, 11, difficulty=band, **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=4)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="not_a_profile")
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 0, texture="no_bar", grid_h=7)


def test_schedule_covers_every_profile_and_lessons_kill_named_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCENE_PROFILES)):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(300 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            profiles = {
                GEN.observe_overrides(pair["input"])["scene_profile"]
                for pair in pairs[: GEN.EXAMPLES_NEEDED]
            }
            assert profiles == set(GEN.SCENE_PROFILES)
            assert GEN.lesson_identifiable(
                pairs[: GEN.EXAMPLES_NEEDED], pairs[GEN.EXAMPLES_NEEDED]
            ) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert any(
                    rival(pair["input"]) != pair["output"]
                    for pair in pairs[: GEN.EXAMPLES_NEEDED]
                )


def test_every_semantic_witness_fires_and_proves_its_named_rival_wrong():
    grids = [GEN.generate(77, index, difficulty="medium") for index in range(5)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert all(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for grid in firing
            )


def test_mutation_fixtures_are_rejected_and_inputs_are_not_mutated():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == before


def _row_color_presence_shortcut(grid):
    facts = GEN._analysis(grid)
    output = [[0 for _ in row] for row in grid]
    half = facts["half_w"]
    for row, col, value in facts["left"]:
        if value in grid[row][half + 1 :]:
            output[row][2 * half - col] = value
    return output


def test_wrong_color_decoy_refutes_same_row_color_presence_regression():
    # Baseline v3.0.0 seed: all five scheduled demonstrations were accepted by
    # this wrong rule because the global decoy landed on a different row.
    grids = [GEN.generate(44, index, difficulty="easy") for index in range(5)]
    assert any(
        _row_color_presence_shortcut(grid) != GEN.rule_mirror(grid)
        for grid in grids
    )
