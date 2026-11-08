"""Native candidate: select a square source, then build rotated quadrants.

The exact canonical setting comes from canonical.rkt. The retained handedness
prototype supplies the tiling operation; the new object-source setting first
discovers the unique largest same-color four-connected nonzero component and
extracts only its cells into its tight square box. Python labels are claims;
native qualification independently executes the materialized Racket programs.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("quadrant_retained_prototype", HERE / "prototype.py")
_old = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_old)

DEFAULT = {"source_mode": "whole", "handedness": "clockwise"}
SETTINGS = tuple({"source_mode": source, "handedness": turn}
                 for source in ("whole", "largest_component")
                 for turn in ("clockwise", "counterclockwise"))


def normalize_settings(settings=None):
    if settings is None:
        return dict(DEFAULT)
    if type(settings) is not dict or set(settings) - set(DEFAULT):
        raise ValueError("settings must contain only source_mode and handedness")
    result = {**DEFAULT, **settings}
    for key, allowed in (("source_mode", ("whole", "largest_component")),
                         ("handedness", ("clockwise", "counterclockwise"))):
        if type(result[key]) is not str or result[key] not in allowed:
            raise ValueError(f"invalid {key}: expected one of {allowed}")
    return result


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _square(grid):
    if (type(grid) is not list or not 2 <= len(grid) <= 15
            or any(type(row) is not list or len(row) != len(grid)
                   or any(type(c) is not int or not 0 <= c <= 9 for c in row)
                   for row in grid)):
        raise ValueError("input must be a square 2..15 of exact integer colors 0..9")
    return deepcopy(grid)


def components(grid):
    """Same-color four-connected components; zero is fixed background."""
    n = len(grid)
    seen = set()
    result = []
    for r in range(n):
        for c in range(n):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append([rr, cc])
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    q = (rr+dr, cc+dc)
                    if (0 <= q[0] < n and 0 <= q[1] < n and q not in seen
                            and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        todo.append(q)
            cells.sort()
            rs, cs = zip(*cells)
            result.append({"color": color, "cells": cells, "size": len(cells),
                           "bbox": [min(rs), min(cs), max(rs), max(cs)]})
    return result


def analyze_scene(grid):
    grid = _square(grid)
    found = components(grid)
    if not found:
        raise ValueError("at least one nonzero component is required")
    selected = max(found, key=lambda o: o["size"])
    if sum(o["size"] == selected["size"] for o in found) != 1:
        raise ValueError("largest component must be unique")
    r0, c0, r1, c1 = selected["bbox"]
    size = r1-r0+1
    if size != c1-c0+1 or size < 2:
        raise ValueError("selected component must have a square bbox of side 2..15")
    crop = [[0]*size for _ in range(size)]
    for r, c in selected["cells"]:
        crop[r-r0][c-c0] = selected["color"]
    rotations = _old._rotations(crop)
    if len({repr(g) for g in rotations}) != 4:
        raise ValueError("selected component must have four distinct rotations")
    return {"height": len(grid), "width": len(grid), "components": found,
            "component_count": len(found), "selected": selected,
            "selected_bbox_side": size, "intermediate": crop,
            "input_nonzero": sum(c != 0 for row in grid for c in row)}


def python_apply(grid, settings=None):
    setting = normalize_settings(settings)
    source = (_square(grid) if setting["source_mode"] == "whole"
              else analyze_scene(grid)["intermediate"])
    return _old.solve(source, handedness=setting["handedness"])


def program(settings=None):
    setting = normalize_settings(settings)
    if setting == DEFAULT:
        return (HERE / "canonical.rkt").read_text()
    if setting["source_mode"] == "whole":
        return _old.program_for(setting["handedness"])
    tr = "rotate-cw" if setting["handedness"] == "clockwise" else "rotate-ccw"
    bl = "rotate-ccw" if setting["handedness"] == "clockwise" else "rotate-cw"
    return f"""(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (chosen (argmax obj-size objs))
         (bb (obj-bbox chosen))
         (cells (obj-cells chosen))
         (source (grid-from-fn (+ 1 (- (third bb) (first bb)))
                               (+ 1 (- (fourth bb) (second bb)))
                   (lambda (r c)
                     (if (member (list (+ r (first bb)) (+ c (second bb))) cells)
                         (obj-color chosen) 0)))))
    (stack-grids 'vertical
      (list (stack-grids 'horizontal (list source ({tr} source)))
            (stack-grids 'horizontal (list ({bl} source) (rotate-180 source))))))))"""


def _rng(seed, slot):
    raw = hashlib.sha256(f"196a7ec58bbc-native-v1:{seed}:{slot}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _dense_mask(k):
    # The two adjacent top-edge gaps preserve the right-hand connection even
    # at k=4; removing (1,k-1) instead isolates the bottom-right three cells.
    removed = {(0,k-1), (0,k-2), (k-1,1), (k-2,k-2)}
    return {(r,c) for r in range(k) for c in range(k)} - removed


def _core(n, a, b, c):
    g = [[0]*n for _ in range(n)]
    k = 5 if n == 11 else 4
    span = k+2
    for r, col in {(0,i) for i in range(span)} | {(i,0) for i in range(span)}:
        g[r][col] = b
    for r, col in _dense_mask(k):
        g[r+2][col+2] = a
    g[1][1] = a  # Joins only under the eight-connected rival.
    g[k][k] = b  # Inside target bbox but outside its component.
    for r, col in [(0,8),(0,10),(2,8),(2,10),(4,8),(4,10),(6,8),(6,10),
                   (8,0),(8,2),(8,4),(8,6),(8,8),(8,10),
                   (10,0),(10,2),(10,4),(10,6),(10,8),(10,10)]:
        g[r][col] = b
    g[7][7] = c
    if n == 12:
        g[11][11] = c
    return g


def _medium(n, k, colors, rng):
    a, b, c = colors
    g = [[0]*n for _ in range(n)]
    r0, c0 = rng.randrange(n-k+1), rng.randrange(n-k+1)
    for r, col in _dense_mask(k):
        g[r+r0][col+c0] = a
    g[r0+k-2][c0+k-2] = b  # Internal distractor is intentionally retained in input.
    for r in range(0, n, 2):
        for col in range(0, n, 2):
            if not g[r][col] and rng.random() < .65:
                g[r][col] = b if rng.random() < .5 else c
    return g


def _large(colors, rng, query):
    a, b, c = colors
    n = 15
    g = [[0]*n for _ in range(n)]
    cells = {(0,i) for i in range(n)} | {(i,0) for i in range(n)}
    bar_rows = (2,4,6,9,12) if query else (2,5,8,11)
    for r in bar_rows:
        end = rng.randint(11,14) if query else rng.randint(8,10)
        cells.update((r,col) for col in range(1,end))
    for r,col in cells:
        g[r][col] = a
    for r in range(1,n,2):
        for col in range(1,n,2):
            if not g[r][col] and rng.random() < .6:
                g[r][col] = rng.choice((b,c))
    return g


def _scene(seed, slot):
    rng = _rng(seed, slot)
    a, b, c = rng.sample(range(1,10), 3)
    if slot in (0,1):
        g = _core(11+slot, a,b,c)
    elif slot == 2:
        g = [[a,a],[0,a]]
    elif slot == 3:
        g = [[a,a,a],[a,0,0],[a,0,b]]
    elif slot == 4:
        g = _medium(9,5,(a,b,c),rng)
    elif slot in (5,9):
        g = _large((a,b,c),rng,query=slot==9)
    elif slot == 6:
        g = [[a,a,0],[a,a,a],[a,0,b]]
    elif slot == 7:
        g = _medium(9,4,(a,b,c),rng)
    else:
        g = _medium(12,7,(a,b,c),rng)
    for _ in range(rng.randrange(4)):
        g = _old._rotate_cw(g)
    analyze_scene(g)
    return g


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, "seed", 0, 2**63-1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    setting = normalize_settings(settings)
    bank = [_scene(seed, slot) for slot in range(10)]
    if len({repr(g) for g in bank}) != 10:
        raise RuntimeError("constructive profile bank unexpectedly contains duplicate inputs")
    def pair(g):
        return {"input": deepcopy(g), "output": python_apply(g, setting)}
    return {"train": [pair(g) for g in bank[:demos]],
            "test": [pair(g) for g in bank[6:6+queries]],
            "program_solution": program(setting), "settings": setting,
            "meta": {"status": "proposed_owner_pending", "training_admitted": False,
                     "seed": seed, "candidate_attempts": 10, "rejections": 0,
                     "label_basis": "Python claims; protected Racket required",
                     "input_rng_independent_of_settings_and_counts": True,
                     "input_side_range": [2,15], "output_side_range": [4,30],
                     "canonical_production_side_range": [2,3]}}
