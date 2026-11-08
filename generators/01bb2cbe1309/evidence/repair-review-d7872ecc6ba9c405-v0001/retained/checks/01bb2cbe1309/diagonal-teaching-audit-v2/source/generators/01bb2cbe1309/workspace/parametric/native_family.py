"""One or two complete snapshot passes of canonical diagonal completion."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

TASK_ID = "01bb2cbe1309"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"passes": [1, 2]}
DEFAULT = {"passes": 1}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
_BODY = CANONICAL[len("(rule! "):-1]
ALTERNATIVE = "(rule! (let* ((first-grid " + _BODY + ") (g first-grid)) " + _BODY + "))"


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"passes"}:
        raise ValueError("settings must contain exactly passes")
    _integer(settings["passes"], 1, 2, "passes")
    return settings["passes"]


def program(settings):
    return CANONICAL if _settings(settings) == 1 else ALTERNATIVE


def _pass(grid):
    out = [row[:] for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c:c + 2]
            c1, d = grid[r + 1][c:c + 2]
            if a and a == d and b == c1 == 0:
                out[r][c + 1] = out[r + 1][c] = a
            elif b and b == c1 and a == d == 0:
                out[r][c] = out[r + 1][c + 1] = b
    return out


def solve(grid, passes=1):
    validate_grid(grid)
    _integer(passes, 1, 2, "passes")
    out = [row[:] for row in grid]
    for _ in range(passes):
        out = _pass(out)
    return out


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _paint(grid, motif, row, col):
    for r, values in enumerate(motif):
        for c, value in enumerate(values):
            if value:
                assert grid[row + r][col + c] == 0
                grid[row + r][col + c] = value


def _variant(grid, rng, rotate=False):
    if rotate:
        if rng.randrange(2):
            grid = [row[::-1] for row in grid]
        for _ in range(rng.randrange(4)):
            grid = [list(row) for row in zip(*grid[::-1])]
    colors = list(range(1, 10))
    rng.shuffle(colors)
    palette = [0] + colors
    return [[palette[value] for value in row] for row in grid]


_WAVE = [[2, 0, 2, 0], [0, 0, 0, 2], [0, 2, 0, 0]]
_CONFLICT = [[0, 2, 0], [2, 0, 3], [0, 3, 0]]
_DEFERRED_CONFLICT = [[0, 2, 0], [0, 0, 2], [2, 0, 3], [3, 0, 0], [0, 3, 0]]


def _core(which, rng):
    """Separated motifs retain original-scan conflict and wave witnesses."""
    h, w = ((14, 20), (16, 23))[which]
    grid = [[0] * w for _ in range(h)]
    motifs = [
        _WAVE,
        [list(row) for row in zip(*_WAVE[::-1])],
        _CONFLICT,
        [[4, 0], [0, 4]],
        [[0, 5], [5, 0]],
        [[6, 7], [0, 6]],
        [[8, 8], [0, 0]],
        [[2, 0], [0, 9]],
        [[4, 0], [4, 0]],
        [[3, 3], [3, 3]],
        [[6]],
        [[2, 0, 0], [0, 0, 0], [0, 0, 2]],
    ]
    if which:
        motifs = [motifs[i] for i in (2, 1, 5, 7, 0, 8, 4, 3, 11, 9, 6, 10)]
        motifs = [[row[::-1] for row in motif] for motif in motifs]
        motifs[0] = _DEFERRED_CONFLICT
    row_offset = rng.randrange(2) if which else 0
    col_offset = rng.randrange(3) if which else 0
    for i, motif in enumerate(motifs):
        _paint(grid, motif, (i // 4) * (6 if which else 5) + row_offset, (i % 4) * 5 + col_offset)
    return _variant(grid, rng)


def _mosaic(h, w, rng, waves=False):
    grid = [[0] * w for _ in range(h)]
    if waves:
        for index, (r, c) in enumerate((r, c) for r in range(0, h - 2, 4) for c in range(0, w - 3, 4)):
            motif = _WAVE if index % 3 else _CONFLICT
            if rng.randrange(2):
                motif = motif[::-1]
            motif = _variant(motif, rng)
            _paint(grid, motif, r, c)
    else:
        for index, (r, c) in enumerate((r, c) for r in range(0, h - 1, 3) for c in range(0, w - 1, 3)):
            color, other = rng.sample(range(1, 10), 2)
            patterns = (
                [[color, 0], [0, color]],
                [[0, color], [color, 0]],
                [[color, other], [0, color]],
                [[color, 0], [0, other]],
                [[color, color], [0, 0]],
            )
            # Half the motifs are guaranteed positive; the rest supply varied negatives.
            motif = patterns[index % 2] if index % 2 == 0 else rng.choice(patterns)
            _paint(grid, motif, r, c)
    return _variant(grid, rng, rotate=True)


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos_rng, queries_rng = _rng(seed, "demos"), _rng(seed, "queries")
    train = [
        _core(0, demos_rng), _core(1, demos_rng),
        [[demos_rng.randrange(10)]],
        _mosaic(7, 9, demos_rng), _mosaic(20, 25, demos_rng, True),
        _mosaic(30, 30, demos_rng),
    ]
    test = [
        _mosaic(4, 7, queries_rng, True), _mosaic(15, 18, queries_rng, True),
        _mosaic(26, 29, queries_rng), _mosaic(30, 30, queries_rng, True),
    ]
    # Source order stays reproducible. Native v2 preview handles private presentation order.
    keys = [tuple(map(tuple, grid)) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("constructed inputs must be distinct")
    return train, test


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"passes": _rng(seed, "settings").choice((1, 2))}
    passes = _settings(settings)
    train, test = input_bank(seed)
    def pair(grid):
        return {"input": [row[:] for row in grid], "output": solve(grid, passes)}
    return {
        "train": [pair(grid) for grid in train[:demos]],
        "test": [pair(grid) for grid in test[:queries]],
        "program_solution": program(settings),
    }
