from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.4d8f78cee8b3.generator"
)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_match_rule_mirror():
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_axes_are_observable_and_unknown_axes_reject():
    for grid_profile in GEN.GRID_PROFILES:
        for palette_kind in GEN.PALETTE_KINDS:
            for scene_profile in GEN.SCENE_PROFILES:
                grid = GEN.generate(
                    77,
                    9,
                    difficulty="hard",
                    grid_profile=grid_profile,
                    palette_kind=palette_kind,
                    scene_profile=scene_profile,
                )
                assert GEN.observe_overrides(grid) == {
                    "grid_profile": grid_profile,
                    "palette_kind": palette_kind,
                    "scene_profile": scene_profile,
                }
                assert GEN.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="x")


def test_three_sample_sliding_windows_identify_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                GEN.generate(9000 + start, index, difficulty=difficulty)
                for index in range(start, start + 4)
            ]
            demos = [_pair(grid) for grid in grids[:3]]
            query = _pair(grids[3])
            assert GEN.lesson_identifiable(demos, query) == []
            assert {
                GEN.observe_overrides(pair["input"])["scene_profile"]
                for pair in demos
            } == set(GEN.SCENE_PROFILES)


def test_self_check_rejects_targeted_impostors():
    valid = GEN.generate(
        123,
        1,
        grid_profile="canonical_6x9",
        palette_kind="low",
        scene_profile="cross_row",
    )
    assert GEN.self_check(valid) == []

    blank = [[0 for _ in row] for row in valid]
    no_repeat = copy.deepcopy(valid)
    for row in no_repeat:
        seen = set()
        for c, value in enumerate(row):
            if value == 0:
                continue
            if value in seen:
                row[c] = 0
            else:
                seen.add(value)
    no_singleton_row = copy.deepcopy(valid)
    active = next(row for row in no_singleton_row if any(row))
    color = next(value for value in active if value)
    active[:] = [0] * len(active)
    active[0] = color
    active[2] = color
    fourfold = copy.deepcopy(valid)
    active = next(row for row in fourfold if any(row))
    color = next(value for value in active if value)
    active[:] = [0] * len(active)
    for c in (0, 2, 4, 6):
        active[c] = color
    six_colors = copy.deepcopy(valid)
    removed = next(value for row in six_colors for value in row if value)
    for row in six_colors:
        for c, value in enumerate(row):
            if value == removed:
                row[c] = 0

    findings = [
        GEN.self_check(blank),
        GEN.self_check(no_repeat),
        GEN.self_check(no_singleton_row),
        GEN.self_check(fourfold),
        GEN.self_check(six_colors),
    ]
    assert all(result for result in findings)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(42, 8, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(42, 8, difficulty="medium")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(42, 8, difficulty="medium") == second
