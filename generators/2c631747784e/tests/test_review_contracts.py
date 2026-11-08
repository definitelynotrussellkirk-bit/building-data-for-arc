from __future__ import annotations

import importlib

import pytest



gen = importlib.import_module("puzzle_generators.per_puzzle.2c631747784e.generator")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_scalar_coercions(bad_seed: object) -> None:
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_sample_index_rejects_scalar_coercions(bad_index: object) -> None:
    with pytest.raises(TypeError, match="sample_index"):
        gen.generate(1, bad_index, difficulty="easy")


def test_sample_index_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(1, -1, difficulty="easy")


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "invalid"])
def test_difficulty_rejects_unsupported_scalars(bad_difficulty: object) -> None:
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "path_length", "n_distinct_colors"])
@pytest.mark.parametrize("bad_value", [True, False, 8.0, 8.75, "8"])
def test_integer_override_axes_reject_scalar_coercions(
    axis: str, bad_value: object
) -> None:
    with pytest.raises(TypeError, match=axis):
        gen.generate(1, 0, difficulty="easy", **{axis: bad_value})


@pytest.mark.parametrize("bad_value", [0, 1, 0.0, 1.0, "true", "false"])
def test_boolean_override_axis_requires_literal_bool(bad_value: object) -> None:
    with pytest.raises(TypeError, match="anchor_corner"):
        gen.generate(1, 0, difficulty="easy", anchor_corner=bad_value)


def test_partial_rivals_are_not_declared_as_canonical_shortcuts() -> None:
    assert set(gen.CANONICAL_SHORTCUTS).isdisjoint(gen.LESSON_COMPETITORS)
