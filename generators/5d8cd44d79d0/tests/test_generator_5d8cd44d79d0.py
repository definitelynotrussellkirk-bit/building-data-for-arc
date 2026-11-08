from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "5d8cd44d79d0"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.5d8cd44d79d0.generator"
)


def test_all_canonical_inputs_are_accepted_and_outputs_match_rule_mirror():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 10
    for pair in pairs:
        grid = pair["input"]
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_regression_color_boundaries_define_objects_without_blank_rows():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 2, 2, 0, 0],
        [0, 2, 0, 0, 0],
        [0, 3, 3, 3, 0],
        [0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    assert gen.self_check(grid) == []
    expected = [
        [0, 0, 0, 0, 0],
        [0, 3, 3, 3, 0],
        [0, 0, 3, 0, 0],
        [0, 2, 2, 0, 0],
        [0, 2, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    assert gen.rule_mirror(grid) == expected


def test_every_exact_axis_round_trips_at_boundaries():
    cases = [
        {
            "profile": profile,
            "shape_variant": shape_variant,
            "column_layout": layout,
            "palette_variant": palette_variant,
            "color_pattern": pattern,
        }
        for profile in ("compact", "wide", "large")
        for shape_variant in (0, 3)
        for layout in ("left", "right", "staggered")
        for palette_variant in (0, 3)
        for pattern in ("rotate", "zigzag", "swap_pairs")
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(9100 + index, index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_override_is_rejected():
    with pytest.raises(TypeError):
        gen.generate(1, 0, unknown_axis=1)


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        77,
        0,
        profile="compact",
        shape_variant=0,
        column_layout="staggered",
        palette_variant=0,
        color_pattern="rotate",
    )

    gap = copy.deepcopy(base)
    gap.insert(3, [0] * len(gap[0]))
    assert any("consecutive" in error for error in gen.self_check(gap))

    overlap = copy.deepcopy(base)
    overlap[2][1] = overlap[1][1]
    assert any("overlap" in error for error in gen.self_check(overlap))

    disconnected = copy.deepcopy(base)
    color = next(value for value in disconnected[1] if value)
    disconnected[-2][1] = color
    assert any("exactly one 8-connected" in error for error in gen.self_check(disconnected))

    missing_border = copy.deepcopy(base)
    missing_border[0][1] = missing_border[1][1]
    assert any("blank row above" in error for error in gen.self_check(missing_border))


def test_generated_examples_refute_all_named_rivals():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = gen.generate(5000 + sample_index, sample_index, difficulty=band)
            answer = gen.rule_mirror(grid)
            assert gen.strict_canonical_like(grid) == []
            for rival in gen.SEMANTIC_RIVALS.values():
                assert rival(grid) != answer


def test_deterministic_fresh_and_input_pure():
    kwargs = dict(
        difficulty="medium",
        profile="large",
        shape_variant=2,
        column_layout="right",
        palette_variant=1,
        color_pattern="swap_pairs",
    )
    first = gen.generate(123, 4, **kwargs)
    second = gen.generate(123, 4, **kwargs)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    before = copy.deepcopy(first)
    gen.rule_mirror(first)
    assert first == before
