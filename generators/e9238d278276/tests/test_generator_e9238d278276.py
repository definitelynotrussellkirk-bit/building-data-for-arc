from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.e9238d278276 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_python_mirror_matches_all_pairs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_training_descending_shortcut_fits_demos_but_fails_query():
    pairs = canonical_pairs(gen.TASK_ID)
    train, query = pairs[:2], pairs[2]
    rival = gen.SEMANTIC_RIVALS["sort_descending_then_pack_up"]
    assert all(rival(pair["input"]) == pair["output"] for pair in train)
    assert rival(query["input"]) != query["output"]


def test_every_sliding_four_example_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(5)]
            assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:4]), name


def test_schedule_covers_every_profile_from_every_residue():
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(4):
        observed = {
            gen.schedule_profile(0, start + offset)
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert observed == expected


def test_exact_override_axes_round_trip_at_boundaries_in_every_band():
    for band in ("easy", "medium", "hard"):
        for grid_h, grid_w in ((6, 6), (16, 16)):
            for n_cols in (3, 6):
                for n_colors in (2, 9):
                    for order_profile in gen.ORDER_PROFILES:
                        overrides = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_cols": n_cols,
                            "n_distinct_colors": n_colors,
                            "order_profile": order_profile,
                        }
                        grid = gen.generate(91, 17, difficulty=band, **overrides)
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == overrides


def test_unknown_override_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=4)


def test_mutation_fixtures_and_targeted_impostors_are_rejected():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name

    valid = gen.generate(1234, 1, difficulty="medium")

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()

    foreign_color = copy.deepcopy(valid)
    foreign_color[0][0] = 10

    removed_column = copy.deepcopy(valid)
    active = gen._active_columns(removed_column)
    for row in removed_column:
        for column in active[:3]:
            row[column] = 0

    packed = gen.rule_mirror(valid)

    for fixture in (ragged, foreign_color, removed_column, packed):
        assert gen.self_check(fixture)


def test_generation_is_deterministic_fresh_and_preserves_global_rng_state():
    random.seed(20260729)
    state_before = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")

    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_canonical_profile_support_and_semantic_witnesses_exist_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(808, index, difficulty=band) for index in range(40)]
        strict = sum(not gen.strict_canonical_like(grid) for grid in grids)
        assert strict >= 20
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), name


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = gen.generate(19, 1, difficulty="medium")
    recombined = gen.rule_mirror(grid)
    assert gen.self_check(recombined)
    assert gen.rule_mirror(recombined) == recombined
