"""Regression tests for strict public scalar validation."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "7b8cb193f82c"
ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0, difficulty="medium")


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, bad_sample_index, difficulty="medium")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_schedule_profile_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.schedule_profile(bad_seed, 0, difficulty="medium")


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_schedule_profile_rejects_invalid_sample_index_scalars(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.schedule_profile(991, bad_sample_index, difficulty="medium")


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "invalid"])
def test_schedule_profile_rejects_invalid_difficulty_scalars(bad_difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.schedule_profile(991, 0, difficulty=bad_difficulty)
