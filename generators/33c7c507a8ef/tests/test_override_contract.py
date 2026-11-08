"""Regressions for exact scalar controls and the no-override convention."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


generator, _, _ = load_selected_generator(
    "33c7c507a8ef", root=find_root(__file__)
)


@pytest.mark.parametrize(
    "override",
    [
        {"code": True},
        {"code": 2.9},
        {"interior_h": 2.5},
        {"interior_w": "3"},
        {"frame_top": True},
        {"frame_left": 1.9},
        {"n_content_colors": 3.9},
        {"include_frame_color": 1},
    ],
    ids=[
        "boolean-code",
        "fractional-code",
        "fractional-height",
        "string-width",
        "boolean-frame-top",
        "fractional-frame-left",
        "fractional-color-count",
        "integer-gray-flag",
    ],
)
def test_wrong_type_overrides_are_rejected_before_coercion(override):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, scene_family="generalized", **override)


def test_canonical_wrong_type_is_a_caller_error():
    # A float equal to a legal code must not reach grid construction and cause
    # an internal RuntimeError while the same value is coerced in another family.
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, scene_family="canonical", code=2.0)


@pytest.mark.parametrize("family", ["canonical", "generalized"])
@pytest.mark.parametrize(
    "axis",
    [
        "code",
        "interior_h",
        "interior_w",
        "frame_top",
        "frame_left",
        "n_content_colors",
        "include_frame_color",
    ],
)
def test_none_known_axis_is_identical_to_omission(family, axis):
    expected = generator.generate(0, 0, scene_family=family)
    actual = generator.generate(0, 0, scene_family=family, **{axis: None})
    assert actual == expected


def test_none_scene_family_is_identical_to_omission():
    assert generator.generate(0, 0, scene_family=None) == generator.generate(0, 0)


def test_none_does_not_hide_unknown_axis_names():
    with pytest.raises(ValueError, match="unknown"):
        generator.generate(0, 0, misspelled_code=None)


@pytest.mark.parametrize(
    "case",
    [
        dict(code=1, interior_h=2, interior_w=2, frame_top=1, frame_left=1,
             n_content_colors=3, include_frame_color=False),
        dict(code=2, interior_h=2, interior_w=3, frame_top=1, frame_left=1,
             n_content_colors=4, include_frame_color=True),
        dict(code=4, interior_h=3, interior_w=2, frame_top=4, frame_left=5,
             n_content_colors=4, include_frame_color=False),
        dict(code=3, interior_h=6, interior_w=7, frame_top=4, frame_left=5,
             n_content_colors=4, include_frame_color=True),
    ],
    ids=["minimum-area", "four-colors-short-wide", "four-colors-tall-narrow", "maximum-bounds"],
)
def test_valid_joint_boundary_controls_remain_exact(case):
    grid = generator.generate(0, 0, scene_family="generalized", **case)
    assert generator.self_check(grid) == []
    observed = generator.observe_overrides(grid)
    assert observed["scene_family"] == "generalized"
    for name, requested in case.items():
        assert type(observed[name]) is type(requested)
        assert observed[name] == requested


@pytest.mark.parametrize("code", [2, 3, 4])
def test_linked_canonical_profiles_remain_available(code):
    grid = generator.generate(
        0, 0, scene_family="canonical", code=code,
        include_frame_color=(code == 3),
    )
    assert generator.self_check(grid) == []
    assert generator.canonical_profile_signature(grid) is not None


@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize(
    "value",
    [False, True, 0.0, 1.5, "0", -1],
    ids=["false", "true", "integral-float", "fractional-float", "numeric-string", "negative"],
)
def test_generation_arguments_require_exact_nonnegative_integers(argument, value):
    arguments = {"seed": 0, "sample_index": 0}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError)):
        generator.generate(**arguments)


@pytest.mark.parametrize("value", [0, 1])
def test_generation_arguments_accept_nonnegative_integer_boundaries(value):
    grid = generator.generate(seed=value, sample_index=value)
    assert generator.self_check(grid) == []
