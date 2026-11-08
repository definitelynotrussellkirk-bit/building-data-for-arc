from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "7768dfc99e25"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"


def generator():
    spec = importlib.util.spec_from_file_location("_generator_7768_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selected_rule_hash_is_declared():
    assert generator().RULE_HASH == "be1e3a1eb944"


def test_self_check_rejects_one_red_component_that_spans_border_and_interior():
    module = generator()
    grid = [[0] * 6 for _ in range(6)]
    for row, col in [(0, 2), (1, 2), (1, 3), (2, 2)]:
        grid[row][col] = 2
    errors = module.self_check(grid)
    assert any("at least two" in error or "component" in error for error in errors), errors


def test_self_check_requires_exactly_one_border_touching_red_component():
    module = generator()
    valid = [[0] * 8 for _ in range(8)]
    for row, col in [(0, 1), (1, 1), (1, 2)]:
        valid[row][col] = 2
    for row, col in [(4, 4), (4, 5), (5, 5)]:
        valid[row][col] = 2
    assert module.self_check(valid) == []

    invalid = [row[:] for row in valid]
    invalid[7][6] = invalid[6][6] = 2
    errors = module.self_check(invalid)
    assert any("exactly one" in error for error in errors), errors
