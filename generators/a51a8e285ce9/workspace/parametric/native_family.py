"""Match D4 prototypes, then restore the prototype or transfer its transform."""
from __future__ import annotations
import hashlib
from pathlib import Path
import random

TASK_ID = "a51a8e285ce9"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"mode": ["prototype", "transfer"]}
DEFAULT = {"mode": "prototype"}
LIMITS = {"demos": [4, 6], "queries": [1, 4]}
NAMES = ("id", "rot90", "rot180", "rot270", "flip-h", "flip-v", "transpose", "anti-transpose")
TALL_NAMES = ("id", "rot180", "flip-h", "flip-v")
RENDER = "(support->grid (support-of match) q-color)"
CODE_EXPRESSION = "(first (filter (lambda (name) (equal? q-supp (transform-support-name name match))) transform-names))"
TRANSFER_RENDER = (
    "(let* ((other (if (equal? match (first protos)) (second protos) (first protos))) "
    "(code " + CODE_EXPRESSION + ")) "
    "(support->grid (transform-support-name code other) q-color))"
)
assert CANONICAL.count(RENDER) == 1
ALTERNATIVE = CANONICAL.replace(RENDER, TRANSFER_RENDER, 1)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    if type(settings["mode"]) is not str or settings["mode"] not in PARAMETERS["mode"]:
        raise ValueError("mode must be prototype or transfer")
    return settings["mode"]


def program(settings):
    return CANONICAL if _setting(settings) == "prototype" else ALTERNATIVE


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def transform(cells, name):
    functions = {
        "id": lambda r, c: (r, c), "rot90": lambda r, c: (c, -r),
        "rot180": lambda r, c: (-r, -c), "rot270": lambda r, c: (-c, r),
        "flip-h": lambda r, c: (r, -c), "flip-v": lambda r, c: (-r, c),
        "transpose": lambda r, c: (c, r), "anti-transpose": lambda r, c: (-c, -r),
    }
    if type(name) is not str or name not in functions:
        raise ValueError("unknown D4 transform")
    return normalize(functions[name](r, c) for r, c in cells)


def orbit(cells):
    return tuple(sorted({transform(cells, name) for name in NAMES}))


def _connected(cells):
    cells = set(cells)
    reached = {min(cells)}
    stack = list(reached)
    while stack:
        r, c = stack.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in reached:
                reached.add(point)
                stack.append(point)
    return reached == cells


def analyze(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("need a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors0..9")
    p = (w - 2) // 3
    if p < 1:
        raise ValueError("need three positive-width panels")
    if any(row[p] != 8 or row[2 * p + 1] != 8 for row in grid):
        raise ValueError("geometric separators must be full-height color8")
    if any(v for row in grid for v in row[3 * p + 2:]):
        raise ValueError("the quotient remainder must be a zero-only right tail")
    panels = []
    for index in range(3):
        left = index * (p + 1)
        cells = [(r, c) for r in range(h) for c in range(p) if grid[r][left + c]]
        colors = {grid[r][left + c] for r, c in cells}
        if len(colors) != 1:
            raise ValueError("each panel must contain one nonempty monochrome support")
        if not _connected(cells):
            raise ValueError("each support must be four-connected")
        panels.append({"cells": normalize(cells), "color": colors.pop()})
    if len({panel["color"] for panel in panels}) != 3:
        raise ValueError("all three support colors must be distinct")
    orbits = [orbit(panel["cells"]) for panel in panels[:2]]
    if any(len(o) != 8 for o in orbits):
        raise ValueError("both prototypes must have eight distinct D4 orientations")
    if set(orbits[0]).intersection(orbits[1]):
        raise ValueError("prototypes must be from distinct D4 classes")
    matches = [i for i, o in enumerate(orbits) if panels[2]["cells"] in o]
    if len(matches) != 1:
        raise ValueError("query must match exactly one prototype")
    index = matches[0]
    code = next(name for name in NAMES if transform(panels[index]["cells"], name) == panels[2]["cells"])
    return {"panels": panels, "match_index": index, "transform": code, "panel_w": p}


def _mask(cells, color):
    cells = set(normalize(cells))
    return [[color if (r, c) in cells else 0 for c in range(max(c for _, c in cells) + 1)]
            for r in range(max(r for r, _ in cells) + 1)]


def solve(grid, mode="prototype"):
    _setting({"mode": mode})
    a = analyze(grid)
    panels, index = a["panels"], a["match_index"]
    cells = panels[index]["cells"] if mode == "prototype" else transform(panels[1 - index]["cells"], a["transform"])
    return _mask(cells, panels[2]["color"])


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


_SMALL = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)),
)


def _colors(rng, core=None):
    if core == 0:
        a, b = rng.sample(range(1, 8), 2)
        return (8, a, b)
    if core == 1:
        a, b = rng.sample(range(1, 8), 2)
        return (a, 8, b)
    if core == 2:
        a, b = sorted(rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2))
        return (a, b, 8)
    return tuple(rng.sample([1, 2, 3, 4, 5, 6, 7, 9] if core == 3 else range(1, 10), 3))


def _scene(h, p, tail, protos, match, code, colors, rng):
    grid = [[0] * (3 * p + 2 + tail) for _ in range(h)]
    for row in grid:
        row[p] = row[2 * p + 1] = 8
    supports = [*protos, transform(protos[match], code)]
    for index, (cells, color) in enumerate(zip(supports, colors)):
        sh, sw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
        row, col = rng.randrange(h - sh + 1), rng.randrange(p - sw + 1)
        for r, c in cells:
            grid[row + r][index * (p + 1) + col + c] = color
    return grid


def _small(h, p, tail, rng, core=None):
    protos = [transform(shape, rng.choice(NAMES)) for shape in _SMALL]
    rng.shuffle(protos)
    if core is None:
        match, code = rng.randrange(2), rng.choice(NAMES)
    else:
        match, code = ((0, "rot90"), (1, "rot270"), (0, "flip-h"), (1, "transpose"))[core]
    return _scene(h, p, tail, protos, match, code, _colors(rng, core), rng)


def _tall_pair(h, w, rng):
    common_rows = {0, h - 1, h - 3, h - 2} | set(rng.sample(range(3, h - 3), (h - 6) // 2))
    spine = {(r, 0) for r in range(h)}
    return [normalize(spine | {(r, c) for r in common_rows | {extra} for c in range(w)})
            for extra in (1, 2)]


def _large(h, p, tail, sh, sw, rng):
    protos = [transform(shape, rng.choice(TALL_NAMES)) for shape in _tall_pair(sh, sw, rng)]
    rng.shuffle(protos)
    return _scene(h, p, tail, protos, rng.randrange(2), rng.choice(TALL_NAMES), _colors(rng), rng)


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    d, q = _rng(seed, "demos"), _rng(seed, "queries")
    demos = [_small(4, 4, 0, d, 0), _small(5, 5, 1, d, 1),
             _small(6, 6, 2, d, 2), _small(7, 7, 0, d, 3),
             _large(18, 8, 0, 15, 7, d), _large(30, 9, 1, 26, 8, d)]
    queries = [_small(3, 3, 0, q), _large(16, 7, 0, 14, 6, q),
               _large(24, 9, 0, 22, 8, q), _large(30, 9, 1, 24, 9, q)]
    return demos, queries


def generate(seed, settings=None, demos=4, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 4, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"mode": _rng(seed, "settings").choice(PARAMETERS["mode"])}
    mode = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, mode)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
