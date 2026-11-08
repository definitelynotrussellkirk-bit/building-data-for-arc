"""Focused regression for the public generation schedule domain."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root


REPO = find_root(__file__)
GENERATOR_PATH = REPO / "generators" / "49754d8fa42e" / "generator.py"


def _load_generator():
    name = "generator_49754d8fa42e_negative_index_regression"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_public_generation_schedule_rejects_negative_sample_index():
    gen = _load_generator()
    for function in (gen.generate, gen.schedule_profile, gen.schedule_spatial_witness):
        with pytest.raises(ValueError, match="sample_index.*nonnegative"):
            function(0, -1)
