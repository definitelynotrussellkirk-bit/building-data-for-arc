from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "c0bd45c81959"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _counts(grid, r1, c1):
    return Counter(
        grid[r][c]
        for r in range(r1, r1 + 3)
        for c in range(c1, c1 + 2)
        if grid[r][c] != 0
    )


def _assert_unique_modes(grid):
    for br in range(2):
        for bc in range(3):
            counts = _counts(grid, 1 + 4 * br, 1 + 3 * bc)
            assert counts
            top = max(counts.values())
            assert sum(value == top for value in counts.values()) == 1, counts


def test_exact_three_distractor_override_preserves_unique_modes():
    grid = GEN.generate(
        10,
        0,
        difficulty="hard",
        n_distract_min=3,
        n_distract_max=3,
    )
    assert GEN.self_check(grid, difficulty="hard") == []
    _assert_unique_modes(grid)


def test_self_check_rejects_saved_tied_mode_witness():
    path = HOME / "counterexamples" / "review-ea54c56b6ee87171-v0001" / "retained" / "checks" / "audit" / TASK_ID / "input.json"
    grid = json.loads(path.read_text(encoding="utf-8"))
    errors = GEN.self_check(grid, difficulty="hard")
    assert any("unique" in error or "tie" in error for error in errors), errors


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generated_domain_has_unique_modes_and_zero_nonblock_cells(difficulty):
    for seed in range(8):
        grid = GEN.generate(seed, seed % 4, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        _assert_unique_modes(grid)
