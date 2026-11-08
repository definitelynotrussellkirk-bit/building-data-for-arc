from __future__ import annotations

import importlib
import random
from itertools import product
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.4ee97d4d2321.generator"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_python_reference_are_pinned_to_canonical_authority():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "7546649ac4b7"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_set_exercises_both_sides_and_out_of_bounds_branches():
    observed = [gen.observe_overrides(pair["input"]) for pair in canonical_pairs(gen.TASK_ID)]
    assert any(row["source_mode"] == "both" for row in observed)
    assert any(row["source_mode"] == "partial_oob" for row in observed)
    assert any(row["axis_offset"] != 0 for row in observed)


def test_unknown_override_key_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(0, 0, difficulty="easy", typo_axis=3)


def test_each_declared_axis_round_trips_at_boundaries_and_modes():
    cases = [
        {"grid_h": 6},
        {"grid_h": 12},
        {"grid_w": 9},
        {"grid_w": 13},
        {"axis_offset": -2},
        {"axis_offset": 2},
        {"n_cells": 4},
        {"n_cells": 10},
        {"n_colors": 2},
        {"n_colors": 4},
        *({"source_mode": mode} for mode in gen.SOURCE_MODES),
        {
            "grid_h": 6,
            "grid_w": 9,
            "axis_offset": -2,
            "n_cells": 4,
            "n_colors": 2,
            "source_mode": "both",
        },
        {
            "grid_h": 12,
            "grid_w": 13,
            "axis_offset": 2,
            "n_cells": 10,
            "n_colors": 4,
            "source_mode": "partial_oob",
        },
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
        for name, value in overrides.items():
            assert observed[name] == value
        assert gen.self_check(grid) == []


def test_only_the_declared_centered_odd_clipping_tuple_is_rejected():
    for width in (9, 11, 13):
        with pytest.raises(
            ValueError,
            match=r"source_mode=.*axis_offset=0.*grid_w=",
        ):
            gen.generate(
                1,
                3,
                difficulty="medium",
                source_mode="partial_oob",
                axis_offset=0,
                grid_w=width,
            )

    # Pinning any two members still leaves the generator room to adapt the third.
    assert gen.observe_overrides(
        gen.generate(
            1,
            3,
            source_mode="partial_oob",
            axis_offset=0,
        )
    )["grid_w"] % 2 == 0
    assert gen.observe_overrides(
        gen.generate(
            1,
            3,
            source_mode="partial_oob",
            grid_w=9,
        )
    )["axis_offset"] != 0


def test_every_four_consecutive_examples_cover_the_semantic_schedule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(gen.generate(777, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                gen.generate(777, start + gen.EXAMPLES_NEEDED, difficulty=band)
            )
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen.observe_overrides(pair["input"])["source_mode"]
                for pair in demos
            } == set(gen.SOURCE_MODES)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (band, start, name)


def test_every_witness_really_refutes_at_least_one_claimed_rival():
    grids = [gen.generate(123, index, difficulty="medium") for index in range(16)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for grid in firing:
            expected = gen.rule_mirror(grid)
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != expected
                for rival_name in rival_names
            ), witness_name


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(55, 2, difficulty="medium", source_mode="both")
    info, errors = gen._analyse(base)
    assert errors == []
    axis = info["axis"]

    no_axis = deepcopy(base)
    no_axis[0][axis] = 0

    second_axis = deepcopy(base)
    second_col = 0 if axis != 0 else len(base[0]) - 1
    for row in range(len(second_axis)):
        second_axis[row][second_col] = 8

    off_axis_cyan = deepcopy(base)
    target = next(
        (r, c)
        for r, row in enumerate(off_axis_cyan)
        for c, value in enumerate(row)
        if c != axis and value == 0
    )
    off_axis_cyan[target[0]][target[1]] = 8

    occupied_mirror = deepcopy(base)
    source = info["active_sources"][0]
    mirror = (source[0], 2 * axis - source[1])
    occupied_mirror[mirror[0]][mirror[1]] = 3

    one_color = deepcopy(base)
    for row, col in info["sources"]:
        one_color[row][col] = 1

    ragged = deepcopy(base)
    ragged[-1] = ragged[-1][:-1]

    for impostor in (
        no_axis,
        second_axis,
        off_axis_cyan,
        occupied_mirror,
        one_color,
        ragged,
    ):
        assert gen.self_check(impostor), impostor


def test_negative_recombination_is_grammar_invalid_but_oracle_execution_is_separate():
    grid = gen.generate(901, 0, difficulty="easy", source_mode="left")
    info, errors = gen._analyse(grid)
    assert errors == []
    row, col = info["active_sources"][0]
    mirror_col = 2 * info["axis"] - col

    recombined = deepcopy(grid)
    recombined[row][mirror_col] = 9 if grid[row][col] != 9 else 7
    assert gen.self_check(recombined)

    # The selected rule is still executable on this broader input.  This does
    # not make the recombination a calibrated generator scene.
    output = gen.rule_mirror(recombined)
    assert len(output) == len(recombined)
    assert all(len(row_out) == len(recombined[0]) for row_out in output)


def test_replay_is_deterministic_fresh_and_global_rng_independent():
    before_state = random.getstate()
    first = gen.generate(100, 9, difficulty="hard")
    after_state = random.getstate()
    second = gen.generate(100, 9, difficulty="hard")

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before_state == after_state

    first[0][0] = 5
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


def _axis_offset_side_shortcut(grid):
    """Plausible shortcut: infer which side to mirror from axis displacement."""
    height, width = len(grid), len(grid[0])
    axis = next(
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    )
    offset = axis - (width - 1) // 2
    if offset == 0:
        selected_side = "both"
    elif abs(offset) == 1:
        selected_side = "left" if offset < 0 else "right"
    else:
        selected_side = "right" if offset < 0 else "left"

    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 8):
                continue
            if selected_side == "left" and col > axis:
                continue
            if selected_side == "right" and col < axis:
                continue
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = value
    return out


def test_default_schedule_crosses_mode_with_offset_and_refutes_position_shortcut():
    expected_joint_support = set(product(gen.SOURCE_MODES, range(-2, 3)))

    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(8700, index, difficulty=band) for index in range(23)]
        observed = [gen.observe_overrides(grid) for grid in grids]

        assert {
            (row["source_mode"], row["axis_offset"])
            for row in observed[:20]
        } == expected_joint_support

        for start in range(20):
            window = grids[start : start + gen.EXAMPLES_NEEDED]
            assert any(
                _axis_offset_side_shortcut(grid) != gen.rule_mirror(grid)
                for grid in window
            ), (band, start)



def test_declared_schedule_profiles_expose_the_full_joint_cycle():
    expected = set(product(gen.SOURCE_MODES, range(-2, 3)))
    profiles = [gen.schedule_profile(99, index, "medium") for index in range(20)]

    assert set(gen.SCHEDULE_PROFILES) == expected
    assert set(profiles) == expected
    assert [gen.schedule_profile(99, index + 20, "medium") for index in range(20)] == profiles


def test_axis_position_shortcut_is_a_declared_lesson_competitor():
    name = "infer_source_side_from_axis_offset"
    assert name in gen.LESSON_COMPETITORS

    for band in ("easy", "medium", "hard"):
        for index in range(20):
            grid = gen.generate(8800, index, difficulty=band)
            assert gen.LESSON_COMPETITORS[name](grid) == _axis_offset_side_shortcut(grid)
