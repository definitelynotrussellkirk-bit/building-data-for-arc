"""Enclosed-region area controls horizontal docking; canonical at threshold one.

The Python labels are claims for the independent native Racket worker to check.
Inputs depend only on seed/split/index, never on the private episode threshold.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import random


TASK_ID = "7c7f1f574a18"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
THRESHOLDS = (1, 2, 3)
DEMO_SIZES = ((19, 21), (24, 25), (22, 26), (25, 27), (24, 29), (27, 30))
QUERY_SIZES = ((19, 19), (23, 27), (27, 29), (30, 30))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CLOSED = "(or (empty? gaps) (for/or ((p gaps)) (interior-gap? obj p)))"
_INTERIOR_START = "(not (for/or ((q region))"
_INTERIOR_END = "(= (second q) c2))))))"


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) - {"min_hole_area"}:
        raise ValueError("settings must contain only min_hole_area")
    return {"min_hole_area": _integer(settings.get("min_hole_area", 1), 1, 3, "min_hole_area")}


def _replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Pinned canonical program no longer has the expected expression")
    return source.replace(old, new)


def _region_guard(source, guard):
    source = _replace_once(source, _INTERIOR_START, f"(and {guard} {_INTERIOR_START}")
    return _replace_once(source, _INTERIOR_END, _INTERIOR_END + ")")


def program(settings):
    """Return exact canonical bytes at one, or a thresholded Racket predicate."""
    threshold = _settings(settings)["min_hole_area"]
    if threshold == 1:
        return CANONICAL
    return _region_guard(CANONICAL, f"(>= (length region) {threshold})")


def rival_programs(settings):
    """Standalone executable finite rivals for bounded teaching self-review.

