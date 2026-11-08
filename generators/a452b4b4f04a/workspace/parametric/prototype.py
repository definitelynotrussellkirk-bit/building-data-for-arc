"""Proposed episode-fixed rectangle render variants.

The input grammar stays the canonical corner-marker task.  The private setting
chooses whether each color-specific bounding box is rendered as the canonical
outline or as a filled rectangle.  Python outputs are claims until the protected
Racket worker executes every label.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "a452b4b4f04a"
SETTINGS = ({"render": "outline"}, {"render": "filled"})

# height, width, number of rectangles, corner-marker count
_DEMO_PROFILES = (
    (8, 8, 1, 3),
    (9, 12, 2, 2),
    (12, 9, 2, 4),
    (14, 18, 3, 3),
    (18, 20, 3, 2),
    (20, 16, 2, 4),
)
_QUERY_PROFILES = (
    (6, 6, 1, 2),
    (16, 21, 2, 3),
    (24, 29, 3, 4),
    (30, 30, 3, 3),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"render"}
            or type(settings["render"]) is not str
            or settings["render"] not in {"outline", "filled"}):
        raise ValueError("settings must be exactly {'render': 'outline'|'filled'}")
    return settings["render"]


def program(settings):
    render = _setting(settings)
    return (HERE / ("canonical.rkt" if render == "outline" else "filled.rkt")).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _rectangles(height, width, count, rng):
    """Return disjoint, nondegenerate bboxes with broad canvas coverage."""
    if count == 1:
        # Alternate between an interior and a boundary-touching rectangle.
        if rng.randrange(2):
            return [(0, 0, height - 2, width - 2)]
        return [(1, 1, height - 1, width - 1)]
    if count == 2:
        if width >= height:
            gap = 1
            mid = width // 2
            left = (0, 0, height - 2, max(2, mid - gap - 1))
            right = (1, min(width - 3, mid + gap), height - 1, width - 1)
            return [left, right]
        gap = 1
        mid = height // 2
        top = (0, 1, max(2, mid - gap - 1), width - 1)
        bottom = (min(height - 3, mid + gap), 0, height - 1, width - 2)
        return [top, bottom]

    # Two separated upper boxes and a lower box spanning both lower quadrants.
    split_row = height // 2
    split_col = width // 2
    top_bottom = max(2, split_row - 2)
    lower_top = min(height - 3, split_row + 1)
    left = (0, 0, top_bottom, max(2, split_col - 2))
    right = (1, min(width - 3, split_col + 1), top_bottom + 1, width - 1)
    lower = (lower_top, max(0, width // 6), height - 1, min(width - 1, width - 1 - width // 6))
    boxes = [left, right, lower]
    for r0, c0, r1, c1 in boxes:
        if r1 - r0 < 2 or c1 - c0 < 2:
            raise ValueError("profile cannot fit three nondegenerate rectangles")
    return boxes


def _selected_corners(box, count, rng):
    r0, c0, r1, c1 = box
    corners = [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]
    if count == 2:
        return corners[::3] if rng.randrange(2) == 0 else corners[1:3]
    if count == 3:
        omitted = rng.randrange(4)
        return [cell for i, cell in enumerate(corners) if i != omitted]
    return corners


def sample_input(seed, split, index):
    """Deterministic, prefix-stable input independent of the private setting."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    height, width, count, marker_count = profiles[index]
    rng = _rng(seed, split, index)
    boxes = _rectangles(height, width, count, rng)
    colors = rng.sample(range(1, 10), count)
    grid = [[0] * width for _ in range(height)]
    for color, box in zip(colors, boxes):
        for row, col in _selected_corners(box, marker_count, rng):
            grid[row][col] = color
    return grid


def _objects(grid):
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or len(grid) > 30 or len(grid[0]) > 30):
        raise ValueError("grid must be a nonempty rectangle no larger than 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must contain exact ARC integers 0..9")
    by_color = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                by_color.setdefault(color, []).append((row, col))
    if not by_color:
        raise ValueError("at least one colored corner marker is required")
    objects = []
    for color, cells in sorted(by_color.items()):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
        corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
        if not 2 <= len(cells) <= 4 or not set(cells) <= corners or r1 - r0 < 2 or c1 - c0 < 2:
            raise ValueError(f"color {color} is not a lawful 2..4-corner rectangle marker")
        objects.append((color, r0, c0, r1, c1))
    for i, (_, ar0, ac0, ar1, ac1) in enumerate(objects):
        for _, br0, bc0, br1, bc1 in objects[i + 1:]:
            if not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0):
                raise ValueError("color bounding boxes must be area-disjoint")
    return objects


def transform(grid, settings):
    render = _setting(settings)
    objects = _objects(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for color, r0, c0, r1, c1 in objects:
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if render == "filled" or row in {r0, r1} or col in {c0, c1}:
                    output[row][col] = color
    return output


def generate(seed, settings, demos=3, queries=4):
    """Generate 2..6 demonstrations and 1..4 distinct queries independently."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "program_solution": program(settings),
        "train": [],
        "test": [],
    }
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate generated input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
