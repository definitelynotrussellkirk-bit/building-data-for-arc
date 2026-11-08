"""Independent geometry oracle and portable helpers for abe8a3c35e86 tests.

This module intentionally does not import implementation helpers from generator.py.
The canonical Racket rule remains label authority; this Python oracle makes branch
reasoning, shortcut probes, and regression failures easier to inspect.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

TASK_ID = "abe8a3c35e86"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py")
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _pivot_and_motif(grid):
    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    motif = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 9)]
    if len(pivots) != 1:
        raise ValueError(f"expected one pivot, found {len(pivots)}")
    return pivots[0], motif


def classify_layout(grid) -> str:
    """Classify the motif relative to the pivot using the task's branch geometry."""
    (pr, pc), motif = _pivot_and_motif(grid)
    if not motif:
        return "none"
    rows = [r for r, _ in motif]
    cols = [c for _, c in motif]
    column_side = "left" if max(cols) < pc else ("right" if min(cols) > pc else None)
    row_side = "above" if max(rows) < pr else ("below" if min(rows) > pr else None)
    if column_side and row_side:
        return f"{'upper' if row_side == 'above' else 'lower'}_{column_side}"
    return column_side or row_side or "none"


def _reflect(grid, *, row_axis: bool, column_axis: bool):
    (pr, pc), motif = _pivot_and_motif(grid)
    out = [list(row) for row in grid]
    for r, c in motif:
        rr = 2 * pr - r if row_axis else r
        cc = 2 * pc - c if column_axis else c
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            out[rr][cc] = grid[r][c]
    return out


def canonical_output(grid):
    """Column-side branch first, matching the selected canonical Racket cond."""
    layout = classify_layout(grid)
    if layout in {"left", "right", "upper_left", "upper_right", "lower_left", "lower_right"}:
        return _reflect(grid, row_axis=False, column_axis=True)
    if layout in {"above", "below"}:
        return _reflect(grid, row_axis=True, column_axis=False)
    return [list(row) for row in grid]


def row_priority_output(grid):
    """Plausible shortcut: prefer row reflection when both axes qualify."""
    layout = classify_layout(grid)
    if layout in {"above", "below", "upper_left", "upper_right", "lower_left", "lower_right"}:
        return _reflect(grid, row_axis=True, column_axis=False)
    if layout in {"left", "right"}:
        return _reflect(grid, row_axis=False, column_axis=True)
    return [list(row) for row in grid]


def column_only_output(grid):
    layout = classify_layout(grid)
    if layout in {"left", "right", "upper_left", "upper_right", "lower_left", "lower_right"}:
        return _reflect(grid, row_axis=False, column_axis=True)
    return [list(row) for row in grid]


def row_only_output(grid):
    layout = classify_layout(grid)
    if layout in {"above", "below", "upper_left", "upper_right", "lower_left", "lower_right"}:
        return _reflect(grid, row_axis=True, column_axis=False)
    return [list(row) for row in grid]
