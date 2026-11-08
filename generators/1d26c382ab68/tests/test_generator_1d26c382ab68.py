"""Focused regressions for generator 1d26c382ab68."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "1d26c382ab68"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.1d26c382ab68.generator"
)


def test_rule_hash_and_canonical_inputs_are_pinned() -> None:
    assert MODULE.RULE_HASH == "e4dd26fbc01b"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 9,
            "grid_w": 13,
            "candidate_color": 3,
            "template_cells": 5,
            "match_slot": 2,
            "match_rotation": "270",
        },
        {
            "grid_h": 11,
            "grid_w": 11,
            "candidate_color": 8,
            "template_cells": 4,
            "match_slot": 0,
            "match_rotation": "0",
        },
    ],
)
def test_exact_overrides_are_observable(overrides: dict) -> None:
    grid = MODULE.generate(417, 29, difficulty="hard", **overrides)
    observed = MODULE.observe_overrides(grid)
    assert observed == overrides
    assert MODULE.self_check(grid) == []


def test_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(99173)
    before = random.getstate()
    first = MODULE.generate(19, 7, difficulty="medium")
    after = random.getstate()
    second = MODULE.generate(19, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == after
    first[0][0] = 7
    assert MODULE.generate(19, 7, difficulty="medium") == second


def test_self_check_rejects_targeted_impostors() -> None:
    grid = MODULE.generate(
        123,
        5,
        difficulty="medium",
        grid_h=10,
        grid_w=12,
        candidate_color=8,
        template_cells=5,
        match_slot=1,
        match_rotation="90",
    )
    info = MODULE._structure(grid)

    broken_separator = copy.deepcopy(grid)
    broken_separator[info["separator_row"]][0] = 0
    assert MODULE.self_check(broken_separator)

    disconnected_template = copy.deepcopy(grid)
    occupied = set(info["template_cells_abs"])
    candidate = next(
        (row, col)
        for row in range(info["separator_row"])
        for col in range(info["grid_w"])
        if (row, col) not in occupied
        and all(
            (row + dr, col + dc) not in occupied
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    )
    disconnected_template[candidate[0]][candidate[1]] = 1
    assert MODULE.self_check(disconnected_template)

    mixed_candidate_colors = copy.deepcopy(grid)
    row, col = info["candidate_components_abs"][0][0]
    mixed_candidate_colors[row][col] = 7
    assert MODULE.self_check(mixed_candidate_colors)

    wrong_candidate_size = copy.deepcopy(grid)
    row, col = info["candidate_components_abs"][2][0]
    wrong_candidate_size[row][col] = 0
    assert MODULE.self_check(wrong_candidate_size)

    second_match = copy.deepcopy(grid)
    distractor_slot = next(index for index in range(3) if index != info["match_slot"])
    distractor_cells = info["candidate_components_abs"][distractor_slot]
    for row, col in distractor_cells:
        second_match[row][col] = 0
    match_shape = MODULE._rotate(info["template"], 2)
    top = min(row for row, _col in distractor_cells)
    left = min(col for _row, col in distractor_cells)
    for row, col in match_shape:
        second_match[top + row][left + col] = info["candidate_color"]
    assert MODULE.self_check(second_match)


def test_three_consecutive_demos_identify_the_rule() -> None:
    demos = []
    for sample_index in range(30, 33):
        grid = MODULE.generate(456, sample_index, difficulty="hard")
        demos.append({"input": grid, "output": MODULE.expected_output(grid)})
    query_grid = MODULE.generate(456, 33, difficulty="hard")
    query = {"input": query_grid, "output": MODULE.expected_output(query_grid)}
    assert MODULE.lesson_identifiable(demos, query) == []
    assert {MODULE.observe_overrides(pair["input"])["match_slot"] for pair in demos} == {0, 1, 2}
    assert len({MODULE.observe_overrides(pair["input"])["match_rotation"] for pair in demos}) == 3


def test_reflection_is_preserved_but_rotation_is_recolored() -> None:
    grid = MODULE.generate(
        808,
        12,
        difficulty="easy",
        candidate_color=6,
        match_slot=2,
        match_rotation="90",
    )
    info = MODULE._structure(grid)
    output = MODULE.expected_output(grid)
    for slot, component in enumerate(info["candidate_components_abs"]):
        expected = 2 if slot == info["match_slot"] else info["candidate_color"]
        assert {output[row][col] for row, col in component} == {expected}
    assert info["reflection_distractor"] is True


def test_declared_rivals_are_executable_and_default_lessons_refute_them() -> None:
    rival_names = {
        "always_left",
        "exact_orientation_only",
        "accept_reflection",
        "all_same_size",
    }
    assert set(MODULE.SEMANTIC_RIVALS) == rival_names
    assert set(MODULE.LESSON_COMPETITORS) == rival_names
    assert set(MODULE.CANONICAL_SHORTCUTS) == {"always_left"}

    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    always_left = MODULE.CANONICAL_SHORTCUTS["always_left"]
    assert all(always_left(pair["input"]) == pair["output"] for pair in canonical)

    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for sample_index in range(start, start + MODULE.EXAMPLES_NEEDED):
                grid = MODULE.generate(9001, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": MODULE.expected_output(grid)})
            query_grid = MODULE.generate(
                9001, start + MODULE.EXAMPLES_NEEDED, difficulty=difficulty
            )
            query = {"input": query_grid, "output": MODULE.expected_output(query_grid)}
            assert MODULE.lesson_identifiable(demos, query) == []
            for name, rival in MODULE.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), f"{difficulty=} {start=} did not refute {name}"
