from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.e2fa7e7aee7c import generator as gen


def _canonical_inputs():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [pair["input"] for pair in row["train"]] + [row["test"]["input"]]
    raise AssertionError("canonical task missing")


def test_canonical_inputs_pass_structural_check():
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


def test_exact_override_boundaries_are_observable():
    cases = [
        {"grid_h": 7, "grid_w": 7, "triples": 2, "orientation_mode": "mixed"},
        {"grid_h": 18, "grid_w": 18, "triples": 9, "orientation_mode": "horizontal"},
        {"grid_h": 7, "grid_w": 18, "triples": 9, "orientation_mode": "vertical"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, 400 + index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []


def test_replay_is_deterministic_fresh_and_rng_pure():
    random.seed(112233)
    state = random.getstate()
    first = gen.generate(17, 23, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 23, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        41,
        43,
        grid_h=9,
        grid_w=9,
        triples=3,
        orientation_mode="mixed",
    )
    colors = sorted({value for row in base for value in row if value})
    features, errors = gen._analyze(base)
    assert not errors
    midpoint = features["midpoints"][0]

    singleton = copy.deepcopy(base)
    singleton[0][0] = next(color for color in range(1, 10) if color not in colors)

    filled_midpoint = copy.deepcopy(base)
    filled_midpoint[midpoint[0]][midpoint[1]] = next(
        color for color in range(1, 10) if color not in colors
    )

    three_endpoints = copy.deepcopy(base)
    target_color = colors[0]
    free = next(
        (row, col)
        for row in range(len(base))
        for col in range(len(base[0]))
        if base[row][col] == 0 and (row, col) != midpoint
    )
    three_endpoints[free[0]][free[1]] = target_color

    diagonal_pair = [[0] * 7 for _ in range(7)]
    diagonal_pair[1][1] = diagonal_pair[3][3] = 4
    diagonal_pair[5][1] = diagonal_pair[5][3] = 6

    for impostor in (singleton, filled_midpoint, three_endpoints, diagonal_pair):
        assert gen.self_check(impostor)


def test_canonical_schedule_is_linked_not_marginal():
    matches = 0
    for sample_index in range(40):
        grid = gen.generate(700, sample_index, difficulty="hard")
        observed = gen.observe_overrides(grid)
        if (
            observed["grid_h"] == observed["grid_w"]
            and observed["grid_h"] in (7, 8)
            and observed["triples"] == 2
            and observed["orientation_mode"] == "mixed"
        ):
            matches += 1
    assert matches >= 10
