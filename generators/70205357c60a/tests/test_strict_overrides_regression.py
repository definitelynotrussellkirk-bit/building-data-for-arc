"""Focused regression for strict numeric override handling.

The inherited root test_generator_70205357c60a.py is a frozen fixture.  New
repair coverage belongs in this separate task-local test module.
"""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator("70205357c60a", root=ROOT)


@pytest.mark.parametrize("axis", ("grid_h", "grid_w", "n_components"))
@pytest.mark.parametrize("bad_value", (9.75, True, "10"))
def test_integer_overrides_reject_non_literal_integers(
    axis: str, bad_value: object
) -> None:
    with pytest.raises((TypeError, ValueError), match=rf"{axis}.*integer"):
        gen.generate(0, 0, **{axis: bad_value})


@pytest.mark.parametrize("bad_difficulty", ("__invalid_difficulty__", True, 1))
def test_generate_rejects_invalid_difficulty_scalars(bad_difficulty: object) -> None:
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(0, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize("bad_seed", (True, 1.0, "1"))
def test_generate_rejects_non_integer_seed_scalars(bad_seed: object) -> None:
    with pytest.raises(TypeError, match="seed.*integer"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_sample_index", (True, 1.0, "1"))
def test_generate_rejects_non_integer_sample_index_scalars(
    bad_sample_index: object,
) -> None:
    with pytest.raises(TypeError, match="sample_index.*integer"):
        gen.generate(0, bad_sample_index)


def test_generate_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="sample_index.*non-negative"):
        gen.generate(0, -1)
