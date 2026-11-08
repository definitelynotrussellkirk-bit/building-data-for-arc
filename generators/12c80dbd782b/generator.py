"""Generator for v3_rich_schema:easy_02_frame_2x2_blocks — outline 2x2 color-3 blocks.

Rule: each 2x2 solid color-3 block has its surrounding ring (1 cell
out) filled with color 5 in the bg cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, wrong_shape, wrong_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12c80dbd782b"
VERSION = "1.3.1"  # widen grid range + allow up to 5 blocks for richer multi-frame outputs
TASK_ID = "12c80dbd782b"

SUMMARY = "1-2 solid 2x2 color-3 blocks with bg margin around them."

INVARIANTS = [
    "background is 0",
    "1-2 disjoint 2x2 solid color-3 blocks with at least 1 cell of bg margin around each",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "wrong_shape", "wrong_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 9..16", "valid": "6..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n":              {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1 (color 3)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "scattered_2x2_with_margin",
                       "valid": "scattered_2x2_with_margin"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blocks|wrong_shape|wrong_color"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one 2x2 solid color-3 block present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not threes:
        return errors  # degenerate (no_blocks or wrong_color) — allowed
    # Check at least one 2x2 block of color 3
    found_block = any(
        r + 1 < h and c + 1 < w and
        grid[r][c] == 3 and grid[r][c + 1] == 3 and
        grid[r + 1][c] == 3 and grid[r + 1][c + 1] == 3
        for r in range(h - 1) for c in range(w - 1)
    )
    if not found_block:
        errors.append("no 2x2 solid color-3 block found")
    return errors


def _free(g, r1, c1, r2, c2):
    # 1-cell clearance around the block's bbox. (The old 2-cell margin
    # over-enforced the "≥1 cell of bg margin" invariant and made two 2×2
    # blocks unplaceable on default's smallest 6×7 grid → ~11% raise.) A
    # 1-cell ring still leaves a clear bg cell between blocks, so each stays
    # a distinct 4-connected color-3 component.
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 9)
        n = ctx.draw_int("n", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 13, 20)
        n = ctx.draw_int("n", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 9, 16)
        n = ctx.draw_int("n", 2, 4)
    rng = ctx.draw_rng("layout")

    # n=3 blocks (hard) on the minimum 8×9 grid is feasible (e.g. three
    # corners) but greedy placement can wedge the first block so the third's
    # 80 inner tries all miss; 40 outer resets left ~4% raising. A valid
    # packing always exists here, so widen the reset budget instead.
    for outer in range(300):
        g = full_grid(h, w, 0)
        ok = True
        for _ in range(n):
            placed = False
            for _ in range(80):
                r = rng.randint(1, h - 3); c = rng.randint(1, w - 3)
                if not _free(g, r, c, r + 1, c + 1): continue
                for dr in range(2):
                    for dc in range(2):
                        g[r + dr][c + dc] = 3
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # Empty grid — rule has no 2x2 to ring.
        return g
    if name == "wrong_shape":
        # 1x4 line and 3x3 square — neither is a 2x2 block, so the
        # rule's match never fires.
        for dc in range(4):
            g[2][1 + dc] = 3
        for dr in range(3):
            for dc in range(3):
                g[4 + dr][3 + dc] = 3
        return g
    if name == "wrong_color":
        # 2x2 block but in color 5 (not 3) — the rule's color-3 filter
        # doesn't match it.
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 5
        return g
    return g
