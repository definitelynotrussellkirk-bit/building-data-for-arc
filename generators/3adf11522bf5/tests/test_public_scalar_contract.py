"""Regression tests for strict public scalar validation."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "3adf11522bf5"
ROOT = find_root(__file__)
GEN, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_nonliteral_integer_seed(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(991, sample_index, difficulty="easy")
