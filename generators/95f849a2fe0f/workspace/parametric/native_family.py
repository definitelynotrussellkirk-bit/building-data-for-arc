"""Independently align two colored shapes, then XOR or subtract in that frame."""
from __future__ import annotations
import hashlib
from pathlib import Path
import random

TASK_ID = "95f849a2fe0f"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"combine": ["xor", "difference"]}
DEFAULT = {"combine": "xor"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
XOR_EXPRESSION = "(append (filter (lambda (p) (not (member? p b))) a) (filter (lambda (p) (not (member? p a))) b))"
DIFFERENCE_EXPRESSION = "(filter (lambda (p) (not (member? p b))) a)"
assert CANONICAL.count(XOR_EXPRESSION) == 1
ALTERNATIVE = CANONICAL.replace(XOR_EXPRESSION, DIFFERENCE_EXPRESSION, 1)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"combine"}:
        raise ValueError("settings must contain exactly combine")
    if type(settings["combine"]) is not str or settings["combine"] not in PARAMETERS["combine"]:
        raise ValueError("combine must be xor or difference")
    return settings["combine"]


def program(settings):
    return CANONICAL if _setting(settings) == "xor" else ALTERNATIVE


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


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
    colors = sorted({v for row in grid for v in row if v})
    if len(colors) != 2:
        raise ValueError("need exactly two distinct nonzero colors")
    objects = []
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        reached = {min(cells)}
        stack = list(reached)
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in cells and point not in reached:
                    reached.add(point)
                    stack.append(point)
        if reached != cells:
            raise ValueError("each foreground color must form one four-connected component")
        objects.append(tuple(sorted(cells)))
    return tuple(objects)


def combine_cells(a, b, combine):
    _setting({"combine": combine})
    a, b = set(a), set(b)
    return a ^ b if combine == "xor" else a - b


def solve(grid, combine="xor"):
    a, b = analyze(grid)
    cells = combine_cells(normalize(a), normalize(b), combine)
    if not cells:
        return [[0]]
    return [[8 if (r, c) in cells else 0 for c in range(max(c for _, c in cells) + 1)]
            for r in range(max(r for r, _ in cells) + 1)]


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _colors(rng, teaching=False):
    return sorted(rng.sample([1, 2, 3, 4, 5, 6, 7, 9] if teaching else range(1, 10), 2))


def _paint(grid, cells, color, row, col):
    for r, c in cells:
        assert 0 <= r + row < len(grid) and 0 <= c + col < len(grid[0])
        assert grid[r + row][c + col] == 0
        grid[r + row][c + col] = color


_FRAME = {(r, c) for r in range(4) for c in range(4) if r in (0, 3) or c in (0, 3)}
CORE_PAIRS = (
    (_FRAME | {(1, 1), (1, 2), (1, 4)}, _FRAME | {(2, 1)}),
    ({(r, 0) for r in range(5)} | {(4, 1), (4, 2)},
     {(0, c) for c in range(6)} | {(1, 5), (2, 5), (2, 4), (2, 3), (2, 2)}),
)
_FREE = (
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
)


def _pose(shape, k):
    cells = [(r, -c if k >= 4 else c) for r, c in shape]
    for _ in range(k % 4):
        cells = [(c, -r) for r, c in cells]
    return normalize(cells)


def _core(which, rng):
    h, w = ((13, 20), (14, 23))[which]
    grid = [[0] * w for _ in range(h)]
    origins = (((1, 1), (7, 11)), ((6, 12), (1, 1)))[which]
    for cells, color, (row, col) in zip(CORE_PAIRS[which], _colors(rng, True), origins):
        _paint(grid, cells, color, row + rng.randrange(2), col + rng.randrange(2))
    return grid


def _comb_pair(h, w, rng):
    common = {(r, 0) for r in range(h)} | {(r, c) for r in (0, h - 1) for c in range(w)}
    a, b = set(common), set(common)
    roles = []
    for start in range(1, h - 1, 4):
        block = ["a", "b", "both", "neither"][:min(4, h - 1 - start)]
        rng.shuffle(block)
        roles.extend(block)
    for r, role in enumerate(roles, 1):
        if role in ("a", "both"):
            a.update((r, c) for c in range(w))
        if role in ("b", "both"):
            b.update((r, c) for c in range(w))
    return a, b


def _scene(h, w, a, b, rng, spread=False):
    grid = [[0] * w for _ in range(h)]
    entries = list(zip((a, b), _colors(rng)))
    rng.shuffle(entries)
    widths = [max(c for _, c in cells) + 1 for cells, _ in entries]
    space = w - sum(widths)
    assert space >= 1
    gap = space if spread else rng.randint(1, space)
    col = rng.randrange(space - gap + 1)
    for (cells, color), width in zip(entries, widths):
        height = max(r for r, _ in cells) + 1
        _paint(grid, cells, color, rng.randrange(h - height + 1), col)
        col += width + gap
    return grid


def _small(h, w, rng):
    return _scene(h, w, *[_pose(rng.choice(_FREE), rng.randrange(8)) for _ in range(2)], rng)


def _large(h, w, sh, sw, rng):
    return _scene(h, w, *_comb_pair(sh, sw, rng), rng, spread=True)


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    d, q = _rng(seed, "demos"), _rng(seed, "queries")
    demos = [_core(0, d), _core(1, d), [_colors(d)], _small(7, 12, d),
             _large(24, 27, 20, 10, d), _large(30, 30, 26, 12, d)]
    queries = [_small(4, 9, q), _large(17, 22, 14, 8, q),
               _large(26, 29, 22, 11, q), _large(30, 30, 23, 13, q)]
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"combine": _rng(seed, "settings").choice(PARAMETERS["combine"])}
    combine = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, combine)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
