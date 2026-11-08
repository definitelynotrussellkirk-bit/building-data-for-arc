from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "9fe97c2dd8a4"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def test_canonical_inputs_are_accepted_and_rule_mirror_matches_all_pairs():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_regression_canonical_test_with_three_fives_is_lawful():
    grid = _canonical_row()["test"][0]["input"]
    assert sum(value == 5 for row in grid for value in row) == 3
    assert gen.self_check(grid) == []


def test_exact_override_boundaries_are_observable():
    single_cases = [
        {"grid_h": 4},
        {"grid_h": 14},
        {"grid_w": 3},
        {"grid_w": 18},
        {"marker_col": 2},
        {"marker_col": 17},
        {"bar_count": 1},
        {"bar_count": 6},
        {"duplicate_mode": False},
        {"duplicate_mode": True},
    ]
    for overrides in single_cases:
        grid = gen.generate(123, 8, difficulty="easy", **overrides)
        assert gen.self_check(grid) == []
        observed = {
            "grid_h": len(grid),
            "grid_w": len(grid[0]),
            **gen.observe_overrides(grid),
        }
        for key, value in overrides.items():
            assert observed[key] == value

    combined = {
        "grid_h": 14,
        "grid_w": 18,
        "marker_col": 17,
        "bar_count": 6,
        "duplicate_mode": True,
    }
    grid = gen.generate(456, 3, difficulty="hard", **combined)
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        **gen.observe_overrides(grid),
    }
    assert observed == combined


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 4, "bar_count": 6},
        {"grid_w": 3, "marker_col": 17},
        {"bar_count": 1, "duplicate_mode": True},
        {"marker_col": 2, "duplicate_mode": True},
    ],
)
def test_incompatible_override_pairs_reject_loudly(overrides):
    with pytest.raises(ValueError, match=".+"):
        gen.generate(1, 0, **overrides)


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(
        99,
        1,
        grid_h=10,
        grid_w=10,
        marker_col=8,
        bar_count=4,
        duplicate_mode=True,
    )
    assert gen.self_check(base) == []

    no_marker = copy.deepcopy(base)
    no_marker[0][8] = 0
    assert gen.self_check(no_marker)

    split_bar = copy.deepcopy(base)
    row = gen._bar_rows(split_bar)[0]
    positions = [c for c, value in enumerate(split_bar[row]) if value]
    split_bar[row][positions[len(positions) // 2]] = 0
    assert any("contiguous" in error for error in gen.self_check(split_bar))

    adjacent_bar = copy.deepcopy(base)
    source_row = gen._bar_rows(adjacent_bar)[0]
    adjacent_bar[source_row + 1] = adjacent_bar[source_row][:]
    assert any("alternating" in error for error in gen.self_check(adjacent_bar))

    crosses_marker = copy.deepcopy(base)
    row = gen._bar_rows(crosses_marker)[0]
    crosses_marker[row][8] = next(value for value in crosses_marker[row] if value)
    assert any("marker column" in error for error in gen.self_check(crosses_marker))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    before = random.getstate()
    first = gen.generate(777, 12, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 12, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after

    first[0][0] = 9
    third = gen.generate(777, 12, difficulty="hard")
    assert third == second


def test_four_demo_schedule_identifies_all_decisive_branches():
    demos = []
    for sample_index in range(4):
        grid = gen.generate(314159, sample_index)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(314159, 4)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}

    assert any(not gen._duplicate_state(pair["input"])[0] for pair in demos)
    assert any(gen._has_unique_adjustment(pair["input"]) for pair in demos)
    assert any(gen._has_five_bar(pair["input"]) for pair in demos)
    assert gen.lesson_identifiable(demos, query) == []