Some rivals are equivalent at threshold one. The audit asks whether a rival
fits all demonstrations yet predicts a different query, not that every name
must be eliminated in every setting.
"""
    threshold = _settings(settings)["min_hole_area"]
    chosen = program(settings)
    rivals = {f"threshold_{n}": program({"min_hole_area": n})
              for n in THRESHOLDS if n != threshold}
    rivals.update({
        "solid_only": _replace_once(CANONICAL, _CLOSED, "(empty? gaps)"),
        "hole_only": _replace_once(chosen, _CLOSED,
                                  "(for/or ((p gaps)) (interior-gap? obj p))"),
        "any_hole": CANONICAL,
        "bbox_gap_total": _replace_once(CANONICAL, _CLOSED,
            f"(or (empty? gaps) (>= (length gaps) {threshold}))"),
        "enclosed_gap_total": _replace_once(CANONICAL, _CLOSED,
            f"(or (empty? gaps) (>= (length (filter (lambda (p) (interior-gap? obj p)) gaps)) {threshold}))"),
        "all_gaps_qualify": _replace_once(chosen, _CLOSED,
            "(or (empty? gaps) (for/and ((p gaps)) (interior-gap? obj p)))"),
        "gap_connectivity_8": _replace_once(chosen,
            "                                                4)))",
            "                                                8)))"),
        "all_left": _replace_once(chosen, "(if (closed-class? obj)", "(if #t"),
        "all_right": _replace_once(chosen, "(if (closed-class? obj)", "(if #f"),
        "nearest_side": _replace_once(chosen, "(if (closed-class? obj)",
            "(if (<= (+ (obj-c1 obj) (obj-c2 obj)) (- w 1))"),
        "opposite_side": _replace_once(chosen, "(if (closed-class? obj)",
            "(if (> (+ (obj-c1 obj) (obj-c2 obj)) (- w 1))"),
        "literal_background_5": _replace_once(chosen,
            "(define bg (mode g -1))", "(define bg 5)"),
        "literal_foreground_7": _replace_once(chosen, "(objects g bg)",
            "(filter (lambda (obj) (= (obj-color obj) 7)) (objects g bg))"),
    })
    for name, coordinate in (("hole_width", "second"), ("hole_height", "first")):
        guard = (f"(>= (+ 1 (- (apply max (map {coordinate} region)) "
                 f"(apply min (map {coordinate} region)))) {threshold})")
        rivals[name] = _region_guard(CANONICAL, guard)
    return rivals


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if any(type(row) is not list for row in grid) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    counts = Counter(cell for row in grid for cell in row)
    winners = [color for color, count in counts.items() if count == max(counts.values())]
    if len(winners) != 1:
        raise ValueError("background must be uniquely modal")
    return winners[0]


def _region(start, unseen):
    unseen.remove(start)
    todo, found = [start], {start}
    while todo:
        row, col = todo.pop()
        for dr, dc in _DIR4:
            point = row + dr, col + dc
            if point in unseen:
                unseen.remove(point)
                found.add(point)
                todo.append(point)
    return found


def analyze(grid):
    """JSON-compatible object/gap partition, including the causal intermediate."""
    background = _grid(grid)
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row)
              if color != background}
    components = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        same_color = {p for p in unseen if grid[p[0]][p[1]] == color}
        cells = _region(start, same_color)
        unseen.difference_update(cells)
        r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
        r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
        gaps = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                if (r, c) not in cells}
        regions = []
        while gaps:
            gap = _region(min(gaps), gaps)
            regions.append({"area": len(gap), "cells": [list(p) for p in sorted(gap)],
                            "touches_boundary": any(r in (r0, r1) or c in (c0, c1)
                                                    for r, c in gap)})
        components.append({
            "color": color, "cells": [list(p) for p in sorted(cells)],
            "bbox": [r0, c0, r1, c1], "height": r1-r0+1, "width": c1-c0+1,
            "solid_bbox": not regions, "gap_regions": regions,
            "max_enclosed_area": max((region["area"] for region in regions
                                      if not region["touches_boundary"]), default=0),
        })
    components.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    return {"background": background, "height": len(grid), "width": len(grid[0]),
            "components": components}


def solve(grid, threshold=1):
    """Independent Python claim; protected Racket remains label authority."""
    threshold = _integer(threshold, 1, 3, "threshold")
    scene = analyze(grid)
    result = [[scene["background"]] * scene["width"] for _ in grid]
    for obj in scene["components"]:
        closed = obj["solid_bbox"] or obj["max_enclosed_area"] >= threshold
        column = 0 if closed else scene["width"] - obj["width"]
        for r, c in obj["cells"]:
            result[r][column + c - obj["bbox"][1]] = 2 if closed else 3
    return result


def _shape(kind, width, rng):
    height = {"solid": 2, "joined3": 3, "split21": 3, "split111": 3,
              "open3": 3, "diagonal3": 3, "bent3": 4, "vertical3": 5}[kind]
    cells = {(r, c) for r in range(height) for c in range(width)}
    if kind == "joined3":
        first = rng.randint(1, width - 4)
        holes = {(1, first + j) for j in range(3)}
    elif kind == "split21":
        holes = {(1, 1), (1, 2), (1, 4)}
    elif kind == "split111":
        holes = {(1, 1), (1, 3), (1, 5)}
    elif kind == "open3":
        first = rng.randint(1, width - 4)
        holes = {(0, first + j) for j in range(3)}
    elif kind == "diagonal3":
        holes = {(0, 0), (1, 1), (1, 2), (1, 3)}
    elif kind == "bent3":
        first = rng.randint(1, width - 3)
        holes = {(1, first), (1, first + 1), (2, first)}
    elif kind == "vertical3":
        column = rng.randint(1, width - 2)
        holes = {(1, column), (2, column), (3, column)}
    else:
        holes = set()
    cells.difference_update(holes)
    if rng.randrange(2):
        cells = {(height - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, width - 1 - c) for r, c in cells}
    return height, width, cells


def _rng(seed, split, index):
    token = hashlib.sha256(f"{TASK_ID}:hole-area-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(token, "big"))


def _sample(rng, height, width, profile, phase, background=None):
    # Equal-bbox/equal-cell-count groups defeat arbitrary object-size-only
    # classifiers. Demo 1 adds bent/vertical cavities and diagonal leakage.
    if profile == 1:
        kinds = ["solid", "diagonal3", "bent3", "vertical3", "open3"]
    else:
        kinds = ["solid", "joined3", "split21", "split111", "open3"]
        if profile >= 2:
            kinds.append("bent3")
        if profile >= 3:
            kinds.append("vertical3")
    body_width = rng.randint(width - 5, width - 3) if profile >= 2 else rng.randint(7, 9)
    shapes = []
    for kind in kinds:
        body = body_width
        if kind == "solid":
            body = rng.randint(3, 9)
        elif kind == "diagonal3":
            body = rng.randint(6, 9)
        elif kind == "bent3":
            body = rng.randint(4, 7)
        elif kind == "vertical3":
            body = rng.randint(3, 7)
        shapes.append((kind, *_shape(kind, body, rng)))
    rng.shuffle(shapes)
    spare = height - sum(shape[1] for shape in shapes) - len(shapes) + 1
    if spare < 0:
        raise ValueError("Scene geometry does not fit its declared profile")
    margins = [0] * (len(shapes) + 1)
    for _ in range(spare):
        margins[rng.randrange(len(margins))] += 1
    if background is None:
        background = rng.choice((0, 4, 5, 6, 7, 8, 9))
    palette = [color for color in range(10) if color != background]
    rng.shuffle(palette)
    result = [[background] * width for _ in range(height)]
    row = margins[0]
    for index, (kind, sh, sw, cells) in enumerate(shapes):
        # Solid and open appear on BOTH starting sides across the first two
        # demonstrations, ruling out both nearest-edge and switch-sides rules.
        side = phase % 2 if kind in ("solid", "open3") else rng.randrange(2)
        half = (width - sw) // 2
        col = rng.randint(0, half) if side == 0 else rng.randint(half + 1, width - sw)
        if profile >= 2:
            color = palette[index % len(palette)]
        elif profile == 1:
            # A second foreground color must be visible within the minimum
            # lesson. One color still spans both output classes.
            color = palette[1] if kind in ("bent3", "vertical3") else palette[0]
        else:
            color = palette[0]
        for r, c in cells:
            result[row + r][col + c] = color
        row += sh + 1 + margins[index + 1]
    _grid(result)
    return result


def generate(seed, settings, demos=3, queries=4):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    settings = _settings(settings)
    threshold = settings["min_hole_area"]
    teaching_backgrounds = _rng(seed, "teaching-palette", 0).sample((0, 4, 5, 6, 7, 8, 9), 2)
    train, test = [], []
    for split, count, output in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            height, width = (DEMO_SIZES if split == "train" else QUERY_SIZES)[index]
            profile = index % 2 if split == "train" else index
            background = teaching_backgrounds[index % 2] if split == "train" else None
            grid = _sample(_rng(seed, split, index), height, width, profile, index, background)
            output.append({"input": grid, "output": solve(grid, threshold)})
    fingerprints = {tuple(map(tuple, pair["input"])) for pair in train + test}
    if len(fingerprints) != demos + queries:
        raise ValueError("Unexpected duplicate scene; no short batches are emitted")
    return {"train": train, "test": test, "program_solution": program(settings)}
