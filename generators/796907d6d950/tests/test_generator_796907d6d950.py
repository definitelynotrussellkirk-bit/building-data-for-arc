from __future__ import annotations

import copy
import importlib
import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.796907d6d950.generator"
)


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != MODULE.TASK_ID:
            continue
        for split in ("train", "test"):
            for pair in row[split]:
                yield pair["input"]


def _base_grid():
    return MODULE.generate(913, 7, difficulty="medium")


def test_canonical_inputs_satisfy_structural_checker():
    inputs = list(_canonical_inputs())
    assert len(inputs) == 6
    assert all(MODULE.self_check(grid) == [] for grid in inputs)


def test_exact_overrides_are_observable_at_boundaries():
    cases = (
        dict(cell_size=3, row_count=3, col_count=3, marker_size=3,
             template_size=5, template_row_index=0, template_col_index=1),
        dict(cell_size=5, row_count=5, col_count=5, marker_size=4,
             template_size=8, template_row_index=4, template_col_index=4),
    )
    for index, case in enumerate(cases):
        grid = MODULE.generate(400 + index, 23 + index, difficulty="hard", **case)
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        assert {name: observed[name] for name in case} == case


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(20260724)
    before = random.getstate()
    first = MODULE.generate(17, 9, difficulty="hard")
    middle = random.getstate()
    second = MODULE.generate(17, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_targeted_impostors():
    valid = _base_grid()
    assert MODULE.self_check(valid) == []
    observed = MODULE.observe_overrides(valid)
    cell = observed["cell_size"]
    sep = valid[cell][0]

    full = [[sep for _ in row] for row in valid]
    assert MODULE.self_check(full)

    no_template = copy.deepcopy(valid)
    tr = observed["template_row_index"] * (cell + 1)
    tc = observed["template_col_index"] * (cell + 1)
    for row in range(tr, tr + cell):
        for col in range(tc, tc + cell):
            no_template[row][col] = 0
    assert any("template" in error for error in MODULE.self_check(no_template))

    second_template = copy.deepcopy(valid)
    target_col = 1 if observed["template_col_index"] != 1 else 2
    target_row = (observed["template_row_index"] + 1) % observed["row_count"]
    source_cells = [
        (row - tr, col - tc, valid[row][col])
        for row in range(tr, tr + cell)
        for col in range(tc, tc + cell)
        if valid[row][col] != 0
    ]
    row0 = target_row * (cell + 1)
    col0 = target_col * (cell + 1)
    for local_row, local_col, color in source_cells:
        second_template[row0 + local_row][col0 + local_col] = color
    assert any("occupied non-marker" in error for error in MODULE.self_check(second_template))

    broken_marker = copy.deepcopy(valid)
    second_row0 = cell + 1
    marker_cells = [
        (row, col)
        for row in range(second_row0, second_row0 + cell)
        for col in range(cell)
        if broken_marker[row][col] != 0
    ]
    broken_marker[marker_cells[0][0]][marker_cells[0][1]] = 0
    assert any("marker" in error for error in MODULE.self_check(broken_marker))

    broken_separator = copy.deepcopy(valid)
    broken_separator[cell][cell // 2] = 0
    assert any("separator" in error or "lattice" in error for error in MODULE.self_check(broken_separator))


def test_four_example_schedule_exposes_rule_cues():
    for band in ("easy", "medium", "hard"):
        observations = [
            MODULE.observe_overrides(MODULE.generate(3001, index, difficulty=band))
            for index in range(4)
        ]
        assert {item["marker_size"] for item in observations} == {3, 4}
        assert len({item["template_size"] for item in observations}) >= 3
        assert any(item["template_row_index"] == 0 for item in observations)
        assert any(
            item["template_row_index"] == item["row_count"] - 1
            for item in observations
        )
        assert len({item["template_col_index"] for item in observations}) >= 2


def test_linked_semantic_census_200_per_band():
    for band_offset, band in enumerate(("easy", "medium", "hard")):
        grids = []
        observations = []
        for draw in range(200):
            grid = MODULE.generate(
                100_000 + band_offset * 10_000 + draw,
                8_000 + draw,
                difficulty=band,
            )
            assert MODULE.self_check(grid) == []
            grids.append(tuple(tuple(row) for row in grid))
            observations.append(MODULE.observe_overrides(grid))
        assert len(set(grids)) >= 195
        assert {item["marker_size"] for item in observations} == {3, 4}
        assert {item["template_size"] for item in observations} == {5, 6, 7, 8}
        assert len({
            (item["template_row_index"], item["template_col_index"])
            for item in observations
        }) >= 9
        assert Counter(item["cell_size"] for item in observations)[4] > 0
