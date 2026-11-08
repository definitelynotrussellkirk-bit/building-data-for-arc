"""Native matched-input nearest-object lessons with two distance metrics."""
import copy
import hashlib
import math
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
METRICS = ("manhattan", "chebyshev")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _metric(settings):
    if (type(settings) is not dict or set(settings) != {"metric"}
            or type(settings["metric"]) is not str or settings["metric"] not in METRICS):
        raise ValueError("settings must contain only metric='manhattan' or 'chebyshev'")
    return settings["metric"]


def program(settings):
    return (HERE / (_metric(settings) + ".rkt")).read_text()


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)}
    result = []
    while unseen:
        origin = min(unseen)
        unseen.remove(origin)
        color = grid[origin[0]][origin[1]]
        cells, stack = {origin}, [origin]
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                p = r + dr, c + dc
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    cells.add(p)
                    stack.append(p)
        result.append({"color": color, "cells": cells,
                       "bbox": (min(r for r, c in cells), min(c for r, c in cells),
                                max(r for r, c in cells), max(c for r, c in cells))})
    return result  # Same row-major discovery order as the Racket objects primitive.


def analyze(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 5 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0])
            or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError("expected a rectangular 5..30 grid of exact integer colors")
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(markers) != 1:
        raise ValueError("expected exactly one marker of color 9")
    objs = components(grid)
    if not 2 <= len(objs) <= 8:
        raise ValueError("expected 2..8 monochrome cardinal components after removing marker")
    return markers[0], objs


def distance(marker, cells, metric):
    if metric == "manhattan":
        return min(abs(r - marker[0]) + abs(c - marker[1]) for r, c in cells)
    if metric == "chebyshev":
        return min(max(abs(r - marker[0]), abs(c - marker[1])) for r, c in cells)
    raise ValueError("unknown distance metric")


def crop(obj):
    top, left, bottom, right = obj["bbox"]
    result = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for r, c in obj["cells"]:
        result[r - top][c - left] = obj["color"]
    return result


def solve(grid, metric="manhattan"):
    if type(metric) is not str or metric not in METRICS:
        raise ValueError("unknown distance metric")
    marker, objs = analyze(grid)
    # min is stable: a complete distance/top/left tie retains discovery order.
    chosen = min(objs, key=lambda o: (distance(marker, o["cells"], metric), *o["bbox"][:2]))
    return crop(chosen)


def _rng(seed, split, index, attempt=0):
    data = f"25e18d9bd322-input-v1:{seed}:{split}:{index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(data).digest(), "big"))


def _paint(grid, cells, color, dr=0, dc=0):
    for r, c in cells:
        if grid[r + dr][c + dc] != 0:
            raise ValueError("constructed objects overlap")
        grid[r + dr][c + dc] = color


def _teaching(index, rng):
    low, middle_a, middle_b, high = sorted(rng.sample(range(1, 9), 4))
    if index == 0:
        grid, marker = [[0] * 25 for _ in range(18)], (10, 10)
        a = {(r, 3) for r in range(2, 11)} | {(2, 4), (2, 5)}
        b = {(r, 22) for r in range(2, 15)} | {(15, c) for c in range(15, 23)}
        shapes = [(a, middle_a), ({(0, 2), (1, 2)}, middle_a),
                  (b, middle_b), ({(0, 21), (1, 21)}, middle_b),
                  ({(5, 4), (6, 4)}, low),
                  ({(13, 16), (13, 17), (14, 17)}, high)]
        # Manhattan selects A, Chebyshev selects B, Euclidean selects E.
        # Diagonal same-color satellites and edge-touching different-color
        # intruders expose connectivity, grouping and raw-crop shortcuts.
    else:
        grid, marker = [[0] * 18 for _ in range(22)], (10, 10)
        w = ({(4, c) for c in range(5, 14)} | {(r, 5) for r in range(5, 11)}
             | {(r, 13) for r in range(5, 15)} | {(14, c) for c in range(8, 13)})
        b = ({(r, 11) for r in range(5, 13)} | {(12, c) for c in range(3, 12)}
             | {(r, c) for r in range(12, 17) for c in range(3, 8)
                if r in (12, 16) or c in (3, 7)})
        d = ({(11, c) for c in range(1, 11)} | {(r, 1) for r in range(12, 20)}
             | {(r, c) for r in range(17, 20) for c in range(1, 9)})
        shapes = [(w, high), (b, low), ({(r, 10) for r in range(5, 10)}, middle_a),
                  (d, middle_b), ({(14, 5)}, low), ({(2, 4), (3, 4)}, high)]
        # B/C/D tie at distance one under both metrics. B wins by bbox top,
        # then left, despite C being discovered earlier. B has a real hole;
        # its crop must erase the marker and a disconnected same-color cell.
    dr, dc = rng.randrange(2), rng.randrange(2)
    for cells, color in shapes:
        _paint(grid, cells, color, dr, dc)
    grid[marker[0] + dr][marker[1] + dc] = 9
    return grid


