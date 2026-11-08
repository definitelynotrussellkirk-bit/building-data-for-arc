"""Observable strict override contract, including the complete bounded matrix."""
from copy import deepcopy
import random

import pytest

from oracle_3b1ef21add2f import red_components, red_windows, window_cells


AXIS_LIMITS = {"grid_h": (7, 16), "grid_w": (7, 16), "n_windows": (0, 8)}
BANDS = (None, "easy", "medium", "hard")


def test_declared_axes_and_version_match_public_contract(generator):
    assert generator.VERSION == "3.0.0"
    assert set(generator.AXES) == set(AXIS_LIMITS)
    for name, (low, high) in AXIS_LIMITS.items():
        assert generator.AXES[name]["type"] == "int"
        assert generator.AXES[name]["valid"] == f"{low}..{high}"


@pytest.mark.parametrize("name", AXIS_LIMITS)
@pytest.mark.parametrize("value", [True, False, 7.0, 7.5, "7", "", [], {}, float("nan")])
def test_exact_axes_reject_coercible_and_noninteger_values(generator, name, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(7, 1, **{name: value})


@pytest.mark.parametrize("name", AXIS_LIMITS)
def test_exact_axes_reject_both_out_of_range_boundaries(generator, name):
    low, high = AXIS_LIMITS[name]
    for value in (low - 1, high + 1, -1000, 1000):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(5, 2, **{name: value})


@pytest.mark.parametrize("name, value", [
    ("n_blocks", 2), ("palette_kind", "default"), ("palette_size", 1),
    ("position_bias", "spaced_2x2_red_blocks"), ("n_distinct_colors", 1),
    ("density", "sparse"), ("texture", "default"),
    ("texture", "no_full_blocks"), ("texture", "blocks_touching"),
    ("unrecognized_control", 1), ("unrecognized_control", None),
])
def test_unknown_and_obsolete_axes_are_rejected(generator, name, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(3, 1, **{name: value})


@pytest.mark.parametrize("difficulty", BANDS)
def test_none_is_equivalent_to_an_omitted_known_axis(generator, difficulty):
    expected = generator.generate(18, 2, difficulty=difficulty)
    for overrides in ({"grid_h": None}, {"grid_w": None}, {"n_windows": None},
                      dict.fromkeys(AXIS_LIMITS)):
        assert generator.generate(18, 2, difficulty=difficulty, **overrides) == expected


@pytest.mark.parametrize("difficulty", BANDS)
def test_joint_dimension_and_window_bounds_are_realizable(generator, difficulty):
    # 10 x 10 x 9 combinations per band. This catches clipped requests,
    # overlap undercounting, infeasible placement, and difficulty-bound leaks.
    for height in range(7, 17):
        for width in range(7, 17):
            for count in range(9):
                index = (height + width + count) % 8
                grid = generator.generate(29, index, difficulty=difficulty,
                                          grid_h=height, grid_w=width, n_windows=count)
                call = (difficulty, height, width, count, index)
                assert type(grid) is list and len(grid) == height, call
                assert all(type(row) is list and len(row) == width for row in grid), call
                assert all(type(value) is int and 0 <= value <= 9
                           for row in grid for value in row), call
                assert len(red_windows(grid)) == count, call
                assert any(0 in row for row in grid), call
                assert len(red_components(grid)) >= 2, call
                if count:
                    covered = window_cells(grid)
                    assert any(value == 2 and (row, col) not in covered
                               for row, values in enumerate(grid)
                               for col, value in enumerate(values)), call
                assert generator.self_check(grid) == [], call


@pytest.mark.parametrize("difficulty", BANDS)
def test_replay_has_no_global_rng_or_returned_grid_dependency(generator, difficulty):
    overrides = {"grid_h": 7, "grid_w": 16, "n_windows": 8}
    before = deepcopy(overrides)
    state = random.getstate()
    first = generator.generate(91, 7, difficulty=difficulty, **overrides)
    expected = deepcopy(first)
    assert random.getstate() == state
    first[0][0] = 9 if first[0][0] != 9 else 8
    generator.generate(999, 24, difficulty=difficulty)
    assert generator.generate(91, 7, difficulty=difficulty, **overrides) == expected
    assert overrides == before
