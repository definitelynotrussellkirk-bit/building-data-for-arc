"""Focused regressions for the centered object-gallery generator."""
from __future__ import annotations

import copy
import importlib
import random
from collections import Counter
from itertools import product

import pytest

from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
    normalized_rule_hash,
)


gen = importlib.import_module("puzzle_generators.per_puzzle.e68b376152cd.generator")
BANDS = ("easy", "medium", "hard")


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_four_canonical_pairs_are_exact_and_input_pure() -> None:
    assert canonical_rule_hash(gen.TASK_ID) == gen.RULE_HASH
    source = canonical_rule_source(gen.TASK_ID)
    assert normalized_rule_hash(source) == gen.RULE_HASH

    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    for band, grid_h, grid_w, n_objects in product(
        BANDS, (4, 8), (6, 12), (2, 5)
    ):
        requested = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_objects": n_objects,
        }
        grid = gen.generate(
            grid_h * 10_000 + grid_w * 100 + n_objects,
            17,
            difficulty=band,
            **requested,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bogus_axis": 1},
        {"grid_h": 3},
        {"grid_h": 9},
        {"grid_w": 5},
        {"grid_w": 13},
        {"n_objects": 1},
        {"n_objects": 6},
    ],
)
def test_unknown_and_out_of_domain_overrides_reject_loudly(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty="easy", **kwargs)


def test_strict_linked_semantic_census_200_per_band_and_disjoint_stability() -> None:
    expected_profiles = Counter({profile: 50 for profile in gen.SCHEDULE_PROFILES})
    expected_witnesses = Counter({
        "refutes_identity": 200,
        "refutes_row_major_order": 200,
        "refutes_sort_by_color": 200,
        "refutes_sort_by_area_ascending": 100,
        "refutes_sort_by_area_descending": 150,
        "refutes_reverse_left_to_right": 200,
        "refutes_top_align": 150,
        "refutes_bottom_align": 150,
        "refutes_fill_bounding_boxes": 200,
        "refutes_zero_column_gap": 200,
        "refutes_two_column_gap": 200,
    })

    for seed_start in (100_000, 900_000):
        for band in BANDS:
            profiles = Counter()
            witnesses = Counter()
            inputs = set()
            outputs = set()
            for offset in range(200):
                seed = seed_start + offset
                sample_index = seed_start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                assert gen.self_check(grid) == []
                assert gen.strict_canonical_like(grid) == []
                profiles[gen.schedule_profile(seed, sample_index, band)] += 1
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witnesses[name] += int(witness(grid))
                inputs.add(_key(grid))
                outputs.add(_key(gen.rule_mirror(grid)))
            assert profiles == expected_profiles
            assert witnesses == expected_witnesses
            assert len(inputs) >= 190
            assert len(outputs) >= 180


@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("band", BANDS)
def test_every_sliding_four_example_window_is_identifiable(start: int, band: str) -> None:
    demos = [
        _pair(710_001, index, band)
        for index in range(start, start + gen.EXAMPLES_NEEDED)
    ]
    query = _pair(710_001, start + gen.EXAMPLES_NEEDED, band)
    assert gen.lesson_identifiable(demos, query) == []
    assert {
        gen.schedule_profile(710_001, index, difficulty=band)
        for index in range(start, start + gen.EXAMPLES_NEEDED)
    } == set(gen.SCHEDULE_PROFILES)
    for name, competitor in gen.LESSON_COMPETITORS.items():
        assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(pair["input"]) for pair in demos), name


def test_targeted_mutation_fixtures_are_all_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_generation_is_replayable_fresh_global_rng_neutral_and_band_sensitive() -> None:
    random.seed(424_242)
    before = random.getstate()
    first = gen.generate(51, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(51, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(51, 7, difficulty="hard")

    band_outputs = {
        _key(gen.generate(51, 7, difficulty=band))
        for band in BANDS
    }
    assert len(band_outputs) >= 2
