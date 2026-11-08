"""Portable regressions for strict generator scalar validation."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "089c14df9952"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_sample_index_scalars(bad_sample_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.generate(991, bad_sample_index, difficulty="easy")


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        GEN.generate(991, -1, difficulty="easy")


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        ("grid_h", "11"),
        ("grid_h", 11.0),
        ("grid_h", 11.75),
        ("grid_w", "12"),
        ("grid_w", 12.0),
        ("grid_w", 12.75),
        ("target_count", True),
        ("target_count", "1"),
        ("target_count", 1.0),
        ("target_count", 1.75),
    ],
)
def test_generate_rejects_coercible_non_integer_axis_overrides(axis, bad_value):
    with pytest.raises(TypeError, match="override must be an integer"):
        GEN.generate(991, 0, difficulty="easy", **{axis: bad_value})
