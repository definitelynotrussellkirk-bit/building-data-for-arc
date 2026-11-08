from __future__ import annotations

import importlib
import itertools
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.56169a1e5c1d.generator")
TASK_ID = "56169a1e5c1d"


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "d1b9f133bb98"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_are_consumed_and_observable() -> None:
    cases = list(
        itertools.product(
            (7, 16),
            (7, 16),
            (2, 3),
        )
    )
    assert len(cases) == 8
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, (h, w, pair_count) in enumerate(cases):
            grid = gen.generate(
                50_000 + 1000 * band_index + case_index,
                80_000 + case_index,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                pair_count=pair_count,
            )
            assert (len(grid), len(grid[0])) == (h, w)
            assert gen.observe_overrides(grid)["pair_count"] == pair_count
            assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, difficulty="easy", invented_axis="accepted")


def test_three_sample_schedule_covers_all_near_misses_and_identifies_lessons() -> None:
    expected_modes = set(gen.DECOY_MODES)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(9):
            demos = [
                _pair(110_000 + 1000 * band_index + start, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                110_000 + 1000 * band_index + start,
                start + gen.EXAMPLES_NEEDED,
                band,
            )
            modes = {
                gen.decoy_mode(start + offset)
                for offset in range(gen.EXAMPLES_NEEDED)
            }
            assert modes == expected_modes
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_profile_anchor_is_real_in_every_band() -> None:
    canonical_profiles = set(gen.CANONICAL_MORPHOLOGY_PROFILES)
    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 3, 6, 9):
            grid = gen.generate(20260815, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            assert profile in canonical_profiles
            assert gen.strict_canonical_like(grid) == []


def test_targeted_structural_impostors_are_rejected() -> None:
    assert gen.self_check([[0] * 7 for _ in range(7)])

    ambiguous = [[0] * 7 for _ in range(7)]
    ambiguous[1][1] = ambiguous[3][3] = 2
    ambiguous[1][3] = ambiguous[3][1] = 4
    errors = gen.self_check(ambiguous)
    assert any("ambiguous active midpoint" in error for error in errors)

    unsupported_repeat = gen.generate(41, 0, difficulty="easy")
    unsupported_repeat = deepcopy(unsupported_repeat)
    # Fresh color 9 repeated at an unsupported horizontal distance three.
    unsupported_repeat[0][0] = 9
    unsupported_repeat[0][3] = 9
    assert gen.self_check(unsupported_repeat)

    too_many = gen.generate(42, 0, difficulty="easy")
    too_many = deepcopy(too_many)
    color = next(pair.color for pair in gen._fillable_pairs(too_many))
    empties = [
        (r, c)
        for r, row in enumerate(too_many)
        for c, value in enumerate(row)
        if value == 0
    ]
    too_many[empties[0][0]][empties[0][1]] = color
    too_many[empties[1][0]][empties[1][1]] = color
    assert any("expected one to three" in e for e in gen.self_check(too_many))

    invalid_color = gen.generate(43, 0, difficulty="easy")
    invalid_color = deepcopy(invalid_color)
    invalid_color[0][0] = 10
    assert any("invalid color" in e for e in gen.self_check(invalid_color))


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(555, 777, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(555, 777, difficulty="medium")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if second[0][0] != 9 else 8
    assert first != second


def test_every_four_pair_window_survives_query_rotation() -> None:
    """Any one of four consecutive pairs may be the held-out query."""
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(9):
            pairs = [
                _pair(
                    210_000 + 1000 * band_index + start,
                    start + offset,
                    band,
                )
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_offset, query in enumerate(pairs):
                demos = [
                    pair
                    for pair_offset, pair in enumerate(pairs)
                    if pair_offset != query_offset
                ]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_offset,
                    gen.lesson_identifiable(demos, query),
                )
