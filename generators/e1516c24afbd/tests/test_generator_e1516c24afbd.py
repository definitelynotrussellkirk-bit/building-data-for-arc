from __future__ import annotations

import copy

from puzzle_generators.per_puzzle.e1516c24afbd import generator as gen
from reviewer_support import canonical_pairs, find_root


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted():
    assert gen.RULE_HASH == "de03400353f9"
    assert gen.VERSION == "2.0.0"
    pairs = _pairs()
    assert len(pairs) == 6
    for pair in pairs:
        grid = pair["input"]
        before = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]
        assert grid == before

import random

import pytest

from puzzle_generators import base


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_are_lawful_branch_complete_diverse_and_observable(band):
    inputs = set()
    outputs = set()
    for seed in range(60):
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = gen.generate(10_000 + seed, seed * 17 + 5, difficulty=band)
        finally:
            base.set_ctx_observer(None)
        assert len(captured) == 1
        assert gen.self_check(grid) == []
        facts = gen.semantic_observables(grid)
        assert all(facts["state_counts"][state] >= 1 for state in ("00", "10", "01", "11"))
        assert 2 not in {value for row in grid for value in row}
        assert captured[0].recorded_draws() == gen.observe_overrides(grid)
        inputs.add(_frozen(grid))
        outputs.add(_frozen(gen.rule_mirror(grid)))
    assert len(inputs) >= 55
    assert len(outputs) >= 40


def test_replay_is_deterministic_fresh_and_global_rng_is_untouched():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(77, 91, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "half_h": 3,
            "grid_w": 3,
            "top_color": 1,
            "bot_color": 9,
            "both_zero_count": 1,
            "layout": "random",
        },
        {
            "half_h": 10,
            "grid_w": 10,
            "top_color": 9,
            "bot_color": 1,
            "both_zero_count": 6,
            "layout": "checker",
        },
    ],
)
def test_exact_axis_boundaries_work_in_every_band(band, overrides):
    grid = gen.generate(991, 17, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"half_h": 2},
        {"half_h": 11},
        {"grid_w": 2},
        {"grid_w": 11},
        {"top_color": 0},
        {"top_color": 2},
        {"bot_color": 0},
        {"bot_color": 2},
        {"top_color": 7, "bot_color": 7},
        {"both_zero_count": 0},
        {"both_zero_count": 7},
        {"layout": "not-a-layout"},
        {"bogus_axis": 1},
        {"texture": "not-a-texture"},
        {"texture": "checker", "layout": "border"},
        {"panel_pattern": "checker", "layout": "border"},
        {"both_zero_target": 2, "both_zero_count": 3},
        {"texture": "no_both_zero", "both_zero_count": 2},
    ],
)
def test_invalid_or_conflicting_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(2, 3, **kwargs)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(2, 3, difficulty="extreme")


@pytest.mark.parametrize("texture", gen.DEGENERATE_TEXTURES)
def test_negative_fixtures_execute_the_rule_but_are_rejected_by_teaching_grammar(texture):
    grid = gen.generate(812, 4, texture=texture, half_h=5, grid_w=6)
    assert gen.self_check(grid)
    output = gen.rule_mirror(grid)
    assert len(output) == 5
    assert all(len(row) == 6 for row in output)


def test_self_check_rejects_minimal_structural_and_semantic_impostors():
    blank = [[0] * 3 for _ in range(6)]
    monochrome = [[1] * 3 for _ in range(6)]
    same_occupancy = [
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [3, 0, 3],
        [0, 3, 0],
        [3, 0, 0],
    ]
    no_both_zero = [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
        [3, 0, 3],
        [0, 3, 0],
        [3, 0, 3],
    ]
    no_both_nonzero = [
        [1, 0, 1],
        [0, 1, 0],
        [0, 0, 0],
        [0, 3, 0],
        [3, 0, 0],
        [0, 0, 0],
    ]
    answer_color_leak = copy.deepcopy(gen.generate(9, 9))
    answer_color_leak[0][0] = 2
    ragged = [[0, 1, 0], [0, 1]]
    odd_height = [[0, 1, 0] for _ in range(7)]

    for grid in (
        blank,
        monochrome,
        same_occupancy,
        no_both_zero,
        no_both_nonzero,
        answer_color_leak,
        ragged,
        odd_height,
    ):
        assert gen.self_check(grid), grid


def test_declared_semantic_contract_is_live_on_every_normal_draw():
    assert set(gen.SEMANTIC_WITNESSES) == {"state_00", "state_10", "state_01", "state_11"}
    assert set(gen.SEMANTIC_RIVALS) == {
        "constant_zero",
        "top_zero",
        "bottom_zero",
        "equal_occupancy",
        "xor_occupancy",
        "both_nonzero",
        "either_zero",
    }
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    assert gen.CANONICAL_SHORTCUTS == {}

    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(20_000 + index, index, difficulty=band)
            official = gen.rule_mirror(grid)
            assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != official, (band, index, name)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_demo_lessons_are_identifiable_across_cyclic_windows(band):
    grids = [gen.generate(30_000 + i, i * 7, difficulty=band) for i in range(24)]
    pairs = [_pair(grid) for grid in grids]
    for start in range(len(pairs)):
        demos = [pairs[(start + offset) % len(pairs)] for offset in range(3)]
        query = pairs[(start + 3) % len(pairs)]
        assert gen.lesson_identifiable(demos, query) == []


def test_lesson_identifiable_rejects_too_few_or_incorrect_demos():
    grids = [gen.generate(44, i) for i in range(4)]
    pairs = [_pair(grid) for grid in grids]
    assert gen.lesson_identifiable(pairs[:2], pairs[2])
    bad_demo = copy.deepcopy(pairs[0])
    bad_demo["output"] = [[0 for _ in row] for row in bad_demo["output"]]
    assert gen.lesson_identifiable([bad_demo, pairs[1], pairs[2]], pairs[3])


def test_equal_color_rejection_names_the_incompatible_axes():
    with pytest.raises(ValueError) as caught:
        gen.generate(18, 2, top_color=7, bot_color=7)
    assert set(caught.value.incompatible_axes) == {"top_color", "bot_color"}
