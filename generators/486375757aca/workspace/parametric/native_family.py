"""Exact seeded-frame fill followed by optional largest-component recoloring."""
from pathlib import Path
import random

TASK_ID = "486375757aca"
DEFAULT = {"post": "none"}
SETTINGS = ({"post": "none"}, {"post": "largest_to_8"})
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _setting(settings):
    if settings is None:
        return "none"
    if type(settings) is not dict or set(settings) != {"post"}:
        raise ValueError("settings must name exactly post")
    value = settings["post"]
    if type(value) is not str or value not in ("none", "largest_to_8"):
        raise ValueError("post must be none or largest_to_8")
    return value


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def components(grid, colors=None):
    """Monochromatic cardinal components, discovered in row-major order."""
    allowed = set(range(1, 10) if colors is None else colors)
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color not in allowed or (row, column) in seen:
                continue
            cells, stack = set(), [(row, column)]
            seen.add((row, column))
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in CARDINAL:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width and (rr, cc) not in seen
                            and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            result.append({"color": color, "cells": frozenset(cells),
                           "bbox": (min(r for r, c in cells), min(c for r, c in cells),
                                    max(r for r, c in cells), max(c for r, c in cells))})
    return result


def analyze(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30 or
            type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30):
        raise ValueError("native grid axes must be 3..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("native grid must be rectangular exact integer colors 0..9")
    blue = components(grid, {1})
    if not blue:
        raise ValueError("at least one blue component is required")
    for obj in blue:
        top, left, bottom, right = obj["bbox"]
        seeds = [(row, col, grid[row][col])
                 for row in range(top + 1, bottom) for col in range(left + 1, right)
                 if grid[row][col] not in (0, 1)]
        if not seeds:
            raise ValueError("every blue component bbox needs a nonempty seeded interior")
        obj["seeds"] = seeds
    return blue


def fill(grid):
    # Both object extraction and every seed read are frozen before any writes.
    blue = analyze(grid)
    output = [row[:] for row in grid]
    for obj in blue:
        top, left, bottom, right = obj["bbox"]
        color = obj["seeds"][-1][2]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = color
    return output


def transform(grid, settings=None):
    post = _setting(settings)
    output = fill(grid)
    if post == "largest_to_8":
        groups = components(output, range(2, 10))
        maximum = max(len(obj["cells"]) for obj in groups)
        selected = [obj for obj in groups if len(obj["cells"]) == maximum]
        for obj in selected:
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def program(settings=None):
    post = _setting(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if post == "none":
        return canonical
    stripped = canonical.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")") or stripped.count("(rule!") != 1:
        raise ValueError("expected one exact selected canonical rule wrapper")
    body = stripped[len("(rule!"):-1].strip()
    return """(rule!
  (let* ((filled %s)
         (groups (filter (lambda (obj) (not (member (obj-color obj) (list 0 1))))
                         (objects filled 0)))
         (maximum (apply max (map (lambda (obj) (length (obj-cells obj))) groups)))
         (chosen (filter (lambda (obj) (= (length (obj-cells obj)) maximum)) groups)))
    (for*/fold ([out filled]) ([obj (in-list chosen)] [p (in-list (obj-cells obj))])
      (set-cell out (first p) (second p) 8))))""" % body


def _frame(grid, top, left, bottom, right):
    if not (0 <= top < bottom < len(grid) and 0 <= left < right < len(grid[0])):
        raise ValueError("frame bounds must be inside the canvas")
    for row in range(top, bottom + 1):
        grid[row][left] = grid[row][right] = 1
    for col in range(left, right + 1):
        grid[top][col] = grid[bottom][col] = 1


def _seed(grid, row, col, color):
    if grid[row][col] != 0 or not 2 <= color <= 9:
        raise ValueError("constructed seeds need an unused cell and a non-blue color")
    grid[row][col] = color


def _core_a():
    grid = [[0] * 26 for _ in range(17)]
    for bounds in ((1, 1, 5, 5), (3, 6, 8, 10), (1, 14, 7, 22),
                   (9, 11, 11, 17), (13, 0, 15, 25)):
        _frame(grid, *bounds)
    seeds = [(2, 2, 2), (7, 9, 3), (4, 21, 7), (5, 20, 2), (6, 19, 4),
             (10, 12, 4), (10, 16, 6), (14, 24, 8)]
    seeds += [(row, col, 6) for row in (2, 3) for col in (15, 16, 17)]
    for row, col, color in seeds:
        _seed(grid, row, col, color)
    return grid


def _core_b():
    grid = [[0] * 26 for _ in range(21)]
    for bounds in ((0, 0, 10, 10), (3, 3, 7, 7), (0, 14, 9, 24)):
        _frame(grid, *bounds)
    for row, col, color in ((6, 6, 3), (9, 9, 4), (8, 23, 2)):
        _seed(grid, row, col, color)
    for row in range(12, 19):
        for col in range(10):
            _seed(grid, row, col, 3)
    for row in range(12, 20):
        for col in range(14, 23):
            _seed(grid, row, col, 5)
    return grid


def _bounds(length, count, rng):
    available = length - count + 1
    base, extra = divmod(available, count)
    widths = [base + (index < extra) for index in range(count)]
    rng.shuffle(widths)
    if min(widths) < 3:
        raise ValueError("mosaic tiles must have nonempty interiors")
    result, start = [], 0
    for width in widths:
        result.append((start, start + width - 1))
        start += width + 1
    return result


def _mosaic(height, width, nr, nc, rng):
    grid = [[0] * width for _ in range(height)]
    rows, columns = _bounds(height, nr, rng), _bounds(width, nc, rng)
    boxes = [(top, left, bottom, right) for top, bottom in rows for left, right in columns]
    for bounds in boxes:
        _frame(grid, *bounds)
    edges = []
    if nr == nc == 4:
        for row in (0, 2):
            for col in (0, 2):
                edges += [((row, col), (row, col + 1)), ((row, col + 1), (row + 1, col + 1))]
    elif nr >= 2 and nc >= 2:
        edges = [((0, 0), (0, 1)), ((0, 1), (1, 1))]
        if nr >= 3 and nc >= 3:
            edges += [((1, 2), (2, 2)), ((2, 0), (2, 1))]
        elif nc >= 3:
            edges += [((0, 2), (1, 2))]
    for (r0, c0), (r1, c1) in edges:
        if r0 == r1:
            row, col = sum(rows[r0]) // 2, columns[c0][1] + 1
        else:
            row, col = rows[r0][1] + 1, sum(columns[c0]) // 2
        grid[row][col] = 1
    for top, left, bottom, right in boxes:
        interior = [(r, c) for r in range(top + 1, bottom) for c in range(left + 1, right)]
        count = rng.randint(min(2, len(interior)), min(5, len(interior)))
        for row, col in rng.sample(interior, count):
            _seed(grid, row, col, rng.randrange(2, 10))
    return grid


def _vary(grid, rng, *, core=False):
    colors = [2, 3, 4, 5, 6, 7, 9]
    shuffled = colors[:]
    rng.shuffle(shuffled)
    palette = dict(zip(colors, shuffled))
    out = [[palette.get(value, value) for value in row] for row in grid]
    if core:
        occupied = [(r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value]
        dr = rng.randint(-min(r for r, c in occupied), len(out) - 1 - max(r for r, c in occupied))
        dc = rng.randint(-min(c for r, c in occupied), len(out[0]) - 1 - max(c for r, c in occupied))
        shifted = [[0] * len(out[0]) for row in out]
        for row, col in occupied:
            shifted[row + dr][col + dc] = out[row][col]
        return shifted
    if rng.randrange(2):
        out = [row[::-1] for row in out]
    if rng.randrange(2):
        out = out[::-1]
    if rng.randrange(2):
        out = [list(row) for row in zip(*out)]
    return out


def inputs(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    rng = random.Random(seed ^ 0x486375)
    demos = [_vary(_core_a(), rng, core=True), _vary(_core_b(), rng, core=True)]
    demos += [_vary(_mosaic(h, w, nr, nc, rng), rng)
              for h, w, nr, nc in ((3, 3, 1, 1), (13, 17, 2, 3), (24, 27, 3, 3), (30, 30, 3, 3))]
    queries = [_vary(_mosaic(h, w, nr, nc, rng), rng)
               for h, w, nr, nc in ((5, 9, 1, 2), (18, 23, 2, 3), (27, 29, 3, 3), (30, 30, 4, 4))]
    random.Random(seed ^ 0xF2A4E).shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = (dict(random.Random(seed ^ 0xA11CE).choice(SETTINGS)) if settings is None
              else dict(settings) if type(settings) is dict else settings)
    _setting(chosen)
    demo_inputs, query_inputs = inputs(seed)
    def pairs(grids):
        return [{"input": grid, "output": transform(grid, chosen)} for grid in grids]
    return {"train": pairs(demo_inputs[:demos]), "test": pairs(query_inputs[:queries]),
            "program_solution": program(chosen), "settings": dict(chosen)}
