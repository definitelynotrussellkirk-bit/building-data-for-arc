from __future__ import annotations

import copy
import importlib
import random

gen = importlib.import_module("puzzle_generators.per_puzzle.7d1e8744229a.generator")


CANONICAL_INPUTS = [
    [[2, 3, 3, 3, 2], [3, 3, 5, 3, 3], [3, 5, 5, 5, 3], [3, 3, 5, 3, 3], [2, 3, 3, 3, 2]],
    [[9, 8, 8, 8, 9], [8, 8, 2, 8, 8], [8, 2, 2, 2, 8], [8, 8, 2, 8, 8], [9, 8, 8, 8, 9]],
    [[5, 1, 1, 1, 5], [1, 1, 9, 1, 1], [1, 9, 9, 9, 1], [1, 1, 9, 1, 1], [5, 1, 1, 1, 5]],
]


def _normalized(grid):
    roles = (grid[0][0], grid[0][1], grid[2][2])
    mapping = {color: index for index, color in enumerate(roles)}
    return tuple(tuple(mapping[value] for value in row) for row in grid)


def test_canonical_inputs_are_accepted_and_exactly_normalized():
    for grid in CANONICAL_INPUTS:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert _normalized(grid) == gen.INPUT_TEMPLATE


def test_generated_distribution_is_canonical_in_every_band():
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed, seed % 7, difficulty=band)
            assert gen.self_check(grid) == []
            assert _normalized(grid) == gen.INPUT_TEMPLATE
            assert gen.observe_overrides(grid) == {
                "grid_size": 5,
                "template": "canonical",
                "palette_size": 3,
            }


def test_self_check_rejects_four_targeted_impostors():
    base = copy.deepcopy(CANONICAL_INPUTS[0])

    wrong_size = [row[:-1] for row in base]
    duplicate_roles = copy.deepcopy(base)
    duplicate_roles[2][2] = duplicate_roles[0][0]
    off_template_cell = copy.deepcopy(base)
    off_template_cell[1][1] = off_template_cell[2][2]
    zero_role = copy.deepcopy(base)
    zero_role[0][0] = 0

    assert gen.self_check(wrong_size)
    assert gen.self_check(duplicate_roles)
    assert gen.self_check(off_template_cell)
    assert gen.self_check(zero_role)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(17, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(17, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert gen.generate(17, 4, difficulty="hard") == second


def test_exact_singleton_overrides_are_consumed_and_invalid_values_reject():
    grid = gen.generate(3, 1, grid_size=5, template="canonical", palette_size=3)
    assert gen.observe_overrides(grid)["grid_size"] == 5
    for kwargs in (
        {"grid_size": 4},
        {"template": "random"},
        {"palette_size": 2},
    ):
        try:
            gen.generate(3, 1, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"override should have rejected: {kwargs}")


def test_semantic_witnesses_and_lesson_identifiability():
    grids = [gen.generate(seed, seed) for seed in (11, 12, 13)]
    for grid in grids:
        assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())

    demos = []
    for grid in grids:
        roles = (grid[0][0], grid[0][1], grid[2][2])
        output = [[roles[symbol] for symbol in row] for row in gen.OUTPUT_TEMPLATE]
        demos.append({"input": grid, "output": output})
    assert gen.lesson_identifiable(demos, {"input": gen.generate(99, 0)}) == []
