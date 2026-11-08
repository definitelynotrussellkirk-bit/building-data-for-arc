"""Opt-in one/two-pass component closure; production generator is unchanged.

The second pass reads the first pass's green connected components. It is a
simultaneous snapshot pass, not an in-place scan or iteration to convergence.
Python outputs are claims: native qualification executes the Racket programs.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random

TASK_ID = "699479899861"
VERSION = "closure-rounds-v1"
SETTINGS = ({"closure_rounds": 1}, {"closure_rounds": 2})
DEMO_SHAPES = ((16, 17), (18, 20), (21, 23), (24, 27), (28, 26), (29, 30))
QUERY_SHAPES = ((17, 19), (22, 25), (30, 30), (27, 29))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"closure_rounds"}:
        raise ValueError("settings must name exactly closure_rounds")
    return _integer(settings["closure_rounds"], 1, 2, "closure_rounds")


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def components(grid, color, connectivity=4):
    validate_grid(grid)
    _integer(color, 0, 9, "color")
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in steps:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        result.append(sorted(cells))
    return result


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def closure(grid, color=2):
    """Fill boxes of the chosen color's ORIGINAL 4-components green."""
    groups = components(grid, color)
    output = [row[:] for row in grid]
    for cells in groups:
        top, left, bottom, right = _bbox(cells)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                output[r][c] = 3
    return output


def mirror(grid, settings):
    rounds = _settings(settings)
    first = closure(grid, 2)
    return first if rounds == 1 else closure(first, 3)


def _racket_pass(grid_name, color):
    return f"""(for/fold ([out {grid_name}])
       ([obj (in-list (filter (lambda (o) (= (obj-color o) {color})) (objects {grid_name} 0)))])
      (let* ([rs (remove-duplicates (map first (obj-cells obj)))]
             [cs (remove-duplicates (map second (obj-cells obj)))]
             [cells (for*/list ([r (in-list rs)] [c (in-list cs)]) (list r c))])
        (paint-cells out cells 3)))"""


def program(settings):
    if _settings(settings) == 1:
        return Path(__file__).with_name("canonical.rkt").read_bytes().decode("utf-8")
    return "(rule!\n  (let ([stage1 " + _racket_pass("g", 2) + "])\n    " + _racket_pass("stage1", 3) + "))"


def transform(grid, code):
    """The eight dihedral transforms; rectangular canvases may transpose."""
    validate_grid(grid)
    _integer(code, 0, 7, "transform code")
    result = [row[:] for row in grid]
    if code & 4:
        result = [list(row) for row in zip(*result)]
    if code & 2:
        result.reverse()
    if code & 1:
        result = [list(reversed(row)) for row in result]
    return result


def _partition(total, minima, rng):
    result = list(minima)
    for _ in range(total - sum(result)):
        result[rng.randrange(len(result))] += 1
    return result


def _ell(top, left, height, width, corner):
    row = top if corner in ("tl", "tr") else top + height - 1
    col = left if corner in ("tl", "bl") else left + width - 1
    return {(row, c) for c in range(left, left + width)} | {
        (r, col) for r in range(top, top + height)}


def _motif(kind, h, w, rng, *, horizontal_only=False):
    if kind == "chain":
        ah, bh, ch = _partition(h + 1, (3, 3, 2), rng)
        aw, bw = _partition(w, (3, 2), rng)
        cw = rng.randint(2, aw - 1)
        shapes = [_ell(0, 0, ah, aw, "tl"),
                  _ell(ah - 1, aw, bh, bw, "br"),
                  _ell(ah + bh - 1, aw - cw, ch, cw, "bl")]
    elif kind == "merge":
        ah, bh = _partition(h + 1, (3, 3), rng)
        aw, bw = _partition(w, (3, 2), rng)
        shapes = [_ell(0, 0, ah, aw, "tl"), _ell(ah - 1, aw, bh, bw, "br")]
    elif kind == "diagonal":
        ah, bh = _partition(h, (2, 2), rng)
        aw, bw = _partition(w, (2, 2), rng)
        shapes = [_ell(0, 0, ah, aw, "tr"), _ell(ah, aw, bh, bw, "bl")]
    else:
        shapes = [_ell(0, 0, h, w, rng.choice(("tl", "tr", "bl", "br")))]
    grid = [[0] * w for _ in range(h)]
    for shape in shapes:
        for r, c in shape:
            grid[r][c] = 2
    return transform(grid, rng.randrange(2 if horizontal_only else 4))


