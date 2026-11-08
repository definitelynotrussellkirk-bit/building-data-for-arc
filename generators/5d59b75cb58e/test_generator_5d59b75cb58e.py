from __future__ import annotations

import copy
import random

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.5d59b75cb58e.generator")
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_inputs_are_owned_and_rule_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(before) == []
        assert gen.strict_canonical_like(before) == []
        assert gen.rule_mirror(before) == pair["output"]
        assert before == pair["input"]


def test_exact_override_boundaries_are_observable():
    for side in (8, 12):
        for n_blobs in (2, 3):
            for blob_size in (3, 5):
                for source_sides in gen.SCHEDULE_PROFILES:
                    grid = gen.generate(
                        41,
                        7,
                        difficulty="easy",
                        side=side,
                        n_blobs=n_blobs,
                        blob_size=blob_size,
                        source_sides=source_sides,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "side": side,
                        "n_blobs": n_blobs,
                        "blob_size": blob_size,
                        "source_sides": source_sides,
                    }


def test_schedule_covers_all_source_modes_in_every_three_example_window():
    for start in range(20):
        profiles = {
            gen.schedule_profile(123, index, "hard")
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        }
        assert profiles == set(gen.SCHEDULE_PROFILES)


def test_upper_source_is_a_regression_witness_against_lower_only_shortcut():
    grid = gen.generate(90210, 1, difficulty="medium", source_sides="upper")
    official = gen.rule_mirror(grid)
    assert gen._lower_only_add(grid) != official
    assert gen.SEMANTIC_WITNESSES["upper_sources"](grid)


def test_structural_impostors_are_rejected():
    valid = gen.generate(7, 2, difficulty="medium", source_sides="both")

    nonsquare = [row[:-1] for row in valid]
    assert gen.self_check(nonsquare)

    diagonal_only = [[0] * 8 for _ in range(8)]
    diagonal_only[1][1] = 2
    diagonal_only[2][2] = 3
    assert gen.self_check(diagonal_only)

    already_symmetric = [[0] * 8 for _ in range(8)]
    for r, c in ((5, 1), (5, 2), (4, 2)):
        already_symmetric[r][c] = 2
        already_symmetric[c][r] = 2
    for r, c in ((6, 3), (6, 4), (5, 4)):
        already_symmetric[r][c] = 3
        already_symmetric[c][r] = 3
    assert gen.self_check(already_symmetric)

    rectangular_blobs = [[0] * 8 for _ in range(8)]
    for r, c in ((5, 1), (5, 2), (6, 1), (6, 2)):
        rectangular_blobs[r][c] = 2
    for r, c in ((1, 5), (1, 6), (2, 5), (2, 6)):
        rectangular_blobs[r][c] = 3
    assert gen.self_check(rectangular_blobs)


def test_unknown_override_and_invalid_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, mystery_axis=1)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="impossible")


def test_determinism_fresh_returns_and_global_rng_preservation():
    random.seed(991)
    before = random.getstate()
    first = gen.generate(12345, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(12345, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
