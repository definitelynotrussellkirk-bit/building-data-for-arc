from __future__ import annotations

import importlib

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.3a0af56db83e.generator")


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_non_integer_seed(bad):
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad, 0)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_non_integer_sample_index(bad):
    with pytest.raises(TypeError, match="sample_index"):
        gen.generate(991, bad)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(991, -1)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_schedule_profile_rejects_non_integer_seed(bad):
    with pytest.raises(TypeError, match="seed"):
        gen.schedule_profile(bad, 0)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_schedule_profile_rejects_non_integer_sample_index(bad):
    with pytest.raises(TypeError, match="sample_index"):
        gen.schedule_profile(991, bad)


def test_schedule_profile_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        gen.schedule_profile(991, -1)


def test_negative_integer_seed_remains_valid_and_deterministic():
    first = gen.generate(-7, 0)
    second = gen.generate(-7, 0)
    assert first == second
    assert gen.self_check(first) == []
