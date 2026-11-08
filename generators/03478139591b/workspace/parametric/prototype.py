"""Parametric complement family for 03478139591b.

The canonical setting preserves the selected ARC program byte-for-byte.  The
sequential setting first performs that complement/recolor operation, then finds
the largest connected region in the resulting grid and marks its boundary with
the original foreground color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "03478139591b"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"finish": "canonical"},
    {"finish": "mark_largest_boundary"},
)
DEMO_SHAPES = ((9, 13), (13, 9), (11, 17), (17, 11), (15, 19), (19, 15))
QUERY_SHAPES = ((7, 11), (16, 20), (23, 29), (30, 30))
_MAP = {3: 1, 5: 4, 8: 2}


def _integer(value, label, low=None, high=None):
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    if low is not None and value < low or high is not None and value > high:
        raise ValueError(f"{label} must be in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in {row["finish"] for row in SETTINGS}:
        raise ValueError("finish must be canonical or mark_largest_boundary")
    return value


def _grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    colors = {cell for row in grid for cell in row}
    foreground = colors - {0}
    if 0 not in colors or len(foreground) != 1 or next(iter(foreground), None) not in _MAP:
        raise ValueError("grid must contain 0 and exactly one foreground color from 3,5,8")
    return deepcopy(grid)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def program(settings):
    name = "canonical.rkt" if _setting(settings) == "canonical" else "sequential.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _foreground_color(grid):
    return next(cell for row in grid for cell in row if cell != 0)


def _intermediate(grid):
    source = _grid(grid)
    color = _foreground_color(source)
    mapped = _MAP[color]
    return [[0 if value != 0 else mapped for value in row] for row in source]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def _boundary(cells):
    cell_set = set(cells)
    return sorted(
        (r, c)
        for r, c in cells
        if any((r + dr, c + dc) not in cell_set for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    )


def stage_summary(grid):
    source = _grid(grid)
    intermediate = _intermediate(source)
    components = _components(intermediate)
    if not components:
        raise ValueError("intermediate must contain at least one nonzero component")
    largest = max(components, key=len)  # stable: row-major component order wins ties
    return {
        "intermediate": intermediate,
        "component_count": len(components),
        "largest_size": len(largest),
        "largest_anchor": list(min(largest)),
        "largest_boundary": [list(cell) for cell in _boundary(largest)],
    }


def transform(grid, settings):
    mode = _setting(settings)
    source = _grid(grid)
    intermediate = _intermediate(source)
    if mode == "canonical":
        return intermediate
    color = _foreground_color(source)
    result = deepcopy(intermediate)
    for r, c in stage_summary(source)["largest_boundary"]:
        result[r][c] = color
    return result


def _rng(seed, stream, index):
    payload = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _paint_frame(grid, top, left, bottom, right, color):
    if bottom - top < 2 or right - left < 2:
        return
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


def sample_input(seed, stream, index, height, width):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 7, 30)
    _integer(width, "width", 7, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be nonempty text")
    rng = _rng(seed, stream, index)
    color = (3, 5, 8)[rng.randrange(3)]
    grid = [[0] * width for _ in range(height)]
    role = index % 3
    if role in (0, 2):
        wall_c = max(2, min(width - 3, width // 3 + rng.choice((-1, 0, 1))))
        for r in range(height):
            grid[r][wall_c] = color
    if role in (1, 2):
        wall_r = max(2, min(height - 3, (2 * height) // 3 + rng.choice((-1, 0, 1))))
        for c in range(width):
            grid[wall_r][c] = color

    # An enclosed region and distributed islands make the second stage depend
    # on actual component geometry rather than a fixed side of one wall.
    box_h = max(3, min(height - 2, height // 3))
    box_w = max(3, min(width - 2, width // 3))
    top = 1 if role != 1 else max(1, height - box_h - 1)
    left = max(1, width - box_w - 1) if role == 0 else 1
    _paint_frame(grid, top, left, top + box_h - 1, left + box_w - 1, color)

    for r in range(2, height - 1, 5):
        for c in range(2, width - 1, 7):
            for rr in (r, min(r + 1, height - 1)):
                for cc in (c, min(c + 1, width - 1)):
                    grid[rr][cc] = color

    # Seed-dependent asymmetric cues defeat row/column-only fixed templates.
    for _ in range(max(1, (height * width) // 180)):
        r = rng.randrange(1, height - 1)
        c = rng.randrange(1, width - 1)
        grid[r][c] = color

    if all(value != 0 for row in grid for value in row):
        grid[-1][-1] = 0
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "prototype": True,
    }
    seen = set()
    for split, shapes in (("train", DEMO_SHAPES[:demos]), ("test", QUERY_SHAPES[:queries])):
        for index, (height, width) in enumerate(shapes):
            grid = sample_input(seed, split, index, height, width)
            key = digest(grid)
            if key in seen:
                raise ValueError("episode inputs must be distinct")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
