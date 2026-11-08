"""Behavioral regressions for the stable row-packing generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "a1b1c1f9b042"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_row_pack_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def stable_pack(grid):
    return [
        [value for value in row if value != 0]
        + [0] * sum(value == 0 for value in row)
        for row in grid
    ]


def measured(grid):
    colors = {value for row in grid for value in row if value != 0}
    return len(grid), len(grid[0]), len(colors)


def has_descending_row(grid):
    for row in grid:
        values = [value for value in row if value != 0]
        if any(left > right for left, right in zip(values, values[1:])):
            return True
    return False


def needs_left_shift(grid):
    return any(
        [c for c, value in enumerate(row) if value != 0]
        != list(range(sum(value != 0 for value in row)))
        for row in grid
    )


def test_declares_exact_current_rule_identity_and_real_axes_only():
    assert gen.RULE_HASH == "8cd149b15ecf"
    assert set(gen.AXES) == {"grid_h", "grid_w", "palette_size"}
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "h,w,palette_size",
    [(2, 4, 2), (3, 6, 5), (4, 5, 7), (8, 10, 9)],
)
def test_exact_joint_controls_are_realized_in_pixels(band, h, w, palette_size):
    grid = gen.generate(
        712,
        5,
        difficulty=band,
        grid_h=h,
        grid_w=w,
        palette_size=palette_size,
    )
    assert measured(grid) == (h, w, palette_size)
    assert not gen.self_check(grid)
    assert has_descending_row(grid)
    assert needs_left_shift(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_largest_palette_override_remains_feasible_in_every_band(band):
    grid = gen.generate(37, 0, difficulty=band, palette_size=9)
    assert measured(grid)[2] == 9
    assert not gen.self_check(grid)


@pytest.mark.parametrize(
    "axes",
    [
        {"misspelled_axis": 3},
        {"grid_h": 1},
        {"grid_h": 9},
        {"grid_w": 3},
        {"grid_w": 11},
        {"grid_h": True},
        {"grid_w": 6.5},
        {"palette_size": "4"},
        {"palette_size": 1},
        {"palette_size": 10},
        {"grid_h": 2, "grid_w": 4, "palette_size": 7},
    ],
)
def test_invalid_or_impossible_controls_fail_loudly(axes):
    with pytest.raises(ValueError):
        gen.generate(12, 0, **axes)


@pytest.mark.parametrize("difficulty", ["", "expert", 3, True])
def test_invalid_difficulty_values_fail_loudly(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_seed_scalars_fail_loudly(seed):
    with pytest.raises(ValueError):
        gen.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_scalars_fail_loudly(sample_index):
    with pytest.raises(ValueError):
        gen.generate(991, sample_index, difficulty="hard")


def test_impossible_joint_control_names_the_incompatible_axes():
    with pytest.raises(ValueError) as caught:
        gen.generate(1, 2, grid_h=2, grid_w=4, palette_size=7)
    assert set(caught.value.incompatible_axes) == {
        "grid_h",
        "grid_w",
        "palette_size",
    }


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 2], [0]],
        [[0] * 6 for _ in range(3)],
        [[3] * 6 for _ in range(3)],
        [[False, 2, 0, 0], [0, 3, 0, 0]],
        [[10, 2, 0, 0], [0, 3, 0, 0]],
        [[1, 2, 3, 4], [0, 5, 0, 6]],
        [[1, 0, 0, 0], [0, 0, 0, 0]],
        [[1, 2, 0, 0], [3, 4, 0, 0]],
    ],
)
def test_validator_rejects_malformed_or_non_teaching_inputs(grid):
    assert gen.self_check(grid)


def test_validator_accepts_every_canonical_input():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    assert all(not gen.self_check(pair["input"]) for pair in pairs)
    assert all(gen.strict_canonical_like(pair["input"]) == [] for pair in pairs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_schedule_profiles_match_exact_color_and_occupancy_profiles(band):
    for seed in range(6):
        three_by_six = gen.generate(seed, 0, difficulty=band)
        four_by_five = gen.generate(seed, 1, difficulty=band)

        three_profile = (
            len(three_by_six),
            len(three_by_six[0]),
            len({value for row in three_by_six for value in row}),
        )
        four_profile = (
            len(four_by_five),
            len(four_by_five[0]),
            len({value for row in four_by_five for value in row}),
        )
        assert three_profile in {(3, 6, 8), (3, 6, 9)}
        assert sum(value != 0 for row in three_by_six for value in row) in {7, 8}
        assert four_profile == (4, 5, 10)
        assert sum(value != 0 for row in four_by_five for value in row) == 9


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_contains_canonical_shapes_and_extended_shapes(band):
    shapes = {
        measured(gen.generate(103, index, difficulty=band))[:2]
        for index in range(18)
    }
    assert {(3, 6), (4, 5)} <= shapes
    assert any(shape not in {(3, 6), (4, 5)} for shape in shapes)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_sample_is_a_sort_shortcut_counterexample(band):
    for seed in range(12):
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty=band)
            truth = stable_pack(grid)
            assert not gen.self_check(grid)
            assert has_descending_row(grid)
            assert needs_left_shift(grid)
            assert gen.SEMANTIC_RIVALS["sort_then_pack_left"](grid) != truth


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_window_refutes_all_declared_lesson_competitors(band):
    for seed in range(12):
        for start in range(6):
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": stable_pack(grid)} for grid in grids]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_retained_ambiguous_lesson_is_detected_by_the_contract():
    old_inputs = [
        [[0, 0, 0, 5, 0], [0, 0, 7, 0, 0], [3, 0, 7, 7, 0]],
        [[0, 0, 0, 0, 7], [0, 0, 0, 3, 0], [0, 1, 0, 5, 0], [3, 0, 0, 0, 0]],
        [[0, 3, 6, 0, 0], [3, 4, 0, 6, 0], [0, 0, 0, 4, 0]],
        [[0, 0, 0, 5, 0, 0], [0, 0, 8, 7, 0, 0], [0, 8, 0, 0, 5, 0]],
    ]
    pairs = [{"input": grid, "output": stable_pack(grid)} for grid in old_inputs]
    reasons = gen.lesson_identifiable(pairs[:3], pairs[3])
    assert reasons == ["declared rival sort_then_pack_left survives demonstrations and changes query"]


def test_observer_reports_every_exact_axis_from_pixels():
    for index in range(12):
        grid = gen.generate(312, index)
        h, w, palette_size = measured(grid)
        assert gen.observe_overrides(grid) == {
            "grid_h": h,
            "grid_w": w,
            "palette_size": palette_size,
        }


def test_determinism_and_no_returned_grid_aliasing():
    first = gen.generate(876, 9, difficulty="hard")
    expected = [row[:] for row in first]
    first[0][0] = 99
    assert gen.generate(876, 9, difficulty="hard") == expected
