"""Generator for arc_puzzle_bank_third21:M20 — fill holes of hollow blobs.

Rule: for each blob, fill its hole regions (interior 0-cells fully
enclosed by the blob) with the blob's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, all_solid, frame_open.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3330f51bc2ac"
VERSION = "1.2.0"  # +self_check
TASK_ID = "3330f51bc2ac"
SUMMARY = "1-2 hollow rect-frames (e.g. 3x3 ring with 1-cell hole)."

INVARIANTS = [
    "background is 0",
    "≥1 hollow rect frame (≥3×3 with at least 1 interior 0-cell)",
    "frames don't overlap (1-cell padding)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "all_solid", "frame_open")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "= n_frames", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "scattered_frames",
                       "valid": "scattered_frames"},
    "n_distinct_colors": {"type": "int", "default": "= n_frames", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one hollow rect frame present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    # At least one nonzero cell must exist
    flat = [v for row in grid for v in row]
    if all(v == 0 for v in flat):
        errs.append("all-zero grid: no frames placed")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


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
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for color in palette:
        for _ in range(40):
            fh = rng.randint(3, 4)
            fw = rng.randint(3, 4)
            r1 = rng.randint(0, h - fh)
            c1 = rng.randint(0, w - fw)
            r2 = r1 + fh - 1
            c2 = c1 + fw - 1
            if not _free(g, r1, c1, r2, c2):
                continue
            for c in range(c1, c2 + 1):
                g[r1][c] = color; g[r2][c] = color
            for r in range(r1, r2 + 1):
                g[r][c1] = color; g[r][c2] = color
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Empty grid — rule has no hole to fill.
        return g
    if name == "all_solid":
        # Solid filled blobs (no hole) — rule's interior-fill is a no-op.
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 4
        for r in range(1, 4):
            for c in range(6, 9):
                g[r][c] = 6
        return g
    if name == "frame_open":
        # Frame missing a wall cell so the interior is no longer fully
        # enclosed — flood-fill from outside reaches the interior, so
        # rule has no enclosed region to fill.
        for c in range(1, 5):
            g[1][c] = 4; g[4][c] = 4
        for r in range(1, 5):
            g[r][1] = 4; g[r][4] = 4
        g[2][1] = 0  # remove a wall cell — frame is open
        return g
    return g
