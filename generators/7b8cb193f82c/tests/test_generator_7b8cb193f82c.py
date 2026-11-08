from __future__ import annotations

import importlib
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.7b8cb193f82c.generator"
)


def _pairs(start: int, band: str = "medium"):
    pairs = []
    for index in range(start, start + MODULE.EXAMPLES_NEEDED):
        grid = MODULE.generate(991, index, difficulty=band)
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    return pairs


def test_canonical_inputs_and_outputs_match_authority_examples():
    pairs = canonical_pairs(MODULE.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_every_five_example_window_identifies_the_rule():
    for start in range(12):
        demos = _pairs(start)
        query_grid = MODULE.generate(992, start + 5, difficulty="medium")
        query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
        assert MODULE.lesson_identifiable(demos, query) == []
        observed = {MODULE.observe_overrides(pair["input"])["max_depth"] for pair in demos}
        assert observed == {1, 2, 3, 4, 5}


def test_exact_overrides_are_observable_and_impossible_tuple_rejects():
    cases = [
        {"grid_h": 9},
        {"grid_w": 24},
        {"n_frames": 3},
        {"thickness": 2},
        {"max_depth": 5},
        {"grid_h": 24, "grid_w": 24, "n_frames": 3, "thickness": 1, "max_depth": 5},
    ]
    for overrides in cases:
        grid = MODULE.generate(13, 4, difficulty="hard", **overrides)
        observed = MODULE.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value
        assert MODULE.self_check(grid, meta={"overrides": overrides}) == []

    with pytest.raises(MODULE.IncompatibleOverrides):
        MODULE.generate(
            13,
            4,
            difficulty="hard",
            grid_h=9,
            grid_w=10,
            n_frames=3,
            thickness=2,
            max_depth=5,
        )


def test_self_check_rejects_targeted_impostors():
    valid = MODULE.generate(31, 1, difficulty="easy")
    assert MODULE.self_check(valid) == []

    no_frame = [[0 for _ in row] for row in valid]
    assert MODULE.self_check(no_frame)

    open_frame = deepcopy(valid)
    facts, errors = MODULE._analyze(open_frame)
    assert errors == []
    r1, c1, _r2, c2 = facts["frames"][0]["bbox"]
    open_frame[r1][(c1 + c2) // 2] = 0
    assert MODULE.self_check(open_frame)

    solid_block = deepcopy(valid)
    frame = facts["frames"][0]
    for row, col in frame["hole_cells"]:
        solid_block[row][col] = 8
    assert MODULE.self_check(solid_block)

    wrong_palette = deepcopy(valid)
    wrong_palette[0][0] = 1
    assert MODULE.self_check(wrong_palette)

    lopsided_ring = deepcopy(valid)
    r1, c1, r2, _c2 = facts["frames"][0]["bbox"]
    lopsided_ring[(r1 + r2) // 2][c1] = 0
    assert MODULE.self_check(lopsided_ring)


def test_canonical_fitting_depth_cap_is_killed_by_generated_depth_five():
    for pair in canonical_pairs(MODULE.TASK_ID):
        assert MODULE._rival_canonical_depth_cap(pair["input"]) == pair["output"]

    depth_five = MODULE.generate(51, 4, difficulty="hard")
    assert MODULE.observe_overrides(depth_five)["max_depth"] == 5
    assert MODULE._rival_canonical_depth_cap(depth_five) != MODULE.rule_mirror(depth_five)


def test_deterministic_fresh_returns_and_global_rng_purity():
    before = random.getstate()
    first = MODULE.generate(77, 5, difficulty="hard")
    second = MODULE.generate(77, 5, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert MODULE.generate(77, 5, difficulty="hard") == second
    assert random.getstate() == before
