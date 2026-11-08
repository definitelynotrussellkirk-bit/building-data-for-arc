"""Generator for arc_puzzle_bank_21_set6:medium_f01 — recolor objects by hole count.

Rule: each connected component has a 'hole count' (number of bg-cells
fully enclosed by it). The component is recolored according to a fixed
hole-count → color mapping.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_solid, all_holed, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "3d0427aad724"
VERSION = "1.2.0"  # stronger self_check for hollow frames
TASK_ID = "3d0427aad724"

SUMMARY = "1-2 hollow rectangles + 0-1 solid blob in distinct colors."

INVARIANTS = [
    "background is 0",
    "1-2 hollow rectangular frames (≥3×3) in distinct colors (each has 1+ enclosed holes)",
    "0-1 small solid blob (no holes) in another color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_solid", "all_holed", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "frames_plus_solid",
                       "valid": "frames_plus_solid"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify at least one hollow rectangular frame plus valid object colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        return ["no non-zero cells found"]
    hollow_frames = 0
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 >= 2 and c1 - c0 >= 2:
            border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                      if r in (r0, r1) or c in (c0, c1)}
            if border == set(cells):
                hollow_frames += 1
    if hollow_frames < 1:
        errs.append("expected at least one hollow rectangular frame")
    return errs


def _free(g, r1, c1, r2, c2):
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
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        n_frames = rng.randint(1, 2)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_frames + 1)
        ok = True
        for i in range(n_frames):
            placed = False
            for _ in range(80):
                fh = rng.choice([3, 4]); fw = rng.choice([3, 4])
                r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, colors[i])
                placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue
        for _ in range(40):
            r0 = rng.randint(0, h - 2); c0 = rng.randint(0, w - 2)
            if not _free(g, r0, c0, r0 + 1, c0 + 1): continue
            g[r0][c0] = colors[-1]; g[r0][c0 + 1] = colors[-1]
            break
        return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "all_solid":
        # all objects hole-count 0 → all recolored same; no aspect signal
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 4
        for r in range(3):
            for c in range(3): g[3 + r][5 + c] = 6
        return g
    if name == "all_holed":
        # all objects are frames (hole-count 1) → all recolored same
        draw_frame(g, 1, 1, 3, 3, 4)
        draw_frame(g, 1, 6, 3, 8, 6)
        return g
    if name == "no_objects":
        # blank → no objects, rule has no effect
        return g
    return g
