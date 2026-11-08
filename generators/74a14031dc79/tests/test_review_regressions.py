"""Focused reviewer regressions for task 74a14031dc79."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators/74a14031dc79/generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("review_generator_74a14031dc79", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize(
    "seed,sample_index",
    [
        (True, 0),
        (False, 0),
        (1.0, 0),
        (1.75, 0),
        ("1", 0),
        (0, True),
        (0, False),
        (0, 1.0),
        (0, 1.75),
        (0, "1"),
        (0, -1),
    ],
)
def test_seed_and_sample_index_require_strict_literal_integers(seed, sample_index):
    with pytest.raises(ValueError):
        gen.generate(seed, sample_index)
