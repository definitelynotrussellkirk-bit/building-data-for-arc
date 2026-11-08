"""Independent, source-selectable probes for a8a8969ab4f1 review work.

This module deliberately does not import implementation helpers from generator.py.
Set GENERATOR_UNDER_TEST to replay the tests or qualification script against a
retained candidate source.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "a8a8969ab4f1"
TASK_HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def analyze_pixels(grid: list[list[int]]) -> dict[str, Any]:
    """Recover structural facts without using production implementation code."""
    h, w = len(grid), len(grid[0])
    active_rows = [r for r, row in enumerate(grid) if row[0] not in (0, 8)]
    blank_rows = [r for r, row in enumerate(grid) if row[0] == 0]
    key_colors = [grid[r][0] for r in active_rows]
    marker_counts = [sum(value == 8 for value in grid[r][1:]) for r in active_rows]
    unkeyed_markers = [(r, c) for r in blank_rows for c in range(1, w) if grid[r][c] == 8]
    return {
        "shape": f"{h}x{w}",
        "active_rows": active_rows,
        "key_colors": key_colors,
        "marker_counts": marker_counts,
        "unkeyed_markers": unkeyed_markers,
    }


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected prose rule for focused tests only."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        key = row[0]
        if key == 0:
            continue
        for c in range(1, len(row)):
            if row[c] == 8:
                out[r][c] = key
    return out
