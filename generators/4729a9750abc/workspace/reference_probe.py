"""Independent reviewer oracle and structural probes for 4729a9750abc.

This module is test-only.  It deliberately does not import implementation
helpers from generator.py, so task tests can catch parser and rule regressions.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "4729a9750abc"


def load_generator(path: str | None = None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_4729_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _components(grid, *, background: int = 0, color: int | None = None):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if (r, c) in seen or value == background or (color is not None and value != color):
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    if grid[nr][nc] == value and (color is None or value == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": value, "cells": tuple(sorted(cells))})
    return result


def _bbox(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_frame(component) -> bool:
    r1, c1, r2, c2 = _bbox(component["cells"])
    height, width = r2 - r1 + 1, c2 - c1 + 1
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return height >= 3 and width >= 3 and set(component["cells"]) == border


def frames(grid):
    found = []
    for component in _components(grid, color=9):
        if _is_frame(component):
            found.append((*_bbox(component["cells"]),))
    return sorted(found, key=lambda box: (box[0], box[1]))


def _first_key(values):
    return next(value for value in values if value not in (0, 9))


def frame_keys(grid, frame):
    r1, c1, r2, c2 = frame
    select = _first_key(grid[r1 - 1][c1 : c2 + 1])
    transform = _first_key(grid[r][c1 - 1] for r in range(r1, r2 + 1))
    return select, transform


def frame_components(grid, frame):
    r1, c1, r2, c2 = frame
    sub = [row[c1 + 1 : c2] for row in grid[r1 + 1 : r2]]
    return _components(sub)


def _crop_component(component):
    color = component["color"]
    r1, c1, r2, c2 = _bbox(component["cells"])
    out = [[0] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]
    for r, c in component["cells"]:
        out[r - r1][c - c1] = color
    return out


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _transform(piece, key):
    if key == 4:
        return _rotate_cw(piece)
    if key == 5:
        return [row[::-1] for row in piece]
    if key == 6:
        return _rotate_180(piece)
    return [row[:] for row in piece]


def oracle_output(grid, *, frame_limit=None, selection=None, apply_transform=True):
    pieces = []
    chosen_frames = frames(grid)
    if frame_limit is not None:
        chosen_frames = chosen_frames[:frame_limit]
    for frame in chosen_frames:
        select_key, transform_key = frame_keys(grid, frame)
        components = sorted(frame_components(grid, frame), key=lambda obj: len(obj["cells"]))
        effective = select_key if selection is None else selection
        chosen = components[0] if effective == 2 else components[-1]
        piece = _crop_component(chosen)
        if apply_transform:
            piece = _transform(piece, transform_key)
        pieces.append(piece)
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            out[top + r][left : left + len(row)] = row
        left += len(piece[0]) + 1
    return out


def observed_axes(grid):
    found = frames(grid)
    heights = {r2 - r1 + 1 for r1, _, r2, _ in found}
    widths = {c2 - c1 + 1 for _, c1, _, c2 in found}
    component_counts = {len(frame_components(grid, frame)) for frame in found}
    if len(heights) != 1 or len(widths) != 1 or len(component_counts) != 1:
        raise ValueError("generated frames do not share exact axis values")
    return {
        "n_frames": len(found),
        "frame_h": next(iter(heights)),
        "frame_w": next(iter(widths)),
        "n_components": next(iter(component_counts)),
    }
