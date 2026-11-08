"""Independent geometry oracle and rival probe for 57799de7f990.

This module is task-local test tooling.  It deliberately does not import
production helpers from generator.py.  The selected Racket program remains the
label authority; these routines make structural claims independently testable.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

TASK_ID = "57799de7f990"
ROOT = Path(__file__).resolve().parents[3]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path=None):
    source = Path(path or ROOT / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_path() -> Path:
    candidates = (
        ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl",
        ROOT / "data" / "canonical" / "puzzles.jsonl",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("canonical puzzles.jsonl is absent from the portable runtime")


def canonical_row():
    with _canonical_path().open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task {TASK_ID} is absent")


def _normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return deepcopy(grid)


def canonical_pairs():
    row = canonical_row()
    pairs = []
    for split in ("train", "test"):
        raw = row.get(split) or []
        if isinstance(raw, dict):
            raw = [raw]
        for pair in raw:
            pairs.append({"input": _normalize_grid(pair["input"]),
                          "output": _normalize_grid(pair["output"])})
    return pairs


def diamond_centers(grid):
    """Authority-like center detection: only the four arms matter."""
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if all(grid[r + dr][c + dc] == 2 for dr, dc in _CARDINAL)
    ]


def _paint_consecutive(grid, horizontal, vertical):
    out = deepcopy(grid)
    for r, columns in horizontal.items():
        ordered = sorted(set(columns))
        for left, right in zip(ordered, ordered[1:]):
            for c in range(left + 1, right):
                if out[r][c] == 0:
                    out[r][c] = 1
    for c, rows in vertical.items():
        ordered = sorted(set(rows))
        for top, bottom in zip(ordered, ordered[1:]):
            for r in range(top + 1, bottom):
                if out[r][c] == 0:
                    out[r][c] = 1
    return out


def intended_output(grid):
    horizontal = defaultdict(list)
    vertical = defaultdict(list)
    for r, c in diamond_centers(grid):
        horizontal[r].append(c)
        vertical[c].append(r)
    return _paint_consecutive(grid, horizontal, vertical)


def axis_local_rival(grid):
    """Plausible wrong rule retained from review-10a65405aae36591.

    It recognizes horizontal and vertical centers independently.  A candidate
    needs both arms on the relevant axis and only one arm on the other axis,
    rather than all four arms of a true diamond.
    """
    h, w = len(grid), len(grid[0])
    horizontal = defaultdict(list)
    vertical = defaultdict(list)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if (grid[r][c - 1] == grid[r][c + 1] == 2
                    and (grid[r - 1][c] == 2 or grid[r + 1][c] == 2)):
                horizontal[r].append(c)
            if (grid[r - 1][c] == grid[r + 1][c] == 2
                    and (grid[r][c - 1] == 2 or grid[r][c + 1] == 2)):
                vertical[c].append(r)
    return _paint_consecutive(grid, horizontal, vertical)


def observed(grid):
    intended = intended_output(grid)
    rival = axis_local_rival(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_diamonds": len(diamond_centers(grid)),
        "three_arm_witness": intended != rival,
    }


def explicit_witness():
    """9x9, three true diamonds; rival inserts false centers at (2,3),(2,5)."""
    grid = [[0] * 9 for _ in range(9)]
    for r, c in ((2, 1), (3, 4), (2, 7)):
        for dr, dc in _CARDINAL:
            grid[r + dr][c + dc] = 2
    return grid
