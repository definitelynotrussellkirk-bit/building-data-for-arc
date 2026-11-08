"""Regression tests for direct ``generate`` scalar arguments.

This is canonical-repair coverage, not part of the parametric prototype.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


_spec = importlib.util.spec_from_file_location(
    "projection_call_contract_support", Path(__file__).with_name("contract_support.py")
)
support = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(support)
GEN, _SOURCE, _ROOT = support.load_generator(__file__)


INVALID_SEEDS = (True, False, 1.0, 1.75, "1")
INVALID_SAMPLE_INDICES = (True, False, 1.0, 1.75)
DIFFICULTIES = ("easy", None, "hard")


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("seed", INVALID_SEEDS, ids=repr)
def test_non_integer_seed_rejects(seed, difficulty):
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(seed, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("sample_index", INVALID_SAMPLE_INDICES, ids=repr)
def test_non_integer_sample_index_rejects(sample_index, difficulty):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.generate(991, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_negative_sample_index_rejects(difficulty):
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        GEN.generate(991, -1, difficulty=difficulty)


EXPECTED_VALID_HASHES = {
    "easy": "555bb4d6f178dd08b17be85dea991e1573050a885999d2ec4faeb334e1b8aca0",
    "None": "555bb4d6f178dd08b17be85dea991e1573050a885999d2ec4faeb334e1b8aca0",
    "hard": "555bb4d6f178dd08b17be85dea991e1573050a885999d2ec4faeb334e1b8aca0",
}


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_valid_calls_remain_deterministic_and_byte_stable(difficulty):
    first = GEN.generate(991, 0, difficulty=difficulty)
    second = GEN.generate(991, 0, difficulty=difficulty)
    assert first == second
    digest = hashlib.sha256(
        json.dumps(first, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert digest == EXPECTED_VALID_HASHES[str(difficulty)]
