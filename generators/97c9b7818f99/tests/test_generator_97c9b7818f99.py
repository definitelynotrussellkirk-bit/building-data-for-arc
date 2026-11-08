from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "97c9b7818f99"
ROOT = find_root(__file__)
MODULE, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _pair(sample_index: int, *, seed: int = 701, difficulty: str = "medium"):
    grid = MODULE.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": MODULE.rule_mirror(grid)}


def test_canonical_inputs_and_outputs_include_gray_seed_case():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    assert all(MODULE.self_check(pair["input"]) == [] for pair in pairs)
    assert any(
        5 in MODULE._analyze(pair["input"])["seed_colors"]
        for pair in pairs
    )
    assert all(MODULE.rule_mirror(pair["input"]) == pair["output"] for pair in pairs)


def test_self_check_rejects_four_targeted_impostors():
    grid = MODULE.generate(11, 1, difficulty="medium")

    broken_border = copy.deepcopy(grid)
    broken_border[0][2] = 0
    assert MODULE.self_check(broken_border)

    interior_cyan = copy.deepcopy(grid)
    interior_cyan[1][1] = 8
    assert MODULE.self_check(interior_cyan)

    duplicate_color = copy.deepcopy(grid)
    seeds = MODULE._analyze(duplicate_color)["seeds"]
    duplicate_color[seeds[1][0]][seeds[1][1]] = seeds[0][2]
    assert MODULE.self_check(duplicate_color)

    output_like = MODULE.rule_mirror(grid)
    assert MODULE.self_check(output_like)


def test_exact_overrides_are_observable_and_unknown_keys_fail():
    for values in (
        {"grid_h": 7, "grid_w": 8, "n_seeds": 2, "include_gray_seed": False},
        {"grid_h": 13, "grid_w": 15, "n_seeds": 4, "include_gray_seed": True},
    ):
        grid = MODULE.generate(29, 0, difficulty="hard", **values)
        assert MODULE.observe_overrides(grid) == values
        assert MODULE.self_check(grid, meta=values) == []
    with pytest.raises(TypeError):
        MODULE.generate(1, 0, unknown_axis=3)


def test_every_four_example_sliding_window_is_identifiable():
    pairs = [_pair(index) for index in range(17)]
    for start in range(13):
        demos = pairs[start : start + MODULE.EXAMPLES_NEEDED]
        query = pairs[start + MODULE.EXAMPLES_NEEDED]
        assert MODULE.lesson_identifiable(demos, query) == []


def test_generated_scenes_exercise_tie_unique_and_seed_ownership_branches():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = MODULE.generate(31337, sample_index, difficulty=difficulty)
            analysis = MODULE._analyze(grid)
            assert analysis["errors"] == []
            assert analysis["tie_cells"]
            assert analysis["unique_cells"]
            assert min(analysis["owner_counts"]) >= 1
            assert MODULE.rule_mirror(grid) != grid


def test_determinism_fresh_returns_and_global_rng_state():
    state = random.getstate()
    first = MODULE.generate(404, 7, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(404, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[1][1] = 9
    assert MODULE.generate(404, 7, difficulty="hard") == second


def test_adversarial_four_example_window_refutes_euclidean_rival():
    demos = [
        _pair(index, seed=93, difficulty="easy")
        for index in range(9, 13)
    ]
    query = _pair(13, seed=93, difficulty="easy")

    assert MODULE.lesson_identifiable(demos, query) == []
