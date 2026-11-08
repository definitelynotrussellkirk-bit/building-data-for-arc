from __future__ import annotations

import copy
import importlib

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.47993d3762b9.generator")
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_inputs_are_accepted_and_mirror_outputs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_texture_override_is_exact_and_transforming():
    for index, texture in enumerate(gen.HELPFUL_TEXTURES):
        grid = gen.generate(
            1234,
            index,
            difficulty="medium",
            grid_h=10,
            grid_w=11,
            n_colors=3,
            texture=texture,
        )
        assert gen.self_check(
            grid,
            meta={
                "overrides": {
                    "grid_h": 10,
                    "grid_w": 11,
                    "n_colors": 3,
                    "texture": texture,
                }
            },
        ) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": 10,
            "grid_w": 11,
            "n_colors": 3,
            "texture": texture,
        }
        assert gen.rule_mirror(grid) != grid


def test_four_consecutive_demos_cover_every_scheduled_texture():
    for start in range(8):
        seen = {
            gen.observe_overrides(gen.generate(7, start + offset, difficulty="hard"))["texture"]
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert seen == set(gen.HELPFUL_TEXTURES)


def test_distributed_extrema_kills_diagonal_endpoint_shortcut():
    grid = gen.generate(99, 3, difficulty="easy", texture="distributed_extrema")
    assert gen.SEMANTIC_WITNESSES["distributed_extrema"](grid)
    assert gen._diagonal_endpoints_rival(grid) != gen.rule_mirror(grid)


def test_self_check_rejects_targeted_rule_hiding_mutations():
    blank = [[0] * 7 for _ in range(7)]
    assert gen.self_check(blank)

    one_color = copy.deepcopy(blank)
    one_color[1][1] = 2
    one_color[5][5] = 2
    assert gen.self_check(one_color)

    line_bbox = copy.deepcopy(blank)
    line_bbox[1][1] = line_bbox[1][5] = 2
    line_bbox[4][1] = line_bbox[6][5] = 3
    assert any("rule-hiding" in reason for reason in gen.self_check(line_bbox))

    no_op = copy.deepcopy(blank)
    for row, col in ((1, 1), (1, 3), (3, 1), (3, 3)):
        no_op[row][col] = 2
    no_op[4][4] = no_op[6][6] = 3
    assert any("no-op" in reason for reason in gen.self_check(no_op))


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unsupported override"):
        gen.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, grid_h=6)


def test_returns_are_fresh_and_deterministic():
    first = gen.generate(42, 5, difficulty="medium")
    second = gen.generate(42, 5, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
