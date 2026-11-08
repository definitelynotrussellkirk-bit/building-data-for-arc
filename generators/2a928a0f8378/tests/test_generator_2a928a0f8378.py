from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.2a928a0f8378.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "2a928a0f8378"


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _active(grid):
    return [row[:] for row in grid if any(value != 0 for value in row)]


def test_rule_hash_pin_and_canonical_self_check():
    row = _canonical_row()
    actual = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual == "12cdce90baa1"
    for split in ("train", "test"):
        for index, pair in enumerate(row[split]):
            assert gen.self_check(
                pair["input"],
                meta={"canonical": True, "split": split, "pair_index": index},
            ) == []
            assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_boundary_overrides_and_loud_incompatibility():
    cases = [
        {"grid_h": 6, "grid_w": 6, "active_rows": 2, "palette_size": 2},
        {"grid_h": 16, "grid_w": 16, "active_rows": 8, "palette_size": 6},
        {"active_rows": 8},
        {"grid_h": 6},
        {"grid_w": 6, "palette_size": 6},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(100 + index, 30 + index, difficulty="medium", **overrides)
        observed = gen.observe_overrides(grid)
        for axis, requested in overrides.items():
            assert observed[axis] == requested
        assert gen.self_check(grid, difficulty="medium", meta={"overrides": overrides}) == []
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 1, grid_h=6, active_rows=8)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, obsolete_axis=3)


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(987654321)
    state = random.getstate()
    first = gen.generate(42, 7, difficulty="hard")
    assert random.getstate() == state
    replay = gen.generate(42, 7, difficulty="hard")
    assert replay == first
    assert replay is not first
    assert all(a is not b for a, b in zip(replay, first))
    replay[0][0] = (replay[0][0] + 1) % 10
    assert gen.generate(42, 7, difficulty="hard") == first


def test_semantic_distribution_and_sequential_order_witness():
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed, seed, difficulty=band)
            facts = gen.observe_overrides(grid)
            active = _active(grid)
            output = gen.rule_mirror(grid)
            assert output != grid
            assert output[: len(active)] == active
            assert all(all(value == 0 for value in row) for row in output[len(active) :])
            assert gen.self_check(grid, difficulty=band) == []
            assert 2 <= facts["active_rows"] <= 8
            assert 2 <= facts["palette_size"] <= 6

    # Consecutive demonstrations alternate whether the one-cell row precedes
    # or follows the multicolor row, defeating stable density sorting.
    grids = [gen.generate(777, index, difficulty="medium") for index in range(4)]
    counts = [[sum(value != 0 for value in row) for row in _active(grid)] for grid in grids]
    assert counts[0][0] < counts[0][1]
    assert counts[1][0] > counts[1][1]
    assert counts[2][0] < counts[2][1]
    assert counts[3][0] > counts[3][1]

    # Even demos falsify lexicographic sorting; odd demos falsify sorting by
    # first nonzero column. Column 0 belongs only to the solid witness.
    for index in (0, 2):
        rows = _active(grids[index])
        assert rows[0][0] != 0 and rows[1][0] == 0
        assert sorted(rows) != rows
    rows = _active(grids[1])
    assert rows[0][0] == 0 and rows[1][0] != 0
    first_nonzero = lambda row: next(i for i, value in enumerate(row) if value)
    assert sorted(rows, key=first_nonzero) != rows


def test_self_check_rejects_targeted_impostors():
    grid = gen.generate(123, 5, difficulty="medium", grid_h=10, active_rows=4)
    active = _active(grid)
    h, w = len(grid), len(grid[0])
    blank = [0] * w

    top_packed = [row[:] for row in active] + [blank[:] for _ in range(h - len(active))]

    no_internal_gap = [blank[:]] + [row[:] for row in active]
    no_internal_gap += [blank[:] for _ in range(h - len(no_internal_gap))]

    all_monochrome = copy.deepcopy(grid)
    for r, row in enumerate(all_monochrome):
        colors = [value for value in row if value != 0]
        if colors:
            color = colors[0]
            all_monochrome[r] = [color if value != 0 else 0 for value in row]

    duplicate_rows = copy.deepcopy(grid)
    indices = [r for r, row in enumerate(duplicate_rows) if any(value != 0 for value in row)]
    duplicate_rows[indices[1]] = duplicate_rows[indices[0]][:]

    absent_color_full_row = copy.deepcopy(grid)
    used = {value for row in absent_color_full_row for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    blank_index = next(r for r, row in enumerate(absent_color_full_row) if all(v == 0 for v in row))
    absent_color_full_row[blank_index] = [replacement] * w

    impostors = [
        top_packed,
        no_internal_gap,
        all_monochrome,
        duplicate_rows,
        absent_color_full_row,
    ]
    for impostor in impostors:
        assert gen.self_check(impostor), impostor
