from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.6aaddc95d135.generator"
)
TASK_ID = "6aaddc95d135"
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def test_generator_6aaddc95d135_accepts_and_solves_all_canonical_pairs():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_generator_6aaddc95d135_exact_overrides_work_in_every_band():
    for band in ("easy", "medium", "hard"):
        for h, w, n_cols in ((7, 8, 3), (10, 10, 6)):
            grid = MODULE.generate(
                71,
                9,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                n_cols=n_cols,
                palette_mode="mixed_ids",
            )
            assert (len(grid), len(grid[0])) == (h, w)
            assert MODULE.observe_overrides(grid) == {"n_cols": n_cols}
            assert MODULE.self_check(grid, difficulty=band) == []


def test_generator_6aaddc95d135_is_deterministic_fresh_and_rng_pure():
    random.seed(9137)
    state = random.getstate()
    first = MODULE.generate(123, 4, difficulty="hard")
    second = MODULE.generate(123, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state
    assert all(predicate(first) for predicate in MODULE.SEMANTIC_WITNESSES.values())
    assert MODULE.rule_mirror(first) != first


def test_generator_6aaddc95d135_palette_modes_are_behavioral():
    grids = {
        mode: MODULE.generate(
            55,
            2,
            difficulty="medium",
            grid_h=8,
            grid_w=9,
            n_cols=3,
            palette_mode=mode,
        )
        for mode in MODULE.PALETTE_MODES
    }
    assert len({json.dumps(grid) for grid in grids.values()}) == len(grids)


def test_generator_6aaddc95d135_rejects_targeted_impostors():
    lawful = MODULE.generate(321, 7, difficulty="medium")
    h, w = len(lawful), len(lawful[0])

    all_background = [[0 for _ in range(w)] for _ in range(h)]
    full_one_color = [[4 for _ in range(w)] for _ in range(h)]
    short_line = [[0, 3, 0, 3]]
    already_packed = [[0 for _ in range(w)] for _ in range(h)]
    for c, count, color in ((1, 1, 2), (3, 2, 4), (5, 3, 6)):
        for r in range(h - count, h):
            already_packed[r][c] = color

    active = MODULE._active_columns(lawful)
    mixed_column = copy.deepcopy(lawful)
    c = next(col for col in active if len(MODULE._column_rows(lawful, col)) >= 2)
    rows = MODULE._column_rows(mixed_column, c)
    used = {value for row in lawful for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    mixed_column[rows[0]][c] = replacement

    for impostor in (
        all_background,
        full_one_color,
        short_line,
        already_packed,
        mixed_column,
    ):
        assert MODULE.self_check(impostor), impostor

    # The malformed mixed-color lesson is rejected by the teaching grammar,
    # while the canonical oracle remains total on it. These are distinct facts.
    output = MODULE.rule_mirror(mixed_column)
    assert len(output) == h and len(output[0]) == w


def test_generator_6aaddc95d135_lesson_rebuts_plausible_rivals():
    pairs = []
    for index in range(4):
        grid = MODULE.generate(800 + index, index, difficulty="medium")
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_generator_6aaddc95d135_rule_hash_is_pinned():
    assert MODULE.RULE_HASH == "7640715456c4"
