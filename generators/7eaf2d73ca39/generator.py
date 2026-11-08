"""Generator for additional_bank:M1.

Rule: horizontal green objects become 1; vertical green objects become 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, orientation_balance, texture.
Degenerates: only_horizontal, only_vertical, l_shaped_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "7eaf2d73ca39"
VERSION = "1.2.1"
TASK_ID = "7eaf2d73ca39"
SUMMARY = "Horizontal green objects become 1; vertical green objects become 8."

INVARIANTS = [
    "straight color-3 objects are separated by background",
    "both one-row and one-column green objects are present",
]

PALETTE_KINDS = ("default", "horiz_dominant", "vert_dominant", "balanced")
DEGENERATE_TEXTURES = ("only_horizontal", "only_vertical", "l_shaped_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..15"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "orientation_balance": {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Require straight green components and both nontrivial orientations.

    Match the reference rule's four-neighbor, same-color objects. Counts across
    disconnected components cannot establish that an orientation is present.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    green = components(grid, colors={3}, connectivity=4)
    if not green:
        return ["expected ≥1 color-3 (green) cell; found none"]
    errs = []
    horizontal = vertical = False
    for obj in green:
        r1, c1, r2, c2 = obj["bbox"]
        if r1 == r2 and c1 == c2:
            # A singleton is lawful to the reference, but teaches no orientation.
            continue
        if r1 == r2 and c1 < c2:
            horizontal = True
        elif c1 == c2 and r1 < r2:
            vertical = True
        else:
            errs.append("expected every green object to be straight")
    if not horizontal:
        errs.append("expected ≥1 horizontal green object; found none")
    if not vertical:
        errs.append("expected ≥1 vertical green object; found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # Place one horizontal and one vertical GREEN object with a guaranteed gap.
    # The previous default could let them CROSS into a single T-shaped blob
    # (violating INVARIANT "straight color-3 objects are separated by background")
    # and always emitted an L-shaped green distractor for large grids even though
    # l_shaped_blob is a DEGENERATE texture. Normal rows must exercise exactly the
    # two rule branches: horizontal -> 1, vertical -> 8.
    row = rng.randint(1, max(1, h // 3))
    max_start = max(1, (w // 2) - 4)
    start = rng.randint(1, max_start)
    for c in range(start, start + 4):
        g[row][c] = 3

    col_lo = min(w - 2, max(w // 2, start + 5))
    col = rng.randint(col_lo, w - 2) if col_lo <= w - 2 else w - 2
    top = rng.randint(h // 2, h - 5 if h >= 9 else h - 4)
    for r in range(top, min(h - 1, top + 4)):
        g[r][col] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "only_horizontal":
        # all green objects horizontal → "vertical → 8" branch never fires
        for c in range(1, 5):
            g[2][c] = 3
        for c in range(3, 7):
            g[6][c] = 3
        return g
    if name == "only_vertical":
        # all green objects vertical → "horizontal → 1" branch never fires
        for r in range(1, 5):
            g[r][2] = 3
        for r in range(2, 6):
            g[r][7] = 3
        return g
    if name == "l_shaped_blob":
        # an L-shape that is neither purely horizontal nor purely vertical
        for c in range(1, 5):
            g[2][c] = 3
        for r in range(2, 6):
            g[r][1] = 3
        return g
    return g
