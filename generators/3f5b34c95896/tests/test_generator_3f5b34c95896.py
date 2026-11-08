from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.3f5b34c95896.generator"
)


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError("canonical row not found")


def _expected_output(grid: list[list[int]]) -> list[list[int]]:
    facts, errors = GEN._analyze(grid)
    assert not errors
    occupied = facts["occupied"]
    dot_color = facts["dot_color"]
    return [
        [dot_color if (row, col) in occupied else 0 for col in range(3)]
        for row in range(3)
    ]


def test_rule_hash_and_task_local_sources_match_canonical() -> None:
    row = _canonical_row()
    source = row["program_solution"]
    assert GEN.RULE_HASH == hashlib.sha256(
        " ".join(source.split()).encode()
    ).hexdigest()[:12]

    base = json.loads(
        (
            ROOT
            / "data/base/solutions/training/5ad4f10b__3f5b34c95896.json"
        ).read_text()
    )
    assert base["racket_target"]["target_code"] == source
    assert base["racket_target"]["raw_code"] == source


def test_all_canonical_inputs_pass_structural_self_check() -> None:
    row = _canonical_row()
    inputs = [pair["input"] for pair in row["train"] + row["test"]]
    assert len(inputs) == 4
    for grid in inputs:
        assert GEN.self_check(copy.deepcopy(grid)) == []


def test_default_schedule_is_exact_replayable_and_identifiable() -> None:
    seed = 1729
    demos = []
    for sample_index in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index)
        assert GEN.self_check(grid) == []
        facts, errors = GEN._analyze(grid)
        assert not errors
        assert GEN.observe_overrides(grid) == {
            name: facts[name] for name in GEN.AXES
        }
        demos.append({"input": grid, "output": _expected_output(grid)})
    assert GEN.lesson_identifiable(demos, demos[-1]) == []


def test_boundary_overrides_are_observed_exactly() -> None:
    grid = GEN.generate(
        77,
        8,
        difficulty="hard",
        grid_h=20,
        grid_w=23,
        block_size=5,
        n_occupied=7,
        dot_count=55,
        shape_color=9,
        dot_color=1,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 20,
        "grid_w": 23,
        "block_size": 5,
        "n_occupied": 7,
        "dot_count": 55,
        "shape_color": 9,
        "dot_color": 1,
    }
    with pytest.raises(ValueError, match="must be distinct"):
        GEN.generate(1, 0, shape_color=4, dot_color=4)


def test_self_check_rejects_targeted_impostors() -> None:
    grid = GEN.generate(101, 0, block_size=3, dot_count=20)
    facts, errors = GEN._analyze(grid)
    assert not errors

    all_background = [[0 for _ in row] for row in grid]
    assert GEN.self_check(all_background)

    partial_block = copy.deepcopy(grid)
    row0, col0, _row1, _col1 = facts["shape_bbox"]
    partial_block[row0][col0] = 0
    assert any("partial" in error or "shape color" in error for error in GEN.self_check(partial_block))

    third_color = copy.deepcopy(grid)
    for row in range(len(third_color)):
        for col in range(len(third_color[0])):
            if third_color[row][col] == 0:
                third_color[row][col] = next(
                    color
                    for color in range(1, 10)
                    if color not in (facts["shape_color"], facts["dot_color"])
                )
                break
        else:
            continue
        break
    assert any("exactly two" in error for error in GEN.self_check(third_color))

    no_dots = [
        [0 if value == facts["dot_color"] else value for value in row]
        for row in grid
    ]
    assert GEN.self_check(no_dots)

    unsafe_dot_component = copy.deepcopy(grid)
    r0, c0, r1, c1 = facts["shape_bbox"]
    patch = None
    for row in range(len(grid) - 2):
        for col in range(len(grid[0]) - 2):
            cells = {
                (rr, cc)
                for rr in range(row, row + 3)
                for cc in range(col, col + 3)
            }
            if all(not (r0 <= rr <= r1 and c0 <= cc <= c1) for rr, cc in cells):
                patch = (row, col)
                break
        if patch:
            break
    assert patch is not None
    row, col = patch
    for rr in range(max(0, row - 1), min(len(grid), row + 4)):
        for cc in range(max(0, col - 1), min(len(grid[0]), col + 4)):
            if not (r0 <= rr <= r1 and c0 <= cc <= c1):
                unsafe_dot_component[rr][cc] = 0
    for rr in range(row, row + 3):
        for cc in range(col, col + 3):
            unsafe_dot_component[rr][cc] = facts["dot_color"]
    assert any(
        "noise component" in error
        for error in GEN.self_check(unsafe_dot_component)
    )


def test_fresh_returns_and_process_global_rng_purity() -> None:
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(33, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(33, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    original = first[0][0]
    second[0][0] = (second[0][0] + 1) % 10
    assert first[0][0] == original
