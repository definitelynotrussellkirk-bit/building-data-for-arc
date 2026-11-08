"""Matched-input native family for prototype-controlled stamping.

The canonical ``mixed`` setting preserves the exact selected Racket program.
The alternate ``rotations`` setting keeps the same visible grammar but interprets
controls 1..4 as quarter turns 0, 1, 2 and 3. Python outputs are deterministic
claims; native qualification independently executes every label in Racket.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
from itertools import combinations
from pathlib import Path
import random

TASK_ID = "274345a1792c"
FAMILIES = ("mixed", "rotations")
SETTINGS = tuple({"transform_family": name} for name in FAMILIES)
DEMO_SIZES = ((13, 15), (17, 18), (21, 21), (24, 24), (19, 23), (23, 19))
QUERY_SIZES = ((30, 30), (24, 30), (30, 24), (27, 29))


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"transform_family"}
            or type(settings["transform_family"]) is not str
            or settings["transform_family"] not in FAMILIES):
        raise ValueError("settings must be exactly transform_family=mixed|rotations")
    return settings["transform_family"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate(cells):
    return _normalize((c, -r) for r, c in cells)


def _flip_lr(cells):
    return _normalize((r, -c) for r, c in cells)


def _transform(cells, code, family):
    cells = _normalize(cells)
    if code not in (1, 2, 3, 4):
        raise ValueError("control code must be 1..4")
    if family == "mixed":
        if code == 1:
            return cells
        if code == 2:
            return _rotate(cells)
        if code == 3:
            return _flip_lr(cells)
        return _rotate(_flip_lr(cells))
    result = cells
    for _ in range(code - 1):
        result = _rotate(result)
    return result


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in cells and q not in seen:
                seen.add(q)
                todo.append(q)
    return seen == cells


def _orbit(cells):
    cells = _normalize(cells)
    result = set()
    for reflected in (False, True):
        cur = _flip_lr(cells) if reflected else cells
        for _ in range(4):
            result.add(cur)
            cur = _rotate(cur)
    return result


@lru_cache(maxsize=3)
def _shape_bank(count):
    universe = tuple((r, c) for r in range(3) for c in range(3))
    shapes = {
        _normalize(cells)
        for cells in combinations(universe, count)
        if _connected(cells)
    }
    result = tuple(sorted(
        shape for shape in shapes
        if max(r for r, _ in shape) == 2
        and max(c for _, c in shape) == 2
        and len(_orbit(shape)) == 8
    ))
    if not result:
        raise RuntimeError(f"no asymmetric 3x3 shapes with {count} cells")
    return result


def _rng(seed, split, index):
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _spread_slots(height, width, rng):
    row_offsets = tuple(dict.fromkeys((0, height % 4)))
    col_offsets = tuple(dict.fromkeys((0, width % 3)))
    ro = rng.choice(row_offsets)
    co = rng.choice(col_offsets)
    bins = [(r, c)
            for r in range(ro, height - 3, 4)
            for c in range(co, width - 2, 3)]
    if len(bins) < 6:
        raise ValueError("canvas cannot hold the constructive six-bin grammar")
    first = rng.choice(bins)
    selected = [first]
    remaining = set(bins) - {first}
    while len(selected) < 6:
        scores = []
        for cell in remaining:
            distance = min(abs(cell[0] - r) + abs(cell[1] - c) for r, c in selected)
            edge = min(cell[0], cell[1], height - 4 - cell[0], width - 3 - cell[1])
            scores.append((distance, -edge, rng.random(), cell))
        chosen = max(scores)[-1]
        selected.append(chosen)
        remaining.remove(chosen)
    return selected


def _placements(height, width, split, index, rng):
    if split == "query" and index == 0:
        # Visible input markers, not only the eventual stamps, reach all four
        # boundaries: the prototype occupies the bottom-right 3x3 box while
        # top/left control-anchor groups cover the opposite edges.
        return (height - 3, width - 3), [
            (1, 0),
            (1, width - 3),
            (height - 3, 0),
            (height // 2, 0),
            (height // 2, width // 2),
        ]
    bins = _spread_slots(height, width, rng)
    prototype = bins[0]
    anchors = [(r + 1, c) for r, c in bins[1:]]
    return prototype, anchors


def sample_input(seed, split, index, *, height, width):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 9, 30, "height")
    _integer(width, 12, 30, "width")
    rng = _rng(seed, split, index)
    count = (5, 6, 7)[(index + (1 if split == "query" else 0)) % 3]
    shape = rng.choice(_shape_bank(count))
    prototype_origin, anchors = _placements(height, width, split, index, rng)
    repeated = 3 + ((seed + index + (split == "query")) % 2)
    codes = [1, 2, 3, 4, repeated]
    rng.shuffle(codes)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    pr, pc = prototype_origin
    for r, c in shape:
        grid[pr + r][pc + c] = 9
    for (ar, ac), code in zip(anchors, codes):
        grid[ar - 1][ac] = code
        grid[ar][ac] = 6
    facts = analyze(grid)
    if not facts["valid_for_both_settings"]:
        raise RuntimeError("constructive sampler produced an invalid scene")
    return grid


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _parts(grid):
    prototype = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    anchors = [(r, c, grid[r - 1][c]) for r, row in enumerate(grid)
               for c, v in enumerate(row) if v == 6 and r > 0]
    return prototype, anchors


def analyze(grid):
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    prototype, anchors = _parts(grid)
    shape = _normalize(prototype) if prototype else ()
    all_anchors = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6}
    controls = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3, 4)}
    bound = {(r - 1, c) for r, c in all_anchors if r > 0}
    valid = bool(prototype and _connected(prototype) and controls == bound and len(anchors) == len(all_anchors))
    protected = set(prototype) | controls | all_anchors
    for family in FAMILIES:
        stamped = set()
        for ar, ac, code in anchors:
            if code not in (1, 2, 3, 4):
                valid = False
                continue
            cells = {(ar + r, ac + c) for r, c in _transform(shape, code, family)}
            if (any(not (0 <= r < height and 0 <= c < width) for r, c in cells)
                    or cells & (protected - {(ar, ac)}) or cells & stamped):
                valid = False
            stamped |= cells
    values = [code for _, _, code in anchors]
    return {
        "prototype_cells": len(prototype),
        "prototype_bbox": ([1 + max(r for r, _ in shape), 1 + max(c for _, c in shape)]
                           if shape else [0, 0]),
        "prototype_orbit": len(_orbit(shape)) if shape else 0,
        "anchor_count": len(anchors),
        "controls": sorted(set(values)),
        "repeated_control": len(values) != len(set(values)),
        "valid_for_both_settings": valid,
    }


def solve_with_shape(grid, settings, shape):
    family = _settings(settings)
    grid = _grid(grid)
    shape = _normalize(shape)
    _, anchors = _parts(grid)
    out = [row[:] for row in grid]
    for ar, ac, code in anchors:
        for r, c in _transform(shape, code, family):
            rr, cc = ar + r, ac + c
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = 8
    return out


def solve(grid, settings):
    prototype, _ = _parts(_grid(grid))
    if not prototype or not _connected(prototype):
        raise ValueError("one connected maroon prototype is required")
    return solve_with_shape(grid, settings, _normalize(prototype))


def program(settings):
    family = _settings(settings)
    name = "canonical.rkt" if family == "mixed" else "rotations.rkt"
    return Path(__file__).resolve().with_name(name).read_text(encoding="utf-8")


def generate(seed, settings, demos=3, queries=4):
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [sample_input(seed, "demo", i, height=h, width=w)
                    for i, (h, w) in enumerate(DEMO_SIZES[:demos])]
    test_inputs = [sample_input(seed, "query", i, height=h, width=w)
                   for i, (h, w) in enumerate(QUERY_SIZES[:queries])]
    return {
        "train": [{"input": g, "output": solve(g, settings)} for g in train_inputs],
        "test": [{"input": g, "output": solve(g, settings)} for g in test_inputs],
        "program_solution": program(settings),
    }


def public_turn(episode, query_index=0):
    if type(query_index) is not int:
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode needs visible train pairs and the selected query")
    return {
        "train": [{"input": copy.deepcopy(pair["input"]),
                   "output": copy.deepcopy(pair["output"])} for pair in train],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }
