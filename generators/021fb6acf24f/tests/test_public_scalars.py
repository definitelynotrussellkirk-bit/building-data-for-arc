"""Regression tests for the generator's public scalar call contract."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import load_generator  # noqa: E402


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


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
