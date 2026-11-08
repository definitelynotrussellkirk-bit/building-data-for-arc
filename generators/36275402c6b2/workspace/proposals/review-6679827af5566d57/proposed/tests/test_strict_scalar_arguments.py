"""Regression tests for exact public generator call types."""
from __future__ import annotations

import pytest
from reviewer_support import find_root, load_selected_generator

TASK_ID = "36275402c6b2"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", -1])
def test_seed_requires_non_negative_literal_integer(bad_seed):
    with pytest.raises(ValueError, match="seed must be a non-negative literal integer"):
        GEN.generate(bad_seed, 0, difficulty="medium")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_non_negative_literal_integer(bad_index):
    with pytest.raises(
        ValueError, match="sample_index must be a non-negative literal integer"
    ):
        GEN.generate(17, bad_index, difficulty="medium")


@pytest.mark.parametrize(
    "bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_difficulty_requires_declared_literal(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty must be None"):
        GEN.generate(17, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    "axis,bad_value",
    [
        ("grid_h", True),
        ("grid_h", 11.0),
        ("grid_h", "11"),
        ("grid_w", True),
        ("grid_w", 11.0),
        ("grid_w", "11"),
        ("rect_h", True),
        ("rect_h", 4.0),
        ("rect_h", "4"),
        ("rect_w", True),
        ("rect_w", 4.0),
        ("rect_w", "4"),
        ("frame_color", True),
        ("frame_color", 1.0),
        ("frame_color", "1"),
        ("pair_count", True),
        ("pair_count", 2.0),
        ("pair_count", "2"),
    ],
)
def test_integer_axes_reject_bool_float_and_string(axis, bad_value):
    with pytest.raises(ValueError, match=rf"{axis} must be a literal integer"):
        GEN.generate(17, 0, difficulty="medium", **{axis: bad_value})


def test_none_remains_the_shared_no_override_sentinel():
    expected = GEN.generate(17, 0, difficulty="medium")
    actual = GEN.generate(
        17,
        0,
        difficulty="medium",
        grid_h=None,
        grid_w=None,
        rect_h=None,
        rect_w=None,
        frame_color=None,
        pair_count=None,
    )
    assert actual == expected
