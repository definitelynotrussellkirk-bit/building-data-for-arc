"""Portable regression tests for strict generator call arguments."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    helper = ancestor / "shared" / "runtime"
    if (helper / "reviewer_support.py").is_file():
        sys.path.insert(0, str(helper))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import find_root, load_selected_generator

TASK_ID = "f1347e0836ec"
ROOT = find_root(__file__)
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        GENERATOR.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_sample_index_scalars(sample_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GENERATOR.generate(991, sample_index, difficulty="easy")


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        GENERATOR.generate(991, -1, difficulty="easy")
