"""Regression tests for the selected generator's public call boundary."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import load_generator


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_ambiguous_seed_scalars(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_ambiguous_or_negative_sample_indices(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index)
