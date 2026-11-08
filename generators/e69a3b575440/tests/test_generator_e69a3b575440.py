"""Focused regression tests for generator e69a3b575440."""
from __future__ import annotations

import copy

import pytest

from puzzle_generators.per_puzzle.e69a3b575440 import generator as gen
from scripts.canonical_profile_gate import canonical_inputs


def _pair(grid):
    facts = gen.profile_signature(grid)
    assert facts["valid"], facts["errors"]
    return {
        "input": copy.deepcopy(grid),
        "output": gen._transform(facts["crop"], facts["cmd"]),
    }


def test_canonical_inputs_are_owned_by_structural_checker():
    inputs = canonical_inputs(gen.TASK_ID)
    assert len(inputs) == 5
    assert [gen.self_check(grid) for grid in inputs] == [[]] * len(inputs)
    assert [gen.strict_canonical_like(grid) for grid in inputs] == [[]] * len(inputs)


def test_sequential_lesson_covers_every_command_and_is_identifiable():
    grids = [
        gen.generate(90210, sample_index, difficulty="medium")
        for sample_index in range(9)
    ]
    demos = [_pair(grid) for grid in grids[:8]]
    query = _pair(grids[8])
    assert [gen.observe_overrides(grid)["cmd"] for grid in grids[:8]] == list(range(1, 9))
    assert gen.lesson_identifiable(demos, query) == []


def test_exact_override_boundaries_are_observable_and_unknown_axes_reject():
    cases = (
        {"grid_h": 7, "grid_w": 7, "cmd": 1, "object_color_count": 1},
        {"grid_h": 14, "grid_w": 14, "cmd": 8, "object_color_count": 3},
    )
    for sample_index, overrides in enumerate(cases):
        grid = gen.generate(31415, sample_index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="warm")


def test_named_mutation_fixtures_are_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), f"fixture {name!r} was accepted"


def test_nonidentity_commands_visibly_change_the_crop():
    for cmd in range(2, 9):
        grid = gen.generate(777, cmd - 1, difficulty="medium", cmd=cmd)
        facts = gen.profile_signature(grid)
        assert facts["valid"], facts["errors"]
        assert gen._transform(facts["crop"], cmd) != facts["crop"]