def _mixed_shapes(h, w, count, profile, rng):
    """Independent nonrectangular components, separated by one empty row."""
    heights = _partition(h - count + 1, (2,) * count, rng)
    grid = [[0] * w for _ in range(h)]
    kinds = ("plus", "u", "zigzag", "tee", "ell")
    top = 0
    for i, height in enumerate(heights):
        width = max(3, w - rng.randrange(3))
        left = rng.randint(0, w - width)
        bottom, right = top + height - 1, left + width - 1
        middle_r, middle_c = top + height // 2, left + width // 2
        kind = kinds[(profile + i) % len(kinds)]
        if kind == "plus":
            cells = {(middle_r, c) for c in range(left, right + 1)} | {
                (r, middle_c) for r in range(top, bottom + 1)}
        elif kind == "u":
            cells = {(bottom, c) for c in range(left, right + 1)} | {
                (r, c) for r in range(top, bottom + 1) for c in (left, right)}
        elif kind == "zigzag":
            cells = {(top, c) for c in range(left, middle_c + 1)} | {
                (bottom, c) for c in range(middle_c, right + 1)} | {
                (r, middle_c) for r in range(top, bottom + 1)}
        elif kind == "tee":
            cells = {(top, c) for c in range(left, right + 1)} | {
                (r, middle_c) for r in range(top, bottom + 1)}
        else:
            cells = _ell(top, left, height, width, rng.choice(("tl", "tr", "bl", "br")))
        for r, c in cells:
            grid[r][c] = 2
        top += height + 1
    return transform(grid, rng.randrange(4))


def _input(seed, split, index):
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("ascii")
    rng = random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))
    h, w = (DEMO_SHAPES if split == "train" else QUERY_SHAPES)[index]
    grid = [[0] * w for _ in range(h)]
    mr, mc = h // 2, w // 2
    zones = ((0, 0, mr - 1, mc - 1), (0, mc + 1, mr - 1, w - 1),
             (mr + 1, 0, h - 1, mc - 1), (mr + 1, mc + 1, h - 1, w - 1))
    kinds = ("chain", "merge", "diagonal", "single")
    extra_count = ((1, 2, 3, 1, 2, 3) if split == "train" else (2, 3, 3, 1))[index]
    minima = ((7, 5), (5, 5), (4, 4), (3 * extra_count - 1, 3))
    boundary = (h, w) == (30, 30)
    for zone, kind, minimum in zip(zones, kinds, minima):
        top, left, bottom, right = zone
        zh, zw = bottom - top + 1, right - left + 1
        mh = zh if boundary else max(minimum[0], zh - rng.randrange(3))
        mw = zw if boundary else max(minimum[1], zw - rng.randrange(3))
        # The first two lessons must face the chain in opposite scan orders.
        # Keeping its local vertical orientation makes the global choice below
        # a constructive witness, independent of the random component sizes.
        if kind == "single":
            piece = _mixed_shapes(mh, mw, extra_count, index if split == "train" else index + 3, rng)
        else:
            piece = _motif(kind, mh, mw, rng,
                           horizontal_only=(kind == "chain" and split == "train" and index < 2))
        r0, c0 = rng.randint(top, bottom - mh + 1), rng.randint(left, right - mw + 1)
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    grid[r0 + r][c0 + c] = value
    # Decorations occupy cells outside even the converged motif closures.
    filled = closure(closure(closure(grid, 2), 3), 3)
    spots = [(r, c) for r in range(h) for c in range(w) if filled[r][c] == 0]
    rng.shuffle(spots)
    colors = [1, 4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    for (r, c), value in zip(spots[:rng.randint(1, 3)], colors):
        grid[r][c] = value
    if split == "train" and index < 2:
        # Demo0: AB before C; demo1: C before AB. Together they reject both
        # forward and reverse live-update scans without another demonstration.
        return transform(grid, 2 * index + rng.randrange(2))
    return transform(grid, rng.randrange(8))


def generate(seed, settings, demos=3, queries=4):
    """Return a private episode with settings-independent, prefix-stable inputs."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        result[split] = []
        for index in range(count):
            grid = _input(seed, split, index)
            result[split].append({"input": grid, "output": mirror(grid, settings)})
    return result


def analyze(grid):
    first = closure(grid, 2)
    second = closure(first, 3)
    third = closure(second, 3)
    return {"shape": [len(grid), len(grid[0])],
            "red_component_count": len(components(grid, 2)),
            "intermediate_grid": first,
            "intermediate_green_components": [
                {"cells": [list(p) for p in cells], "bbox": list(_bbox(cells))}
                for cells in components(first, 3)],
            "one_vs_two_differing_cells": [[r, c] for r in range(len(grid))
                for c in range(len(grid[0])) if first[r][c] != second[r][c]],
            "two_vs_three_differing_cells": [[r, c] for r in range(len(grid))
                for c in range(len(grid[0])) if second[r][c] != third[r][c]]}
