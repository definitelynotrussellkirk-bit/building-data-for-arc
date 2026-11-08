"""Native parametric family for 0d191ce876ab.

The hidden episode setting controls an input-dependent preprocessing stage:
identity, or merge colour 1 into colour 2.  The canonical local survivor filter
then consumes that intermediate grid.  Input sampling is setting-independent.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "0d191ce876ab"
HERE = Path(__file__).resolve().parent
SETTINGS = ("identity", "merge_1_into_2")
DEMO_SHAPES = ((13, 17), (17, 13), (19, 19), (21, 17), (17, 21), (23, 23))
QUERY_SHAPES = ((9, 11), (16, 20), (23, 29), (30, 30))


def _integer(value, label, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (
            maximum is not None and value > maximum):
        raise ValueError(f"{label} must be an exact integer in {minimum}..{maximum}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"preprocess"}:
        raise ValueError("settings must contain exactly preprocess")
    value = settings["preprocess"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("preprocess must be identity or merge_1_into_2")
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
    filename = "canonical.rkt" if _setting(settings) == "identity" else "merge_1_into_2.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def intermediate(grid, settings):
    source = deepcopy(_grid(grid))
    if _setting(settings) == "merge_1_into_2":
        return [[2 if value == 1 else value for value in row] for row in source]
    return source


def survivor_filter(grid):
    source = _grid(grid)
    h, w = len(source), len(source[0])
    output = [[0] * w for _ in range(h)]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = source[r][c]
            if (value != 0 and source[r - 1][c] == value and source[r + 1][c] == value
                    and source[r][c - 1] == value and source[r][c + 1] == value):
                output[r][c] = value
    return output


def transform(grid, settings):
    return survivor_filter(intermediate(grid, settings))


def _rng(seed, stream, index):
    key = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _motif(kind, rng):
    """Return an independent 5x5 witness patch."""
    grid = [[0] * 5 for _ in range(5)]
    if kind == 0:  # canonical plus: survives under both settings
        for r, c in ((2, 2), (1, 2), (3, 2), (2, 1), (2, 3)):
            grid[r][c] = 2
    elif kind == 1:  # split plus: merge creates the core
        for r, c in ((2, 2), (1, 2), (3, 2), (2, 1), (2, 3)):
            grid[r][c] = 2
        grid[1][2] = 1
    elif kind == 2:  # colour-1 plus: both survive, but labels differ 1 vs 2
        for r, c in ((2, 2), (1, 2), (3, 2), (2, 1), (2, 3)):
            grid[r][c] = 1
    elif kind == 3:  # two adjacent cores; rejects one-centre-per-object
        for r in range(1, 4):
            for c in range(0, 4):
                grid[r][c] = 2
    elif kind == 4:  # mixed 3x4 rectangle: merge creates two adjacent cores
        for r in range(1, 4):
            for c in range(1, 5):
                grid[r][c] = 1 if (r + c) % 2 else 2
    elif kind == 5:  # unaffected core plus mixed near-core
        for r, c in ((1, 1), (0, 1), (2, 1), (1, 0), (1, 2)):
            grid[r][c] = 6
        for r, c in ((3, 3), (4, 3), (3, 2), (3, 4)):
            grid[r][c] = 2
        grid[2][3] = 3
    elif kind == 6:  # four-core colour-1 block
        for r in range(0, 4):
            for c in range(0, 4):
                grid[r][c] = 1
    elif kind == 7:  # hollow ring: no core
        for i in range(5):
            grid[0][i] = grid[4][i] = grid[i][0] = grid[i][4] = 7
    else:  # deterministic sparse texture, still setting-sensitive when 1 occurs
        for r in range(5):
            for c in range(5):
                if rng.random() < 0.34:
                    grid[r][c] = rng.choice((1, 2, 2, 5, 8))
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def _starts(length, rng):
    count = max(1, (length + 1) // 6)
    if count == 1:
        return [rng.randrange(length - 4)]
    return [index * (length - 5) // (count - 1) for index in range(count)]


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
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
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
