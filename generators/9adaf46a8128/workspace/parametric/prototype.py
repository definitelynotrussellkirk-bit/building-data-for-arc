"""Native two-setting family for transformed-template stamping.

``per_marker`` is the exact canonical rule. ``leader_composed`` first uses
its row-major first marker to transform the extracted template, then applies
each marker's transform to that input-dependent intermediate before stamping.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

TASK_ID = "9adaf46a8128"
HERE = Path(__file__).resolve().parent
MODES = ("per_marker", "leader_composed")

_TEMPLATES = (
    ((0, 0), (1, 0), (2, 0), (2, 1), (0, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2), (3, 0), (3, 2)),
    ((0, 0), (0, 2), (1, 0), (2, 0), (2, 1), (3, 2)),
    ((0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (3, 1), (3, 2)),
)
_DEMO_PROFILES = ((12, 15), (14, 18), (16, 20), (20, 22), (24, 26), (28, 30))
_QUERY_PROFILES = ((13, 17), (18, 23), (24, 27), (30, 30))
_DEMO_ROLES = (
    (2, 1, 3, 4), (4, 2, 1, 3), (3, 4, 2, 1),
    (2, 4, 1, 3, 2), (4, 1, 2, 3, 4, 2), (3, 2, 4, 1, 3, 2),
)
_QUERY_ROLES = (
    (4, 1, 3, 2), (2, 3, 4, 1, 2),
    (3, 1, 4, 2, 3, 1), (4, 2, 1, 3, 4, 2, 1, 3),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"transform_mode"}
            or type(settings["transform_mode"]) is not str
            or settings["transform_mode"] not in MODES):
        raise ValueError("settings must contain exactly a declared transform_mode")
    return settings["transform_mode"]


def program(settings):
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "per_marker" else "leader_composed.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def transform(grid, marker):
    if marker == 1:
        return copy.deepcopy(grid)
    if marker == 2:
        return _rotate_cw(grid)
    if marker == 3:
        return _rotate_180(grid)
    if marker == 4:
        return _transpose(grid)
    raise ValueError("marker must be 1..4")


def _validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors")


def analyze(grid):
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    separators = [r for r, row in enumerate(grid) if all(v == 5 for v in row)]
    if len(separators) != 1:
        raise ValueError("grid must have exactly one full color-5 separator")
    sep = separators[0]
    cells = [(r, c) for r in range(sep) for c in range(w) if grid[r][c] != 0]
    if not cells:
        raise ValueError("missing template")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    template = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    markers = [(r - sep - 1, c, grid[r][c])
               for r in range(sep + 1, h) for c in range(w)
               if grid[r][c] in (1, 2, 3, 4)]
    if not markers:
        raise ValueError("missing command markers")
    leader = markers[0]
    intermediate = transform(template, leader[2])
    return {
        "separator": sep,
        "template": template,
        "markers": [list(row) for row in markers],
        "leader_position": [leader[0], leader[1]],
        "leader_marker": leader[2],
        "intermediate_template": intermediate,
    }


def solve(grid, settings):
    mode = _mode(settings)
    facts = analyze(grid)
    base = facts["template"] if mode == "per_marker" else facts["intermediate_template"]
    out_h = len(grid) - facts["separator"] - 1
    width = len(grid[0])
    out = [[0] * width for _ in range(out_h)]
    for row, col, marker in facts["markers"]:
        pattern = transform(base, marker)
        rr0 = row - len(pattern) // 2
        cc0 = col - len(pattern[0]) // 2
        for i, values in enumerate(pattern):
            for j, value in enumerate(values):
                rr, cc = rr0 + i, cc0 + j
                if value != 0 and 0 <= rr < out_h and 0 <= cc < width:
                    out[rr][cc] = value
    return out


def _rng(seed, split, index):
    raw = f"9ada-parametric-v1:{seed}:{split}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _positions(h, w, sep, count, rng):
    bottom_h = h - sep - 1
    rows = sorted({1, max(1, bottom_h // 2), max(1, bottom_h - 2)})
    cols = sorted({1, max(1, w // 2), max(1, w - 2)})
    candidates = [(r, c) for r in rows for c in cols]
    leader = candidates[0]
    followers = candidates[1:]
    rng.shuffle(followers)
    chosen = [leader] + followers[:count - 1]
    if len(chosen) != count or len(set(chosen)) != count:
        raise RuntimeError("could not place distinct markers")
    return chosen


def scene(seed, split, index):
    if split == "demo":
        _integer(index, 0, 5, "demo index")
        h, w = _DEMO_PROFILES[index]
        roles = _DEMO_ROLES[index]
    elif split == "query":
        _integer(index, 0, 3, "query index")
        h, w = _QUERY_PROFILES[index]
        roles = _QUERY_ROLES[index]
    else:
        raise ValueError("split must be demo or query")
    rng = _rng(seed, split, index)
    cells = _TEMPLATES[index % len(_TEMPLATES)]
    th = max(r for r, _ in cells) + 1
    tw = max(c for _, c in cells) + 1
    sep = th + 2
    grid = [[0] * w for _ in range(h)]
    grid[sep] = [5] * w
    tr = 1 if index % 2 == 0 else max(0, sep - th - 1)
    tc = rng.randint(0, max(0, w - tw))
    for r, c in cells:
        grid[tr + r][tc + c] = 2
    for (r, c), role in zip(_positions(h, w, sep, len(roles), rng), roles):
        grid[sep + 1 + r][c] = role
    if split == "query" and index == 3:
        grid[sep + 1][w - 1] = 2
        grid[h - 1][0] = 3
    analyze(grid)
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _mode(settings)
    result = {"program_solution": program(settings), "train": [], "test": []}
    for name, split, count in (("train", "demo", demos), ("test", "query", queries)):
        for index in range(count):
            grid = scene(seed, split, index)
            result[name].append({"input": grid, "output": solve(grid, settings)})
    all_inputs = [repr(pair["input"]) for pair in result["train"] + result["test"]]
    if len(all_inputs) != len(set(all_inputs)):
        raise RuntimeError("duplicate input within episode")
    return result
