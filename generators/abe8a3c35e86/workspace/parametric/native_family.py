"""Execute one or two state-dependent passes of the exact pivot authority."""
from __future__ import annotations
import hashlib
from pathlib import Path
import random

TASK_ID = "abe8a3c35e86"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"passes": [1, 2]}
DEFAULT = {"passes": 1}
LIMITS = {"demos": [4, 6], "queries": [1, 4]}
assert CANONICAL.startswith("(rule!") and CANONICAL.endswith(")")
BODY = CANONICAL[len("(rule!"):-1].strip()
STAGE_BINDING = "(stage " + BODY + ")"
SECOND_STAGE = "(let ((g stage)) " + BODY + ")"
ALTERNATIVE = "(rule! (let* (" + STAGE_BINDING + ") " + SECOND_STAGE + "))"


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"passes"}:
        raise ValueError("settings must contain exactly passes")
    _integer(settings["passes"], 1, 2, "passes")
    return settings["passes"]


def program(settings):
    return CANONICAL if _setting(settings) == 1 else ALTERNATIVE


def _validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("need a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors0..9")
    if sum(v == 9 for row in grid for v in row) != 1:
        raise ValueError("exactly one color9 pivot is required")


def _parts(grid):
    pivot = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    return pivot, cells


def axis(grid):
    """Infer a branch afresh from every non0/non9 cell in this supplied state."""
    _validate_grid(grid)
    (pr, pc), cells = _parts(grid)
    if not cells:
        return None
    if all(c < pc for _, c in cells) or all(c > pc for _, c in cells):
        return "column"
    if all(r < pr for r, _ in cells) or all(r > pr for r, _ in cells):
        return "row"
    return None


def reflect(grid):
    """One canonical pass, preserving source pixels and clipping each copy."""
    selected = axis(grid)
    out = [row[:] for row in grid]
    if selected is None:
        return out
    (pr, pc), cells = _parts(grid)
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        rr, cc = (r, 2 * pc - c) if selected == "column" else (2 * pr - r, c)
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = grid[r][c]
    return out


def solve(grid, passes=1):
    _setting({"passes": passes})
    first = reflect(grid)
    return first if passes == 1 else reflect(first)


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(h, w, pivot, groups, rng):
    grid = [[0] * w for _ in range(h)]
    grid[pivot[0]][pivot[1]] = 9
    for color, cells in zip(rng.sample(range(1, 9), len(groups)), groups):
        for r, c in cells:
            assert grid[r][c] == 0
            grid[r][c] = color
    return _flip(grid, rng)


def _flip(grid, rng):
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def _core0(rng):
    # Both predicates true, with partial clipping on each axis. The missing
    # (1,2) makes clamp-to-boundary observably wrong rather than overwritten.
    return _scene(13, 17, (8, 9), [
        [(1, 1), (1, 3), (1, 4), (2, 1), (2, 4), (3, 4), (4, 4), (5, 4), (5, 5), (6, 5), (7, 5)],
        [(2, 6), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7)],
        [(5, 1), (5, 2), (6, 2)],
    ], rng)


def _core1(rng):
    # Every column copy clips. Legal row copies exist, but neither pass may
    # take that lower-priority branch while the original side remains true.
    return _scene(10, 12, (6, 1), [
        [(2, 3), (2, 4), (3, 4), (4, 4), (4, 5)],
        [(3, 7), (4, 7), (4, 8)], [(2, 10)],
    ], rng)


def _core2(rng):
    # Joint geometry straddles the pivot column although individual colors
    # can lie wholly on one side. Some row copies clip and others survive.
    return _scene(12, 15, (7, 7), [
        [(1, 2), (2, 2), (3, 2), (3, 3), (3, 4), (4, 4), (5, 4)],
        [(3, 10), (4, 10), (4, 11), (5, 11), (5, 12), (6, 12)],
        [(2, 7), (3, 7), (4, 7), (4, 8)],
    ], rng)


def _core3(rng):
    # Neither side: identity is essential. A false unconditional row fallback
    # changes this asymmetric input and is refuted before queries are scored.
    return _scene(8, 11, (3, 5), [
        [(0, 1), (1, 1), (2, 1), (2, 2), (5, 8), (6, 8)],
        [(1, 7), (1, 8), (4, 3), (5, 3), (5, 4)], [(7, 10), (6, 5)],
    ], rng)


def _dense(h, w, kind, rng):
    """Substantive side-constrained content; empty mirror space is functional."""
    if kind == "column":
        pr, pc = h // 2 - 1, w // 2 + 1
        region = ((r, c) for r in range(h) for c in range(pc))
    elif kind == "row":
        pr, pc = h // 2 + 1, w // 2
        region = ((r, c) for r in range(pr) for c in range(w))
    elif kind == "quadrant":
        pr, pc = h // 2, w // 2
        region = ((r, c) for r in range(pr) for c in range(pc))
    elif kind == "clipped":
        pr, pc = h // 2 + 2, 3
        region = ((r, c) for r in range(pr) for c in range(7, w))
    else:
        raise ValueError(f"unknown scene kind {kind}")
    grid = [[0] * w for _ in range(h)]
    palette = rng.sample(range(1, 9), 4)
    salt = rng.randrange(7)
    shift = rng.randrange(4)
    for r, c in region:
        if (r * 3 + c * 5 + salt) % 7:
            grid[r][c] = palette[(r // 3 + c // 4 + shift) % 4]
    grid[pr][pc] = 9
    return _flip(grid, rng)


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    d, q = _rng(seed, "demos"), _rng(seed, "queries")
    demos = [_core0(d), _core1(d), _core2(d), _core3(d), [[9]], _dense(30, 30, "column", d)]
    queries = [_dense(7, 9, "quadrant", q), _dense(14, 19, "row", q),
               _dense(23, 27, "column", q), _dense(30, 30, "clipped", q)]
    q.shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=4, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 4, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"passes": _rng(seed, "settings").choice(PARAMETERS["passes"])}
    passes = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, passes)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
