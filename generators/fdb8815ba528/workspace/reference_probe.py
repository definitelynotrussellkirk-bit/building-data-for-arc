"""Independent probes for fdb8815ba528.

This module deliberately does not import production helper functions except when
``load_generator`` is requested.  It gives future reviewers a small component
oracle, canonical loader, axis observer, and lesson-rival census.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "fdb8815ba528"
PROFILE_DIMS = {
    "canonical_8x9": (8, 9),
    "canonical_7x8": (7, 8),
    "canonical_9x9": (9, 9),
    "canonical_8x10": (8, 10),
}
DIMS_PROFILE = {dims: name for name, dims in PROFILE_DIMS.items()}


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def load_generator(path: str | None = None):
    target = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or Path(__file__).parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location("generator_under_test", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]], *, diagonal: bool = False, ignore_color: bool = False):
    h, w = len(grid), len(grid[0])
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen: set[tuple[int, int]] = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while q:
                rr, cc = q.popleft()
                cells.add((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    if grid[nr][nc] == 0:
                        continue
                    if not ignore_color and grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    q.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            out.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return out


def bbox_border(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = bbox
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def oracle(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for component in components(grid):
        for r, c in bbox_border(component["bbox"]):
            out[r][c] = component["color"]
    return out


def observe(grid: list[list[int]]) -> dict[str, Any]:
    found = components(grid)
    counts = Counter(component["color"] for component in found)
    colors = set(counts)
    if len(counts) == len(found):
        relation = "distinct"
    elif len(counts) == len(found) - 1 and sorted(counts.values()).count(2) == 1:
        relation = "one_repeat"
    else:
        relation = "other"
    if colors and all(1 <= color <= 4 for color in colors):
        palette_kind = "low"
    elif colors and all(6 <= color <= 9 for color in colors):
        palette_kind = "high"
    else:
        palette_kind = "mixed"
    h, w = len(grid), len(grid[0])
    touching = any(
        r in (0, h - 1) or c in (0, w - 1)
        for component in found
        for r, c in component["cells"]
    )
    return {
        "scene_profile": DIMS_PROFILE.get((h, w)),
        "n_blobs": len(found),
        "color_relation": relation,
        "edge_mode": "touching" if touching else "interior",
        "palette_kind": palette_kind,
    }


def rival_one_bbox_per_color(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    grouped: dict[int, set[tuple[int, int]]] = {}
    for component in components(grid):
        grouped.setdefault(component["color"], set()).update(component["cells"])
    for color, cells in grouped.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        for r, c in bbox_border((min(rows), min(cols), max(rows), max(cols))):
            out[r][c] = color
    return out


def rival_solid_bbox(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for component in components(grid):
        r0, c0, r1, c1 = component["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = component["color"]
    return out


def rival_preserve_source(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for component in components(grid):
        for r, c in bbox_border(component["bbox"]):
            out[r][c] = component["color"]
    return out


def rival_same_color_8_connected(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for component in components(grid, diagonal=True):
        for r, c in bbox_border(component["bbox"]):
            out[r][c] = component["color"]
    return out


def rival_color_blind_4_connected(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for component in components(grid, ignore_color=True):
        for r, c in bbox_border(component["bbox"]):
            out[r][c] = component["color"]
    return out


RIVALS = {
    "solid_bbox": rival_solid_bbox,
    "preserve_source": rival_preserve_source,
    "one_bbox_per_color": rival_one_bbox_per_color,
    "same_color_8_connected": rival_same_color_8_connected,
    "color_blind_4_connected": rival_color_blind_4_connected,
}
