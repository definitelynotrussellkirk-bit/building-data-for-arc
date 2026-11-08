"""Strict request-boundary regressions for task 19e04051ad0d."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("19e04051ad0d", root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 7.0, "7"])
def test_seed_must_be_a_literal_python_integer(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 2.0, "2"])
def test_sample_index_must_be_a_literal_python_integer(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(17, bad_index, difficulty="easy")


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(17, -1, difficulty="easy")


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "impossible"])
def test_difficulty_must_use_the_declared_finite_domain(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(17, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        ("grid_h", True),
        ("grid_h", 10.0),
        ("grid_h", "10"),
        ("layout", False),
        ("layout", 312),
        ("bg_color", True),
        ("bg_color", 9.0),
        ("bg_color", 9.75),
        ("bg_color", "9"),
    ],
)
def test_declared_overrides_reject_coercible_scalar_aliases(axis, bad_value):
    with pytest.raises(TypeError, match=axis):
        GEN.generate(23, 0, difficulty="hard", **{axis: bad_value})


def test_none_override_is_behaviorally_identical_to_no_override():
    plain = GEN.generate(991, 5, difficulty="medium")
    explicit_none = GEN.generate(
        991,
        5,
        difficulty="medium",
        grid_h=None,
        layout=None,
        bg_color=None,
    )
    assert explicit_none == plain


def test_valid_exact_boundary_overrides_still_round_trip():
    expected = {"grid_h": 12, "layout": "222", "bg_color": 9}
    grid = GEN.generate(42, 7, difficulty="hard", **expected)
    assert GEN.observe_overrides(grid) == expected
