from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.3551943cf546.generator")
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_python_mirror_matches_all_pairs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_sliding_four_example_window_contains_all_decisive_profiles_and_is_identifiable():
    expected = set(gen.SCHEDULE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(41000 + start, start + offset, band) for offset in range(5)]
            profiles = {
                gen.observe_overrides(pair["input"])["profile"]
                for pair in pairs[: gen.EXAMPLES_NEEDED]
            }
            assert profiles == expected
            assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in pairs[:4]
                ), name


def test_each_named_rival_has_a_targeted_control_profile():
    controls = {
        "mismatch": "connect_any_two_nonzero_cells_in_a_row",
        "multi_pair": "fill_only_first_pair_in_each_row",
        "triple": "fill_any_color_occurring_at_least_twice_in_a_row",
    }
    # Global-count shortcut needs the scheduled multi_pair form with n_pairs >= 3.
    for profile, rival_name in controls.items():
        grid = gen.generate(7123, 1, difficulty="medium", profile=profile)
        expected = gen.rule_mirror(grid)
        assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected

    grid = gen.generate(7123, 2, difficulty="medium", profile="multi_pair", n_pairs=3)
    assert gen.SEMANTIC_WITNESSES["pair_color_reused_across_rows"](grid)
    assert gen.SEMANTIC_RIVALS["require_color_to_occur_exactly_twice_globally"](grid) != gen.rule_mirror(grid)


def test_exact_override_axes_round_trip_at_boundaries_in_every_band():
    cases = [
        {"grid_h": 5, "grid_w": 8, "n_pairs": 2, "profile": "clean"},
        {"grid_h": 8, "grid_w": 12, "n_pairs": 4, "profile": "mismatch"},
        {"grid_h": 8, "grid_w": 12, "n_pairs": 4, "profile": "triple"},
        {"grid_h": 5, "grid_w": 8, "n_pairs": 2, "profile": "multi_pair"},
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(91 + index, 17 + index, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides


def test_unknown_override_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, typo_axis=4)


def test_mutation_fixtures_and_targeted_impostors_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    valid = gen.generate(1234, 1, difficulty="medium")

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()

    bad_color = copy.deepcopy(valid)
    bad_color[0][0] = 10

    filled_input = gen.rule_mirror(valid)

    for fixture in (ragged, bad_color, filled_input):
        assert gen.self_check(fixture)


def test_generation_is_deterministic_fresh_and_preserves_global_rng_state():
    random.seed(20260815)
    state_before = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")

    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_negative_recombination_is_distribution_invalid_but_rule_executable():
    # Apply the rule once, then feed that completed scene back to the oracle.
    # It is intentionally outside the generator's input distribution because
    # pair interiors are no longer background, but the rule itself is defined
    # and idempotent on the recombined grid.
    grid = gen.generate(19, 1, difficulty="medium")
    recombined = gen.rule_mirror(grid)
    assert gen.self_check(recombined)
    assert gen.rule_mirror(recombined) == recombined
