"""Generator for arc_puzzle_bank_fourth21:M25 — show bbox corners.

Rule: replace each blob with the 4 corner cells of its bbox in its color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: line_blobs, single_cell_blobs, solid_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "d1bf9a8e4c69"
VERSION = "2.1.1"
TASK_ID = "d1bf9a8e4c69"
SUMMARY = (
    "0-bg grid (h ∈ 8-11, w ∈ 9-12) "
    "with: 2-3 DISTINCT-COLOR BLOBS, "
    "each a 3-5 cell irregular blob "
    "built via grow_blob random walk, "
    "each in a DISTINCT color drawn "
    "from {1..9}. Each blob has bbox "
    "≥2×2 (so 4 distinct corners "
    "exist). Blobs placed with "
    "non-overlapping (used-set) "
    "tracking. Rule (FOR EACH NON-BG "
    "COMPONENT, REPLACE THE ENTIRE "
    "COMPONENT WITH JUST THE 4 "
    "CORNER CELLS OF ITS BBOX (TOP-"
    "LEFT, TOP-RIGHT, BOTTOM-LEFT, "
    "BOTTOM-RIGHT), PAINTED IN THE "
    "ORIGINAL COLOR; OTHER CELLS "
    "OF THE BLOB BECOME 0): For "
    "EACH blob with bbox "
    "(rmin..rmax, cmin..cmax) and "
    "color c: CLEAR all blob "
    "cells to 0. PAINT the 4 "
    "bbox corners (rmin, cmin), "
    "(rmin, cmax), (rmax, cmin), "
    "(rmax, cmax) with color c. "
    "Net: each blob reduces to its "
    "4 corners; the bbox shape is "
    "preserved as a 4-dot pattern."
)

INVARIANTS = [
    "background is 0",
    "blobs of size >= 3, bbox at least 2x2",
    "blobs are non-rectangular OR rectangular only in ≥3×2 (so corners != solid blob)",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("line_blobs", "single_cell_blobs", "solid_rects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread_blobs",
                       "valid": "spread_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _is_solid_rectangle(cells):
    """True when the blob already equals every cell of its bounding box.

    A 2x2 solid rectangle is exactly its four bbox corners, so the canonical
    "replace by bbox corners" rule leaves it unchanged. Larger solid rectangles
    are still teachable because their interiors get cleared, but the helpful
    texture promises no solid-rect no-ops, so exclude all solid rectangles here.
    """
    if not cells:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    return len(cells) == h * w


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-zero colors (blobs); each blob color has ≥2 cells (≥3)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    counts = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if len(counts) < 2:
        errs.append(f"expected ≥2 distinct non-zero blob colors; found {len(counts)}")
    for color, cnt in counts.items():
        if cnt < 3:
            errs.append(f"blob color {color} has only {cnt} cells; expected ≥3")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=20)
            if cells is None:
                continue
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            bb_h = max(rs) - min(rs) + 1
            bb_w = max(cs) - min(cs) + 1
            if bb_h < 2 or bb_w < 2:
                continue
            if _is_solid_rectangle(cells):
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "line_blobs":
        # 1×N or N×1 lines → bbox is degenerate (only 2 distinct corners along the line)
        for c in range(1, 5): g[2][c] = 4   # horizontal line, bbox 1x4 → 2 corners
        for r in range(4, 8): g[r][8] = 6   # vertical line, bbox 4x1 → 2 corners
        return g
    if name == "single_cell_blobs":
        # 1x1 blobs → bbox has only 1 distinct corner; "4 corners" rule paints just the cell
        g[2][3] = 4; g[5][7] = 6; g[6][1] = 3
        return g
    if name == "solid_rects":
        # solid rectangles → 4 corners are part of the rect, but interior gets cleared by rule
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 4
        for r in range(5, 8):
            for c in range(6, 9): g[r][c] = 6
        return g
    return g
