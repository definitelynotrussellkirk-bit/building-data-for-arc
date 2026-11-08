"""Noisy slot reconstruction with an episode-fixed bounding-box cutoff.

Generation claims labels using the Python mirror. Native qualification and the
separate audit execute the actual Racket programs; generation never nests a
Racket process. The production generator remains unchanged.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random


TASK_ID = "5c9fd75979d1"
CUTOFFS = (2, 4, 8)
HOME = Path(__file__).resolve().parent
CANONICAL = (HOME / "canonical.rkt").read_text(encoding="utf-8")
FILTER = "(> (* bh bw) 2)"
if CANONICAL.count(FILTER) != 1:
    raise ValueError("Expected the exact canonical bounding-box filter")


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"min_bbox_area"}
            or type(settings["min_bbox_area"]) is not int
            or settings["min_bbox_area"] not in CUTOFFS):
        raise ValueError("settings must be exactly min_bbox_area: 2, 4, or 8")
    return settings["min_bbox_area"]


def program(settings):
    cutoff = _settings(settings)
    return CANONICAL if cutoff == 2 else CANONICAL.replace(FILTER, f"(> (* bh bw) {cutoff})")


def rival_program(settings, name):
    """Small, explicit executable rival family for the retained self-audit."""
    cutoff = _settings(settings)
    source = program(settings)
    predicate = f"(> (* bh bw) {cutoff})"
    if name == "pixel_count":
        return source.replace(predicate, f"(> (obj-size o) {cutoff})")
    if name == "inclusive_cutoff":
        return source.replace(predicate, f"(>= (* bh bw) {cutoff})")
    if name == "keep_all":
        return source.replace(predicate, "(> (* bh bw) 0)")
    if name == "partition_before_filter":
        source = source.replace(predicate, "(> (* bh bw) 0)")
        # Keep all edges but only allow the correctly retained boxes to paint.
        return source.replace("(<= r1 rg-r1)",
            f"(and (> (* (+ 1 (- r2 r1)) (+ 1 (- c2 c1))) {cutoff}) (<= r1 rg-r1))")
    if name == "no_mirror":
        return source.replace("(- num-cols 1 c)", "c")
    if name == "corner_pixel":
        return source.replace(
            "(find-color (first rg) (second rg) (first cs) (second cs))",
            "(cell-at g (first rg) (first cs))")
    raise ValueError(f"Unknown rival: {name}")


RIVAL_NAMES = ("pixel_count", "inclusive_cutoff", "keep_all",
               "partition_before_filter", "no_mirror", "corner_pixel")


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")


def components(grid):
    _grid(grid)
    seen, records = set(), []
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r,c) in seen:
                continue
            cells, queue = [], deque([(r,c)])
            seen.add((r,c))
            while queue:
                y,x = queue.popleft()
                cells.append((y,x))
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if (0 <= yy < height and 0 <= xx < width
                            and (yy,xx) not in seen and grid[yy][xx] == color):
                        seen.add((yy,xx))
                        queue.append((yy,xx))
            ys, xs = zip(*cells)
            bbox = [min(ys), min(xs), max(ys), max(xs)]
            records.append({"color": color, "bbox": bbox,
                "area": (bbox[2]-bbox[0]+1)*(bbox[3]-bbox[1]+1),
                "size": len(cells), "cells": [list(p) for p in cells]})
    return records


def analyze(grid, cutoff, *, metric="bbox", inclusive=False, all_edges=False,
            mirror=True, corner=False):
    """Independent Python implementation and observable causal intermediate."""
    if type(cutoff) is not int or not 0 <= cutoff <= 900:
        raise ValueError("cutoff must be an exact integer in 0..900")
    if metric not in ("bbox", "cells"):
        raise ValueError("metric must be bbox or cells")
    objects = components(grid)
    key = "area" if metric == "bbox" else "size"
    retained = [o for o in objects if o[key] >= cutoff] if inclusive else [o for o in objects if o[key] > cutoff]
    if not retained:
        raise ValueError("No component survives the filter")
    edges = objects if all_edges else retained
    rb = sorted({v for o in edges for v in (o["bbox"][0], o["bbox"][2]+1)})
    cb = sorted({v for o in edges for v in (o["bbox"][1], o["bbox"][3]+1)})
    matrix = []
    for r0,r1 in zip(rb,rb[1:]):
        row = []
        for c0,c1 in zip(cb,cb[1:]):
            value = 0
            if corner:
                value = grid[r0][c0]
            else:
                for obj in retained:
                    t,l,b,r = obj["bbox"]
                    if t <= r0 and b >= r1-1 and l <= c0 and r >= c1-1:
                        value = obj["color"]
                        break
            row.append(value)
        matrix.append(list(reversed(row)) if mirror else row)
    return {"retained": [{k:o[k] for k in ("color","bbox","area","size")} for o in retained],
            "row_breaks": rb, "col_breaks": cb, "output": matrix}


def _rng(seed, split, index):
    # Seed, stream and index suffice. Settings/counts cannot affect input draws.
    digest = hashlib.sha256(f"{TASK_ID}/bbox-v1/{seed}/{split}/{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _partitions(total, count, rng):
    parts = [3] * count
    for _ in range(total - 3*count):
        parts[rng.randrange(count)] += 1
    rng.shuffle(parts)
    return parts


def _connected(cells):
    first = next(iter(cells))
    seen, queue = {first}, [first]
    for y,x in queue:
        for p in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if p in cells and p not in seen:
                seen.add(p)
                queue.append(p)
    return len(seen) == len(cells)


def _tile(height, width, rng):
    cells = {(r,c) for r in range(height) for c in range(width)}
    # A cross keeps the exact bbox; connectivity checks prevent detached islands.
    spine_r, spine_c = rng.randrange(height), rng.randrange(width)
    candidates = sorted((r,c) for r,c in cells if r != spine_r and c != spine_c)
    rng.shuffle(candidates)
    holes = max(1, int(height*width*rng.uniform(.12,.30)))
    removed = 0
    for p in candidates:
        cells.remove(p)
        if _connected(cells):
            removed += 1
        else:
            cells.add(p)
        if removed >= holes:
            break
    return cells


_SHAPES = {
    3: {(0,0),(0,1),(0,2)},
    4: {(0,0),(0,1),(1,0)},
    6: {(0,0),(0,1),(0,2),(1,0)},
    8: {(0,0),(0,1),(0,2),(0,3),(1,0)},
    9: {(0,1),(1,0),(1,1),(1,2),(2,1)},
    12: {(0,0),(0,1),(0,2),(0,3),(1,0),(2,0)},
}
_TRAIN_SIZES = ((16,23),(19,24),(20,27),(24,22),(26,30),(30,26))
_QUERY_SIZES = ((14,17),(18,23),(30,30),(29,30))


def _orient(cells, rng):
    cells = set(cells)
    for _ in range(rng.randrange(4)):
        cells = {(c,-r) for r,c in cells}
    if rng.randrange(2):
        cells = {(r,-c) for r,c in cells}
    min_r, min_c = min(r for r,c in cells), min(c for r,c in cells)
    return {(r-min_r,c-min_c) for r,c in cells}


def make_input(seed, split, index):
    sizes = _TRAIN_SIZES if split == "train" else _QUERY_SIZES
    height,width = sizes[index]
    rng = _rng(seed, split, index)
    grid = [[0]*width for _ in range(height)]
    palette = list(range(1,10))
    rng.shuffle(palette)

    def paint(cells, top, left, color):
        for r,c in sorted(cells):
            if not (0 <= top+r < height and 0 <= left+c < width) or grid[top+r][left+c]:
                raise AssertionError("Construction overlap or out-of-bounds")
            grid[top+r][left+c] = color

    # Exact-cutoff distractors have novel edges and stay off the colored core.
    paint({(0,0)}, 0, 0, palette[0])
    paint({(0,0),(0,1)}, 0, width-2, palette[1])
    areas = [3,4,6,8] if split == "train" or index >= 2 else ([3,6] if index == 0 else [4,8])
    rng.shuffle(areas)
    col = 1
    for n,area in enumerate(areas):
        cells = _orient(_SHAPES[area], rng)
        # Maximum rotated fragment height is four; row 5 is a mandatory gap
        # before the core at row 6, even if it reuses the fragment's color.
        paint(cells, 1, col, palette[n+2])
        col += max(c for r,c in cells)+3
    # These two sparse pieces specifically separate bbox area from cell count.
    paint(_SHAPES[9], 6, 1, palette[6])
    if height >= 16:
        paint(_SHAPES[12], 11, 1, palette[7])

    # Large queries exercise actual object count/density and boundary contacts.
    touches = split == "test" and index >= 2
    core_h = height-6-(0 if touches else 1)
    core_w = width-6-(0 if touches else 1)
    nr = min(core_h//3, 5 if touches else 3)
    nc = min(core_w//3, 5 if touches else 4)
    row_sizes, col_sizes = _partitions(core_h,nr,rng), _partitions(core_w,nc,rng)
    colors, row = [], 6
    for ri,rh in enumerate(row_sizes):
        color_row, col = [], 6
        for ci,cw in enumerate(col_sizes):
            forbidden = ({color_row[-1]} if ci else set()) | ({colors[-1][ci]} if ri else set())
            color = rng.choice([c for c in palette if c not in forbidden])
            color_row.append(color)
            paint(_tile(rh,cw,rng),row,col,color)
            col += cw
        colors.append(color_row)
        row += rh
    # D4 layout diversity changes where the cue/fragments are, without changing
    # their sizes. Recompute labels from the resulting input; do not rotate gold.
    turns = (seed + index + (1 if split == "train" else 0)) % 4
    for _ in range(turns):
        grid = [list(row) for row in zip(*grid[::-1])]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def generate(seed, settings, demos=3, queries=4):
    cutoff = _settings(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    def pairs(split, count):
        result = []
        for index in range(count):
            grid = make_input(seed,split,index)
            result.append({"input":grid,"output":analyze(grid,cutoff)["output"]})
        return result
    return {"train":pairs("train",demos), "test":pairs("test",queries),
            "program_solution":program(settings)}
