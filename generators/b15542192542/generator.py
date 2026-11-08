"""Generator for arc_puzzle_bank_21_set3:S3_M6 — bbox corners only.

Rule: replace each blob with the 4 cells at its bbox corners.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: line_blobs, single_cell_blobs, solid_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "b15542192542"
VERSION = "2.0.1"  # add executable self_check for bbox-corner blob invariants
TASK_ID = "b15542192542"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with 2-3 BLOBS in "
    "distinct non-bg colors. Each blob is a connected "
    "polyomino of 3-5 cells with a NON-TRIVIAL bbox "
    "(min bbox dimensions 2×2, so corners are not "
    "collinear). Blobs are 4-conn isolated. Rule: for "
    "each blob, compute its axis-aligned BOUNDING BOX "
    "(rmin, cmin, rmax, cmax). REPLACE the entire blob "
    "with EXACTLY 4 CELLS at its bbox CORNERS — "
    "(rmin, cmin), (rmin, cmax), (rmax, cmin), "
    "(rmax, cmax) — painted in the blob's original "
    "color. ERASE all other cells of the blob to 0. "
    "Net: each blob becomes 4 corner dots marking the "
    "bbox extremes; the blob's interior + edges "
    "vanish."
)

INVARIANTS = [
    "background is 0",
    "blobs of size >= 3, bbox at least 2x2",
    "blobs are 4-disjoint",
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
            if max(rs) - min(rs) < 1 or max(cs) - min(cs) < 1:
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
        # 1xN or Nx1 lines → bbox has only 2 distinct corners
        for c in range(1, 6): g[2][c] = 4
        for r in range(4, 8): g[r][8] = 6
        return g
    if name == "single_cell_blobs":
        # 1x1 blobs → bbox has 1 distinct corner; rule keeps the cell, identity
        g[2][3] = 4; g[5][7] = 6; g[6][1] = 3
        return g
    if name == "solid_rects":
        # solid rectangles → corners are the rect corners; rule erases interior
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 4
        for r in range(5, 8):
            for c in range(6, 9): g[r][c] = 6
        return g
    return g



def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("ragged grid")
        return errs
    comps = _components_by_color(grid)
    if not (2 <= len(comps) <= 3):
        errs.append(f"expected 2-3 blobs, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("blob colors are not distinct")
    occupied = {(r, c) for _, cells in comps for r, c in cells}
    for color, cells in comps:
        if not (3 <= len(cells) <= 5):
            errs.append(f"blob color {color} has size {len(cells)} outside 3..5")
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        if max(rs) == min(rs) or max(cs) == min(cs):
            errs.append(f"blob color {color} has degenerate bbox")
        for r, c in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in occupied and nb not in cells:
                    errs.append(f"blob color {color} touches another blob")
                    return errs
    return errs
