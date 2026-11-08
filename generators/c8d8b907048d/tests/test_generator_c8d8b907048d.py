from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.c8d8b907048d import generator as gen


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "c8d8b907048d"


def _canonical_inputs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair["input"] for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task not found")


def test_rule_hash_and_all_canonical_inputs():
    assert gen.RULE_HASH == "30f91a42c7e5"
    inputs = _canonical_inputs()
    assert len(inputs) == 4
    assert all(gen.self_check(grid) == [] for grid in inputs)


def test_override_boundaries_are_exact_and_observable():
    for difficulty in ("easy", "medium", "hard"):
        for overrides in (
            {"grid_h": 6, "grid_w": 8, "cell_count": 4, "n_distinct_colors": 2},
            {"grid_h": 9, "grid_w": 10, "cell_count": 8, "n_distinct_colors": 3},
        ):
            grid = gen.generate(123, 17, difficulty=difficulty, **overrides)
            observed = gen.observe_overrides(grid)
            assert all(observed[key] == value for key, value in overrides.items())
            assert gen.self_check(grid, difficulty=difficulty, meta=overrides) == []


def test_replay_freshness_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(91, 6, difficulty="hard")
    assert random.getstate() == state
    expected = copy.deepcopy(first)
    first[0][0] = (first[0][0] + 1) % 10
    second = gen.generate(91, 6, difficulty="hard")
    assert second == expected
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(
        7,
        11,
        difficulty="medium",
        grid_h=8,
        grid_w=10,
        cell_count=8,
        n_distinct_colors=2,
    )
    assert gen.self_check(valid) == []

    lower_occupied = copy.deepcopy(valid)
    lower_occupied[-1][0] = 9

    one_color = copy.deepcopy(valid)
    color = next(value for row in one_color for value in row if value)
    one_color = [[color if value else 0 for value in row] for row in one_color]

    missing_top_anchor = copy.deepcopy(valid)
    for c in range(len(missing_top_anchor[0])):
        missing_top_anchor[0][c] = 0

    solid_rectangle = [[0] * 8 for _ in range(6)]
    solid_rectangle[0][0] = 2
    solid_rectangle[0][1] = 3
    solid_rectangle[1][0] = 2
    solid_rectangle[1][1] = 3

    for impostor in (lower_occupied, one_color, missing_top_anchor, solid_rectangle):
        assert gen.self_check(impostor), impostor


def test_generated_distribution_is_structurally_valid():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.observe_overrides(grid)["cell_count"] in range(4, 9)
