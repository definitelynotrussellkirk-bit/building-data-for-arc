"""Regression tests for the generator's public scalar contract."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from puzzle_generators.per_puzzle.f6b9f647b109 import generator as gen


def _generate(seed: Any, sample_index: Any, difficulty: Any) -> Any:
    return gen.generate(seed, sample_index, difficulty=difficulty)


def _profile(seed: Any, sample_index: Any, difficulty: Any) -> Any:
    return gen.schedule_profile(seed, sample_index, difficulty=difficulty)


PUBLIC_ENTRYPOINTS: tuple[Callable[[Any, Any, Any], Any], ...] = (
    _generate,
    _profile,
)


@pytest.mark.parametrize("entrypoint", PUBLIC_ENTRYPOINTS)
@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_public_entrypoints_reject_non_integer_seed(entrypoint, bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        entrypoint(bad_seed, 0, "easy")


@pytest.mark.parametrize("entrypoint", PUBLIC_ENTRYPOINTS)
@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_public_entrypoints_reject_non_integer_sample_index(entrypoint, bad_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        entrypoint(991, bad_index, "medium")


@pytest.mark.parametrize("entrypoint", PUBLIC_ENTRYPOINTS)
def test_public_entrypoints_reject_negative_sample_index(entrypoint):
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        entrypoint(991, -1, "hard")


@pytest.mark.parametrize("entrypoint", PUBLIC_ENTRYPOINTS)
@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_public_entrypoints_reject_invalid_difficulty(entrypoint, bad_difficulty):
    with pytest.raises(ValueError, match="difficulty must be"):
        entrypoint(991, 0, bad_difficulty)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w"])
@pytest.mark.parametrize("bad_value", [True, False, "6", 6.0, 6.75, "26", 26.0, 26.75])
def test_generate_rejects_coercible_non_integer_dimension_overrides(axis, bad_value):
    with pytest.raises(TypeError, match=rf"{axis} must be an integer"):
        gen.generate(991, 0, difficulty="easy", **{axis: bad_value})


@pytest.mark.parametrize("axis", ["grid_h", "grid_w"])
@pytest.mark.parametrize("bad_value", [5, 27])
def test_generate_rejects_out_of_range_dimension_overrides(axis, bad_value):
    with pytest.raises(ValueError, match=rf"{axis} must be in 6\.\.26"):
        gen.generate(991, 0, difficulty="easy", **{axis: bad_value})


def test_valid_identity_and_difficulty_values_remain_supported():
    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(0, 0, difficulty=difficulty, grid_h=6, grid_w=6)
        assert gen.self_check(grid) == []
        assert gen.schedule_profile(0, 0, difficulty=difficulty) == gen.SCHEDULE_PROFILES[0]
