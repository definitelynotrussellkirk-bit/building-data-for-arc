"""Regression and semantic-contract tests for task 01dfed2930fa."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_01dfed2930fa_under_test", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


def _room_features(gen, grid):
    mixed = False
    twins = False
    for cells in gen._rooms(grid):
        seeds = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 8)]
        mixed |= len(set(seeds)) >= 2
        twins |= len(seeds) >= 2 and len(set(seeds)) == 1
    return {"mixed": mixed, "twins": twins}


def _pair(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_reproduced_three_demo_window_covers_mixed_and_twin_branches(gen):
    grids = [gen.generate(0, index, difficulty="easy") for index in (4, 5, 6)]
    features = [_room_features(gen, grid) for grid in grids]
    assert any(item["mixed"] for item in features)
    assert any(item["twins"] for item in features)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_sliding_three_window_covers_both_gate_branches(gen, difficulty):
    for seed in range(20):
        for start in range(9):
            grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(start, start + 3)]
            features = [_room_features(gen, grid) for grid in grids]
            assert any(item["mixed"] for item in features), (seed, start, difficulty)
            assert any(item["twins"] for item in features), (seed, start, difficulty)


def test_explicit_texture_overrides_remain_exact_controls(gen):
    mixed = gen.generate(7, 2, difficulty="easy", texture="mixed_room")
    twins = gen.generate(7, 2, difficulty="easy", texture="twin_seeds")
    plain = gen.generate(7, 2, difficulty="easy", texture="plain")
    assert _room_features(gen, mixed) == {"mixed": True, "twins": False}
    assert _room_features(gen, twins) == {"mixed": False, "twins": True}
    assert _room_features(gen, plain) == {"mixed": False, "twins": False}


def test_schedule_profile_is_three_periodic_and_declares_full_space(gen):
    assert set(gen.SCHEDULE_PROFILES) == {"mixed_room", "twin_seeds", "structural"}
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(10):
            profiles = [gen.schedule_profile(seed, i, difficulty) for i in range(12)]
            assert all(profiles[i] == profiles[i + 3] for i in range(9))
            assert set(profiles[:3]) == set(gen.SCHEDULE_PROFILES)


def test_rule_mirror_has_hand_derived_room_behavior(gen):
    grid = [
        [8, 8, 8, 8, 8, 8, 8],
        [8, 2, 0, 8, 4, 0, 8],
        [8, 0, 2, 8, 5, 0, 8],
        [8, 8, 8, 8, 8, 8, 8],
        [8, 6, 0, 8, 0, 0, 8],
        [8, 0, 0, 8, 0, 0, 8],
        [8, 8, 8, 8, 8, 8, 8],
    ]
    assert gen.rule_mirror(grid) == [
        [8, 8, 8, 8, 8, 8, 8],
        [8, 2, 2, 8, 4, 0, 8],
        [8, 2, 2, 8, 5, 0, 8],
        [8, 8, 8, 8, 8, 8, 8],
        [8, 6, 6, 8, 0, 0, 8],
        [8, 6, 6, 8, 0, 0, 8],
        [8, 8, 8, 8, 8, 8, 8],
    ]


def test_scheduled_lessons_refute_both_named_rivals(gen):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(12):
            grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(4)]
            demos = [_pair(gen, grid) for grid in grids[:3]]
            query = {"input": grids[3]}
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_underteaching_is_reported_with_surviving_rival_names(gen):
    grids = [
        gen.generate(11, index, difficulty="easy", texture="plain")
        for index in range(4)
    ]
    reasons = gen.lesson_identifiable([_pair(gen, grid) for grid in grids[:3]], {"input": grids[3]})
    assert any("fill_any_first_seed" in reason for reason in reasons)
    assert any("exactly_one_seed_cell" in reason for reason in reasons)


def test_semantic_witnesses_are_real_and_bound_to_rivals(gen):
    mixed = gen.generate(5, 1, difficulty="medium", texture="mixed_room")
    twins = gen.generate(5, 1, difficulty="medium", texture="twin_seeds")
    assert gen.SEMANTIC_WITNESSES["mixed_seed_room_stays_unfilled"](mixed)
    assert gen.SEMANTIC_WITNESSES["same_color_twin_seeds_fill"](twins)
    for witness, rivals in gen.WITNESS_RIVALS.items():
        grid = mixed if witness.startswith("mixed") else twins
        expected = gen.rule_mirror(grid)
        assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rivals)


def test_strict_contract_accepts_ordinary_scenes_and_rejects_malformed(gen):
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(6):
            grid = gen.generate(123, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
    malformed = gen.generate(123, 0, difficulty="easy")
    malformed[0][0] = 0
    assert gen.strict_canonical_like(malformed)
