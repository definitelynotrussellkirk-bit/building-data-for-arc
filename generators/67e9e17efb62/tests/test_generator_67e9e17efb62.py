from __future__ import annotations

import copy
import random

import pytest

import importlib
from reviewer_support import canonical_pairs, find_root

gen = importlib.import_module("puzzle_generators.per_puzzle.67e9e17efb62.generator")


def _canonical_rows():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)


def test_canonical_rows_are_accepted_and_mirrored_exactly():
    rows = _canonical_rows()
    assert len(rows) == 12
    for pair in rows:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_self_check_rejects_four_structural_impostors():
    valid = gen.generate(123, 5, difficulty="medium", grid_h=7, grid_w=11,
                         bar_len=5, color=4, position_bias="left")
    assert gen.self_check(valid) == []

    split = copy.deepcopy(valid)
    split[0][2] = 0
    assert any("contiguous" in error for error in gen.self_check(split))

    multicolor = copy.deepcopy(valid)
    multicolor[0][1] = 8
    assert any("one color" in error for error in gen.self_check(multicolor))

    body_noise = copy.deepcopy(valid)
    body_noise[2][2] = 4
    assert any("below row 0" in error for error in gen.self_check(body_noise))

    interior = copy.deepcopy(valid)
    interior[0] = [0, *valid[0][:-1]]
    assert any("horizontal edge" in error for error in gen.self_check(interior))


def test_exact_boundary_overrides_and_incompatibility():
    low = gen.generate(7, 1, difficulty="hard", grid_h=3, grid_w=5,
                       bar_len=3, color=1, position_bias="left")
    high = gen.generate(7, 1, difficulty="easy", grid_h=14, grid_w=23,
                        bar_len=8, color=9, position_bias="right")
    assert gen.observe_overrides(low) == {
        "grid_h": 3, "grid_w": 5, "bar_len": 3,
        "color": 1, "position_bias": "left",
    }
    assert gen.observe_overrides(high) == {
        "grid_h": 14, "grid_w": 23, "bar_len": 8,
        "color": 9, "position_bias": "right",
    }
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(7, 1, grid_w=5, bar_len=8)


def test_replay_fresh_returns_and_global_rng_preservation():
    random.seed(20260724)
    state = random.getstate()
    first = gen.generate(99, 17, difficulty="hard")
    second = gen.generate(99, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state


def test_canonical_prior_is_exactly_one_quarter_per_band():
    for band in ("easy", "medium", "hard"):
        flags = [
            gen.semantic_profile(gen.generate(5000 + i, i, difficulty=band))[
                "canonical_like"
            ]
            for i in range(200)
        ]
        assert sum(flags) == 50


@pytest.mark.parametrize(
    ("args", "overrides"),
    [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((1, True), {}),
        ((1, -1), {}),
        ((1, 0), {"difficulty": "impossible"}),
        ((1, 0), {"grid_h": 3.0}),
        ((1, 0), {"grid_w": "5"}),
        ((1, 0), {"bar_len": True}),
        ((1, 0), {"color": 9.75}),
        ((1, 0), {"position_bias": 1}),
        ((1, 0), {"position_bias": "middle"}),
        ((1, 0), {"bar_lenght": 5}),
    ],
)
def test_invalid_call_and_override_scalars_fail_loudly(args, overrides):
    difficulty = overrides.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(*args, difficulty=difficulty, **overrides)


def test_semantic_contract_refutes_ascending_only_rival():
    grid = gen.generate(
        17,
        3,
        difficulty="medium",
        grid_h=7,
        grid_w=11,
        bar_len=5,
        color=4,
        position_bias="left",
    )
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES["descending_tail"](grid) is True
    rival = gen.SEMANTIC_RIVALS["ascending_only"]
    assert rival(grid) != gen.rule_mirror(grid)
    assert gen.WITNESS_RIVALS == {"descending_tail": ["ascending_only"]}
    assert gen.LESSON_COMPETITORS["ascending_only"] is rival
