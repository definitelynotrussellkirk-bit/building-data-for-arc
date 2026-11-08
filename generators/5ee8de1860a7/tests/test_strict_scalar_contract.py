"""Portable regressions for strict generator scalar validation."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "5ee8de1860a7"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False])
def test_generate_rejects_boolean_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False])
def test_generate_rejects_boolean_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(991, bad_index, difficulty="easy")


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, -1, difficulty="easy")
