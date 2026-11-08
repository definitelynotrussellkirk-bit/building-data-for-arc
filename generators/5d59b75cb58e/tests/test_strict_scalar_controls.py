"""Regression coverage for exact scalar controls in generator 5d59b75cb58e."""
from __future__ import annotations

import importlib

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.5d59b75cb58e.generator")


@pytest.mark.parametrize("value", [True, False, 1.0, "1"])
def test_generate_rejects_non_integer_sample_index(value):
    with pytest.raises(TypeError, match="sample_index.*integer"):
        gen.generate(991, value, difficulty="easy")


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index.*nonnegative"):
        gen.generate(991, -1, difficulty="easy")


@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_generate_rejects_non_integer_seed(value):
    with pytest.raises(TypeError, match="seed.*integer"):
        gen.generate(value, 0, difficulty="easy")


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("side", 12.75),
        ("n_blobs", 3.75),
        ("blob_size", 5.75),
        ("side", 8.0),
        ("n_blobs", "2"),
        ("blob_size", True),
    ],
)
def test_integer_axis_overrides_reject_non_integer_values(axis, value):
    overrides = {
        "side": 8,
        "n_blobs": 2,
        "blob_size": 3,
        "source_sides": "upper",
    }
    overrides[axis] = value
    with pytest.raises(TypeError, match="override must be an integer"):
        gen.generate(29051, 1, difficulty="medium", **overrides)


@pytest.mark.parametrize("value", [True, False, 1.0, "1"])
def test_schedule_profile_rejects_non_integer_sample_index(value):
    with pytest.raises(TypeError, match="sample_index.*integer"):
        gen.schedule_profile(0, value, "easy")


def test_schedule_profile_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index.*nonnegative"):
        gen.schedule_profile(0, -1, "easy")
