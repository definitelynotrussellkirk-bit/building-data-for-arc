from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_inputs, canonical_pairs


TASK_ID = "14f8af78f06e"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_canonical_inputs_and_outputs_match_rule() -> None:
    inputs = canonical_inputs(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(inputs) == 3
    assert all(GEN.self_check(grid) == [] for grid in inputs)
    for pair in pairs:
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_regression_adjacent_mask_bbox_is_canonical() -> None:
    # The original checker incorrectly required an extra blank separator row
    # and rejected canonical train[1] and test[0]. Direct adjacency to the
    # seed terminator is lawful because the mask does not overlap the seed.
    inputs = canonical_inputs(TASK_ID)
    assert GEN.self_check(inputs[1]) == []
    assert GEN.self_check(inputs[2]) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 9, "tile_h": 2, "tile_w": 2, "mask_cells": 4},
        {"grid_h": 14, "grid_w": 16, "tile_h": 4, "tile_w": 4, "mask_cells": 8},
        {"grid_h": 7, "grid_w": 16, "tile_h": 4, "tile_w": 2, "mask_cells": 7},
        {"grid_h": 14, "grid_w": 9, "tile_h": 2, "tile_w": 4, "mask_cells": 5},
    ],
)
def test_exact_override_boundaries_are_observable(overrides: dict[str, int]) -> None:
    grid = GEN.generate(7001, 19, difficulty="hard", **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in overrides} == overrides


def test_unknown_override_rejected_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


def test_self_check_rejects_structural_impostors() -> None:
    good = GEN.generate(9001, 0, difficulty="medium")
    assert GEN.self_check(good) == []

    no_seed = copy.deepcopy(good)
    for row in range(2):
        for col in range(2):
            no_seed[row][col] = 0

    no_mask = [[0 if value == 8 else value for value in row] for row in good]

    rectangular = copy.deepcopy(good)
    facts = GEN.semantic_observables(rectangular)
    r0, c0, r1, c1 = facts["mask_bbox"]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            rectangular[row][col] = 8

    textured = copy.deepcopy(good)
    textured[-1][0] = 6

    disconnected = copy.deepcopy(good)
    mask = [(r, c) for r, row in enumerate(disconnected) for c, v in enumerate(row) if v == 8]
    for row, col in mask:
        disconnected[row][col] = 0
    disconnected[-1][-1] = 8
    disconnected[-3][-3] = 8
    disconnected[-3][-2] = 8
    disconnected[-2][-3] = 8

    for impostor in (no_seed, no_mask, rectangular, textured, disconnected):
        assert GEN.self_check(impostor), impostor


def test_replay_freshness_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after


def test_three_demo_schedule_refutes_declared_rivals() -> None:
    demos = []
    for sample_index in (0, 1, 2):
        grid = GEN.generate(8128, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(8128, 3, difficulty="medium")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []
