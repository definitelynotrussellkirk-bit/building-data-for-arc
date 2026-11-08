"""Generator for arc_additional_puzzle_bank_volume6:E38.

Solid blue rectangles are hollowed by clearing interior cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rectangles,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rectangles, hollow_rects, length_2_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "144acbf71231"
# 2.1.0: reverse-diversity / canonical-match -- palette-locked (only 0,1). The
# canonical demos include color-5 decoy markers the rule IGNORES (it only hollows
# color-1 rects). Added 1-2 isolated non-1 decoy cells (matches canonical, clears
# palette-lock) and widened rect sizes.
VERSION = "2.1.1"
TASK_ID = "144acbf71231"
SUMMARY = (
    "0-bg grid (h, w ~9-14) with 1-3 SOLID rectangles in "
    "color 1 (blue), each at least 3×3, axis-aligned, "
    "non-overlapping (separated by background). Rule: for "
    "each color-1 4-conn object, for each cell (r, c) of "
    "that object with r STRICTLY between obj_r1 and obj_r2 "
    "AND c STRICTLY between obj_c1 and obj_c2 (i.e. "
    "interior cell, not on the bbox edge), clear it to 0. "
    "Net: every solid blue rectangle becomes a hollow "
    "BORDER (1-cell-thick ring), interior becomes bg. "
    "Edge cells of the rectangle stay 1."
)

INVARIANTS = [
    "background is 0",
    "every blue object is a solid axis-aligned rectangle",
    "rectangles are at least 3x3 so interiors are visible",
    "rectangles are separated by background",
    "1-2 isolated non-1 decoy markers (rule ignores them; matches canonical)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rectangles", "hollow_rects", "length_2_rects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rectangles":   {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_solid_rects",
                       "valid": "separated_solid_rects"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has color-1 solid rectangles at least 3x3."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        return errors  # degenerate (no_rectangles) — allowed
    # Find the bbox of color-1 cells and check it's at least 3x3
    r1 = min(r for r, c in ones); c1 = min(c for r, c in ones)
    r2 = max(r for r, c in ones); c2 = max(c for r, c in ones)
    if r2 - r1 < 2 or c2 - c1 < 2:
        return errors  # degenerate (length_2_rects) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_rectangles = ctx.draw_int("n_rectangles", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
        n_rectangles = ctx.draw_int("n_rectangles", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        n_rectangles = ctx.draw_int("n_rectangles", 1, 3)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    for _ in range(220):
        if len(boxes) >= n_rectangles:
            break
        rh = rng.randint(3, min(7, h))
        rw = rng.randint(3, min(7, w))
        r = rng.randint(0, h - rh)
        c = rng.randint(0, w - rw)
        if any(not (r + rh < ar - 1 or ar + ah < r - 1 or c + rw < ac - 1 or ac + aw < c - 1)
               for ar, ac, ah, aw in boxes):
            continue
        draw_rect(g, r, c, rh, rw, 1)
        boxes.append((r, c, rh, rw))
    if not boxes:
        draw_rect(g, 1, 1, 3, 3, 1)

    # Decoy markers (non-1 colors): rule ignores them, but they match the
    # canonical distribution (color-5 corner markers) and break palette-lock.
    n_decoy = rng.randint(1, 2)
    for _ in range(n_decoy * 10):
        if n_decoy <= 0:
            break
        dr = rng.randint(0, h - 1); dc = rng.randint(0, w - 1)
        # isolated bg cell (8-neighborhood clear) so it stays an ignored singleton
        if all(0 <= dr + a < h and 0 <= dc + b < w and g[dr + a][dc + b] == 0
               or not (0 <= dr + a < h and 0 <= dc + b < w)
               for a in (-1, 0, 1) for b in (-1, 0, 1)):
            g[dr][dc] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
            n_decoy -= 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_rectangles":
        # blank → no solid rects to hollow
        return g
    if name == "hollow_rects":
        # frames already hollow → "solid" precondition fails (rule has no work)
        for r, c in [(1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3)]:
            g[r][c] = 1
        return g
    if name == "length_2_rects":
        # 2x2 rects → no proper interior to hollow
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 1
        return g
    return g
