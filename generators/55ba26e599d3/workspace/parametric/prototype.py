"""Episode-fixed line-only / first input-blue component rule family.

Labels here are claims. Native promotion independently executes every Racket
program and checks those claims in its protected worker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

REACHES = ("line_only", "first_blue_component")
_HOME = Path(__file__).resolve().parent
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"reach"}:
        raise ValueError("settings must contain exactly reach")
    if settings["reach"] not in REACHES:
        raise ValueError("reach must be line_only or first_blue_component")
    return settings["reach"]


def program(settings):
    reach = _settings(settings)
    return (_HOME / ("canonical.rkt" if reach == "line_only" else "first_blue_component.rkt")).read_text()


def _endpoints(grid):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]


def line_cells(first, second):
    """Canonical floating operation order; do not reassociate i * delta / steps."""
    r1, c1 = first
    dr, dc = second[0] - r1, second[1] - c1
    steps = max(abs(dr), abs(dc))
    return [(round(r1 + (float(i) / float(steps) if steps else 0.0) * dr),
             round(c1 + (float(i) / float(steps) if steps else 0.0) * dc))
            for i in range(steps + 1)]


def component(grid, start):
    """Four-connected INPUT blue component, with no use of the painted grid."""
    cells, pending = {start}, [start]
    while pending:
        r, c = pending.pop()
        for dr, dc in _CARDINAL:
            p = (r + dr, c + dc)
            if (0 <= p[0] < len(grid) and 0 <= p[1] < len(grid[0])
                    and grid[p[0]][p[1]] == 1 and p not in cells):
                cells.add(p)
                pending.append(p)
    return cells


def solve_python(grid, reach):
    if reach not in REACHES:
        raise ValueError("invalid reach")
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or v not in (0, 1, 2) for row in grid for v in row)):
        raise ValueError("input must be a rectangular grid of exact integer colors 0, 1, 2")
    endpoints = _endpoints(grid)
    if len(endpoints) != 2:
        raise ValueError("input requires exactly two red endpoints")
    path = line_cells(*endpoints)
    output = [row[:] for row in grid]
    for r, c in path:
        output[r][c] = {0: 2, 1: 3, 2: 2}[grid[r][c]]
    if reach == "first_blue_component":
        first_hit = next(((r, c) for r, c in path if grid[r][c] == 1), None)
        if first_hit is not None:
            for r, c in component(grid, first_hit):
                output[r][c] = 3
    return output


def _rng(seed, split, index):
    digest = hashlib.sha256(f"55ba26e599d3:first-hit:v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _neighbors(cells):
    return {(r + dr, c + dc) for r, c in cells for dr, dc in _CARDINAL}


def _grow(anchor, size, h, w, path, blocked, rng):
    cells = {anchor}
    while len(cells) < size:
        frontier = sorted(p for p in _neighbors(cells) - cells - path - blocked
                          if 0 <= p[0] < h and 0 <= p[1] < w)
        if not frontier:
            raise AssertionError("constructed arm lacks room")
        cells.add(rng.choice(frontier))
    return cells


def _scene(h, w, endpoints, first_size, second_size, rng):
    """Construct two separate touched components, then texture their protected exterior."""
    path = line_cells(*sorted(endpoints))
    path_set = set(path)
    a, b = path[max(2, len(path) // 4)], path[min(len(path) - 3, 3 * len(path) // 4)]
    first = _grow(a, first_size, h, w, path_set, {b} | _neighbors({b}), rng)
    second = _grow(b, second_size, h, w, path_set, first | _neighbors(first), rng)
    # A diagonal-only blue witness makes 8-neighbor expansion visibly wrong.
    diagonal = sorted({(r + dr, c + dc) for r, c in first for dr in (-1, 1) for dc in (-1, 1)}
                      - first - _neighbors(first) - path_set - second - _neighbors(second))
    diagonal = [p for p in diagonal if 0 <= p[0] < h and 0 <= p[1] < w]
    if not diagonal:
        raise AssertionError("constructed component lacks diagonal-only witness")
    witness = rng.choice(diagonal)
    protected = path_set | first | second | _neighbors(first | second)
    grid = [[int((r, c) not in protected and rng.random() < 0.45) for c in range(w)] for r in range(h)]
    for r, c in first | second | {witness}:
        grid[r][c] = 1
    for r, c in endpoints:
        grid[r][c] = 2
    return grid


def _demo(seed, index):
    rng = _rng(seed, "demonstrations", index)
    h, w = 10 + 2 * index + rng.randrange(2), 13 + index + rng.randrange(2)
    if index == 0:
        endpoints, sizes = ((0, 0), (h - 1, w - 1)), (3, 7)
    elif index == 1:
        endpoints, sizes = ((1, w - 3), (h - 2, 3)), (8, 3)
    else:
        endpoints, sizes = ((0, w - 1), (h - 1, 0)), (4 + index % 3, 3 + index % 2)
    return _scene(h, w, endpoints, *sizes, rng)


def _query(seed, index):
    rng = _rng(seed, "queries", index)
    if index == 0:
        return _scene(30, 30, ((0, rng.randrange(2)), (29, 21 + rng.randrange(8))), 9, 5, rng)
    if index == 1:
        return _scene(12, 23, ((0, 22), (11, 0)), 4, 8, rng)
    if index == 2:
        return _scene(25, 11, ((0, 1), (24, 9)), 7, 4, rng)
    return _scene(19, 27, ((2, 24), (16, 2)), 5, 9, rng)


def generate(seed, settings, demos=3, queries=4):
    reach = _settings(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2**63-1]")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in [2, 6]")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in [1, 4]")
    def pair(inp):
        return {"input": inp, "output": solve_python(inp, reach)}
    return {"train": [pair(_demo(seed, i)) for i in range(demos)],
            "test": [pair(_query(seed, i)) for i in range(queries)],
            "program_solution": program(settings)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--reach", choices=REACHES, default="first_blue_component")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, {"reach": args.reach}, args.demos, args.queries), separators=(",", ":")))
