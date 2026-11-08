"""Focused regression tests for the 2026-10-21 review repairs."""
from __future__ import annotations

import json

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "964b23808a3c"
ROOT = find_root(__file__)
GENERATOR, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
COUNTEREXAMPLE = json.loads(
    (ROOT / "generators" / TASK_ID / "counterexamples" / "strict_scalar_contract.json").read_text()
)


@pytest.mark.parametrize("bad_seed", COUNTEREXAMPLE["invalid_seed_values"])
def test_generate_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        GENERATOR.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", COUNTEREXAMPLE["invalid_sample_index_values"])
def test_generate_rejects_nonliteral_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        GENERATOR.generate(1, bad_index)


def test_generate_rejects_negative_sample_index_but_accepts_integer_seed_domain():
    with pytest.raises(ValueError, match="sample_index.*nonnegative|nonnegative.*sample_index"):
        GENERATOR.generate(1, COUNTEREXAMPLE["invalid_negative_sample_index"])
    grid = GENERATOR.generate(COUNTEREXAMPLE["lawful_negative_seed"], 0)
    assert GENERATOR.self_check(grid) == []


@pytest.mark.parametrize("bad_seed", COUNTEREXAMPLE["invalid_seed_values"])
def test_schedule_profile_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed"):
        GENERATOR.schedule_profile(bad_seed, 0)


@pytest.mark.parametrize("bad_index", COUNTEREXAMPLE["invalid_sample_index_values"])
def test_schedule_profile_rejects_invalid_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index"):
        GENERATOR.schedule_profile(1, bad_index)


def test_schedule_profile_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index.*nonnegative|nonnegative.*sample_index"):
        GENERATOR.schedule_profile(1, COUNTEREXAMPLE["invalid_negative_sample_index"])
