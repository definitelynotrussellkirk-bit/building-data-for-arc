"""Matched-input object-packing episodes with an episode-fixed transform.

Objects are always read by increasing left edge and packed vertically.  The
private setting chooses the geometric operation applied to every object crop:
canonical transpose or clockwise rotation.  Identical inputs are used for both
settings, and every retained shape makes the two rules disagree.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "d4be41674012"
SETTINGS = ({"transform": "transpose"}, {"transform": "rotate_cw"})

_SHAPES = (
    ((1, 1), (0, 1)),
    ((1, 0), (1, 1)),
    ((0, 1), (1, 1)),
    ((1, 1), (1, 0)),
    ((1, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (1, 1, 0)),
    ((1, 1, 1), (1, 0, 0)),
    ((1, 0), (1, 0), (1, 1)),
    ((1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 1, 1, 0), (0, 0, 1, 1)),
    ((1, 0), (1, 0), (1, 1), (0, 1)),
)

# h, w, shape indices, target row fractions.  Queries deliberately increase
# object count and spatial spread; the final scene fills a genuine 30x30 canvas.
_DEMOS = (
    (9, 12, (0, 1, 2), (0.05, 0.75, 0.40)),
    (11, 15, (3, 4, 7), (0.70, 0.10, 0.50)),
    (14, 18, (5, 0, 8, 2), (0.05, 0.72, 0.35, 0.55)),
    (17, 21, (6, 9, 1, 10), (0.65, 0.05, 0.80, 0.30)),
    (21, 24, (11, 4, 2, 8, 0), (0.05, 0.80, 0.40, 0.65, 0.20)),
    (24, 27, (9, 6, 11, 3, 5), (0.75, 0.05, 0.45, 0.85, 0.20)),
)
_QUERIES = (
    (10, 14, (2, 5, 1), (0.65, 0.05, 0.40)),
    (16, 20, (7, 0, 9, 4), (0.05, 0.78, 0.35, 0.58)),
    (23, 27, (10, 3, 8, 6, 1), (0.80, 0.05, 0.48, 0.68, 0.22)),
    (30, 30, (11, 8, 10, 9, 6), (0.02, 0.90, 0.45, 0.18, 0.72)),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"transform"}
        or type(settings["transform"]) is not str
        or settings["transform"] not in ("transpose", "rotate_cw")
    ):
        raise ValueError("settings must be exactly {'transform': 'transpose'|'rotate_cw'}")
    return settings["transform"]


def program(settings):
    transform = _setting(settings)
    return (HERE / ("canonical.rkt" if transform == "transpose" else "rotate_cw.rkt")).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _transpose(grid):
    return [list(row) for row in zip(*grid, strict=True)]


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1], strict=True)]


def _components4(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        objects.append({
            "c1": c1,
            "r1": r1,
            "crop": [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]],
        })
    return sorted(objects, key=lambda obj: (obj["c1"], obj["r1"]))


def _pack(pieces):
    height = sum(len(piece) for piece in pieces) + len(pieces) - 1
    width = max(len(piece[0]) for piece in pieces)
    output = [[0] * width for _ in range(height)]
    row0 = 0
    for piece in pieces:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value:
                    output[row0 + row][col] = value
        row0 += len(piece) + 1
    return output


def _gap_layout(width, widths, rng):
    minimum = sum(widths) + len(widths) - 1
    if minimum > width:
        raise ValueError("shape set does not fit profile width")
    # Keep one blank column between objects and reserve outer margins when able.
    extras = width - minimum
    left = 1 if extras >= 2 else 0
    right = 1 if extras >= 2 else 0
    extras -= left + right
    gaps = [1] * (len(widths) - 1)
    for index in range(extras):
        gaps[index % len(gaps)] += 1
    # Seed only chooses which gaps receive the earliest extra cells.
    if gaps:
        shift = rng.randrange(len(gaps))
        gaps = gaps[shift:] + gaps[:shift]
    starts = []
    col = left
    for index, shape_width in enumerate(widths):
        starts.append(col)
        col += shape_width
        if index < len(gaps):
            col += gaps[index]
    return starts


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    specs = _DEMOS if split == "train" else _QUERIES
    _integer(index, 0, len(specs) - 1, "index")
    height, width, shape_indices, row_fractions = specs[index]
    rng = _rng(seed, split, index)
    shapes = [_SHAPES[shape_index] for shape_index in shape_indices]
    starts = _gap_layout(width, [len(shape[0]) for shape in shapes], rng)
    colors = rng.sample(range(1, 10), len(shapes))
    grid = [[0] * width for _ in range(height)]
    for shape, col0, fraction, color in zip(shapes, starts, row_fractions, colors, strict=True):
        available = height - len(shape)
        row0 = min(available, max(0, round(fraction * available)))
        for dr, row in enumerate(shape):
            for dc, occupied in enumerate(row):
                if occupied:
                    grid[row0 + dr][col0 + dc] = color
    objects = _components4(grid)
    if len(objects) != len(shapes):
        raise ValueError("object placement changed component count")
    for obj in objects:
        if _transpose(obj["crop"]) == _rotate_clockwise(obj["crop"]):
            raise ValueError("retained object does not distinguish transforms")
    return grid


def claimed_output(grid, settings):
    transform = _setting(settings)
    objects = _components4(grid)
    if not 3 <= len(objects) <= 5:
        raise ValueError("scene must contain 3..5 objects")
    operation = _transpose if transform == "transpose" else _rotate_clockwise
    return _pack([operation(obj["crop"]) for obj in objects])


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, index, split=split)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            canonical = claimed_output(grid, SETTINGS[0])
            alternate = claimed_output(grid, SETTINGS[1])
            if canonical == alternate:
                raise ValueError("sample does not distinguish transforms")
            result[split].append({"input": grid, "output": claimed_output(grid, settings)})
    result["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return result
