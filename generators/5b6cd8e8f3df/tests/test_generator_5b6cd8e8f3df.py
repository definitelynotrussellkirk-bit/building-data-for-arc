from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.5b6cd8e8f3df.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_solved_by_mirror():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.RULE_HASH == "f8f10f7791eb"


def test_exact_axes_are_observable_and_unknown_axes_reject():
    grid = gen.generate(
        17,
        5,
        difficulty="hard",
        grid_h=6,
        grid_w=7,
        n_seeds=5,
        repeat_colors=True,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 6,
        "grid_w": 7,
        "n_seeds": 5,
        "repeat_colors": True,
    }
    assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, imaginary_axis=1)


def test_self_check_rejects_four_targeted_impostor_classes():
    blank = [[0] * 7 for _ in range(6)]
    singleton = copy.deepcopy(blank)
    singleton[2][3] = 4
    border = copy.deepcopy(blank)
    border[0][2] = 4
    border[3][4] = 6
    overlapping = copy.deepcopy(blank)
    overlapping[2][2] = 4
    overlapping[3][3] = 6
    ragged = [[0] * 7 for _ in range(5)] + [[0] * 6]

    assert gen.self_check(blank)
    assert gen.self_check(singleton)
    assert gen.self_check(border)
    assert gen.self_check(overlapping)
    assert gen.self_check(ragged)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(9182)
    before = random.getstate()
    first = gen.generate(1234, 19, difficulty="medium")
    after = random.getstate()
    second = gen.generate(1234, 19, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_every_minimal_demo_window_kills_declared_competitors():
    examples = []
    for sample_index in range(8):
        grid = gen.generate(811, sample_index, difficulty="medium")
        examples.append(_pair(grid))
    for start in range(len(examples) - gen.EXAMPLES_NEEDED):
        demos = examples[start : start + gen.EXAMPLES_NEEDED]
        query = examples[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []


def test_repeated_color_scene_kills_canonical_shortcut():
    canonical = canonical_pairs(gen.TASK_ID)
    shortcut = gen.CANONICAL_SHORTCUTS["one_stamp_per_color"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical)

    grid = gen.generate(91, 1, n_seeds=3, repeat_colors=True)
    assert shortcut(grid) != gen.rule_mirror(grid)
