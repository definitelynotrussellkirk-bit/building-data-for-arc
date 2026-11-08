"""Focused regressions for the 1ba9f2a08016 generator repair."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.1ba9f2a08016.generator")


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_exact_and_input_pure():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "814d01ffdbb0"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_draws_are_lawful_and_keyed_axes_are_observable():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(32):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(5000 + sample_index, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert gen.self_check(grid) == []
            recorded = {
                name: value
                for name, value in captured[-1].recorded_draws().items()
                if name in gen.AXES
            }
            assert recorded == gen.observe_overrides(grid)


def test_every_three_demo_window_refutes_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in range(20):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_four_slot_schedule_has_all_profiles_and_every_window_has_combined_control():
    assert set(gen.SCHEDULE_PROFILES) == {0, 1, 2, 3}
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            observed = {gen.schedule_profile(0, start + offset) for offset in range(4)}
            assert observed == set(gen.SCHEDULE_PROFILES)
            scenes = [
                gen.observe_overrides(gen.generate(0, start + offset, difficulty=band))[
                    "scene_profile"
                ]
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            assert "combined_controls" in scenes


def test_exact_override_surface_round_trips_for_all_boundary_combinations():
    for band in ("easy", "medium", "hard"):
        for grid_h in (6, 10):
            for grid_w in (6, 10):
                for n_seeds in (3, 4):
                    for scene_profile in gen.SCENE_PROFILES:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_seeds": n_seeds,
                            "scene_profile": scene_profile,
                        }
                        grid = gen.generate(99, 17, difficulty=band, **requested)
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == requested


def test_unknown_and_mistyped_overrides_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, typo_palette="warm")
    with pytest.raises(ValueError, match="grid_h must be an integer"):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="scene_profile must be a string"):
        gen.generate(0, 0, scene_profile=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, n_seeds=2)


def test_self_check_rejects_targeted_structural_impostors():
    blank = [[0] * 8 for _ in range(8)]

    solid = [[0] * 8 for _ in range(8)]
    for r, c in ((3, 3), (3, 4), (4, 3), (4, 4)):
        solid[r][c] = 2

    output_color_in_input = gen.generate(100, 0)
    target = next(
        (r, c)
        for r, row in enumerate(output_color_in_input)
        for c, value in enumerate(row)
        if value == 0
    )
    output_color_in_input[target[0]][target[1]] = 6

    extra_decoy_in_clean_profile = gen.generate(101, 0, scene_profile="interior")
    target = next(
        (r, c)
        for r, row in enumerate(extra_decoy_in_clean_profile)
        for c, value in enumerate(row)
        if value == 0
        and all(abs(r - rr) + abs(c - cc) >= 2 for rr, cc in gen._seed_facts(extra_decoy_in_clean_profile)["seeds"])
    )
    extra_decoy_in_clean_profile[target[0]][target[1]] = 9

    missing_remote_control = gen.generate(102, 1, scene_profile="combined_controls")
    remote = gen._seed_facts(missing_remote_control)["remote_other"][0]
    missing_remote_control[remote[0]][remote[1]] = 0

    malformed_row = gen.generate(103, 0)
    malformed_row[0] = malformed_row[0][:-1]

    for fixture in (
        blank,
        solid,
        output_color_in_input,
        extra_decoy_in_clean_profile,
        missing_remote_control,
        malformed_row,
    ):
        assert gen.self_check(fixture), fixture


def test_negative_recombination_is_rejected_but_oracle_mirror_executes():
    grid = gen.generate(314, 0, scene_profile="corner", n_seeds=3)
    seed = gen._seed_facts(grid)["seeds"][1]
    # Replace one red seed with a novel color absent from every remaining part.
    assert all(value != 9 for row in grid for value in row)
    grid[seed[0]][seed[1]] = 9
    assert gen.self_check(grid)
    output = gen.rule_mirror(grid)
    assert output[seed[0]][seed[1]] == 9
    assert output != grid


def test_deterministic_fresh_returns_global_rng_and_reentrant_aba():
    random.seed(20260816)
    state = random.getstate()
    a = gen.generate(44, 9, difficulty="hard")
    b = gen.generate(45, 10, difficulty="easy")
    assert random.getstate() == state

    a_again = gen.generate(44, 9, difficulty="hard")
    assert a == a_again
    assert a is not a_again
    assert all(row is not other for row, other in zip(a, a_again))

    a_before = copy.deepcopy(a)
    b_before = copy.deepcopy(b)
    first = gen.rule_mirror(a)
    gen.rule_mirror(b)
    assert gen.rule_mirror(a) == first
    assert a == a_before
    assert b == b_before


def test_positional_seed_and_sample_index_require_nonnegative_exact_integers():
    for args, message in (
        ((True, 0), "seed must be a nonnegative exact integer"),
        ((0, -1), "sample_index must be a nonnegative exact integer"),
        ((0, "1"), "sample_index must be a nonnegative exact integer"),
    ):
        with pytest.raises(ValueError, match=message):
            gen.generate(*args)
