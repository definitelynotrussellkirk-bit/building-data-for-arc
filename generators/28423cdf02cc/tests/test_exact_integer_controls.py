"""Exact integer controls must never silently coerce a different scalar type."""
from __future__ import annotations

import pytest
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator("28423cdf02cc", root=ROOT)
AXES = [("grid_h", 9, 16), ("grid_w", 13, 20),
        ("n_dots", 3, 6), ("palette_size", 3, 5)]


@pytest.mark.parametrize("axis,lo,hi", AXES)
@pytest.mark.parametrize("kind", ["numeric_string", "fractional_float", "integral_float", "boolean"])
def test_exact_axes_reject_non_integer_scalars(axis, lo, hi, kind):
    bad = {"numeric_string": str(lo), "fractional_float": lo+0.75,
           "integral_float": float(lo), "boolean": True}[kind]
    for band in ("easy", "medium", "hard"):
        with pytest.raises((TypeError, ValueError)):
            GENERATOR.generate(11, 2, difficulty=band, **{axis: bad})


@pytest.mark.parametrize("axis,lo,hi", AXES)
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_literal_integer_boundaries_remain_exact(axis, lo, hi, band):
    for value in (lo, hi):
        grid = GENERATOR.generate(11, 2, difficulty=band, **{axis: value})
        assert not GENERATOR.self_check(grid)
        observed = GENERATOR.observe_overrides(grid)[axis]
        assert type(observed) is int and observed == value


@pytest.mark.parametrize("axis,lo,hi", AXES)
def test_none_keeps_default_schedule_semantics(axis, lo, hi):
    for index in range(5):
        assert GENERATOR.generate(11, index, **{axis: None}) == GENERATOR.generate(11, index)


@pytest.mark.parametrize("argument,bad", [(name, value) for name in ("seed", "sample_index")
                                         for value in (True, False, 1.0, 1.75, "1")]
                                        + [("sample_index", -1)])
def test_call_arguments_reject_invalid_scalars(argument, bad):
    for band in ("easy", "medium", "hard"):
        arguments = {"seed": 11, "sample_index": 2, "difficulty": band}
        arguments[argument] = bad
        with pytest.raises((TypeError, ValueError)):
            GENERATOR.generate(**arguments)


def test_negative_integer_seed_remains_a_valid_deterministic_family():
    first = GENERATOR.generate(-7, 2)
    assert not GENERATOR.self_check(first)
    assert first == GENERATOR.generate(-7, 2)
