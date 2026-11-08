"""Reject malformed exact controls without changing valid seeded samples."""
from __future__ import annotations

import hashlib
import json

import pytest
from reviewer_support import find_root, load_selected_generator


@pytest.fixture(scope="module")
def generator():
    return load_selected_generator("3977ec54e4a0", root=find_root(__file__))[0]


@pytest.mark.parametrize("field", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
def test_call_indices_require_real_python_integers(generator, field, value):
    arguments = {"seed": 17, "sample_index": 0}
    arguments[field] = value
    with pytest.raises((TypeError, ValueError), match=field):
        generator.generate(**arguments)


def test_negative_sample_index_rejected(generator):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        generator.generate(17, -1)


@pytest.mark.parametrize("value", [True, False, 0, 1.0, "other", "", ["medium"]])
def test_unknown_difficulty_does_not_silently_select_medium(generator, value):
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        generator.generate(17, 0, difficulty=value)


@pytest.mark.parametrize("axis,valid", [
    ("grid_h", 12), ("grid_w", 12), ("chevron_count", 2), ("max_depth", 2),
])
@pytest.mark.parametrize("kind", ["string", "whole_float", "fraction", "boolean"])
def test_exact_integer_axes_do_not_coerce(generator, axis, valid, kind):
    value = {"string": str(valid), "whole_float": float(valid),
             "fraction": valid + 0.75, "boolean": True}[kind]
    with pytest.raises((TypeError, ValueError), match=axis):
        generator.generate(17, 0, **{axis: value})


@pytest.mark.parametrize("value", [0, 1, 0.0, 1.0, "true", "false", []])
def test_boolean_axis_requires_a_boolean(generator, value):
    with pytest.raises((TypeError, ValueError), match="asymmetric_arms"):
        generator.generate(17, 0, asymmetric_arms=value)


@pytest.mark.parametrize("difficulty,index,expected", [
    ("easy", 0, "4e9c45ec423cef7a6d0c6a91440f7657a257649db7749ff61c1c59aa37e5101f"),
    ("easy", 2, "50f9bc4bc323b8e9ec79b4ad99106ead1ee0f20601859b045cbba2bd3afd1d36"),
    ("medium", 0, "ced9fc32712e4bbe4e7fc1871df5f82b144a6a19041af1f2f370c7a45c7edd2d"),
    ("medium", 2, "50f9bc4bc323b8e9ec79b4ad99106ead1ee0f20601859b045cbba2bd3afd1d36"),
    ("hard", 0, "1ba2d4128c1771b485bd83e9ae8252a62a753a7b786d99c91fd771a7cce9b292"),
    ("hard", 2, "50f9bc4bc323b8e9ec79b4ad99106ead1ee0f20601859b045cbba2bd3afd1d36"),
])
def test_valid_seeded_outputs_are_unchanged(generator, difficulty, index, expected):
    grid = generator.generate(17, index, difficulty=difficulty)
    digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
    assert digest == expected


def test_none_axis_sentinel_and_signed_seed_remain_supported(generator):
    grid = generator.generate(-17, 0, difficulty=None, grid_h=None,
                              asymmetric_arms=None)
    assert generator.self_check(grid) == []
