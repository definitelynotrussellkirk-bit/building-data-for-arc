from __future__ import annotations

import importlib
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.f1bb0165c32b.generator"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_python_reference_match_canonical_authority():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "ed1061be40ca"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_unknown_override_key_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(0, 0, difficulty="easy", typo_axis=3)


def test_every_axis_round_trips_at_boundaries_and_in_a_mixed_case():
    cases = [
        {"grid_h": 8},
        {"grid_h": 12},
        {"grid_w": 10},
        {"grid_w": 14},
        {"n_runs": 5},
        {"n_runs": 8},
        {"n_length4": 2},
        {"n_length4": 3},
        {"grid_h": 8, "grid_w": 10, "n_runs": 5, "n_length4": 2},
        {"grid_h": 12, "grid_w": 14, "n_runs": 8, "n_length4": 3},
    ]
    bands = ("easy", "medium", "hard")
    for index, overrides in enumerate(cases):
        grid = gen.generate(
            900 + index,
            30 + index,
            difficulty=bands[index % len(bands)],
            **overrides,
        )
        observed = gen.observe_overrides(grid)
        assert all(observed[name] == value for name, value in overrides.items())
        assert gen.strict_canonical_like(grid) == []


def test_every_four_example_window_is_identifiable_and_covers_all_profiles():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(gen.generate(777, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                gen.generate(778, start + gen.EXAMPLES_NEEDED, difficulty=band)
            )
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen.schedule_profile(777, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED)
            } == set(gen.SCHEDULE_PROFILES)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band,
                    start,
                    name,
                )


def test_named_witnesses_refute_every_claimed_rival():
    grids = [gen.generate(123, index, difficulty="medium") for index in range(16)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for rival_name in rival_names:
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)
                for grid in firing
            ), (witness_name, rival_name)


def test_self_check_rejects_all_task_local_mutation_fixtures():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_negative_recombination_is_invalid_for_lessons_but_rule_still_executes():
    grid = gen.generate(901, 0, difficulty="easy")
    recombined = deepcopy(grid)
    row, column = next(
        (r, c)
        for r, values in enumerate(recombined)
        for c, value in enumerate(values)
        if value == 0
    )
    recombined[row][column] = 3  # a replacement color absent from the scene
    assert gen.self_check(recombined)
    output = gen.rule_mirror(recombined)
    assert len(output) == len(recombined)
    assert all(len(out_row) == len(recombined[0]) for out_row in output)


def test_replay_is_deterministic_fresh_and_global_rng_independent():
    before = random.getstate()
    first = gen.generate(100, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(100, 9, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9
    assert gen.generate(100, 9, difficulty="hard") == second


def test_default_population_varies_every_declared_axis_in_each_band():
    for band in ("easy", "medium", "hard"):
        seen = {name: set() for name in gen.AXES}
        for index in range(72):
            observed = gen.observe_overrides(
                gen.generate(5000 + index, index, difficulty=band)
            )
            for name in seen:
                seen[name].add(observed[name])
        assert all(len(values) >= 2 for values in seen.values()), (band, seen)
