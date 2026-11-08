"""Independent test helpers for 4f09f8bfa35a.

This module deliberately does not import production helpers from generator.py.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

TASK_ID = "4f09f8bfa35a"
COMMANDS = (2, 3, 4, 5)
CANONICAL_PROFILES = {(8, 12, 5), (9, 13, 5), (10, 14, 5), (8, 11, 4), (10, 15, 6)}


def load_generator(path: str | None = None):
    target = Path(path or (Path(__file__).resolve().parents[1] / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", target)
    if spec is None or spec.loader is None:
        raise ImportError(target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_path() -> Path:
    start = Path(__file__).resolve()
    for parent in (start.parent, *start.parents):
        for rel in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            path = parent / rel
            if path.is_file():
                return path
    raise FileNotFoundError("canonical puzzles.jsonl not found")


def _norm_grid(grid):
    rows = []
    for row in grid:
        if isinstance(row, str):
            row = [int(ch) for ch in row]
        rows.append(list(row))
    return rows


def canonical_pairs():
    result = []
    for line in _canonical_path().open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            pairs = row.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for pair in pairs:
                result.append({"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])})
    return result


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 1 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(cells)
    return found


def selected_component(grid, *, reverse_ties=False, first=False):
    comps = components(grid)
    if first:
        return min(comps, key=lambda cells: min(cells))
    if reverse_ties:
        return sorted(comps, key=lambda cells: (-len(cells), -min(r for r, _ in cells), -min(c for _, c in cells)))[0]
    return sorted(comps, key=lambda cells: (-len(cells), min(r for r, _ in cells), min(c for _, c in cells)))[0]


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def transform(template, code):
    if code == 2:
        return [row[:] for row in template]
    if code == 3:
        return rotate_cw(template)
    if code == 4:
        return rotate_180(template)
    if code == 5:
        return rotate_ccw(template)
    raise ValueError(code)


def crop_for_component(grid, comp, *, component_cells_only=False):
    r1 = min(r for r, _ in comp)
    r2 = max(r for r, _ in comp)
    c1 = min(c for _, c in comp)
    c2 = max(c for _, c in comp)
    selected = set(comp)
    return [
        [grid[r][c] if (not component_cells_only or (r, c) in selected) else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def pack(copies, *, gap=1):
    height = max(len(piece) for piece in copies)
    width = sum(len(piece[0]) for piece in copies) + gap * (len(copies) - 1)
    out = [[0] * width for _ in range(height)]
    left = 0
    for piece in copies:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(piece[0]) + gap
    return out


def oracle_output(grid, *, selector="canonical", commands=None, component_cells_only=False, gap=1, monochrome=False):
    codes = [value for value in grid[0] if value in COMMANDS]
    if commands is not None:
        codes = commands(codes)
    if selector == "first":
        comp = selected_component(grid, first=True)
    elif selector == "reverse_ties":
        comp = selected_component(grid, reverse_ties=True)
    else:
        comp = selected_component(grid)
    template = crop_for_component(grid, comp, component_cells_only=component_cells_only)
    if monochrome:
        color = grid[min(comp)[0]][min(comp)[1]]
        template = [[color if value else 0 for value in row] for row in template]
    return pack([transform(template, code) for code in codes], gap=gap)


def observed(grid):
    comp = selected_component(grid)
    return {
        "n_commands": sum(value in COMMANDS for value in grid[0]),
        "shape_size": len(comp),
        "n_distractors": len(components(grid)) - 1,
        "shape_color": grid[min(comp)[0]][min(comp)[1]],
    }


def profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def semantic_counterexample():
    # Four commands, a small first object, an 8-cell selected object with an
    # isolated interior cargo cell, and an equally large later object.
    g = [[0] * 12 for _ in range(8)]
    for col, code in zip((0, 3, 6, 9), (5, 2, 4, 3)):
        g[0][col] = code
    g[2][0] = 5
    shape = [(3, 1), (3, 2), (4, 1), (5, 1), (6, 1), (6, 2), (6, 3), (6, 4)]
    for i, (r, c) in enumerate(shape):
        g[r][c] = 2 if i % 2 == 0 else 3
    g[4][3] = 4  # disconnected cargo inside the selected bbox
    rival = [(3, 7), (3, 8), (3, 9), (4, 7), (5, 7), (6, 7), (6, 8), (6, 9)]
    for r, c in rival:
        g[r][c] = 2
    return g
