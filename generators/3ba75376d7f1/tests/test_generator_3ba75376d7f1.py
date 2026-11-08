from __future__ import annotations

import copy
import importlib
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.3ba75376d7f1.generator")
from src.core.canonical_pairs import load_task_pairs


def _colors(grid):
    return {value for row in grid for value in row if value != 8}


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    assert gen.RULE_HASH == "64565f984008"
    canonical = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    pairs = load_task_pairs(gen.TASK_ID, canonical, splits=("train", "test"))
    assert len(pairs) == 5
    assert [gen.self_check(pair["input"]) for pair in pairs] == [[]] * 5
    assert [gen.canonical_profile_signature(pair["input"]) for pair in pairs] == [
        "canonical_train_7",
        "canonical_train_2",
        "canonical_train_9",
        "canonical_train_1",
        "canonical_test_mix",
    ]


def test_episode_schedule_exposes_every_query_color_before_query():
    for seed in range(20):
        demos = [gen.generate(seed, i, difficulty="medium") for i in range(3)]
        query = gen.generate(seed, 3, difficulty="medium")
        demo_colors = set().union(*map(_colors, demos))
        assert _colors(query) <= demo_colors
        assert _colors(query) == {1, 2, 7, 9}


def test_exact_overrides_are_observable_and_incompatible_pair_rejects_loudly():
    grid = gen.generate(11, 6, difficulty="easy", grid_h=16, grid_w=6, n_marks=10)
    assert (len(grid), len(grid[0])) == (16, 6)
    assert gen.observe_overrides(grid) == {"n_marks": 10}
    with pytest.raises(ValueError, match="n_marks=1"):
        gen.generate(11, 0, difficulty="hard", grid_h=6, n_marks=1)


def test_self_check_rejects_targeted_structural_impostors():
    all_background = [[8] * 10 for _ in range(10)]
    full_one_color = [[7] * 10 for _ in range(10)]
    short_line = [[8] * 10 for _ in range(10)]
    short_line[4][4] = short_line[4][5] = 7
    solid_2x2 = [[8] * 10 for _ in range(10)]
    for r in (4, 5):
        for c in (4, 5):
            solid_2x2[r][c] = 2
    target_collision = [[8] * 10 for _ in range(10)]
    target_collision[2][1] = 1   # -> (2,2)
    target_collision[2][4] = 2   # -> (2,2)
    out_of_bounds = [[8] * 10 for _ in range(10)]
    out_of_bounds[0][4] = 7
    for grid in (all_background, full_one_color, short_line, solid_2x2, target_collision, out_of_bounds):
        assert gen.self_check(grid), grid


def test_replay_fresh_returns_and_global_rng_state():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    mutated = copy.deepcopy(first)
    mutated[0][0] = 0
    assert gen.generate(77, 3, difficulty="hard") == second
