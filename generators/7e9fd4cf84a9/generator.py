"""Generator for ARC task 7e9fd4cf84a9 — repair holed green rectangles.

Every four-connected green object is a filled rectangle with exactly one
strictly interior zero.  The transformation fills each such zero cyan while
preserving all unrelated colored distractors.  The generator deliberately
includes distractors in every ordinary draw so an erase-everything-but-green
shortcut is not consistent with generated data.
"""
from __future__ import annotations

from copy import deepcopy
from math import ceil
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e9fd4cf84a9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "806f1d42e5ab"

SUMMARY = (
    "A 0-background grid contains 1–6 separated green rectangles. Each green "
    "rectangle has exactly one strictly interior missing cell. One or more "
    "non-green distractor cells are outside every green bounding box. Fill "
    "every missing rectangle cell cyan (8) and preserve every other cell."
)

INVARIANTS = [
    "background is 0",
    "each green component is a filled rectangle missing exactly one interior cell",
    "green rectangle bounding boxes are separated by at least one background cell",
    "at least one non-green distractor is present and must be preserved",
]

LAYOUT_PROFILES = ("balanced", "wide", "tall")
DISTRACTOR_COLORS = (1, 2, 4, 5, 6, 7, 9)
AXES = {
    "grid_h": {"type": "int", "default": "rng 13..30", "valid": "13..30"},
    "grid_w": {"type": "int", "default": "rng 13..30", "valid": "13..30"},
    "n_rectangles": {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "distractor_count": {"type": "int", "default": "rng 1..5", "valid": "1..5"},
    "layout_profile": {
        "type": "str",
        "default": "rng balanced|wide|tall",
        "valid": "balanced|wide|tall",
    },
}


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("ARC grids may be at most 30x30")
    for row in grid:
        if type(row) is not list or len(row) != w:
            raise ValueError("expected a rectangular grid")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be exact ARC integers 0..9")
    return h, w


def _components(grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (rr + dr, cc + dc)
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        stack.append(point)
            found.append(sorted(cells))
    return found


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows), max(cols)


def analyze_scene(grid) -> dict:
    """Return exact structural facts used by tests and future review agents."""
    _validate_grid(grid)
    rectangles = []
    covered: set[tuple[int, int]] = set()
    for cells in _components(grid, 3):
        r0, c0, r1, c1 = _bbox(cells)
        holes = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if grid[r][c] == 0]
        rectangles.append({
            "bbox": [r0, c0, r1, c1],
            "shape": [r1 - r0 + 1, c1 - c0 + 1],
            "green_cells": len(cells),
            "holes": holes,
        })
        covered.update((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    distractors = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
                   if value not in (0, 3)]
    return {
        "green_rectangle_count": len(rectangles),
        "rectangles": rectangles,
        "rectangle_shapes": [tuple(item["shape"]) for item in rectangles],
        "hole_cells": [hole for item in rectangles for hole in item["holes"]],
        "distractor_cells": distractors,
        "distractor_cell_count": len(distractors),
        "covered_bbox_cells": sorted(covered),
    }


def canonical_transform(grid):
    """Python diagnostic mirror of the canonical Racket rule."""
    _validate_grid(grid)
    out = deepcopy(grid)
    for cells in _components(grid, 3):
        r0, c0, r1, c1 = _bbox(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] == 0:
                    out[r][c] = 8
    return out


solve = canonical_transform


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    analysis = analyze_scene(grid)
    if not analysis["rectangles"]:
        errors.append("no green holed rectangles")
    for item in analysis["rectangles"]:
        r0, c0, r1, c1 = item["bbox"]
        height, width = item["shape"]
        if height < 3 or width < 3:
            errors.append("green rectangle is too small to have an interior hole")
            continue
        bad_inside = [(r, c, grid[r][c]) for r in range(r0, r1 + 1)
                      for c in range(c0, c1 + 1) if grid[r][c] not in (0, 3)]
        if bad_inside:
            errors.append("non-green distractor lies inside a green bounding box")
        holes = item["holes"]
        if len(holes) != 1:
            errors.append("green component does not have exactly one missing cell")
        elif holes[0][0] in (r0, r1) or holes[0][1] in (c0, c1):
            errors.append("green component's missing cell is not strictly interior")
        if item["green_cells"] != height * width - 1:
            errors.append("green component is not otherwise a filled rectangle")
    if analysis["distractor_cell_count"] < 1:
        errors.append("no non-green distractor to prove preservation")
    return errors


def _bands(length: int, count: int) -> list[tuple[int, int]]:
    """Partition the interior into `count` bands with one-cell separators."""
    usable = length - 2 - (count - 1)
    if usable < 3 * count:
        raise ValueError(f"grid dimension {length} cannot fit {count} holed rectangles")
    base, extra = divmod(usable, count)
    sizes = [base + (1 if i < extra else 0) for i in range(count)]
    start = 1
    result = []
    for size in sizes:
        result.append((start, size))
        start += size + 1
    return result


def _rectangle_size(profile: str, band_h: int, band_w: int, rng) -> tuple[int, int]:
    max_h, max_w = min(5, band_h), min(5, band_w)
    if profile == "wide":
        return 3, max_w
    if profile == "tall":
        return max_h, 3
    return rng.randint(3, max_h), rng.randint(3, max_w)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = ctx.draw_int_strict("grid_h", 13, 30)
    w = ctx.draw_int_strict("grid_w", 13, 30)
    count = ctx.draw_int_strict("n_rectangles", 1, 6)
    distractor_count = ctx.draw_int_strict("distractor_count", 1, 5)
    profile = ctx.draw_choice("layout_profile", LAYOUT_PROFILES)

    row_count = 1 if count <= 3 else 2
    col_count = count if count <= 3 else 3
    row_bands = _bands(h, row_count)
    col_bands = _bands(w, col_count)
    slots = [(r, c, bh, bw) for r, bh in row_bands for c, bw in col_bands][:count]
    rng = ctx.draw_rng("scene")
    rng.shuffle(slots)

    grid = full_grid(h, w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    for band_r, band_c, band_h, band_w in slots:
        rh, rw = _rectangle_size(profile, band_h, band_w, rng)
        r = band_r + rng.randint(0, band_h - rh)
        c = band_c + rng.randint(0, band_w - rw)
        for rr in range(r, r + rh):
            for cc in range(c, c + rw):
                grid[rr][cc] = 3
        hole_r = rng.randint(r + 1, r + rh - 2)
        hole_c = rng.randint(c + 1, c + rw - 2)
        grid[hole_r][hole_c] = 0
        boxes.append((r, c, r + rh - 1, c + rw - 1))

    forbidden: set[tuple[int, int]] = set()
    for r0, c0, r1, c1 in boxes:
        for r in range(max(0, r0 - 1), min(h, r1 + 2)):
            for c in range(max(0, c0 - 1), min(w, c1 + 2)):
                forbidden.add((r, c))
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 0 and (r, c) not in forbidden]
    rng.shuffle(candidates)
    if len(candidates) < distractor_count:
        raise ValueError("requested geometry leaves too little room for distractors")
    colors = list(DISTRACTOR_COLORS)
    rng.shuffle(colors)
    for index, (r, c) in enumerate(candidates[:distractor_count]):
        grid[r][c] = colors[index % len(colors)]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return grid
