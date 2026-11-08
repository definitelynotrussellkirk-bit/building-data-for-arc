from __future__ import annotations

import pytest

from puzzle_generators.per_puzzle.e1516c24afbd import generator as gen


@pytest.mark.parametrize(
    ("seed", "sample_index"),
    [
        (True, 0),
        (1.0, 0),
        ("1", 0),
        (1, True),
        (1, 1.0),
        (1, "1"),
        (1, -1),
    ],
)
def test_generate_rejects_nonliteral_or_negative_call_scalars(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


@pytest.mark.parametrize("axis", ["half_h", "grid_w", "both_zero_count"])
@pytest.mark.parametrize("value", [True, 3.0, "3"])
def test_integer_overrides_reject_bool_float_and_string(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, **{axis: value})


@pytest.mark.parametrize("axis", ["top_color", "bot_color"])
@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_color_overrides_reject_bool_float_and_string(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, **{axis: value})


def test_literal_integer_boundaries_remain_supported():
    grid = gen.generate(
        17,
        0,
        half_h=3,
        grid_w=3,
        top_color=1,
        bot_color=9,
        both_zero_count=1,
        layout="random",
    )
    assert gen.observe_overrides(grid) == {
        "half_h": 3,
        "grid_w": 3,
        "top_color": 1,
        "bot_color": 9,
        "both_zero_count": 1,
        "layout": "random",
    }
