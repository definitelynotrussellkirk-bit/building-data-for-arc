from __future__ import annotations

import copy
import importlib
import random

import pytest


GEN = importlib.import_module("puzzle_generators.per_puzzle.67a35830fe56.generator")

CANONICAL = [
    (
        [[0, 2, 2], [0, 0, 2], [0, 0, 0]],
        [[0, 0, 0], [0, 2, 2], [0, 0, 2]],
    ),
    (
        [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [1, 1, 1]],
    ),
    (
        [[0, 1, 0], [1, 1, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 1, 0], [1, 1, 0]],
    ),
    (
        [[1, 1, 1], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
    ),
    (
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [0, 1, 0]],
    ),
    (
        [[2, 0, 0], [2, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [2, 0, 0], [2, 0, 0]],
    ),
]


def test_canonical_inputs_are_accepted_and_mirror_exactly():
    for inp, expected in CANONICAL:
        assert GEN.self_check(inp) == []
        assert GEN.strict_canonical_like(inp) == []
        assert GEN.rule_mirror(inp) == expected


def test_exact_boundary_overrides_are_observable():
    for band in ("easy", "medium", "hard"):
        for profile in GEN.ROW_PROFILES:
            grid = GEN.generate(
                123,
                9,
                difficulty=band,
                grid_h=6,
                grid_w=3,
                fg_color=9,
                row_profile=profile,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {
                "grid_h": 6,
                "grid_w": 3,
                "fg_color": 9,
                "row_profile": profile,
            }


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


def test_bottom_drop_refutes_wraparound_shortcut():
    grid = GEN.generate(8, 3, grid_h=5, grid_w=5, row_profile="bottom_drop")
    assert GEN.SEMANTIC_WITNESSES["bottom_row_is_dropped"](grid)
    assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS["shift_down_with_wraparound"](grid)
    assert all(value == 0 for value in GEN.rule_mirror(grid)[0])


def test_self_check_rejects_targeted_impostors():
    impostors = [
        [[0] * 5 for _ in range(5)],
        [[1, 2, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
        [[1, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
        [[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
        [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [1, 1, 0, 0, 0]],
    ]
    for grid in impostors:
        assert GEN.self_check(grid), grid


def test_four_sequential_demos_are_identifiable():
    demos = []
    profiles = []
    for sample_index in range(4):
        inp = GEN.generate(777, sample_index, difficulty="medium")
        profiles.append(GEN.observe_overrides(inp)["row_profile"])
        demos.append({"input": inp, "output": GEN.rule_mirror(inp)})
    query_input = GEN.generate(777, 4, difficulty="medium")
    assert profiles == list(GEN.ROW_PROFILES)
    assert GEN.lesson_identifiable(demos, {"input": query_input}) == []


def test_generation_is_deterministic_fresh_and_rng_pure():
    random.seed(991)
    before = random.getstate()
    first = GEN.generate(2026, 11, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(2026, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    mutated = copy.deepcopy(first)
    mutated[0][0] = 9 if mutated[0][0] != 9 else 8
    assert second != mutated
