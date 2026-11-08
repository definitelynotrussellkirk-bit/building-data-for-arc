from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.dfdc40167549 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_sliding_five_sample_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            pairs = [
                _pair(8100 + start, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_schedule_covers_all_profiles_from_every_residue():
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(len(gen.SCHEDULE_PROFILES)):
        observed = {
            gen.schedule_profile(0, start + offset)
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert observed == expected


def test_exact_override_axes_round_trip_at_boundaries_in_every_band():
    for band in ("easy", "medium", "hard"):
        for grid_h, grid_w in ((9, 12), (16, 18)):
            for direction in gen.DIRECTIONS:
                for translation_mode in gen.TRANSLATION_MODES:
                    for shape_mode in gen.SHAPE_MODES:
                        overrides = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "vector_direction": direction,
                            "translation_mode": translation_mode,
                            "shape_mode": shape_mode,
                        }
                        grid = gen.generate(91, 17, difficulty=band, **overrides)
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == overrides


def test_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis="clipped")


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(1234, 0, difficulty="medium")
    ones, twos = gen._markers(valid)

    no_two = copy.deepcopy(valid)
    no_two[twos[0][0]][twos[0][1]] = 0

    extra_object = copy.deepcopy(valid)
    extra_object[-1][-1] = 6
    if extra_object[-1][-1] in (extra_object[ones[0][0]][ones[0][1]], 2):
        extra_object[-1][0] = 6

    source_color, source_cells, _ = gen._source_component(valid)
    output_color_source = copy.deepcopy(valid)
    for row, column in source_cells:
        output_color_source[row][column] = 7

    thin = [[0] * 12 for _ in range(9)]
    for column in range(2, 7):
        thin[2][column] = 3
    thin[6][1] = 1
    thin[7][8] = 2

    axis_aligned = copy.deepcopy(valid)
    axis_aligned[twos[0][0]][twos[0][1]] = 0
    replacement = next(
        (ones[0][0], column)
        for column in range(len(valid[0]))
        if axis_aligned[ones[0][0]][column] == 0 and column != ones[0][1]
    )
    axis_aligned[replacement[0]][replacement[1]] = 2

    fixtures = [no_two, extra_object, output_color_source, thin, axis_aligned]
    for fixture in fixtures:
        assert gen.self_check(fixture), fixture


def test_clipped_canonical_regression_is_accepted_not_rejected():
    clipped = canonical_pairs(gen.TASK_ID)[-1]["input"]
    assert gen.observe_overrides(clipped)["translation_mode"] == "clipped"
    assert gen.self_check(clipped) == []


def test_concave_witness_refutes_bounding_box_boundary_rival():
    grid = gen.generate(
        17,
        2,
        difficulty="hard",
        shape_mode="concave",
        translation_mode="full",
        vector_direction="down_left",
    )
    assert gen._bbox_border_translation(grid) != gen.rule_mirror(grid)


def test_generation_is_deterministic_fresh_and_preserves_global_rng_state():
    random.seed(20260729)
    state_before = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")

    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(first_row is not second_row for first_row, second_row in zip(first, second))


def test_canonical_profile_support_exists_in_every_band():
    for band in ("easy", "medium", "hard"):
        assert gen.strict_canonical_like(gen.generate(808, 0, difficulty=band)) == []
        assert gen.strict_canonical_like(gen.generate(808, 1, difficulty=band)) == []
