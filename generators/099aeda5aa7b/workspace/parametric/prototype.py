"""Native horizontal-versus-vertical reflection family for 099aeda5aa7b."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "099aeda5aa7b"
HERE = Path(__file__).resolve().parent
AXES = ("horizontal", "vertical")
DEMO_SHAPES = ((13, 17), (17, 13), (19, 19), (21, 17), (17, 21), (23, 23))
QUERY_SHAPES = ((9, 13), (16, 20), (23, 29), (30, 30))


def _integer(value, label, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (
            maximum is not None and value > maximum):
        raise ValueError(f"{label} must be an exact integer in {minimum}..{maximum}")
    return value


def _axis(settings):
    if type(settings) is not dict or set(settings) != {"axis"}:
        raise ValueError("settings must contain exactly axis")
    value = settings["axis"]
    if type(value) is not str or value not in AXES:
        raise ValueError("axis must be horizontal or vertical")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colours 0..9")
    return grid


def program(settings):
    filename = "horizontal.rkt" if _axis(settings) == "horizontal" else "vertical.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def intermediate(grid, settings):
    source = deepcopy(_grid(grid))
    if _axis(settings) == "horizontal":
        return [row[::-1] for row in source]
    return source[::-1]


def overlay(base, top):
    left, right = _grid(base), _grid(top)
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError("overlay grids must have matching dimensions")
    return [[right[r][c] if right[r][c] != 0 else left[r][c]
             for c in range(len(left[0]))] for r in range(len(left))]


def transform(grid, settings):
    source = deepcopy(_grid(grid))
    return overlay(source, intermediate(source, settings))


def _rng(seed, stream, index):
    key = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _motif(kind, rng):
    grid = [[0] * 5 for _ in range(5)]
    patterns = {
        0: ((0, 0, 1), (0, 1, 2), (1, 0, 3), (2, 0, 4), (3, 1, 5)),
        1: ((0, 3, 1), (1, 3, 2), (2, 2, 3), (3, 1, 4), (4, 1, 5)),
        2: ((2, 0, 1), (2, 4, 3), (0, 1, 4), (1, 2, 5), (4, 3, 6)),
        3: ((0, 2, 4), (4, 2, 6), (1, 0, 2), (2, 3, 7), (3, 4, 8)),
        4: ((0, 0, 2), (1, 0, 2), (2, 0, 3), (2, 1, 4), (2, 2, 5), (3, 2, 6)),
        5: ((0, 0, 1), (1, 1, 2), (2, 2, 3), (3, 3, 4), (4, 4, 5), (0, 4, 6)),
        6: ((0, 0, 2), (0, 4, 2), (1, 1, 3), (1, 3, 3), (2, 2, 4)),
        7: ((0, 0, 2), (4, 0, 2), (1, 1, 3), (3, 1, 3), (2, 2, 4)),
        8: ((0, 0, 1), (0, 2, 2), (0, 4, 3), (2, 1, 4), (2, 3, 5),
            (4, 0, 6), (4, 2, 7), (4, 4, 8), (3, 1, 9)),
    }
    for r, c, value in patterns[kind]:
        grid[r][c] = value
    # Whole-axis flips preserve the family contrast while varying placements.
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def _starts(length, rng):
    # Leave a guaranteed trailing canvas margin whenever the dimension permits.
    # Together with the fixed top-left anchor below, this makes reflection about
    # the occupied bounding box observably different from reflection about the
    # full grid.
    trailing_margin = 1 if length >= 6 else 0
    last_start = length - 5 - trailing_margin
    count = max(1, (length + 1) // 6)
    if count == 1:
        return [rng.randrange(last_start + 1)]
    return [index * last_start // (count - 1) for index in range(count)]


def sample_input(seed, stream, index, height, width, motif_ids=None):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 5, 30)
    _integer(width, "width", 5, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    rng = _rng(seed, stream, index)
    positions = [(r, c) for r in _starts(height, rng) for c in _starts(width, rng)]
    ids = list(range(9)) if motif_ids is None else list(motif_ids)
    if not ids or any(type(kind) is not int or kind not in range(9) for kind in ids):
        raise ValueError("motif_ids must be nonempty integers 0..8")
    if motif_ids is not None and len(ids) > len(positions):
        raise ValueError("canvas cannot hold requested constructive motifs")
    rng.shuffle(ids)
    order = [ids[i % len(ids)] for i in range(len(positions))]
    rng.shuffle(order)
    grid = [[0] * width for _ in range(height)]
    for (r0, c0), kind in zip(positions, order):
        patch = _motif(kind, rng)
        for r, row in enumerate(patch):
            grid[r0 + r][c0:c0 + 5] = row
    # Pin the occupied extent to the top and left while the sampler leaves the
    # bottom and right edges empty.  The full-canvas axis is therefore visible.
    grid[0][0] = 9
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _axis(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {"train": [], "test": [], "program_solution": program(settings),
              "settings": dict(settings), "seed": seed, "prototype": True}
    seen = set()
    for split, shapes in (("train", DEMO_SHAPES[:demos]), ("test", QUERY_SHAPES[:queries])):
        for index, (height, width) in enumerate(shapes):
            motifs = [0, 1, 2, 3, 4, 5] if split == "train" else None
            grid = sample_input(seed, split, index, height, width, motifs)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
