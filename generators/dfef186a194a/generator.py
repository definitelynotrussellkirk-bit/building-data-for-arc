"""Generator for 8a371977.

Rule: bg=1; objects in grid layout; rule recolors boundary objects red,
interior green.

Combinatorial axes (8): grid_h/w, n_rows, n_cols, obj_h_max, obj_w_max,
palette_kind, anchor_corner, asymmetry_force.
Degenerates: single_object, no_objects, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dfef186a194a"
VERSION = "2.0.0"
TASK_ID = "dfef186a194a"
SUMMARY = (
    "Color-1 (blue) background grid (~12-22 per side) with non-bg "
    "OBJECTS arranged in a regular N×M GRID LAYOUT (N, M = 3..5 "
    "each). All objects share a single non-1 color, each 1-2 "
    "cells, separated by ≥1 cell of bg. Rule: detect all non-bg "
    "objects (bg=1). Determine each object's row-index ri (in "
    "sorted unique top-rows) and column-index ci (in sorted "
    "unique left-cols). If object is on the BORDER of the layout "
    "(ri == 0 OR ri == N-1 OR ci == 0 OR ci == M-1), recolor its "
    "cells to color 2 (red). Otherwise (interior of layout), "
    "recolor to color 3 (green). Background stays 1."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 1",
    "objects share a single non-1 non-{2,3} color",
    "objects arranged as an N×M grid where N, M >= 3",
    "objects separated by ≥1 cell of bg",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("single_object", "no_objects", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_rows":         {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "n_cols":         {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "obj_h_max":      {"type": "int", "default": "2", "valid": "1..3"},
    "obj_w_max":      {"type": "int", "default": "2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 12, 14
        nr_choices = (3,)
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
        nr_choices = (3, 4, 5)
    else:
        h_lo, h_hi = 14, 18
        nr_choices = (3, 4)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    obj_color = pal[0] if pal else 5
    n_rows = int(overrides.get("n_rows",
                               rng.choice(nr_choices)))
    n_cols = int(overrides.get("n_cols",
                               rng.choice(nr_choices)))
    n_rows = max(3, min(5, n_rows))
    n_cols = max(3, min(5, n_cols))
    max_obj_h = 2 if _can_fit_axis(h, n_rows, 2) else 1
    max_obj_w = 2 if _can_fit_axis(w, n_cols, 2) else 1
    if not _can_fit_axis(h, n_rows, max_obj_h) or not _can_fit_axis(w, n_cols, max_obj_w):
        return _draw_from_degenerate("no_objects", rng)
    row_tops = _spaced_starts(h, n_rows, max_obj_h, rng)
    col_lefts = _spaced_starts(w, n_cols, max_obj_w, rng)
    g = full_grid(h, w, 1)
    for ri in range(n_rows):
        for ci in range(n_cols):
            tr = row_tops[ri]
            tc = col_lefts[ci]
            obj_h = rng.randint(1, max_obj_h)
            obj_w = rng.randint(1, max_obj_w)
            for dr in range(obj_h):
                for dc in range(obj_w):
                    g[tr + dr][tc + dc] = obj_color
    return g


def _can_fit_axis(length: int, count: int, size: int) -> bool:
    return count > 0 and length >= count * size + (count - 1)


def _spaced_starts(length: int, count: int, size: int, rng) -> list[int]:
    """Starts for count objects of max extent size with >=1 bg cell between.

    The previous generator jittered top/left independently per object; the
    Racket rule indexes objects by unique top-rows and left-cols, so that jitter
    exploded an intended N×M layout into many phantom rows/cols.  Starts are now
    shared per logical row/column.
    """
    min_total = count * size + (count - 1)
    slack = max(0, length - min_total)
    gaps = [0 for _ in range(count + 1)]
    for _ in range(slack):
        gaps[rng.randrange(count + 1)] += 1
    starts: list[int] = []
    pos = gaps[0]
    for i in range(count):
        starts.append(pos)
        pos += size
        if i < count - 1:
            pos += 1 + gaps[i + 1]
    return starts


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [4, 6, 9]
    elif kind == "cool":
        pool = [5, 7, 8]
    elif kind == "primary":
        pool = [4]
    else:
        pool = [4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (1, 2, 3)]
    rng.shuffle(pool)
    return pool


def _components_bg1(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 1 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color and color != 1):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the regular object-grid layout."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    vals = {v for row in grid for v in row}
    obj_colors = sorted(v for v in vals if v != 1)
    if len(obj_colors) != 1:
        errors.append(f"objects should use exactly one non-bg color, found {obj_colors}")
    elif obj_colors[0] in (2, 3):
        errors.append("input object color should not already be an output label color 2/3")

    comps = _components_bg1(grid)
    if not (9 <= len(comps) <= 25):
        errors.append(f"expected a 3..5 by 3..5 object grid, found {len(comps)} components")
    tops = sorted({min(r for r, _ in cells) for _, cells in comps})
    lefts = sorted({min(c for _, c in cells) for _, cells in comps})
    if not (3 <= len(tops) <= 5 and 3 <= len(lefts) <= 5):
        errors.append(f"expected 3..5 unique top rows and left cols, got {len(tops)}x{len(lefts)}")
    if len(comps) != len(tops) * len(lefts):
        errors.append(f"component count {len(comps)} does not fill the inferred {len(tops)}x{len(lefts)} layout")
    anchors = {(min(r for r, _ in cells), min(c for _, c in cells)) for _, cells in comps}
    missing = [(r, c) for r in tops for c in lefts if (r, c) not in anchors]
    if missing:
        errors.append(f"missing object at {len(missing)} inferred row/col intersections")
    for _, cells in comps:
        if not (1 <= len(cells) <= 4):
            errors.append(f"object area should be 1..4 cells, found {len(cells)}")
            break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 16, 16
    g = full_grid(h, w, 1)
    if name == "single_object":
        g[7][7] = 5; g[7][8] = 5
        return g
    if name == "no_objects":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
