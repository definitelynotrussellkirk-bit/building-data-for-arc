"""Generator for 21_bundle:m145 — fill ring component holes.

Rule: each rect-frame (ring) → fill its bbox-interior holes with the
ring's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, all_solid, ring_open.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, interior_cells, is_full_frame_component

GENERATOR_ID = "24bb2221ca5c"
VERSION = "2.1.0"  # add executable self_check coverage for hollow-ring inputs
TASK_ID = "24bb2221ca5c"
SUMMARY = (
    "0-bg grid (h~8-13, w~10-14) with 1-2 "
    "RECTANGULAR FRAMES (rect-OUTLINES of "
    "size 3×3 to 5×5), each in a DISTINCT "
    "non-zero color. Each frame has a HOLLOW "
    "INTERIOR (0 cells inside the rectangle's "
    "bbox bound by the colored perimeter). "
    "Frames don't 4-touch each other (≥1-cell "
    "margin between them and from grid edges). "
    "Rule: for EACH RECT-FRAME (ring), "
    "IDENTIFY its interior cells (bbox cells "
    "strictly inside the perimeter that are "
    "currently 0). FILL every interior cell "
    "with the RING'S COLOR. The frame "
    "perimeter STAYS in place. Net: each "
    "hollow ring becomes a SOLID monochrome "
    "rectangle of the ring's color."
)

INVARIANTS = [
    "background is 0",
    "≥1 rect-outline frame ≥3×3 with hollow interior",
    "frames don't 4-touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "all_solid", "ring_open")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "= n_frames", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "scattered_rings",
                       "valid": "scattered_rings"},
    "n_distinct_colors": {"type": "int", "default": "= n_frames", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


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
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for color in palette:
        for _ in range(40):
            fh = rng.randint(3, 5); fw = rng.randint(3, 5)
            r1 = rng.randint(0, h - fh)
            c1 = rng.randint(0, w - fw)
            r2 = r1 + fh - 1; c2 = c1 + fw - 1
            if _free(g, r1, c1, r2, c2):
                for c in range(c1, c2 + 1):
                    g[r1][c] = color; g[r2][c] = color
                for r in range(r1, r2 + 1):
                    g[r][c1] = color; g[r][c2] = color
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # Empty grid — rule has no ring to hole-fill.
        return g
    if name == "all_solid":
        # Solid rectangles — no interior holes, so the rule is a no-op.
        for r in range(1, 5):
            for c in range(1, 5):
                g[r][c] = 4
        for r in range(1, 5):
            for c in range(7, 10):
                g[r][c] = 6
        return g
    if name == "ring_open":
        # Frame missing one wall cell so the interior leaks to the
        # background — flood-fill from outside reaches inside, no
        # enclosed region exists.
        for c in range(1, 5):
            g[1][c] = 4; g[5][c] = 4
        for r in range(1, 6):
            g[r][1] = 4; g[r][4] = 4
        g[3][1] = 0
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    frames = [c for c in components(grid) if is_full_frame_component(c, color=c["color"], min_size=3)]
    if not frames:
        errs.append("expected at least one hollow rectangular frame")
    for frame in frames:
        interior = interior_cells(frame["bbox"])
        if not interior:
            errs.append("frame should have a non-empty interior")
        elif any(grid[r][c] != 0 for r, c in interior):
            errs.append("frame interior should be empty before hole fill")
    return errs
