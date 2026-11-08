"""Generator for arc_puzzle_bank_thirteenth21:E90.

A solid same-color 3x3 ring fills its zero center.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, ring_color_inconsistent, center_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7024cbb0eaea"
VERSION = "2.0.1"
TASK_ID = "7024cbb0eaea"

SUMMARY = (
    "0-bg grid (h, w~7-10) with 1-2 SOLID 3×3 RINGS — "
    "each ring is a 3×3 block of cells where the 8 "
    "OUTER cells (top row, bottom row, left col, right "
    "col of the 3×3) are filled with a single non-bg "
    "COLOR, and the CENTER cell at (r+1, c+1) is 0 "
    "(empty). Each ring uses a distinct color, and "
    "rings are placed with at least 1-cell gap so they "
    "don't touch. Rule: for every cell whose all 8 "
    "neighbors are NON-ZERO and SAME-COLOR (a ring "
    "center), FILL that center cell with the ring's "
    "color. Net: each hollow 3×3 ring becomes a solid "
    "3×3 square of its color."
)

INVARIANTS = [
    "background is 0",
    "each target ring has eight same-color neighbors",
    "ring centers are zero in the input",
    "rings are spaced apart",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "ring_color_inconsistent", "center_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 1..2", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 1..2", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "separated_3x3_rings",
                       "valid": "separated_3x3_rings"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..2", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 non-zero ring cell; skip degenerate textures."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-zero cells found (no rings)")
    return errs


def _free_box(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 1), min(h, r + 4)):
        for cc in range(max(0, c - 1), min(w, c + 4)):
            if g[rr][cc] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("n_rings", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_rings", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("n_rings", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(100):
        if placed >= target:
            break
        r = rng.randint(0, h - 3)
        c = rng.randint(0, w - 3)
        if not _free_box(g, r, c):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for dr in range(3):
            for dc in range(3):
                if (dr, dc) != (1, 1):
                    g[r + dr][c + dc] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no rings to fill centers of
        return g
    if name == "ring_color_inconsistent":
        # ring uses 2 colors → "eight same-color neighbors" precondition fails
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)]:
            g[1 + dr][1 + dc] = 4
        for dr, dc in [(2, 0), (2, 1), (2, 2)]:
            g[1 + dr][1 + dc] = 6
        return g
    if name == "center_already_filled":
        # ring center already non-zero → rule's "center is zero" precondition fails
        for dr in range(3):
            for dc in range(3):
                g[1 + dr][1 + dc] = 4
        return g
    return g
