"""Opt-in exact-line family with an input-derived marker-size selector.

The production generator and canonical authority are not modified.  Python
outputs are checked by native protected Racket before any qualification claim.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import random


TASK_ID = "7bba59d92716"
VERSION = "marker-size-1"
MODES = ("fixed_five", "marker_size")
DEMO_SHAPES = ((14, 21), (17, 24), (21, 27), (24, 30), (28, 27), (30, 30))
QUERY_SHAPES = ((14, 24), (21, 27), (30, 30), (29, 30))
DEMO_MARKERS = (3, 7, 5, 7, 3, 5)
QUERY_MARKERS = (5, 3, 7, 5)


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"length_rule"}:
        raise ValueError("settings must contain exactly length_rule")
    value = settings["length_rule"]
    if type(value) is not str or value not in MODES:
        raise ValueError("length_rule must be fixed_five or marker_size")
    return value


def program(settings):
    """Return one complete rule!, with exact canonical bytes at the default."""
    if _mode(settings) == "fixed_five":
        return Path(__file__).with_name("canonical.rkt").read_text()
    return """(rule!
  (lambda (g)
    (let* ([markers (filter (lambda (o) (= (obj-color o) 6)) (objects g 0))]
           [k (obj-size (first markers))])
      (for/fold ([out g])
                ([obj (filter (lambda (o)
                                (and (= (obj-color o) 1)
                                     (= (obj-c1 o) (obj-c2 o))
                                     (= (obj-size o) k)))
                              (objects g 0))])
        (set-cell out (quotient (+ (obj-r1 obj) (obj-r2 obj)) 2)
                      (obj-c1 obj) 2)))))"""


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a list with 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular lists")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be integer ARC colors, not bool")
    return grid


def components(grid, color):
    """Independent strict-grid, four-neighbor connected-component analysis."""
    _grid(grid)
    height, width = len(grid), len(grid[0])
    visited, result = set(), []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != color or (r, c) in visited:
                continue
            stack, cells = [(r, c)], []
            visited.add((r, c))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def analyze(grid, settings):
    mode = _mode(settings)
    _grid(grid)
    markers = components(grid, 6)
    if mode == "marker_size" and len(markers) != 1:
        raise ValueError("marker_size domain requires exactly one color-6 component")
    length = 5 if mode == "fixed_five" else len(markers[0])
    targets = [cells for cells in components(grid, 1)
               if len(cells) == length and len({c for _, c in cells}) == 1]
    output = [row[:] for row in grid]
    centers = []
    for cells in targets:
        row = (cells[0][0] + cells[-1][0]) // 2
        col = cells[0][1]
        output[row][col] = 2
        centers.append([row, col])
    return {"marker_cells": [list(p) for p in markers[0]] if len(markers) == 1 else [],
            "target_length": length, "target_centers": centers, "output": output}


def mirror(grid, settings):
    return analyze(grid, settings)["output"]


def _rng(seed, split, index):
    material = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(sha256(material).digest(), "big"))


def _paint(grid, cells, color):
    for row, col in cells:
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            raise RuntimeError("constructive placement went outside the canvas")
        if grid[row][col] != 0:
            raise RuntimeError("constructive placement collided")
        grid[row][col] = color


def _marker(size, rng):
    shapes = {
        3: [(0, 0), (1, 0), (1, 1)],
        5: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
        # The interior center distinguishes occupied-cell count (7) from
        # boundary-cell count (6) within the two-demo teaching minimum.
        7: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (0, 0), (2, 2)],
    }
    cells = shapes[size]
    for _ in range(rng.randrange(4)):
        cells = [(c, -r) for r, c in cells]
    if rng.randrange(2):
        cells = [(r, -c) for r, c in cells]
    low_r, low_c = min(r for r, _ in cells), min(c for _, c in cells)
    return [(r - low_r, c - low_c) for r, c in cells]


def _sample(seed, split, index):
    rng = _rng(seed, split, index)
    shapes = DEMO_SHAPES if split == "train" else QUERY_SHAPES
    sizes = DEMO_MARKERS if split == "train" else QUERY_MARKERS
    height, width = shapes[index]
    key_size = sizes[index]
    grid = [[0] * width for _ in range(height)]

    # The bottom five rows teach marker measurement and horizontal negatives.
    # Upper bands have one entire blank row between them: blue lines never merge
    # vertically across bands, including on the dense 30x30 profile.
    vertical_height = height - 5
    if vertical_height >= 19:
        first = (vertical_height - 1) // 2
        bands = ((0, first), (first + 1, vertical_height - first - 1))
    else:
        bands = ((0, vertical_height),)
    for band_index, (top, band_height) in enumerate(bands):
        # kind, line/run length, diagonal endpoint witness.
        items = [("line", 5, True), ("line", key_size, True),
                 ("branch", 5, False), ("branch", key_size, False),
                 ("line", 4, False), ("line", 9, False),
                 ("line", 7 if key_size == 3 else 3, False)]
        while len(items) < width // 3:
            items.append(("line", rng.choice((2, 3, 5, 7, key_size)), False))
        rng.shuffle(items)
        # A genuine branched blue object contacts the right edge; marker/targets
        # are not the only content on an otherwise empty large canvas.
        branch_index = next(i for i, item in enumerate(items) if item[0] == "branch")
        items[-1], items[branch_index] = items[branch_index], items[-1]
        for lane, (kind, length, diagonal) in enumerate(items):
            column = lane * 3 + 1
            start = top + rng.randint(1 if diagonal else 0, band_height - length)
            if kind == "line" and length == 9:
                start = top  # At least one meaningful component reaches row 0.
            cells = [(start + offset, column) for offset in range(length)]
            if kind == "branch":
                patterns = ((0,), (1, length - 2), (length - 1,), (0, length - 1))
                offsets = patterns[(index + band_index + lane) % len(patterns)]
                cells += [(start + offset, column + 1) for offset in set(offsets)]
            _paint(grid, cells, 1)
            if diagonal:
                _paint(grid, [(start - 1, column + 1)], 1)

    marker = _marker(key_size, rng)
    marker_top = height - 4
    marker_left = 0 if height == width == 30 else rng.randint(0, 2)
    _paint(grid, [(marker_top + r, marker_left + c) for r, c in marker], 6)
    _paint(grid, [(height - 5 + r, 6 + c) for r in range(2) for c in range(2)], 7)
    for row, length in ((height - 1, 5), (height - 3, key_size)):
        left = rng.randint(9, width - length)
        _paint(grid, [(row, left + c) for c in range(length)], 1)

    # Reflections preserve the task's vertical orientation.  No 90-degree
    # whole-grid rotation is claimed or performed.
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if len(components(grid, 6)) != 1 or sum(v == 6 for row in grid for v in row) != key_size:
        raise RuntimeError("constructed marker is not unique and connected")
    return grid


def generate(seed, settings, demos=3, queries=4):
    """Return independent demo/query prefixes and complete private Python labels.

    Inputs depend only on seed, split and pair index, never on the private rule
    setting or requested counts.  Native qualification executes every label.
    """
    _mode(settings)
    if type(seed) is not int or not 0 <= seed < 2 ** 63:
        raise ValueError("seed must be an integer in [0, 2**63), not bool")
    for value, low, high, name in ((demos, 2, 6, "demos"), (queries, 1, 4, "queries")):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an integer in {low}..{high}, not bool")
    episode = {"program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = _sample(seed, split, index)
            signature = json.dumps(grid, separators=(",", ":"))
            if signature in seen:
                raise RuntimeError("constructed duplicate input; never silently shorten an episode")
            seen.add(signature)
            pairs.append({"input": grid, "output": mirror(grid, settings)})
        episode[split] = pairs
    return episode
