"""Independent authoring probes for task 6145142974ff.

This module intentionally does not import implementation helpers from generator.py.
It gives reviewers a small oracle, component census, canonical-pair loader, and
portable generator loader for regression tests and future audits.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

TASK_ID = "6145142974ff"
TASK_ROOT = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    target = Path(path) if path else TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    try:
        from reviewer_support import canonical_pairs as shared_pairs, find_root

        return shared_pairs(TASK_ID, root=find_root(__file__))
    except (ImportError, FileNotFoundError, ValueError):
        root = TASK_ROOT
        while root != root.parent and not (root / "shared/data/canonical/puzzles.jsonl").exists():
            root = root.parent
        path = root / "shared/data/canonical/puzzles.jsonl"
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row.get("train", []), *row.get("test", [])]
        raise KeyError(TASK_ID)


def components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
        result.append(sorted(component))
    return sorted(result, key=lambda cells: cells[0])


def normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def marker_counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value not in (0, 1, 3))


def majority_color(grid: list[list[int]]) -> int:
    counts = marker_counts(grid)
    if not counts:
        raise ValueError("no marker colors")
    return max(counts, key=lambda color: (counts[color], color))


def oracle(grid: list[list[int]]) -> list[list[int]]:
    template_components = components(grid, 1)
    if not template_components:
        raise ValueError("missing color-1 template")
    target = normalized(template_components[0])
    selected = majority_color(grid)
    out = [[0 for _ in row] for row in grid]
    for component in components(grid, 3):
        if normalized(component) == target:
            for r, c in component:
                out[r][c] = selected
    return out


def recolor_all_green_rival(grid: list[list[int]]) -> list[list[int]]:
    selected = majority_color(grid)
    return [[selected if value == 3 else 0 for value in row] for row in grid]


def same_cell_count_rival(grid: list[list[int]]) -> list[list[int]]:
    template_components = components(grid, 1)
    size = len(template_components[0])
    selected = majority_color(grid)
    out = [[0 for _ in row] for row in grid]
    for component in components(grid, 3):
        if len(component) == size:
            for r, c in component:
                out[r][c] = selected
    return out


def largest_marker_color_rival(grid: list[list[int]]) -> list[list[int]]:
    colors = marker_counts(grid)
    if not colors:
        raise ValueError("no marker colors")
    selected = max(colors)
    target = normalized(components(grid, 1)[0])
    out = [[0 for _ in row] for row in grid]
    for component in components(grid, 3):
        if normalized(component) == target:
            for r, c in component:
                out[r][c] = selected
    return out


def first_match_only_rival(grid: list[list[int]]) -> list[list[int]]:
    target = normalized(components(grid, 1)[0])
    selected = majority_color(grid)
    out = [[0 for _ in row] for row in grid]
    for component in components(grid, 3):
        if normalized(component) == target:
            for r, c in component:
                out[r][c] = selected
            break
    return out
