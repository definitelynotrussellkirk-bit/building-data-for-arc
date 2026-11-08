from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.47be86674731.generator")


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    expected_ranks = [0, 2, 1, 3]
    for index, pair in enumerate(pairs):
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert gen.semantic_observables(pair["input"])["target_rank"] == expected_ranks[index]
        assert pair["input"] == original


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_is_valid_and_covers_every_target_rank(band):
    grids = [gen.generate(1729, index, difficulty=band) for index in range(16)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert {gen.observe_overrides(grid)["target_rank"] for grid in grids} == {0, 1, 2, 3}
    assert {gen.observe_overrides(grid)["palette_mode"] for grid in grids} == {
        "nine_nonzero",
        "eight_nonzero",
    }
    assert {gen.observe_overrides(grid)["target_distribution"] for grid in grids} == {
        "balanced",
        "mixed",
        "skewed",
    }


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_axes_round_trip_at_boundaries(band):
    cases = (
        {
            "grid_h": 12,
            "grid_w": 18,
            "target_rank": 0,
            "palette_mode": "nine_nonzero",
            "target_distribution": "balanced",
        },
        {
            "grid_h": 18,
            "grid_w": 12,
            "target_rank": 3,
            "palette_mode": "eight_nonzero",
            "target_distribution": "skewed",
        },
        {
            "grid_h": 15,
            "grid_w": 15,
            "target_rank": 2,
            "palette_mode": "nine_nonzero",
            "target_distribution": "mixed",
        },
    )
    for overrides in cases:
        grid = gen.generate(99, 7, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_overrides_and_invalid_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="warm")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_declared_mutation_impostors_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(copy.deepcopy(grid)), name


def test_every_three_demo_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            demos = pairs[: gen.EXAMPLES_NEEDED]
            query = pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_deterministic_fresh_return_and_global_rng_purity():
    random.seed(2026)
    state = random.getstate()
    first = gen.generate(314159, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    original = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == original
    assert gen.generate(314159, 7, difficulty="hard") == original
