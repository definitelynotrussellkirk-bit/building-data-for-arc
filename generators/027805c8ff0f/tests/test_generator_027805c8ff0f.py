from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "027805c8ff0f"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"


def _load():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load()


def _canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row["program_solution"])
    assert len(set(rows)) == 1
    return rows[0]


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _panel_cells(grid: list[list[int]], panel: int) -> int:
    n = len(grid)
    start = panel * (n + 1)
    if panel:
        start -= 0
    return sum(
        grid[r][c] not in (0, 1)
        for r in range(n)
        for c in range(start, start + n)
    )


def test_shape_k_override_is_consumed_exactly(gen):
    common = dict(panel_n=5, transform=2)
    small = gen.generate(7301, 0, shape_k=3, **common)
    large = gen.generate(7301, 0, shape_k=8, **common)
    assert _panel_cells(small, 0) == 3
    assert _panel_cells(large, 0) == 8
    assert small != large


@pytest.mark.parametrize(
    "overrides",
    [
        {"shape_k": 2},
        {"shape_k": 13},
        {"shape_k": True},
        {"panel_n": True},
        {"transform": 7},
        {"definitely_not_an_axis": 1},
    ],
)
def test_invalid_or_unknown_overrides_fail_closed(gen, overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7302, 0, **overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"texture": "identity_transform", "shape_k": 5},
        {"texture": "ambiguous_symmetric", "transform": 3},
    ],
)
def test_degenerate_textures_reject_axes_they_cannot_honor(gen, overrides):
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(7302, 0, **overrides)


def test_self_check_rejects_broken_transform_relation(gen):
    grid = gen.generate(7303, 0, panel_n=5, transform=2, shape_k=5)
    assert gen.self_check(grid) == []
    broken = [row[:] for row in grid]
    n = len(broken)
    # Toggle one B-panel content cell while preserving dividers and non-emptiness.
    candidates = [
        (r, c)
        for r in range(n)
        for c in range(n + 1, 2 * n + 1)
        if broken[r][c] == 0
    ]
    r, c = candidates[0]
    broken[r][c] = next(v for v in range(2, 10) if v != broken[0][0])
    assert any("transform" in message or "match" in message for message in gen.self_check(broken))


@pytest.mark.parametrize("difficulty", [None, "medium"])
def test_generated_inputs_are_deterministic_valid_and_racket_executable(gen, difficulty):
    first = gen.generate(7304, 7, difficulty=difficulty)
    second = gen.generate(7304, 7, difficulty=difficulty)
    assert first == second
    assert gen.self_check(first) == []
    with RacketBridge(timeout=60) as bridge:
        output = normalize_grid(
            bridge.eval_text(f"({wrap_rule(_canonical_program())} {_datum(first)})")
        )
    assert output
    assert 1 <= len(output) <= 30
    assert 1 <= len(output[0]) <= 30
