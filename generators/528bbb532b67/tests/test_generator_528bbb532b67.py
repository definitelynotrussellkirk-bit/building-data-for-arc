from __future__ import annotations

import copy
import random

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.528bbb532b67.generator")


CANONICAL_INPUTS = [
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 8, 8, 8, 8, 8, 8, 8, 0],
        [0, 8, 0, 3, 0, 0, 0, 8, 0],
        [0, 8, 0, 0, 3, 0, 0, 8, 0],
        [0, 8, 0, 0, 0, 0, 0, 8, 0],
        [0, 8, 8, 8, 8, 8, 8, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 8, 8, 8, 8, 8, 8, 8, 0],
        [0, 0, 8, 0, 4, 0, 0, 0, 8, 0],
        [0, 0, 8, 4, 4, 0, 0, 0, 8, 0],
        [0, 0, 8, 0, 0, 0, 0, 0, 8, 0],
        [0, 0, 8, 8, 8, 8, 8, 8, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 8, 8, 8, 8, 8, 8, 8, 8, 0],
        [0, 0, 8, 0, 0, 6, 0, 0, 0, 8, 0],
        [0, 0, 8, 0, 6, 6, 0, 0, 0, 8, 0],
        [0, 0, 8, 0, 0, 0, 0, 0, 0, 8, 0],
        [0, 0, 8, 8, 8, 8, 8, 8, 8, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
]


def test_rule_hash_and_canonical_inputs_are_pinned_and_valid():
    assert gen.RULE_HASH == "1684ca9647a8"
    for grid in CANONICAL_INPUTS:
        assert gen.self_check(grid) == []


def test_exact_overrides_are_observable_at_valid_boundaries():
    cases = [
        dict(grid_h=7, grid_w=9, box_h=5, box_w=7, n_distinct_colors=1),
        dict(grid_h=22, grid_w=24, box_h=12, box_w=14, n_distinct_colors=5),
    ]
    for case in cases:
        grid = gen.generate(17, 23, difficulty="easy", **case)
        observed = gen.observe_overrides(grid)
        assert len(grid) == case["grid_h"]
        assert len(grid[0]) == case["grid_w"]
        assert observed == {
            "box_h": case["box_h"],
            "box_w": case["box_w"],
            "n_distinct_colors": case["n_distinct_colors"],
        }


def test_incompatible_dimension_overrides_reject_loudly():
    with pytest.raises(ValueError, match="box_h requires"):
        gen.generate(0, 0, difficulty="medium", grid_h=7, box_h=12)
    with pytest.raises(ValueError, match="box_w requires"):
        gen.generate(0, 0, difficulty="medium", grid_w=9, box_w=14)


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(3, 7, difficulty="medium")
    assert gen.self_check(valid) == []

    impostors = []
    impostors.append([[0 for _ in row] for row in valid])

    broken_frame = copy.deepcopy(valid)
    facts = gen._analyze(valid)["facts"]
    r0, c0, _, _ = facts["frame_bbox"]
    broken_frame[r0][c0] = 0
    impostors.append(broken_frame)

    outside_source = copy.deepcopy(valid)
    outside_source[0][0] = 3
    impostors.append(outside_source)

    right_source = copy.deepcopy(valid)
    r0, c0, r1, c1 = facts["frame_bbox"]
    placed = False
    for row in range(r0 + 1, r1):
        for col in range(c1 - 1, c0, -1):
            if 2 * col > c0 + c1 and right_source[row][col] == 0:
                right_source[row][col] = 4
                placed = True
                break
        if placed:
            break
    assert placed
    impostors.append(right_source)

    mirror_collision = copy.deepcopy(valid)
    source = next(
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if mirror_collision[r][c] not in (0, 8) and 2 * c < c0 + c1
    )
    mirror_collision[source[0]][c0 + c1 - source[1]] = 5
    impostors.append(mirror_collision)

    for impostor in impostors:
        assert gen.self_check(impostor), impostor


def test_replay_freshness_input_purity_and_global_rng_state():
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(11, 13, difficulty="hard")
    after = random.getstate()
    second = gen.generate(11, 13, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    snapshot = copy.deepcopy(first)
    first[0][0] = 9
    assert second == snapshot
