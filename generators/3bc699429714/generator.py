"""Generator for arc_puzzle_bank_21_set11_s:S11_E7.

Rule: for each non-bg blob, paint only the 4 corners of its bbox in
its color (on a fresh empty grid).

Combinatorial axes (8): grid_h/w, palette_kind, num_blobs, blob_size,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: blob_1x1, no_blobs, blob_line.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "3bc699429714"
VERSION = "1.2.0"  # defect-lint identity_demo: a 2x2 block IS its own four bbox
# corners, so an all-2x2 instance was a no-op demo. Every rectangle now has at
# least one dimension >= 3; self_check enforces it.
TASK_ID = "3bc699429714"
SUMMARY = "2-3 solid rectangles in distinct colors."

INVARIANTS = [
    "≥2 solid rectangles, each ≥2×2",
    "rectangles don't touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("blob_1x1", "no_blobs", "blob_line")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_blobs":      {"type": "int", "default": "2", "valid": "2..3"},
    "blob_size":      {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8"},
    "position_bias":  {"type": "str", "default": "diagonal_corners",
                       "valid": "diagonal_corners"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3",
                          "valid": "2..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 distinct non-zero colors (one per rectangle)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    cells_by_color: dict[int, list[tuple[int, int]]] = {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                cells_by_color.setdefault(grid[r][c], []).append((r, c))
    if len(cells_by_color) < 2:
        errs.append(f"expected >=2 distinct non-zero colors, found {len(cells_by_color)}")
    for color, cells in cells_by_color.items():
        rh = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        rw = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if max(rh, rw) < 3:
            errs.append(f"color {color} block is {rh}x{rw}: its corners ARE the block "
                        f"— the rule would be invisible (need a dimension >= 3)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    # The rule keeps only bbox CORNERS: a 2x2 block equals its corners and the
    # demo shows nothing. Force one dimension >= 3 on every rectangle.
    rh1 = rng.randint(2, 4)
    rw1 = rng.randint(3, 4) if rh1 == 2 else rng.randint(2, 4)
    draw_rect(g, 1, 1, rh1, rw1, pal[0])
    rh2 = rng.randint(2, 3)
    rw2 = 3 if rh2 == 2 else rng.randint(2, 3)
    draw_rect(g, h - rh2 - 1, w - rw2 - 1, rh2, rw2, pal[1])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "blob_1x1":
        # 1×1 blobs — all 4 corners coincide at the same cell
        g[2][2] = 4
        g[5][7] = 7
        return g
    if name == "no_blobs":
        return g
    if name == "blob_line":
        # 1-row blob — bbox has zero height, top and bottom corners coincide
        for c in range(2, 6):
            g[2][c] = 4
        for r in range(2, 6):
            g[r][8] = 7
        return g
    return g
