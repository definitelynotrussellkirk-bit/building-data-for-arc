"""Regression tests for strict public call-argument validation."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import load_generator  # noqa: E402


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_non_integer_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_rejects_non_integer_or_negative_scalars(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(991, bad_index, difficulty="hard")
