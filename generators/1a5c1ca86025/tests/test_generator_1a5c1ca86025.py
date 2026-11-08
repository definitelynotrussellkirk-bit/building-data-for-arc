from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "1a5c1ca86025"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.1a5c1ca86025.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        if TASK_ID not in line:
            continue
        row = json.loads(line)
        rows.extend(pair["input"] for pair in row["train"])
        test = row["test"]
        rows.extend([test["input"]] if isinstance(test, dict) else [p["input"] for p in test])
    return [
        [[int(value) for value in line] for line in grid]
        for grid in rows
    ]


def _blank():
    return [[0 for _ in range(9)] for _ in range(9)]


def _frame(grid, row0, col0, row1, col1, color):
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            if row in (row0, row1) or col in (col0, col1):
                grid[row][col] = color


def test_rule_pin_and_distribution_version():
    assert MODULE.RULE_HASH == "85ff67d41b51"
    assert MODULE.VERSION == "3.0.0"
    assert set(MODULE.AXES) == {"grid_h", "grid_w", "n_rects", "palette_kind"}
    assert MODULE.DEGENERATE_TEXTURES == ()


def test_all_canonical_inputs_pass_structural_checker():
    canonical = _canonical_inputs()
    assert len(canonical) == 3
    assert all(MODULE.self_check(grid) == [] for grid in canonical)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_realized(difficulty):
    for height, width, count in ((9, 9, 1), (9, 9, 3), (18, 20, 1), (18, 20, 3)):
        grid = MODULE.generate(
            23,
            17,
            difficulty=difficulty,
            grid_h=height,
            grid_w=width,
            n_rects=count,
            palette_kind="cool",
        )
        assert (len(grid), len(grid[0])) == (height, width)
        assert MODULE.observe_overrides(grid)["n_rects"] == count
        assert MODULE.self_check(grid) == []


def test_lesson_schedule_keeps_multi_object_demonstrations():
    expected = {
        "easy": [1, 2, 2, 2],
        "medium": [2, 2, 2, 2],
        "hard": [3, 2, 2, 3],
    }
    for difficulty, counts in expected.items():
        actual = [
            MODULE.observe_overrides(
                MODULE.generate(91, sample_index, difficulty=difficulty)
            )["n_rects"]
            for sample_index in range(4)
        ]
        assert actual == counts
        assert sum(value >= 2 for value in actual[:3]) >= 2


def test_self_check_rejects_targeted_impostors():
    impostors = {}

    singleton = _blank()
    singleton[4][4] = 4
    impostors["singleton"] = singleton

    short_line = _blank()
    short_line[4][2:7] = [4] * 5
    impostors["short_line"] = short_line

    solid = _blank()
    for row in range(2, 5):
        for col in range(2, 5):
            solid[row][col] = 4
    impostors["solid_rectangle"] = solid

    broken = _blank()
    _frame(broken, 1, 1, 4, 5, 4)
    broken[1][3] = 0
    impostors["broken_border"] = broken

    touching = _blank()
    _frame(touching, 0, 0, 2, 2, 4)
    _frame(touching, 3, 3, 5, 5, 7)
    impostors["diagonal_touch"] = touching

    duplicate = _blank()
    _frame(duplicate, 0, 0, 2, 2, 4)
    _frame(duplicate, 5, 5, 8, 8, 4)
    impostors["duplicate_colors"] = duplicate

    accepted = {name: MODULE.self_check(grid) for name, grid in impostors.items()}
    assert all(errors for errors in accepted.values()), accepted


def test_determinism_fresh_return_and_global_rng_state():
    state = random.getstate()
    first = MODULE.generate(101, 7, difficulty="hard")
    assert random.getstate() == state
    pristine = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = MODULE.generate(101, 7, difficulty="hard")
    assert second == pristine
    assert second is not first
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state


def test_palette_override_changes_colors_not_geometry():
    grids = {
        kind: MODULE.generate(
            77,
            9,
            difficulty="medium",
            grid_h=12,
            grid_w=14,
            n_rects=2,
            palette_kind=kind,
        )
        for kind in MODULE.PALETTE_KINDS
    }
    supports = {
        kind: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
        for kind, grid in grids.items()
    }
    assert len(set(map(frozenset, supports.values()))) == 1
    assert len({tuple(map(tuple, grid)) for grid in grids.values()}) == 4


def test_python_mirror_fires_only_inside_each_frame():
    for difficulty in ("easy", "medium", "hard"):
        grid = MODULE.generate(205, 3, difficulty=difficulty)
        output = MODULE.rule_mirror(grid)
        assert output != grid
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] != 0:
                    assert output[row][col] == grid[row][col]
                elif output[row][col] != 0:
                    assert output[row][col] in {value for line in grid for value in line if value}


def test_racket_oracle_matches_generated_inputs_and_executes_recombination():
    from arc_repl.racket_bridge import RacketBridge
    from scripts.rule_smoke import rule_application

    canonical_row = next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if TASK_ID in line
    )
    program = canonical_row["program_solution"]
    bridge = RacketBridge(timeout=30, max_calls_before_restart=None)
    try:
        for index, difficulty in enumerate(("easy", "medium", "hard")):
            grid = MODULE.generate(310 + index, 3, difficulty=difficulty)
            assert bridge.eval_text(rule_application(program, grid)) == MODULE.rule_mirror(grid)

        malformed = MODULE.generate(411, 3, difficulty="medium", n_rects=2)
        replacement = next(color for color in range(1, 10) if color not in {v for row in malformed for v in row})
        changed = False
        for row in range(len(malformed)):
            for col in range(len(malformed[0])):
                if malformed[row][col] != 0:
                    malformed[row][col] = replacement
                    changed = True
                    break
            if changed:
                break
        assert MODULE.self_check(malformed)
        result = bridge.eval_text(rule_application(program, malformed))
        assert isinstance(result, list) and result
    finally:
        bridge.shutdown()
