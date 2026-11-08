"""Independent oracle and curriculum probes for task f705b8f51e62.

The selected Racket rule remains label authority.  This module independently
reconstructs the component/shape semantics for task-local regression tests and
future reviewer probes; it deliberately does not import helpers from generator.py.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Sequence

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "f705b8f51e62"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path=None):
    root = find_root(__file__)
    source = Path(path or root / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_f705b8f51e62", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def components(grid: Sequence[Sequence[int]]):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = int(grid[row][col])
            if color == 0 or (row, col) in seen:
                continue
            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and int(grid[point[0]][point[1]]) == color
                    ):
                        seen.add(point)
                        todo.append(point)
            result.append((color, tuple(sorted(cells))))
    return result


def normalized(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _shape_grid(shape, color):
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    out = [[0] * width for _ in range(height)]
    for row, col in shape:
        out[row][col] = int(color)
    return out


def _entries(grid):
    entries = []
    for color, cells in components(grid):
        entries.append({
            "color": color,
            "cells": cells,
            "shape": normalized(cells),
            "bbox": (
                min(r for r, _ in cells),
                min(c for _, c in cells),
                max(r for r, _ in cells),
                max(c for _, c in cells),
            ),
        })
    return entries


def intended_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    entries = _entries(grid)
    if not entries:
        raise ValueError("no nonzero component")
    canonical_entry = sorted(entries, key=lambda item: (-len(item["shape"]), item["bbox"]))[0]
    canonical = canonical_entry["shape"]
    defective = [
        item for item in entries
        if item["shape"] != canonical and item["shape"] < canonical
    ]
    chosen = defective[0] if defective else min(entries, key=lambda item: len(item["shape"]))
    return _shape_grid(canonical, chosen["color"])


def largest_component_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    entries = _entries(grid)
    chosen = sorted(entries, key=lambda item: (-len(item["shape"]), item["bbox"]))[0]
    return _shape_grid(chosen["shape"], chosen["color"])


def signature(grid: Sequence[Sequence[int]]) -> dict[str, object]:
    entries = _entries(grid)
    sizes = [len(item["shape"]) for item in entries]
    largest = max(sizes)
    fulls = [item for item in entries if len(item["shape"]) == largest]
    defectives = [item for item in entries if len(item["shape"]) < largest]
    profile = None
    if len(defectives) == 1 and len({item["color"] for item in fulls}) == 1:
        profile = "canonical" if defectives[0]["color"] == fulls[0]["color"] else "contrast"
    return {
        "profile": profile,
        "template_size": largest,
        "n_canon": len(fulls),
        "missing": largest - len(defectives[0]["shape"]) if len(defectives) == 1 else None,
        "component_count": len(entries),
        "full_color": fulls[0]["color"] if fulls else None,
        "defective_color": defectives[0]["color"] if len(defectives) == 1 else None,
        "output_shape": tuple(tuple(row) for row in intended_output(grid)),
    }


def pair(grid: Sequence[Sequence[int]]) -> dict[str, list[list[int]]]:
    copied = deepcopy([list(row) for row in grid])
    return {"input": copied, "output": intended_output(copied)}


def canonical_shortcut_fits() -> bool:
    return all(
        largest_component_rival(item["input"]) == item["output"]
        for item in canonical_pairs()
    )
