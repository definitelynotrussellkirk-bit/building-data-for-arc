"""Regression tests for the public recipe-identity scalar boundary."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_66387591ebe6_identity_under_test", TASK_DIR / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize(
    "seed", [True, 1.25, "17", None], ids=["true", "float", "string", "none"]
)
def test_generate_rejects_noninteger_seed(seed):
    with pytest.raises(ValueError, match=r"^seed must be an integer"):
        gen.generate(seed, 3, difficulty="medium")


def test_generate_accepts_negative_integer_seed():
    grid = gen.generate(-7, 3, difficulty="medium", key=1)
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == grid


@pytest.mark.parametrize(
    "sample_index",
    [True, False, 1.25, "3", -1],
    ids=["true", "false", "float", "string", "negative"],
)
def test_generate_rejects_noninteger_or_negative_sample_index(sample_index):
    with pytest.raises(ValueError, match=r"^sample_index must be a nonnegative integer"):
        gen.generate(17, sample_index, difficulty="medium")
