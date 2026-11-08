from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.9edcccd1341f.generator"
)


def test_canonical_inputs_are_accepted_and_rule_mirror_is_exact() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 10
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_override_boundaries_are_observable() -> None:
    cases = [
        {"grid_h": 10},
        {"grid_h": 14},
        {"grid_w": 10},
        {"grid_w": 14},
        {"winner_count": 4},
        {"winner_count": 24},
        {"distractor_count": 2},
        {"distractor_count": 9},
        {"border_color": 1},
        {"border_color": 9},
        {"winner_color": 1},
        {"winner_color": 9},
        {
            "grid_h": 10,
            "grid_w": 10,
            "winner_count": 24,
            "distractor_count": 9,
            "border_color": 1,
            "winner_color": 9,
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(
            72_000 + index,
            5,
            difficulty=("easy", "medium", "hard")[index % 3],
            **overrides,
        )
        observed = gen.observe_overrides(grid)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        for name, expected in overrides.items():
            assert observed[name] == expected


def test_unknown_and_equal_color_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, unexpected_axis=7)
    with pytest.raises(ValueError, match="border_color and winner_color"):
        gen.generate(1, 2, border_color=4, winner_color=4)


def test_mutation_fixtures_and_negative_recombination_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name
    recombined, replacement = gen.negative_recombination_fixture()
    assert replacement not in {
        value
        for row in recombined
        for value in row
        if value != replacement
    }
    assert gen.self_check(recombined)


def test_every_ordinary_draw_refutes_named_rivals() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(30):
            grid = gen.generate(
                81_000 + band_index * 1_000 + seed,
                seed,
                difficulty=band,
            )
            official = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            for witness in gen.SEMANTIC_WITNESSES.values():
                assert witness(grid)
            for rival in gen.SEMANTIC_RIVALS.values():
                assert rival(grid) != official


def test_every_sliding_three_demo_window_is_identifiable() -> None:
    for band in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(14):
            grid = gen.generate(93_333, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(len(pairs) - gen.EXAMPLES_NEEDED):
            demos = pairs[start : start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    state = random.getstate()
    first = gen.generate(12_345, 8, difficulty="hard")
    second = gen.generate(12_345, 8, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    third = gen.generate(12_345, 8, difficulty="hard")
    assert third == second
    assert random.getstate() == state
