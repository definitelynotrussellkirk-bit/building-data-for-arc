"""Fit two-color keys into border sockets; reflection parity controls recoloring."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

TASK_ID = "public_eval_a25697e4"
HOME = Path(__file__).resolve().parents[2]
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"reflection_colors": ["swap", "preserve"]}
DEFAULT = {"reflection_colors": "swap"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
SWAP_BINDING = "(swap-reflections #t)"
assert CANONICAL.count(SWAP_BINDING) == 1
ALTERNATIVE = CANONICAL.replace(SWAP_BINDING, "(swap-reflections #f)", 1)
MATRICES = ((1, 0, 0, 1), (0, 1, -1, 0), (-1, 0, 0, -1), (0, -1, 1, 0),
            (1, 0, 0, -1), (0, -1, -1, 0), (-1, 0, 0, 1), (0, 1, 1, 0))


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"reflection_colors"}
            or type(settings["reflection_colors"]) is not str
            or settings["reflection_colors"] not in PARAMETERS["reflection_colors"]):
        raise ValueError("settings must be exactly reflection_colors=swap or preserve")
    return settings["reflection_colors"]


def program(settings):
    return CANONICAL if _setting(settings) == "swap" else ALTERNATIVE


def _validate(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("need an exact-integer rectangular ARC grid with axes 1..30")
    counts = Counter(v for row in grid for v in row)
    ranking = counts.most_common()
    if len(ranking) < 2 or (len(ranking) > 1 and ranking[0][1] == ranking[1][1]):
        raise ValueError("need a unique modal background and foreground objects")
    return ranking[0][0]


def components(grid, background, allowed=None, colorblind=False):
    cells = set(allowed) if allowed is not None else {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != background}
    result = []
    while cells:
        first = min(cells); color = grid[first[0]][first[1]]
        group, pending = {first}, [first]
        cells.remove(first)
        while pending:
            r, c = pending.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in cells and (colorblind or grid[p[0]][p[1]] == color):
                    cells.remove(p); group.add(p); pending.append(p)
        result.append(tuple(sorted(group)))
    return result


def normalize(cells):
    cells = tuple(cells)
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def extract(grid):
    background = _validate(grid)
    h, w = len(grid), len(grid[0])
    groups = {}
    for cells in components(grid, background):
        edges = {edge for r, c in cells for edge, hit in enumerate((r == 0, c == w - 1, r == h - 1, c == 0)) if hit}
        if len(edges) > 1:
            raise ValueError("an anchored component cannot contact multiple canvas edges")
        if edges:
            key = next(iter(edges)), grid[cells[0][0]][cells[0][1]]
            groups.setdefault(key, set()).update(cells)
    if not 1 <= len(groups) <= 4:
        raise ValueError("need one to four edge sockets")
    anchor_cells = set().union(*groups.values())
    sockets = []
    for (edge, color), cells in sorted(groups.items()):
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        box = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if any(grid[r][c] not in (background, color) for r, c in box):
            raise ValueError("a socket rectangle may contain only its anchor color and background")
        hole = box - cells
        if not hole or any(grid[r][c] != background for r, c in hole):
            raise ValueError("each socket needs a nonempty background cutout")
        sockets.append({"edge": edge, "color": color, "cells": tuple(sorted(cells)), "hole": tuple(sorted(hole)), "box": (r0, c0, r1, c1)})
    free_cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != background} - anchor_cells
    pieces = components(grid, background, free_cells, colorblind=True)
    if len(pieces) != len(sockets):
        raise ValueError("need exactly one free two-color piece per socket")
    if any(len({grid[r][c] for r, c in cells}) != 2 for cells in pieces):
        raise ValueError("each free piece must have exactly two colors")
    return {"grid": grid, "background": background, "height": h, "width": w,
            "sockets": sockets, "pieces": pieces, "anchor_cells": anchor_cells, "source_cells": free_cells}


def candidates(parts, key_index, check_collision=True):
    grid, cells = parts["grid"], parts["pieces"][key_index]
    colors = sorted({grid[r][c] for r, c in cells})
    choices = []
    for si, socket in enumerate(parts["sockets"]):
        hole = socket["hole"]
        for color in colors:
            head = [(r, c) for r, c in cells if grid[r][c] == color]
            if len(head) != len(hole):
                continue
            for mi, (a, b, c, d) in enumerate(MATRICES):
                transform = lambda p: (a * p[0] + b * p[1], c * p[0] + d * p[1])
                changed = [transform(p) for p in head]
                if normalize(changed) != normalize(hole):
                    continue
                dr = min(r for r, _ in hole) - min(r for r, _ in changed)
                dc = min(c for _, c in hole) - min(c for _, c in changed)
                painted = tuple(sorted((transform(p)[0] + dr, transform(p)[1] + dc, grid[p[0]][p[1]]) for p in cells))
                if not all(0 <= r < parts["height"] and 0 <= col < parts["width"] for r, col, _ in painted):
                    continue
                if check_collision and {(r, col) for r, col, _ in painted} & parts["anchor_cells"]:
                    continue
                choices.append({"socket_index": si, "key_index": key_index, "reflected": mi >= 4,
                                "matrix_index": mi, "head_color": color, "colors": colors,
                                "cells": painted, "translation": (dr, dc)})
    return choices


def _plan(parts):
    choices = [candidates(parts, i) for i in range(len(parts["pieces"]))]
    solutions = []
    def search(index, used, occupied, selected):
        if len(solutions) > 1:
            return
        if index == len(choices):
            solutions.append(selected)
            return
        for candidate in choices[index]:
            positions = {(r, c) for r, c, _ in candidate["cells"]}
            si = candidate["socket_index"]
            if si not in used and not positions & occupied:
                search(index + 1, used | {si}, occupied | positions, selected + [candidate])
    search(0, set(), set(), [])
    if len(solutions) != 1:
        raise ValueError("task grammar requires exactly one complete collision-free placement assignment")
    return solutions[0]


def plan(grid):
    return _plan(extract(grid))


def solve(grid, reflection_colors="swap"):
    _setting({"reflection_colors": reflection_colors})
    parts = extract(grid)
    placements = _plan(parts)
    output = [[parts["background"] if (r, c) in parts["source_cells"] else v for c, v in enumerate(row)] for r, row in enumerate(grid)]
    for placement in placements:
        first, second = placement["colors"]
        swap = reflection_colors == "swap" and placement["reflected"]
        for r, c, color in placement["cells"]:
            output[r][c] = (second if color == first else first) if swap else color
    return output


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


@lru_cache(maxsize=2)
def _templates(name):
    source = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("socket_" + name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _single(h, w, reflected):
    templates = _templates("scene_templates")
    grid = [[0] * w for _ in range(h)]
    holes = {(0, 1), (0, 2), (0, 3), (1, 1), (2, 1)}
    templates._socket(grid, 0, (h - 3, 2), 3, 5, holes, 9)
    head = {(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)}
    tail = {(-1, 0), (-2, 0), (-2, -1), (-3, -1), (-3, -2), (-4, -2)}
    origin = (1, w - 6) if reflected else (1, w - 8)
    templates._key(grid, 0, origin, head, tail, (2, 6), 2 if reflected else 1, reflected)
    return grid


def _augment(grid, rng):
    palette = list(range(10)); rng.shuffle(palette)
    grid = [[palette[v] for v in row] for row in grid]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    d, q = _rng(seed, "demonstrations"), _rng(seed, "queries")
    core, large = _templates("scene_templates"), _templates("large_templates")
    demos = [core.core0(), core.core1(), _single(10, 14, False), _single(14, 18, True),
             large.large_scene(26, 28, 1), large.large_scene(30, 30, 0)]
    queries = [_single(12, 17, True), _single(16, 21, False),
               large.large_scene(24, 28, 0), large.large_scene(30, 30, 1)]
    demos = [_augment(g, d) for g in demos]
    queries = [_augment(g, q) for g in queries]
    q.shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"reflection_colors": _rng(seed, "settings").choice(PARAMETERS["reflection_colors"])}
    mode = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, mode)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
