from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "b8d6fabb411e"
ROOT = find_root(__file__)
gen, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_literal_integer_seed(bad_seed) -> None:
    with pytest.raises(TypeError, match="seed must be a literal integer"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_literal_integer_sample_index(bad_sample_index) -> None:
    with pytest.raises(TypeError, match="sample_index must be a literal integer"):
        gen.generate(1, bad_sample_index)


def test_generate_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.generate(1, -1)


@pytest.mark.parametrize("bad_seed", [True, 1.0, "1"])
def test_schedule_rejects_non_literal_integer_seed(bad_seed) -> None:
    with pytest.raises(TypeError, match="seed must be a literal integer"):
        gen.schedule_profile(bad_seed, 0)


@pytest.mark.parametrize("bad_sample_index", [True, 1.0, "1"])
def test_schedule_rejects_invalid_sample_index(bad_sample_index) -> None:
    with pytest.raises(TypeError, match="sample_index must be a literal integer"):
        gen.schedule_profile(1, bad_sample_index)


def test_schedule_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        gen.schedule_profile(1, -1)


def test_schedule_rejects_invalid_difficulty() -> None:
    with pytest.raises(ValueError, match="difficulty must be"):
        gen.schedule_profile(1, 0, difficulty="expert")
