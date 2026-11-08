"""Native mode-selection followed by input-derived component-count rotation.

The original rotation prototype remains intact.  ``canonical`` reuses its
exact canonical program.  ``modal_components`` keeps the selected color's
mask, counts its four-connected components, and rotates its original glyph
clockwise by (count - 1) modulo four.  Generated inputs have sides 8..30,
unique nonzero mode 1/2/3, at least five zeros, and 5..6 visible colors.

Two histogram-matched demonstrations teach the composition using one modal
color; additional demonstrations introduce the other T/L and then the plus.
Queries only use demonstrated classes.  Their independent stream always has
the same prefix, including when only one query is requested.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
import math
from pathlib import Path
import random
import sys


HERE = Path(__file__).resolve().parent
VERSION = "1.0.0"
SETTINGS = ({"orientation": "canonical"}, {"orientation": "modal_components"})


def _load_legacy():
    name = "_49754d8fa42e_legacy_rotation"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / "prototype.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


_LEGACY = _load_legacy()


def _orientation(settings):
    if type(settings) is not dict or set(settings) != {"orientation"}:
        raise ValueError("settings must contain exactly orientation")
    value = settings["orientation"]
    if type(value) is not str or value not in ("canonical", "modal_components"):
        raise ValueError("orientation must be canonical or modal_components")
    return value


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")


def _grid_shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid sides must be in 1..30")
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer colors 0..9")
    return h, w


def mode_color(grid):
    """Validate the composition domain and return its unique nonzero mode."""
    h, w = _grid_shape(grid)
    if min(h, w) < 8:
        raise ValueError("composition input sides must be in 8..30")
    counts = Counter(value for row in grid for value in row)
    if counts[0] < 5 or not 2 <= len(counts) <= 6:
        raise ValueError("need at least five zeros and 2..6 visible colors")
    ranked = sorted((count, color) for color, count in counts.items() if color)
    if not ranked or ranked[-1][0] < 5 or ranked[-1][1] not in (1, 2, 3):
        raise ValueError("need at least five cells of modal color 1, 2, or 3")
    if len(ranked) > 1 and ranked[-2][0] == ranked[-1][0]:
        raise ValueError("nonzero mode must be unique")
    return ranked[-1][1]


def components(grid, diagonal=False):
    """Return row-major same-color component records, excluding literal zero."""
    h, w = _grid_shape(grid)
    if type(diagonal) is not bool:
        raise ValueError("diagonal must be a boolean")
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append([rr, cc])
                for dr, dc in deltas:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append({"color": color, "cells": sorted(cells), "size": len(cells)})
    return result


def transform(grid, settings):
    """Python authoring mirror; native qualification supplies Racket labels."""
    orientation = _orientation(settings)
    color = mode_color(grid)
    turns = 0
    if orientation == "modal_components":
        selected = [[value if value == color else 0 for value in row] for row in grid]
        turns = (len(components(selected)) - 1) % 4
    return _LEGACY.rotated_glyph(color, turns)


@lru_cache(maxsize=1)
def _canonical_program():
    return _LEGACY.program_for(0)


def program(settings):
    """Return one complete program; the canonical setting is byte-identical."""
    if _orientation(settings) == "canonical":
        return _canonical_program()
    clauses = [f"((= color {color}) {_LEGACY._racket_grid(_LEGACY.rotated_glyph(color, 0))})"
               for color in (1, 2, 3)]
    return "\n".join([
        "(rule! (lambda (g)",
        "  (let* ((color (mode g 0))",
        "         (selected (keep-only g color 0))",
        "         (component-count (length (objects selected 0)))",
        "         (turns (modulo (- component-count 1) 4))",
        "         (glyph (cond " + " ".join(clauses),
        "                      (else (list (list 0 0 0) (list 0 0 0) (list 0 0 0))))))",
        "    (cond ((= turns 0) glyph)",
        "          ((= turns 1) (rotate-cw glyph))",
        "          ((= turns 2) (rotate-180 glyph))",
        "          (else (rotate-ccw glyph))))))",
    ])


def _rng(seed, label):
    digest = hashlib.sha256(f"49754d8fa42e:composition:{VERSION}:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _dihedral(grid, code):
    result = [row[:] for row in grid]
    if code >= 4:
        result = [row[::-1] for row in result]
    for _ in range(code % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _endpoints(grid):
    values = [value for row in grid for value in row if value]
    return values[0], values[-1]


def _endpoint_contrast(grids, color):
    ends = [_endpoints(grid) for grid in grids]
    complement = [min({1, 2, 3} - set(pair), default=0) for pair in ends]
    return (any(first != color for first, _ in ends)
            and any(last != color for _, last in ends)
            and any(color not in pair for pair in ends)
            and any(value != color for value in complement))


def _teaching_pair(seed, color):
    # The 9-cell distractor beats every modal 8-component in the second grid;
    # the minor color spans a larger bounding box in the first grid.
    grids = [
        [[1]*9, [3,0,0,0,0,0,0,0,0], [3,0,0,0,0,0,0,0,0],
         [0,0,0,2,2,2,0,0,0], [0,0,0,2,2,2,0,0,0],
         [0,0,0,0,0,0,2,2,2], [0,0,0,0,0,0,2,2,2], [0,0,0,0,0,0,0,0,3]],
        [[2,2,0,1,1,1,1,1,1], [2,2,0,0,0,0,0,1,1],
         [0,0,2,2,0,0,0,0,1], [0,0,2,2,0,0,0,0,0], [0]*9,
         [0,0,0,0,0,0,2,2,0], [3,0,0,0,0,0,2,2,0], [3,0,0,0,0,0,0,0,3]],
    ]
    rng = _rng(seed, "teaching-pair")
    high_colors = rng.sample(range(4, 10), rng.choice((1, 2)))
    for grid in grids:
        for high in high_colors:
            allowed = [(r, c) for r in range(1, 7) for c in range(1, 8) if grid[r][c] == 0]
            first = rng.choice(allowed)
            second = rng.choice([cell for cell in allowed
                                 if max(abs(cell[0]-first[0]), abs(cell[1]-first[1])) > 1])
            for r, c in (first, second):
                grid[r][c] = high
        if color == 3:
            for row in grid:
                for c, value in enumerate(row):
                    row[c] = 3 if value == 2 else 2 if value == 3 else value
    sy, sx = rng.choice((1, 2, 3)), rng.choice((1, 2, 3))
    grids = [[[value for value in row for _ in range(sx)]
              for row in grid for _ in range(sy)] for grid in grids]
    options = [code for code in range(8)
               if _endpoint_contrast([_dihedral(grid, code) for grid in grids], color)]
    code = rng.choice(options)
    return [_dihedral(grid, code) for grid in grids]


def _intervals(length, count):
    usable = length - count + 1
    sizes = [usable // count + int(i < usable % count) for i in range(count)]
    result, start = [], 0
    for size in sizes:
        result.append(range(start, start + size))
        start += size + 1
    return result


def _grow(allowed, amount, start, rng):
    chosen, frontier = {start}, set()
    current = start
    while len(chosen) < amount:
        r, c = current
        frontier.update(cell for cell in ((r-1,c), (r+1,c), (r,c-1), (r,c+1))
                        if cell in allowed and cell not in chosen)
        current = rng.choice(sorted(frontier))
        frontier.remove(current)
        chosen.add(current)
    return chosen


def _scene(seed, label, color, count, *, large=False):
    """Construct exactly count connected modal pieces inside separated regions."""
    rng = _rng(seed, label)
    across = math.ceil(math.sqrt(count))
    down = math.ceil(count / across)
    h = 30 if large else rng.randint(max(8, 5*down-1), 24)
    w = 30 if large else rng.randint(max(9, 5*across-1), 26)
    rows, cols = _intervals(h, down), _intervals(w, across)
    all_regions = [(ri, ci) for ri in range(down) for ci in range(across)]
    corners = list(dict.fromkeys([(0, 0), (0, across-1), (down-1, 0), (down-1, across-1)]))
    selected = corners if len(corners) <= count else corners[:count]
    remaining = [slot for slot in all_regions if slot not in selected]
    rng.shuffle(remaining)
    selected += remaining[:count-len(selected)]
    allowed = [{(r, c) for r in rows[ri] for c in cols[ci]} for ri, ci in selected]
    total = rng.randint(200, 250) if large else rng.randint(max(12, 5*count), min(65, h*w*2//5))
    amounts = [5] * count
    for _ in range(total - sum(amounts)):
        index = rng.choice([i for i, region in enumerate(allowed) if amounts[i] < len(region)])
        amounts[index] += 1
    grid = [[0] * w for _ in range(h)]
    for slot, region, amount in zip(selected, allowed, amounts):
        ri, ci = slot
        if slot in corners:
            start = (rows[ri][0] if ri == 0 else rows[ri][-1],
                     cols[ci][0] if ci == 0 else cols[ci][-1])
        else:
            start = rng.choice(sorted(region))
        for r, c in _grow(region, amount, start, rng):
            grid[r][c] = color
    # Counts are conditioned on remaining capacity, never clipped after placement.
    core = [other for other in (1, 2, 3) if other != color]
    rng.shuffle(core)
    distractors = core + rng.sample(range(4, 10), rng.choice((1, 2)))
    free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    rng.shuffle(free)
    for index, other in enumerate(distractors):
        low_fraction, high_fraction = ((0.65, 0.85) if index == 0 else
                                       (0.35, 0.55) if index == 1 else (0.10, 0.22))
        maximum = min(total-1, len(free)-5-(len(distractors)-index-1))
        low = min(maximum, max(1, int(total*low_fraction)))
        high = min(maximum, max(low, int(total*high_fraction)))
        amount = rng.randint(low, high)
        for _ in range(amount):
            r, c = free.pop()
            grid[r][c] = other
    grid = _dihedral(grid, rng.randrange(8))
    if mode_color(grid) != color or sum(obj["color"] == color for obj in components(grid)) != count:
        raise RuntimeError("constructed scene violates its modal-component contract")
    return grid


def generate(seed, settings, demos=3, queries=4):
    """Build 2..6 demonstrations and an independent prefix of 1..4 queries."""
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _orientation(settings)
    primary = _rng(seed, "primary-color").choice((2, 3))
    other = 5 - primary
    inputs = _teaching_pair(seed, primary)
    extra_specs = [(other, 4), (1, 6), (primary, 9), (other, 2)]
    for index, (color, count) in enumerate(extra_specs[:demos-2], 2):
        inputs.append(_scene(seed, f"demo-{index}", color, count))
    query_colors = ([primary]*4 if demos == 2 else
                    [primary, 1 if demos >= 4 and seed % 2 else other, primary, other])
    query_counts = [1, 4, 5, _rng(seed, "large-count").choice((7, 8))]
    query_inputs = [_scene(seed, f"query-{index}", query_colors[index], query_counts[index], large=index == 3)
                    for index in range(queries)]
    pairs = [{"input": grid, "output": transform(grid, settings)} for grid in inputs + query_inputs]
    return {
        "train": pairs[:demos], "test": pairs[demos:],
        "program_solution": program(settings),
        "meta": {"seed": seed, "settings": dict(settings), "composition_version": VERSION,
                 "domain": "rectangular sides 8..30; unique nonzero mode 1/2/3; zero >=5",
                 "primary_mode": primary,
                 "modal_component_counts": [sum(obj["color"] == mode_color(grid) for obj in components(grid))
                                             for grid in inputs + query_inputs]},
    }
