"""Generator for arc_puzzle_bank_eighth21:E53.

Rule: overlay the image with its reflection across the horizontal midline.

Combinatorial axes (8): grid_h/w, palette_kind, marks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: already_symmetric, no_marks, marks_in_lower.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "edac81ec2559"
VERSION = "2.1.0"  # upper-half marks as small connected blobs (canonical has shapes, not scattered singles) + wider grids
TASK_ID = "edac81ec2559"
SUMMARY = (
    "0-bg grid (h~7-9, w~7-10) with 4-7 "
    "scattered MARK CELLS placed in the UPPER "
    "HALF (rows 0..h//2-1, excluding cells on "
    "the exact midline if h is odd) in various "
    "non-zero colors from {1..9}. The LOWER "
    "HALF (rows h//2..h-1) and the midline (if "
    "odd h) are entirely BACKGROUND. Rule: "
    "REFLECT the grid across the HORIZONTAL "
    "MIDLINE — for every cell (r, c) with a "
    "non-zero value v, also paint cell "
    "(h-1-r, c) with v (its mirror across the "
    "horizontal axis). Original upper-half "
    "cells STAY in place. If the midline row "
    "exists (odd h), it stays. Net: input is "
    "upper-half marks; output is the same "
    "marks ALSO appearing reflected in the "
    "lower half, creating a vertically "
    "symmetric pattern."
)

INVARIANTS = [
    "background is 0",
    "input marks are in the upper half",
    "output keeps originals and adds reflected lower-half copies",
    "height may be odd or even",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("already_symmetric", "no_marks", "marks_in_lower")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "marks":          {"type": "int", "default": "rng 4..7", "valid": "1..20"},
    "density":        {"type": "str", "default": "medium",
                       "valid": "sparse|medium|dense"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "upper_half",
                       "valid": "upper_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..7",
                          "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the canonical upper-half source pattern for horizontal reflection.

    Helpful examples must contain at least one nonzero mark, and all nonzero
    cells must be strictly above the horizontal midline. The lower half is the
    area the rule will fill by reflection; it should therefore start empty.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs

    h = len(grid)
    upper = h // 2
    nonzero = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not isinstance(v, int) or not (0 <= v <= 9):
                errs.append(f"cell ({r},{c}) has invalid color {v!r}")
            if v != 0:
                nonzero.append((r, c, v))
                if r >= upper:
                    errs.append(
                        f"nonzero mark at ({r},{c}) is not in the strict upper half"
                    )
    if not nonzero:
        errs.append("no source marks found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8); w = ctx.draw_int("grid_w", 7, 9)
        n_blobs = ctx.draw_int("marks", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 10, 14)
        n_blobs = ctx.draw_int("marks", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 12)
        n_blobs = ctx.draw_int("marks", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    upper = h // 2                                    # source rows 0..upper-1 (above midline)
    used: set[tuple[int, int]] = set()
    for _ in range(n_blobs):
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        blob = _blob(rng, rng.randint(1, 4))
        bh = max(r for r, _ in blob) + 1; bw = max(c for _, c in blob) + 1
        if bh > upper or bw > w:
            continue
        for _try in range(40):
            r0 = rng.randint(0, upper - bh); c0 = rng.randint(0, w - bw)
            cells = [(r0 + dr, c0 + dc) for dr, dc in blob]
            if any(p in used for p in cells):
                continue
            for (r, c) in cells:
                g[r][c] = color; used.add((r, c))
            break
    if not used:                                     # guarantee >=1 mark
        g[0][1] = 4
    return g


def _blob(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "already_symmetric":
        # both halves filled — rule output equals input
        for r, c, v in [(1, 2, 4), (6, 2, 4), (2, 5, 7), (5, 5, 7)]:
            g[r][c] = v
        return g
    if name == "no_marks":
        return g
    if name == "marks_in_lower":
        # marks in lower half instead of upper — rule reflects them up, but the
        # invariant says marks should be upper-only
        g[5][2] = 4
        g[6][3] = 7
        return g
    return g
