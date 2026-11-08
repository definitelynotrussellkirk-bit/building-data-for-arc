"""Focused regression tests for commanded pivot rotations."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule, run_one
from src.core.canonical_pairs import load_task_pairs

TASK_ID = "256f70c87bba"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(grid):
    return {"input": grid, "output": gen._expected_output(grid)}


def test_rule_hash_and_all_canonical_pairs_are_owned() -> None:
    assert gen.RULE_HASH == "3bc100ea5852"
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen._expected_output(source) == pair["output"]
        assert source == pair["input"]


def test_racket_authority_matches_generated_outputs_and_is_reentrant() -> None:
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        grids = [gen.generate(501, index, difficulty="medium") for index in range(8)]
        outputs = []
        for grid in grids:
            before = copy.deepcopy(grid)
            output = _apply_rule(bridge, fn_name, grid)
            assert output == gen._expected_output(grid)
            assert grid == before
            outputs.append(output)
        assert _apply_rule(bridge, fn_name, grids[0]) == outputs[0]
        assert _apply_rule(bridge, fn_name, grids[1]) == outputs[1]
        assert _apply_rule(bridge, fn_name, grids[0]) == outputs[0]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("grid_h", [10, 12])
@pytest.mark.parametrize("grid_w", [12, 14])
@pytest.mark.parametrize("scene_profile", gen.SCENE_PROFILES)
def test_every_declared_axis_round_trips_exactly(
    grid_h: int, grid_w: int, scene_profile: str
) -> None:
    expected = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "scene_profile": scene_profile,
    }
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(7301, 19, difficulty=band, **expected)
        assert gen.observe_overrides(grid) == expected
        assert gen.self_check(grid, difficulty=band) == []
        assert gen._expected_output(grid) != grid


def test_four_consecutive_examples_identify_every_rule_branch() -> None:
    grids = [gen.generate(8103, index, difficulty="hard") for index in range(4)]
    observations = [gen.semantic_observables(grid) for grid in grids]
    assert {row["scene_profile"] for row in observations} == set(gen.SCENE_PROFILES)
    assert {branch for row in observations for branch in row["command_branches"]} == {1, 2, 3}
    assert any(row["has_idle_branch"] for row in observations)
    assert any(row["detached_component"] for row in observations)
    assert gen.lesson_identifiable([_pair(grid) for grid in grids], _pair(grids[0])) == []


def test_runner_produces_an_identifiable_lesson() -> None:
    instance = run_one(TASK_ID, 9157, 0, n_train=4, n_test=1, difficulty="medium")
    assert gen.lesson_identifiable(instance["train"], instance["test"][0]) == []


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(4127, 2, difficulty="medium", scene_profile="command_1_and_2")
    analysis = gen._analyze(valid)
    impostors = {}

    impostors["all_background"] = [[0 for _ in row] for row in valid]

    missing_pivot = copy.deepcopy(valid)
    pr, pc = analysis["pivots"][0]
    missing_pivot[pr][pc] = 0
    impostors["missing_pivot"] = missing_pivot

    missing_cue = copy.deepcopy(valid)
    pr, pc = analysis["pivots"][1]
    missing_cue[pr][pc - 1] = 0
    impostors["missing_cue"] = missing_cue

    stray_marker = copy.deepcopy(valid)
    stray_marker[0][0] = 1
    impostors["stray_color_one"] = stray_marker

    duplicate_cue = copy.deepcopy(valid)
    (r0, c0), (r1, c1) = analysis["pivots"]
    duplicate_cue[r1][c1 - 1] = duplicate_cue[r0][c0 - 1]
    impostors["duplicate_local_commands"] = duplicate_cue

    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_negative_recombination_is_rejected_by_grammar_but_racket_executes() -> None:
    grid = gen.generate(6217, 1, difficulty="easy")
    recombined = copy.deepcopy(grid)
    recombined[0][0] = 1  # Racket deletes it; the teaching grammar forbids it.
    assert gen.self_check(recombined)

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, recombined)
        assert output
        assert output == gen._expected_output(grid)
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(24680)
    state = random.getstate()
    first = gen.generate(13579, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(13579, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert gen.generate(13579, 2, difficulty="hard") == second


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 9},
        {"grid_h": 13},
        {"grid_w": 11},
        {"grid_w": 15},
        {"scene_profile": "global_command"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_overrides_reject_loudly(kwargs: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, difficulty="medium", **kwargs)
