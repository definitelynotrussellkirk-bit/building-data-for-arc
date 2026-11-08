"""Strict public-call scalar contract for deterministic generation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("call_contract_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_nonliteral_or_negative_seed(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_nonliteral_or_negative_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, bad_index)


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_generate_rejects_unknown_difficulty(bad_difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [(True, 0, None), (0, -1, None), (0, 0, "unexpected")],
)
def test_schedule_profile_uses_the_same_strict_call_boundary(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.schedule_profile(seed, sample_index, difficulty)
