"""Independent review helpers for efb59efe0080 (Normalized XOR).

This module deliberately re-implements the geometry from visible/canonical task
text instead of importing production helpers.  It is test tooling, not label
authority.  ``GENERATOR_UNDER_TEST`` can point the suite at a retained source
file for red/green replay.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK = "efb59efe0080"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py").resolve()
    runtime = ROOT / "shared" / "runtime"
    if runtime.exists() and str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("reviewed_efb59efe0080", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_grid(value):
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return deepcopy(value)


def canonical_row() -> dict:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    if not path.exists():
        # Portable task-test runtimes expose this public helper at their root.
        from reviewer_support import canonical_pairs as portable_pairs
        pairs = portable_pairs(TASK)
        return {"train": pairs[:-1], "test": pairs[-1]}
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {"input": _normalize_grid(pair["input"]), "output": _normalize_grid(pair["output"])}
        for pair in [*row["train"], *tests]
    ]


def cells(grid, color: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = set(points)
    if not points:
        raise ValueError("cannot normalize an empty point set")
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return frozenset((r - r0, c - c0) for r, c in points)


def dimensions(points: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = set(points)
    return max(r for r, _ in points) + 1, max(c for _, c in points) + 1


def _grid_from_cells(points: set[tuple[int, int]], color: int = 8) -> list[list[int]]:
    if not points:
        raise ValueError("empty output")
    h, w = dimensions(points)
    grid = [[0] * w for _ in range(h)]
    for r, c in points:
        grid[r][c] = color
    return grid


def crop_cells(points: set[tuple[int, int]]) -> set[tuple[int, int]]:
    if not points:
        raise ValueError("empty crop")
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return {(r - r0, c - c0) for r, c in points}


def masks(grid) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    return normalize(cells(grid, 2)), normalize(cells(grid, 3))


def raw_xor_cells(grid) -> tuple[set[tuple[int, int]], tuple[int, int]]:
    a, b = masks(grid)
    h = max(dimensions(a)[0], dimensions(b)[0])
    w = max(dimensions(a)[1], dimensions(b)[1])
    return set(a ^ b), (h, w)


def normalized_xor(grid) -> list[list[int]]:
    points, _ = raw_xor_cells(grid)
    return _grid_from_cells(crop_cells(points))


def uncropped_xor(grid) -> list[list[int]]:
    points, (h, w) = raw_xor_cells(grid)
    out = [[0] * w for _ in range(h)]
    for r, c in points:
        out[r][c] = 8
    return out


def normalized_union(grid) -> list[list[int]]:
    a, b = masks(grid)
    return _grid_from_cells(crop_cells(set(a | b)))


def filled_bbox_xor(grid) -> list[list[int]]:
    a, b = masks(grid)
    ah, aw = dimensions(a)
    bh, bw = dimensions(b)
    aa = {(r, c) for r in range(ah) for c in range(aw)}
    bb = {(r, c) for r in range(bh) for c in range(bw)}
    points = aa ^ bb
    return _grid_from_cells(crop_cells(points)) if points else [[0]]


def red_mask_only(grid) -> list[list[int]]:
    a, _ = masks(grid)
    return _grid_from_cells(set(a))


def absolute_position_xor(grid) -> list[list[int]]:
    # The physical objects cannot overlap in one ARC cell, so a mistaken
    # absolute-coordinate XOR is their recolored union cropped in-place.
    return _grid_from_cells(crop_cells(cells(grid, 2) | cells(grid, 3)))


def observed(grid) -> dict[str, int | str]:
    h, w = len(grid), len(grid[0])
    return {
        "canvas_profile": f"{h}x{w}",
        "size_2": len(cells(grid, 2)),
        "size_3": len(cells(grid, 3)),
    }


def crop_required(grid) -> bool:
    return normalized_xor(grid) != uncropped_xor(grid)


def connected(points: set[tuple[int, int]]) -> bool:
    if not points:
        return False
    seen = {next(iter(points))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (r + dr, c + dc)
            if q in points and q not in seen:
                seen.add(q)
                stack.append(q)
    return seen == points
