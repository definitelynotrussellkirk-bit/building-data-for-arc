"""Independent geometry oracle and portable loader for task 43cca8eff94f tests."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path

TASK_ID = "43cca8eff94f"
DIRECTION_SCHEDULE = ("right", "left", "down", "up", "up")
CANONICAL_PROFILES = {(9, 11, (0, 2, 8)), (10, 10, (0, 2, 8)), (9, 12, (0, 2, 8))}


def load_generator(path=None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid, color):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    groups = []
    while cells:
        start = min(cells)
        cells.remove(start)
        queue = deque([start])
        group = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in cells:
                    cells.remove(nxt)
                    group.add(nxt)
                    queue.append(nxt)
        groups.append(group)
    return groups


def bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def expected_border(box):
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def direction_and_gap(obj_box, frame_box):
    or1, oc1, or2, oc2 = obj_box
    fr1, fc1, fr2, fc2 = frame_box
    if oc2 < fc1:
        return "right", fc1 - oc2 - 1
    if oc1 > fc2:
        return "left", oc1 - fc2 - 1
    if or2 < fr1:
        return "down", fr1 - or2 - 1
    if or1 > fr2:
        return "up", or1 - fr2 - 1
    raise ValueError("object is not entirely on one side of frame")


def analyze(grid):
    frames = components(grid, 8)
    objects = components(grid, 2)
    if len(frames) != 1 or len(objects) != 1:
        raise ValueError("expected one connected frame and object")
    frame, obj = frames[0], objects[0]
    frame_box, obj_box = bbox(frame), bbox(obj)
    direction, gap = direction_and_gap(obj_box, frame_box)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "direction": direction,
        "gap": gap,
        "obj_size": len(obj),
        "object_cells": obj,
        "object_box": obj_box,
        "frame_cells": frame,
        "frame_box": frame_box,
        "frame_is_hollow_rectangle": frame == expected_border(frame_box),
        "profile": (len(grid), len(grid[0]), tuple(sorted({v for row in grid for v in row}))),
    }


def slide_rule(grid):
    """Independent Python translation of the pinned Racket authority."""
    out = deepcopy(grid)
    stats = analyze(grid)
    cells = set(stats["object_cells"])
    dr, dc = {
        "right": (0, 1),
        "left": (0, -1),
        "down": (1, 0),
        "up": (-1, 0),
    }[stats["direction"]]
    blockers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2)
    }
    height, width = len(grid), len(grid[0])
    while True:
        nxt = {(r + dr, c + dc) for r, c in cells}
        if not all(0 <= r < height and 0 <= c < width for r, c in nxt):
            break
        if nxt & blockers:
            break
        cells = nxt
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 2:
                out[r][c] = 0
    for r, c in cells:
        out[r][c] = 2
    return out


def no_up_rival(grid):
    return deepcopy(grid) if analyze(grid)["direction"] == "up" else slide_rule(grid)
