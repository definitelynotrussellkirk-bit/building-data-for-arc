"""Independent oracle and repeatable probes for fa5bb24054bc.

This module deliberately does not import geometry helpers from the production
sampler.  It is task-local reviewer tooling, not a replacement label authority.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = "fa5bb24054bc"
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
CANONICAL_PROFILES = {(3, 10, 4), (3, 12, 4), (4, 12, 4)}


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(value):
    if not isinstance(value, list):
        return value
    if value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return deepcopy(value)


def canonical_pairs():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK:
                continue
            test = row.get("test")
            tests = test if isinstance(test, list) else [test]
            return [
                {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                for pair in list(row.get("train") or []) + tests
            ]
    raise ValueError(f"canonical task {TASK} is absent")


def _blank_column(grid, col):
    return all(row[col] == 0 for row in grid)


def panel_spans(grid):
    spans = []
    col = 0
    width = len(grid[0])
    while col < width:
        while col < width and _blank_column(grid, col):
            col += 1
        if col >= width:
            break
        start = col
        while col < width and not _blank_column(grid, col):
            col += 1
        spans.append((start, col))
    return spans


def split_panels(grid):
    return [[row[start:stop] for row in grid] for start, stop in panel_spans(grid)]


def separator_widths(grid):
    spans = panel_spans(grid)
    return [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)]


def _normalized_cells(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def hole_count(panel):
    cells = _normalized_cells(panel)
    if not cells:
        return 0
    height = max(r for r, _ in cells) + 3
    width = max(c for _, c in cells) + 3
    occupied = {(r + 1, c + 1) for r, c in cells}
    free = {(r, c) for r in range(height) for c in range(width) if (r, c) not in occupied}
    outside = {p for p in free if p[0] in (0, height - 1) or p[1] in (0, width - 1)}
    queue = deque(outside)
    seen = set(outside)
    while queue:
        r, c = queue.popleft()
        for dr, dc in CARDINAL:
            q = (r + dr, c + dc)
            if q in free and q not in seen:
                seen.add(q)
                queue.append(q)
    enclosed = free - seen
    holes = 0
    while enclosed:
        holes += 1
        start = enclosed.pop()
        queue = [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in CARDINAL:
                q = (r + dr, c + dc)
                if q in enclosed:
                    enclosed.remove(q)
                    queue.append(q)
    return holes


def features(grid):
    result = []
    for panel in split_panels(grid):
        area = sum(value != 0 for row in panel for value in row)
        result.append((area, hole_count(panel)))
    return result


def relation_output(grid):
    info = features(grid)
    return [
        [
            5 if i == j else 6 if info[i] == info[j] else 2 if info[i][0] == info[j][0]
            else 3 if info[i][1] == info[j][1] else 0
            for j in range(len(info))
        ]
        for i in range(len(info))
    ]


def rival_area_equality_means_both(grid):
    """Canonical-fitting rival: every equal-area pair is mislabeled as 6."""
    info = features(grid)
    return [
        [
            5 if i == j else 6 if info[i][0] == info[j][0]
            else 3 if info[i][1] == info[j][1] else 0
            for j in range(len(info))
        ]
        for i in range(len(info))
    ]


def observed_axes(grid):
    gaps = separator_widths(grid)
    if not gaps or len(set(gaps)) != 1:
        raise ValueError(f"expected one uniform separator width, saw {gaps}")
    return {"grid_h": len(grid), "n_panels": len(panel_spans(grid)), "sep_width": gaps[0]}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def off_diagonal_codes(output):
    return {value for r, row in enumerate(output) for c, value in enumerate(row) if r != c}


def area_only_witness():
    # Left: connected area-8 solid (no hole). Right: area-8 3x3 ring (one hole).
    left = {(r, c) for r in range(3) for c in range(3)} - {(0, 0)}
    right = {(r, c) for r in range(3) for c in range(3) if r in (0, 2) or c in (0, 2)}
    grid = [[0] * 7 for _ in range(3)]
    for r, c in left:
        grid[r][c] = 2
    for r, c in right:
        grid[r][c + 4] = 7
    return grid


def pair(module, seed, sample_index, **kwargs):
    grid = module.generate(seed, sample_index, **kwargs)
    return {"input": grid, "output": relation_output(grid)}
