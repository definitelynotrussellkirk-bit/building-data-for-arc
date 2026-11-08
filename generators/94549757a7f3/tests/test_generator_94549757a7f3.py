from __future__ import annotations

import importlib

import pytest


MODULE = importlib.import_module("puzzle_generators.per_puzzle.94549757a7f3.generator")


def _grid(*rows: str) -> list[list[int]]:
    return [[int(ch) for ch in row] for row in rows]


def test_unknown_override_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 0, __typo_axis=3)


def test_every_declared_axis_is_exactly_observable_at_boundaries() -> None:
    cases = [
        dict(grid_h=6, grid_w=7, n_targets=2, length_profile="all_4", distractor_mode="occupied_right"),
        dict(grid_h=10, grid_w=14, n_targets=3, length_profile="canonical_mix", distractor_mode="none"),
        dict(grid_h=6, grid_w=7, n_targets=3, length_profile="all_2", distractor_mode="mixed"),
    ]
    for index, overrides in enumerate(cases):
        generated = MODULE.generate(17, index, difficulty="hard", **overrides)
        assert MODULE.observe_overrides(generated) == overrides
        assert MODULE.self_check(generated) == []


def test_declared_incompatible_length_profile_rejects() -> None:
    with pytest.raises(ValueError, match="canonical_mix requires n_targets=3"):
        MODULE.generate(2, 0, n_targets=2, length_profile="canonical_mix")


def test_self_check_rejects_four_structural_impostors() -> None:
    no_target = _grid(
        "0000000",
        "0330000",
        "0000000",
        "0000000",
        "0000000",
        "0000000",
    )
    singleton_green = _grid(
        "0300000",
        "0000000",
        "0330000",
        "0000000",
        "0000000",
        "0000000",
    )
    bent_green = _grid(
        "0330000",
        "0030000",
        "0000000",
        "0330000",
        "0000000",
        "0000000",
    )
    red_in_input = _grid(
        "0332000",
        "0000000",
        "0330000",
        "0000000",
        "0000000",
        "0000000",
    )
    for impostor in (no_target, singleton_green, bent_green, red_in_input):
        assert MODULE.self_check(impostor)


def test_each_decisive_skip_branch_is_present_in_one_schedule_window() -> None:
    grids = [MODULE.generate(31, index, difficulty="medium") for index in range(5)]
    modes = {MODULE.observe_overrides(grid)["distractor_mode"] for grid in grids}
    assert modes == {"mixed", "right_edge", "occupied_right", "none", "vertical"}

    pairs = [{"input": grid, "output": MODULE.rule_mirror(grid)} for grid in grids]
    query_grid = MODULE.generate(31, 5, difficulty="medium")
    query = {"input": query_grid, "output": MODULE.rule_mirror(query_grid)}
    assert MODULE.lesson_identifiable(pairs, query) == []


def test_rule_mirror_caps_only_true_targets() -> None:
    generated = MODULE.generate(
        9,
        0,
        grid_h=6,
        grid_w=7,
        n_targets=2,
        length_profile="all_2",
        distractor_mode="mixed",
    )
    facts = MODULE._analyze(generated)
    output = MODULE.rule_mirror(generated)
    changed = {
        (r, c)
        for r in range(len(generated))
        for c in range(len(generated[0]))
        if generated[r][c] != output[r][c]
    }
    assert changed == {target["right"] for target in facts["targets"]}
    assert all(output[r][c] == 2 for r, c in changed)
