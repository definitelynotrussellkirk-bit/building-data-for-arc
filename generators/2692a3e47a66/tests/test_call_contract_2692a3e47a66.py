"""Public call-contract regressions, portable to the selected task runtime."""
from __future__ import annotations

import random

import pytest
from reviewer_support import find_root, load_selected_generator

GEN, _, _ = load_selected_generator("2692a3e47a66", root=find_root(__file__))


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_an_integer_without_coercion(seed):
    state = random.getstate()
    with pytest.raises(ValueError, match="seed"):
        GEN.generate(seed, 0, difficulty="medium")
    assert random.getstate() == state


@pytest.mark.parametrize("index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_integer(index):
    state = random.getstate()
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(71, index, difficulty="medium")
    assert random.getstate() == state


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0])
def test_difficulty_accepts_only_the_documented_names_or_none(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(71, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [71, 911])
@pytest.mark.parametrize("index", range(8))
def test_none_scene_profile_preserves_the_scheduled_draw(seed, index):
    expected = GEN.generate(seed, index, difficulty="medium")
    actual = GEN.generate(seed, index, difficulty="medium", scene_profile=None)
    assert actual == expected
    assert GEN.observe_overrides(actual)["scene_profile"] == GEN.schedule_profile(
        seed, index, "medium"
    )


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_valid_negative_seed_zero_index_and_all_none_overrides(difficulty):
    expected = GEN.generate(-7, 0, difficulty=difficulty)
    actual = GEN.generate(-7, 0, difficulty=difficulty,
                          grid_h=None, grid_w=None, scene_profile=None)
    assert actual == expected
    assert GEN.self_check(actual) == []
