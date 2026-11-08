"""Semantic regression tests for exact-horizontal-triple expansion."""
from __future__ import annotations

import copy
from pathlib import Path
import random
import sys

import pytest


def _bootstrap_reviewer_support() -> None:
    """Make the packet-local public test helpers importable from any cwd."""
    for candidate in Path(__file__).resolve().parents:
        runtime = candidate / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            return
    raise RuntimeError("No packet-local shared/runtime/reviewer_support.py found")


_bootstrap_reviewer_support()

from reviewer_support import (
    canonical_pairs as reviewer_canonical_pairs,
    find_root,
    load_selected_generator,
)

TASK_ID = "a2fc4c442e35"
ROOT = find_root(__file__)
GEN, SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_pairs() -> list[dict]:
    return reviewer_canonical_pairs(TASK_ID, root=ROOT)


def _horizontal_runs(grid) -> list[tuple[int, int, int, int]]:
    runs = []
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            value = row[col]
            if value == 0:
                col += 1
                continue
            start = col
            while col < len(row) and row[col] == value:
                col += 1
            runs.append((row_index, start, col - 1, value))
    return runs


def _apply_run_extension(grid, *, exact_length: int | None) -> list[list[int]]:
    """Independent oracle over runs found in the unchanged input grid."""
    out = copy.deepcopy(grid)
    width = len(grid[0])
    for row, start, end, value in _horizontal_runs(grid):
        length = end - start + 1
        if exact_length is not None and length != exact_length:
            continue
        if start > 0 and grid[row][start - 1] == 0:
            out[row][start - 1] = value
        if end + 1 < width and grid[row][end + 1] == 0:
            out[row][end + 1] = value
    return out


def _blank(height: int = 5, width: int = 9) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def test_metadata_and_canonical_pairs_pin_mixed_run_teaching_domain():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.2.0"

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert _apply_run_extension(pair["input"], exact_length=3) == pair["output"]
        assert _apply_run_extension(pair["input"], exact_length=None) != pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_default_draw_contains_target_and_length_four_negative(difficulty):
    for sample_index in range(32):
        grid = GEN.generate(6100 + sample_index, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []

        runs = _horizontal_runs(grid)
        lengths = [end - start + 1 for _, start, end, _ in runs]
        assert 3 in lengths
        assert 4 in lengths
        assert set(lengths) <= {3, 4}
        assert len({row for row, *_ in runs}) == len(runs)

        intended = _apply_run_extension(grid, exact_length=3)
        overgeneralized = _apply_run_extension(grid, exact_length=None)
        assert overgeneralized != intended


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("target_runs", [1, 2, 3])
def test_runs_override_counts_only_actionable_triples(difficulty, target_runs):
    grid = GEN.generate(991, 7, difficulty=difficulty, runs=target_runs)
    lengths = [end - start + 1 for _, start, end, _ in _horizontal_runs(grid)]
    assert lengths.count(3) == target_runs
    assert lengths.count(4) == 1
    assert GEN.self_check(grid) == []


def test_validator_requires_both_semantic_classes_and_rejects_other_lengths():
    triple_only = _blank()
    triple_only[1][2:5] = [2, 2, 2]
    assert any("length-4" in error for error in GEN.self_check(triple_only))

    longer_only = _blank()
    longer_only[2][2:6] = [4, 4, 4, 4]
    assert any("length-3" in error for error in GEN.self_check(longer_only))

    for bad_length in (1, 2, 5):
        grid = _blank()
        grid[1][1 : 1 + bad_length] = [7] * bad_length
        grid[3][2:6] = [4, 4, 4, 4]
        errors = GEN.self_check(grid)
        assert any(f"length {bad_length}" in error for error in errors)


def test_validator_rejects_shared_rows_and_nonblank_flanks():
    shared_row = _blank(width=12)
    shared_row[1][1:4] = [2, 2, 2]
    shared_row[1][6:10] = [4, 4, 4, 4]
    assert any("runs" in error and "row" in error for error in GEN.self_check(shared_row))

    touching_colors = _blank(width=10)
    touching_colors[1][1:4] = [2, 2, 2]
    touching_colors[1][4:8] = [4, 4, 4, 4]
    errors = GEN.self_check(touching_colors)
    assert any("flank" in error for error in errors)


@pytest.mark.parametrize("grid", [[], [[]], [[0, 0], [0]], [[0], [0, 1]]])
def test_malformed_or_empty_grids_return_diagnostics(grid):
    assert GEN.self_check(grid)


def test_generation_is_deterministic_fresh_and_global_random_pure():
    random.seed(314159)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
