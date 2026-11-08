from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "241567a35764"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _normalize(cells):
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rotate(cells):
    normalized = _normalize(cells)
    return _normalize((c, -r) for r, c in normalized)


def _flip_columns(cells):
    normalized = _normalize(cells)
    cmax = max(c for _, c in normalized)
    return _normalize((r, cmax - c) for r, c in normalized)


def _shape(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    bottom = grid[-1]
    control = next((value for value in (2, 3, 4) if value in bottom), 2)
    times = {2: 0, 3: 1, 4: 2}[control]
    result = _normalize(cells)
    for _ in range(times):
        result = _rotate(result)
    if 6 in bottom:
        result = _flip_columns(result)
    return result


def _stamp_count(grid):
    h, w = len(grid), len(grid[0])
    start = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7)
    nxt = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8)
    dr, dc = nxt[0] - start[0], nxt[1] - start[1]
    shape = _shape(grid)
    count = 0
    ar, ac = start
    while all(0 <= ar + r < h and 0 <= ac + c < w for r, c in shape):
        count += 1
        ar += dr
        ac += dc
    return count


def test_saved_zero_stamp_witness_is_rejected():
    path = HOME / "counterexamples" / "review-747a092dfe8b4a46-v0001" / "retained" / "checks" / "audit" / TASK_ID / "input.json"
    grid = json.loads(path.read_text(encoding="utf-8"))
    errors = GEN.self_check(grid, difficulty="easy")
    assert any("stamp" in error for error in errors), errors


def test_exact_seed_index_has_two_fully_in_bounds_stamps():
    grid = GEN.generate(0, 1, difficulty="easy")
    assert GEN.self_check(grid, difficulty="easy") == []
    assert _stamp_count(grid) >= 2


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generated_marker_pairs_support_two_stamps(difficulty):
    for seed in range(8):
        for sample_index in range(4):
            grid = GEN.generate(seed, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert _stamp_count(grid) >= 2
