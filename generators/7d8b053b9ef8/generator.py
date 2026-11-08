"""Generator for arc_additional_puzzle_bank_volume10:H69.

Rule: a control cell chooses union, intersection, XOR, or
first-minus-second over normalized blue and red shapes.

Combinatorial axes (8): grid_h/w, palette_kind, control_color,
palette_size, position_bias, n_distinct_colors, overlap_kind, texture.
Degenerates: no_control, no_blob_1, no_blob_2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import PLUS_5

GENERATOR_ID = "7d8b053b9ef8"
VERSION = "3.0.1"
TASK_ID = "7d8b053b9ef8"
SUMMARY = (
    "0-bg grid with: (a) a CONTROL cell in {3, 4, 6, 7} placed at any "
    "position (often top-left corner); (b) one color-1 (blue) shape "
    "with ≥3 cells; (c) one color-2 (red) shape with ≥3 cells. Both "
    "shapes' NORMALIZED cells (cells shifted so min row, col = 0) "
    "partially overlap (have at least one common cell AND each has "
    "cells not in the other). Rule: read control. Compute boolean op "
    "on normalized cell sets: 3 → union, 4 → intersection, 6 → XOR, "
    "else → blue minus red. Output is the resulting cells painted 8 "
    "and cropped to their bbox."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one control cell with value in {3, 4, 6, 7}",
    "exactly one color-1 shape (≥3 cells)",
    "exactly one color-2 shape (≥3 cells)",
    "shapes' normalized cells partially overlap (some common, some unique to each)",
]

PALETTE_KINDS = ("default", "control_3", "control_4", "control_6_or_7")
DEGENERATE_TEXTURES = ("no_control", "no_blob_1", "no_blob_2")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "control_color":  {"type": "int", "default": "rng 3|4|6|7",
                       "valid": "3|4|6|7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "overlap_kind":   {"type": "str", "default": "partial", "valid": "partial"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return {(r - rmin, c - cmin) for r, c in cells}


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return set(cells)


def _grow(rng, base, avoid, k):
    cur = set(base)
    for _ in range(k):
        frontier = [(r + dr, c + dc) for (r, c) in cur for dr, dc in _CARD
                    if (r + dr, c + dc) not in cur and (r + dr, c + dc) not in avoid]
        if not frontier:
            break
        cur.add(rng.choice(frontier))
    return cur


def _gen_pair(rng):
    """Two connected polyominoes whose NORMALIZED forms partially overlap."""
    for _ in range(300):
        base = _rand_poly(rng, rng.randint(2, 4))   # shared connected core
        a = _grow(rng, base, set(), rng.randint(1, 3))
        b = _grow(rng, base, a - base, rng.randint(1, 3))
        na, nb = _norm(a), _norm(b)
        if (na & nb) and (na - nb) and (nb - na):
            return sorted(na), sorted(nb)
    return [(0, 0), (0, 1), (1, 0)], [(0, 0), (0, 1), (1, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 control cell in {3,4,6,7}, ≥1 color-1 cell, ≥1 color-2 cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    flat = [v for row in grid for v in row]
    controls = [v for v in flat if v in (3, 4, 6, 7)]
    if not controls:
        errs.append("expected ≥1 control cell in {3,4,6,7}; found none")
    if 1 not in flat:
        errs.append("expected ≥1 color-1 cell (shape a); found none")
    if 2 not in flat:
        errs.append("expected ≥1 color-2 cell (shape b); found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 16, 22)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 13, 18)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = ctx.draw_choice("control_color", [3, 4, 6, 7])

    na, nb = _gen_pair(rng)
    sh1 = max(r for r, _ in na) + 1; sw1 = max(c for _, c in na) + 1
    sh2 = max(r for r, _ in nb) + 1; sw2 = max(c for _, c in nb) + 1
    # color-1 shape in the left band, color-2 shape in the right band
    half = w // 2
    r1 = rng.randint(1, max(1, h - sh1 - 1)); c1 = rng.randint(1, max(1, half - sw1 - 1))
    for dr, dc in na:
        g[r1 + dr][c1 + dc] = 1
    r2 = rng.randint(1, max(1, h - sh2 - 1)); c2 = rng.randint(half + 1, max(half + 1, w - sw2 - 1))
    for dr, dc in nb:
        g[r2 + dr][c2 + dc] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    a = PLUS_5
    b = [(0, 0), (0, 1), (1, 1), (2, 1)]
    if name == "no_control":
        # both shapes but no control → operation undefined
        paint_at(g, h - 5, 1, a, 1)
        paint_at(g, 2, w - 5, b, 2)
        return g
    if name == "no_blob_1":
        # control + only color-2 shape → operand missing
        g[0][0] = 4
        paint_at(g, 2, w - 5, b, 2)
        return g
    if name == "no_blob_2":
        # control + only color-1 shape → operand missing
        g[0][0] = 6
        paint_at(g, h - 5, 1, a, 1)
        return g
    return g
