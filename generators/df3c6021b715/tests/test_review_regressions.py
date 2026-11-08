"""Regressions added by review-92b732083ae35fd7."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_df3c6021b715_regressions", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize(
    "difficulty",
    ["", "__invalid_difficulty__", 0, True, False, 1.5],
)
def test_generate_rejects_unknown_or_coercible_difficulty_values(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_values(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_values(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index)
