"""Regression tests for strict public call controls.

These tests live outside the frozen baseline fixture and cover the exact
strict-scalar defect reported by the before-phase linter.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root

TASK_ID = "8de1c257a9c7"
ROOT = find_root(__file__)
_RUNTIME_GENERATOR = ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
_LIBRARY_GENERATOR = ROOT / f"generators/{TASK_ID}/generator.py"
GENERATOR_PATH = (
    _RUNTIME_GENERATOR if _RUNTIME_GENERATOR.is_file() else _LIBRARY_GENERATOR
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "strict_scalar_generator_8de1c257a9c7", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_coercible_seed_scalars(gen, bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_coercible_sample_index_scalars(gen, bad_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.generate(991, bad_index, difficulty="easy")


def test_generate_rejects_negative_sample_index(gen):
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.generate(991, -1, difficulty="easy")


@pytest.mark.parametrize(
    "bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_generate_rejects_invalid_difficulty_scalars(gen, bad_difficulty):
    with pytest.raises(ValueError, match="difficulty must be one of"):
        gen.generate(991, 0, difficulty=bad_difficulty)


def test_schedule_profile_uses_the_same_strict_public_contract(gen):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.schedule_profile(True, 0, "easy")
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        gen.schedule_profile(1, 0.0, "easy")
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.schedule_profile(1, -1, "easy")
    with pytest.raises(ValueError, match="difficulty must be one of"):
        gen.schedule_profile(1, 0, "expert")
