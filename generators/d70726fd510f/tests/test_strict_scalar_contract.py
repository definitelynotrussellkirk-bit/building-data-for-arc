"""Strict public scalar validation for the selected generator entry point."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    helper = ancestor / "shared/runtime"
    if (helper / "reviewer_support.py").is_file():
        sys.path.insert(0, str(helper))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import find_root

TASK = "d70726fd510f"
ROOT = find_root(__file__)


@pytest.fixture(scope="module")
def generator():
    source = ROOT / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("d707_strict_scalar_generator", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_nonliteral_integer_seeds(generator, seed):
    with pytest.raises(ValueError, match="seed must be an integer"):
        generator.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1])
def test_generate_rejects_invalid_sample_indices(generator, sample_index):
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        generator.generate(991, sample_index)
