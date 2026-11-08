from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "449ea8b9619c"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.449ea8b9619c.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _normalized_selected_shape(grid):
    marker = grid[-1][0]
    shape_color = next(
        value for row in grid for value in row if value not in (0, marker)
    )
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == shape_color
    ]
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _pair(grid):
    return {"input": grid, "output": MODULE.rule_python(grid)}


def test_rule_hash_and_canonical_shape_bank_are_pinned():
    assert MODULE.RULE_HASH == "042c5b1f1719"
    row = _canonical_row()
    derived = tuple(
        _normalized_selected_shape(pair["input"])
        for split in ("train", "test")
        for pair in row[split]
    )
    assert set(derived) == set(MODULE._CANONICAL_SHAPES)


def test_canonical_pairs_pass_self_check_and_python_rule():
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            assert MODULE.self_check(pair["input"]) == []
            assert MODULE.rule_python(pair["input"]) == pair["output"]
            assert MODULE.strict_canonical_like(pair["input"]) == []


def test_exact_overrides_round_trip_and_bad_keys_reject():
    requested = {
        "grid_h": 7,
        "grid_w": 7,
        "shape_size": 15,
        "marker_color": 1,
        "shape_color": 2,
    }
    grid = MODULE.generate(91, 17, difficulty="hard", **requested)
    assert MODULE.observe_overrides(grid) == requested
    assert MODULE.self_check(grid, meta={"overrides": requested}) == []

    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(0, 0, misspelled_axis=3)
    with pytest.raises(ValueError, match="must differ"):
        MODULE.generate(0, 0, marker_color=4, shape_color=4)


def test_every_three_example_window_refutes_all_named_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [
                _pair(MODULE.generate(200 + start, start + offset, difficulty=difficulty))
                for offset in range(3)
            ]
            query = _pair(MODULE.generate(200 + start, start + 3, difficulty=difficulty))
            assert MODULE.lesson_identifiable(demos, query) == []
            for competitor in MODULE.LESSON_COMPETITORS.values():
                assert not all(
                    competitor(pair["input"]) == pair["output"]
                    for pair in demos
                )


def test_self_check_rejects_four_targeted_impostors():
    for texture in MODULE.DEGENERATE_TEXTURES:
        grid = MODULE.generate(0, 0, texture=texture)
        assert MODULE.self_check(grid), texture


def test_default_schedule_covers_canonical_and_counterexample_witnesses_per_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(501, index, difficulty=difficulty) for index in range(40)]
        assert sum(not MODULE.strict_canonical_like(grid) for grid in grids) == 20
        for name, witness in MODULE.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), name


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    before = random.getstate()
    first = MODULE.generate(77, 5, difficulty="medium")
    after = random.getstate()
    second = MODULE.generate(77, 5, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