def _bands(total, count, start):
    usable = total - count + 1
    if usable < 2 * count:
        raise ValueError("canvas too small for separated slots")
    result = []
    for i in range(count):
        size = usable // count + int(i < usable % count)
        result.append((start, size))
        start += size + 1
    return result


def _shape(height, width, kind):
    if kind == "solid":
        return {(r, c) for r in range(height) for c in range(width)}
    if kind == "frame":
        return {(r, c) for r in range(height) for c in range(width) if r in (0, height - 1) or c in (0, width - 1)}
    if kind == "comb":
        return {(r, c) for r in range(height) for c in range(width) if c == 0 or r % 2 == 0}
    if kind == "elbow":
        return {(r, c) for r in range(height) for c in range(width) if r == 0 or c == 0}
    if kind == "notched":
        return {(r, c) for r in range(height) for c in range(width) if not (r < height // 2 and c >= width // 2)}
    raise ValueError("unknown shape")


def scene(height, width, count, rng, *, full=False, contact=False):
    _integer(height, 10, 30, "height"); _integer(width, 10, 30, "width"); _integer(count, 3, 8, "count")
    grid = [[0] * width for _ in range(height)]
    palette = [rng.randrange(1, 9)] * count if rng.randrange(2) else rng.sample(range(1, 9), count)
    _paint(grid, {(r, c) for r in range(height) for c in range(width)
                  if r in (0, height - 1) or c in (0, width - 1)}, palette[0])
    inner = count - 1
    nr = 2 if inner <= 4 else 3
    nc = math.ceil(inner / nr)
    slots = [(r, c, h, w) for r, h in _bands(height - 4, nr, 2)
             for c, w in _bands(width - 4, nc, 2)]
    kinds = ["solid", "frame", "comb", "elbow", "notched"]
    rng.shuffle(kinds)
    for i, (r, c, h, w) in enumerate(slots[:inner]):
        sh, sw = (h, w) if full else (rng.randint(2, h), rng.randint(2, w))
        cells = _shape(sh, sw, kinds[i % len(kinds)])
        if rng.randrange(2): cells = {(sh - 1 - a, b) for a, b in cells}
        if rng.randrange(2): cells = {(a, sw - 1 - b) for a, b in cells}
        _paint(grid, cells, palette[i + 1], r + rng.randint(0, h - sh), c + rng.randint(0, w - sw))
    free = [(r, c) for r in range(2, height - 2) for c in range(2, width - 2) if grid[r][c] == 0]
    adjacent = [p for p in free if any(grid[p[0] + dr][p[1] + dc] for dr, dc in CARDINAL)]
    separated = [p for p in free if p not in adjacent]
    marker = rng.choice((adjacent if contact else separated) or free)
    grid[marker[0]][marker[1]] = 9
    return grid


def _input(seed, split, index, attempt):
    rng = _rng(seed, split, index, attempt)
    if split == "train" and index < 2:
        return _teaching(index, rng)
    if split == "train":
        return scene(15 + index, 18 + index, 4 + index % 4, rng)
    h, w, n = ((12, 15, 4), (20, 24, 6), (30, 30, 8), (25, 29, 7))[index]
    return scene(h, w, n, rng, full=index >= 1, contact=index == 0)


def generate(seed, settings, demos, queries):
    metric = _metric(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos"); _integer(queries, 1, 4, "queries")
    seen, result = set(), {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            for attempt in range(16):
                grid = _input(seed, split, index, attempt)
                identity = tuple(map(tuple, grid))
                if identity not in seen:
                    seen.add(identity)
                    pairs.append({"input": grid, "output": solve(grid, metric)})
                    break
            else:
                raise ValueError("distinct-input generation budget exhausted")
        result[split] = pairs
    return {**result, "program_solution": program(settings), "seed": seed, "settings": copy.deepcopy(settings)}


def public_turn(episode, query_index):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {"train": [{"input": copy.deepcopy(p["input"]), "output": copy.deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
