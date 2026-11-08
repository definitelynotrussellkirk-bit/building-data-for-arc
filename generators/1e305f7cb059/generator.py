"""Generator for arc_puzzle_bank_21_set16_bundle:medium_p05 — fill frame interior with seed color.

Rule: 1-2 hollow color frames each containing a single seed cell of another
color inside; output fills the frame's interior with the seed color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n, texture.
Degenerates: no_frame, no_seed, multi_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "1e305f7cb059"
VERSION = "2.1.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: non-empty grid; bg=0; has non-zero cells (frames + seed markers)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("no non-bg cells (expected frames + seed markers)")
    return errs
TASK_ID = "1e305f7cb059"

SUMMARY = (
    "0-bg grid (h~8-10, w~11-13) with 1-2 HOLLOW "
    "RECTANGULAR FRAMES (5×5 or 5×6 or 6×5 or 6×6 "
    "border-only) drawn in distinct non-bg FRAME "
    "COLORS. Each frame contains EXACTLY ONE SEED "
    "CELL at a random interior position, in a "
    "DIFFERENT non-bg SEED COLOR. Frames are 4-conn "
    "isolated from each other. Rule: for each hollow "
    "frame, identify the single SEED COLOR inside it. "
    "FILL every cell of the frame's strict INTERIOR "
    "with that SEED COLOR (replace the interior 0s — "
    "and the seed itself — with seed_color). The frame "
    "border stays in its original frame color. Net: "
    "each frame's empty interior gets flooded with the "
    "color of the single seed marker that was inside."
)

INVARIANTS = [
    "background is 0",
    "1-2 hollow rectangular frames in distinct colors",
    "each frame strictly contains exactly one seed cell in some other non-zero color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seed", "multi_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n":              {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "= 2*n", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_frames_with_seed",
                       "valid": "scattered_frames_with_seed"},
    "n_distinct_colors": {"type": "int", "default": "= 2*n", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frame|no_seed|multi_seeds"},
}


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
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        # n=3 over-packs the smallest hard grid (10×13): three 5-6 frames each
        # need a 1-cell isolation ring → ~67% of placements fail the 40-retry loop
        # → "could not realize layout". n=3 also violates the stated INVARIANT
        # ("1-2 hollow rectangular frames"). Cap at the contract max of 2.
        n = ctx.draw_int("n", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 1, 2)
    rng = ctx.draw_rng("layout")

    # 40 outer retries left ~2/3000 None-band failures: two 6-sized frames packed
    # into the smallest None grid (8×11) can have frame 1 greedily take a spot that
    # leaves no room for frame 2. Each outer iter redraws fresh sizes/positions, so
    # a higher cap (300) drives the residual to 0 without changing passing seeds
    # (they still return at the same early iteration).
    for outer in range(300):
        g = full_grid(h, w, 0)
        ok = True
        for _ in range(n):
            frame_color, seed_color = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
            placed = False
            for _ in range(80):
                fh = rng.choice([5, 6]); fw = rng.choice([5, 6])
                r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, frame_color)
                ir = rng.randint(r0 + 1, r0 + fh - 2); ic = rng.randint(c0 + 1, c0 + fw - 2)
                g[ir][ic] = seed_color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # Seed but no frame around it — rule has no frame to fill.
        g[4][6] = 4
        return g
    if name == "no_seed":
        # Frame but no seed inside — rule's "fill with seed color"
        # has no color to use.
        draw_frame(g, 1, 1, 6, 7, 3)
        return g
    if name == "multi_seeds":
        # Frame with multiple distinct seed colors inside — rule's
        # "exactly one seed" precondition fails; fill color ambiguous.
        draw_frame(g, 1, 1, 6, 7, 3)
        g[3][3] = 4; g[4][5] = 7
        return g
    return g
