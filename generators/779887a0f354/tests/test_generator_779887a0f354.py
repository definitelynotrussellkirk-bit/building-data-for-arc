from __future__ import annotations

import importlib
import itertools
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.779887a0f354.generator"
)


def _pair(grid):
    return {"input": grid, "output": MODULE.rule_mirror(grid)}


def test_generator_779887a0f354_canonical_parity_and_acceptance():
    pairs = canonical_pairs(MODULE.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_generator_779887a0f354_exact_override_matrix_and_unknown_key():
    for band in ("easy", "medium", "hard"):
        for index, (profile, size, blockers) in enumerate(
            itertools.product(MODULE.SCENE_PROFILES, MODULE.GRID_SIZES, (1, 2))
        ):
            grid = MODULE.generate(
                120_000 + index,
                index,
                difficulty=band,
                scene_profile=profile,
                grid_size=size,
                n_blockers=blockers,
            )
            assert MODULE.observe_overrides(grid) == {
                "scene_profile": profile,
                "grid_size": size,
                "n_blockers": blockers,
            }
            assert MODULE.self_check(grid, difficulty=band) == []
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 0, __override_contract_unknown_axis__="typo")


def test_generator_779887a0f354_every_five_example_window_identifies_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(20):
            seed = 700_000 + start
            demos = [
                _pair(MODULE.generate(seed, start + offset, difficulty=band))
                for offset in range(MODULE.EXAMPLES_NEEDED)
            ]
            query_grid = MODULE.generate(
                seed, start + MODULE.EXAMPLES_NEEDED, difficulty=band
            )
            assert MODULE.lesson_identifiable(demos, _pair(query_grid)) == []


def test_generator_779887a0f354_semantic_witnesses_fire_in_every_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in MODULE.SEMANTIC_WITNESSES}
        for sample_index in range(50):
            grid = MODULE.generate(810_000 + sample_index, sample_index, difficulty=band)
            assert MODULE.strict_canonical_like(grid) == []
            for name, predicate in MODULE.SEMANTIC_WITNESSES.items():
                hits[name] += bool(predicate(grid))
        assert all(count > 0 for count in hits.values()), hits


def test_generator_779887a0f354_self_check_rejects_structural_impostors():
    impostors = []

    empty = [[0] * 7 for _ in range(7)]
    empty[3][3] = 5
    impostors.append(empty)

    single = [[0] * 7 for _ in range(7)]
    single[3][3] = 4
    single[1][1] = 5
    impostors.append(single)

    adjacent_line = [[0] * 7 for _ in range(7)]
    adjacent_line[3][2:5] = [4, 4, 4]
    adjacent_line[1][1] = 5
    impostors.append(adjacent_line)

    solid_square = [[0] * 7 for _ in range(7)]
    solid_square[2][2] = solid_square[2][3] = 4
    solid_square[3][2] = solid_square[3][3] = 4
    solid_square[5][5] = 5
    impostors.append(solid_square)

    valid = MODULE.generate(91, 3, difficulty="medium")
    replacement_absent_elsewhere = [
        [7 if value == 4 else value for value in row] for row in valid
    ]
    impostors.append(replacement_absent_elsewhere)

    for grid in impostors:
        assert MODULE.self_check(grid), grid


def test_generator_779887a0f354_deterministic_fresh_and_global_rng_pure():
    random.seed(987654321)
    state = random.getstate()
    first = MODULE.generate(55, 8, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(55, 8, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
