"""Regression tests for strict public control validation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("strict_controls_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_without_coercion(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_without_coercion(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(991, bad_index, difficulty="easy")


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        ("grid_h", "7"),
        ("grid_h", 7.0),
        ("grid_w", "6"),
        ("grid_w", 6.0),
        ("horizontal_thickness", True),
        ("horizontal_thickness", 1.0),
        ("vertical_thickness", True),
        ("vertical_thickness", 1.0),
        ("horizontal_color", True),
        ("horizontal_color", 1.0),
        ("vertical_color_offset", True),
        ("vertical_color_offset", 1.0),
    ],
)
def test_integer_overrides_reject_bool_float_and_string(axis, bad_value):
    with pytest.raises((TypeError, ValueError), match=axis):
        GEN.generate(991, 0, difficulty="easy", **{axis: bad_value})


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        ("horizontal_position", 1),
        ("vertical_position", 1),
        ("occluder", 1),
    ],
)
def test_choice_overrides_reject_non_strings(axis, bad_value):
    with pytest.raises((TypeError, ValueError), match=axis):
        GEN.generate(991, 0, difficulty="easy", **{axis: bad_value})


def test_schedule_profile_applies_the_same_strict_request_contract():
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.schedule_profile(1.0, 0, "easy")
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.schedule_profile(1, -1, "easy")


def test_valid_integer_controls_and_none_sentinel_remain_supported():
    expected = GEN.generate(991, 0, difficulty="easy")
    assert GEN.generate(991, 0, difficulty="easy", grid_h=None) == expected
    grid = GEN.generate(
        -5,
        0,
        difficulty="hard",
        grid_h=7,
        grid_w=6,
        horizontal_thickness=1,
        vertical_thickness=1,
        horizontal_position="top",
        vertical_position="left",
        horizontal_color=1,
        vertical_color_offset=8,
        occluder="vertical",
    )
    assert GEN.self_check(grid) == []
