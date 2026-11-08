from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base
gen = importlib.import_module("puzzle_generators.per_puzzle.784b131b3b93.generator")
from reviewer_support import canonical_pairs, find_root


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__))


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exact_and_accepted():
    assert gen.RULE_HASH == "4b6cdc515f3f"
    assert gen.VERSION == "2.0.0"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = pair["input"]
        before = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]
        assert grid == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_are_lawful_branch_complete_diverse_and_observable(band):
    inputs = set()
    outputs = set()
    canonical_profile_hits = 0
    for seed in range(60):
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = gen.generate(10_000 + seed, seed * 17, difficulty=band)
        finally:
            base.set_ctx_observer(None)
        assert len(captured) == 1
        assert gen.self_check(grid) == []
        facts = gen.semantic_observables(grid)
        assert all(facts["state_counts"][state] >= 1 for state in ("00", "10", "01", "11"))
        assert 5 not in {value for row in grid for value in row}
        assert captured[0].recorded_draws() == gen.observe_overrides(grid)
        if len(grid) == 4 and len(grid[0]) == 14 and len({v for row in grid for v in row}) == 3:
            canonical_profile_hits += 1
        inputs.add(_frozen(grid))
        outputs.add(_frozen(gen.rule_mirror(grid)))
    assert canonical_profile_hits >= 30
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


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 3,
            "half_w": 3,
            "left_color": 1,
            "right_color": 9,
            "both_zero_target": 1,
            "panel_pattern": "random",
        },
        {
            "grid_h": 14,
            "half_w": 7,
            "left_color": 9,
            "right_color": 1,
            "both_zero_target": 6,
            "panel_pattern": "checker",
        },
    ],
)
def test_exact_axis_boundaries_work_in_every_band(band, overrides):
    grid = gen.generate(991, 17, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


def test_both_zero_target_is_an_exact_observable_contract_regression():
    grid = gen.generate(
        0,
        0,
        difficulty="easy",
        grid_h=3,
        half_w=3,
        left_color=3,
        right_color=2,
        both_zero_target=1,
        panel_pattern="random",
    )
    facts = gen.semantic_observables(grid)
    assert facts["state_counts"]["00"] == 1
    assert gen.observe_overrides(grid)["both_zero_target"] == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 2},
        {"grid_h": 15},
        {"half_w": 2},
        {"half_w": 8},
        {"left_color": 0},
        {"left_color": 5},
        {"right_color": 0},
        {"right_color": 5},
        {"left_color": 7, "right_color": 7},
        {"both_zero_target": 0},
        {"both_zero_target": 7},
        {"panel_pattern": "not-a-pattern"},
        {"bogus_axis": 1},
        {"texture": "not-a-texture"},
        {"texture": "checker", "panel_pattern": "border"},
        {"texture": "no_both_zero", "both_zero_target": 2},
    ],
)
def test_invalid_or_conflicting_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(2, 3, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": True},
        {"grid_h": 4.0},
        {"grid_h": "4"},
        {"half_w": False},
        {"half_w": 7.0},
        {"left_color": True},
        {"left_color": 3.0},
        {"left_color": "3"},
        {"right_color": False},
        {"right_color": 2.0},
        {"both_zero_target": True},
        {"both_zero_target": 3.0},
        {"both_zero_target": "3"},
    ],
)
def test_scalar_axis_overrides_reject_coercion(kwargs):
    with pytest.raises(TypeError):
        gen.generate(2, 3, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (0, True, None),
        (0, 1.0, None),
        (0, "1", None),
        (0, -1, None),
        (0, 0, True),
        (0, 0, 0.5),
        (0, 0, "extreme"),
    ],
)
def test_generate_call_controls_are_strict(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("texture", gen.DEGENERATE_TEXTURES)
def test_negative_fixtures_execute_rule_but_are_rejected_by_teaching_grammar(texture):
    grid = gen.generate(812, 4, texture=texture, grid_h=5, half_w=6)
    assert gen.self_check(grid)
    output = gen.rule_mirror(grid)
    assert len(output) == 5
    assert all(len(row) == 6 for row in output)


def test_self_check_rejects_minimal_structural_and_semantic_impostors():
    blank = [[0] * 6 for _ in range(3)]
    monochrome = [[1] * 6 for _ in range(3)]
    same_occupancy = [
        [1, 0, 1, 3, 0, 3],
        [0, 1, 0, 0, 3, 0],
        [1, 0, 0, 3, 0, 0],
    ]
    no_both_zero = [
        [1, 1, 1, 3, 0, 3],
        [1, 1, 1, 0, 3, 0],
        [1, 1, 1, 3, 0, 3],
    ]
    no_both_nonzero = [
        [1, 0, 1, 0, 3, 0],
        [0, 1, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    answer_color_leak = copy.deepcopy(gen.generate(9, 9))
    answer_color_leak[0][0] = 5
    ragged = [[0, 1, 0], [0, 1]]
    odd_width = [[0, 1, 0, 2, 0] for _ in range(3)]
    boolean = copy.deepcopy(gen.generate(10, 10))
    boolean[0][0] = True

    for grid in (
        blank,
        monochrome,
        same_occupancy,
        no_both_zero,
        no_both_nonzero,
        answer_color_leak,
        ragged,
        odd_width,
        boolean,
    ):
        assert gen.self_check(grid), grid


def test_declared_semantic_contract_is_live_on_every_normal_draw():
    assert set(gen.SEMANTIC_WITNESSES) == {"state_00", "state_10", "state_01", "state_11"}
    assert set(gen.SEMANTIC_RIVALS) == {
        "constant_zero",
        "left_zero",
        "right_zero",
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


def test_equal_color_rejection_names_incompatible_axes():
    with pytest.raises(ValueError) as caught:
        gen.generate(18, 2, left_color=7, right_color=7)
    assert set(caught.value.incompatible_axes) == {"left_color", "right_color"}
