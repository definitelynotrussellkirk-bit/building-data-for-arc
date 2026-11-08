from __future__ import annotations

import copy
import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.ebc5c876edba import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _python_oracle(grid: list[list[int]]) -> list[list[int]]:
    bars = [
        c
        for c in range(len(grid[0]))
        if all(row[c] == 5 for row in grid)
    ]
    assert len(bars) == 1
    axis = bars[0]
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirror = 2 * axis - c
            if value == 2 and 0 <= mirror < len(row) and out[r][mirror] == 0:
                out[r][mirror] = 8
    return out


def test_rule_hash_and_canonical_pairs() -> None:
    assert gen.RULE_HASH == "4f52e6c7b24b"
    row = _canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert _python_oracle(pair["input"]) == pair["output"]


def test_regression_exact_override_boundaries_are_observable() -> None:
    # The pre-repair generator accepted these declarations but ignored semantic
    # axes and rejected full-domain dimension overrides in some bands.
    cases = [
        {
            "grid_h": 6,
            "grid_w": 7,
            "n_cells": 2,
            "source_side": "left",
            "layout": "connected",
            "axis_position": "center",
        },
        {
            "grid_h": 14,
            "grid_w": 18,
            "n_cells": 8,
            "source_side": "right",
            "layout": "split",
            "axis_position": "off_center",
        },
    ]
    for seed, case in enumerate(cases, start=701):
        grid = gen.generate(seed, seed + 3, difficulty="easy", **case)
        assert gen.observe_overrides(grid) == case
        assert gen.self_check(grid, meta={"overrides": case}) == []
        assert _python_oracle(grid) != grid


def test_every_scheduled_four_sample_lesson_covers_semantic_branches() -> None:
    for start in range(16):
        observed = [
            gen.observe_overrides(
                gen.generate(900 + offset, start + offset, difficulty="medium")
            )
            for offset in range(4)
        ]
        assert {item["source_side"] for item in observed} == {"left", "right"}
        assert {item["layout"] for item in observed} == {"connected", "split"}
        assert {item["axis_position"] for item in observed} == {
            "center",
            "off_center",
        }


def test_declared_mutation_fixtures_are_rejected() -> None:
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_targeted_impostor_error_classes() -> None:
    fixtures = dict(gen.mutation_fixtures())
    expected_fragments = {
        "no_bar": "full color-5 guide",
        "multiple_bars": "full color-5 guide",
        "no_cells": "2..8 color-2",
        "cells_both_sides": "exactly one side",
        "clipped_reflection": "out-of-bounds mirrors",
        "occupied_mirror": "non-background mirror targets",
        "unexpected_color": "unexpected colors",
    }
    for name, fragment in expected_fragments.items():
        assert any(fragment in error for error in gen.self_check(fixtures[name])), name


def test_replay_fresh_returns_input_purity_and_global_rng_purity() -> None:
    state = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    snapshot = copy.deepcopy(first)
    second = gen.generate(77, 9, difficulty="hard")
    assert first == second == snapshot
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    _ = _python_oracle(first)
    assert first == snapshot
    first[0][0] = 9 if first[0][0] != 9 else 0
    third = gen.generate(77, 9, difficulty="hard")
    assert third == second
