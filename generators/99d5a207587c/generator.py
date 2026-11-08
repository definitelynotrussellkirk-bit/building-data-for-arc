"""Generator for arc_puzzle_bank_21_set22_bundle:medium_p05 — frame seed fill.

Rule: each rect-frame contains a single non-frame seed; fill the
interior with the seed's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_seed, multiple_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99d5a207587c"
VERSION = "2.0.1"
TASK_ID = "99d5a207587c"
SUMMARY = (
    "0-bg grid (h ∈ 8-13, w ∈ 10-14, "
    "by difficulty) with: N ∈ 1-2 "
    "HOLLOW RECTANGULAR FRAMES, each "
    "fh × fw (fh, fw ∈ 4-5) drawn at "
    "non-overlapping positions via "
    "_free check, each in a DISTINCT "
    "FRAME_COLOR drawn from a 2N-"
    "color palette (so 4 distinct "
    "colors when N=2). INSIDE EACH "
    "FRAME: ONE SINGLE SEED CELL at "
    "a random interior position, "
    "painted in a SEED_COLOR (the "
    "OTHER half of the palette, "
    "distinct from the frame color). "
    "Rule (FOR EACH RECT-FRAME, FIND "
    "THE SINGLE NON-FRAME SEED "
    "INSIDE; FILL ALL OTHER 0-CELLS "
    "OF THE FRAME'S INTERIOR WITH "
    "THE SEED'S COLOR; FRAME "
    "OUTLINE AND SEED CELL "
    "PRESERVED): For EACH rect-"
    "frame: COMPUTE its INTERIOR "
    "(cells strictly inside the "
    "outline). READ the unique "
    "non-frame-color seed cell "
    "inside → seed_color. PAINT "
    "all 0 cells in the interior "
    "with seed_color. Outline "
    "stays frame_color. Net: each "
    "frame's interior floods with "
    "its seed's color."
)

INVARIANTS = [
    "background is 0",
    "≥1 rect-frame ≥4×4 with one seed (different color) inside",
    "frames don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seed", "multiple_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "frame_with_seed",
                       "valid": "frame_with_seed"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..4"},
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 rectangular frame outline; frame interior has ≥1 non-frame non-bg cell (seed)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    found_framed_seed = False
    from collections import defaultdict
    pos: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                pos[v].append((r, c))
    for frame_color, cells in pos.items():
        if len(cells) < 6:
            continue  # too small to be a frame
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 - r1 < 2 or c2 - c1 < 2:
            continue
        # Check it's a frame (all cells on border of bbox)
        bbox_border = {(r1, c) for c in range(c1, c2 + 1)} | {(r2, c) for c in range(c1, c2 + 1)} | \
                      {(r, c1) for r in range(r1, r2 + 1)} | {(r, c2) for r in range(r1, r2 + 1)}
        if not set(cells).issubset(bbox_border):
            continue
        # Check interior has a seed
        interior = any(grid[r][c] not in (0, frame_color)
                       for r in range(r1 + 1, r2) for c in range(c1 + 1, c2))
        if interior:
            found_framed_seed = True
            break
    if not found_framed_seed:
        return ["no rectangular frame with an interior seed cell found"]
    return []


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
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2 * n)
    for i in range(n):
        for _ in range(40):
            fh = rng.randint(4, 5); fw = rng.randint(4, 5)
            r1 = rng.randint(0, h - fh)
            c1 = rng.randint(0, w - fw)
            r2 = r1 + fh - 1; c2 = c1 + fw - 1
            if _free(g, r1, c1, r2, c2):
                fc = palette[2 * i]
                sc = palette[2 * i + 1]
                for c in range(c1, c2 + 1):
                    g[r1][c] = fc; g[r2][c] = fc
                for r in range(r1, r2 + 1):
                    g[r][c1] = fc; g[r][c2] = fc
                interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
                sr, sc_pos = rng.choice(interior)
                g[sr][sc_pos] = sc
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # Loose seed dots but no frame — rule's "fill frame
        # interior" has no frame to fill.
        g[3][3] = 4; g[5][7] = 6
        return g
    if name == "no_seed":
        # Frame but no seed inside — rule's "seed → fill color"
        # has no source; rule's fill branch never fires.
        for c in range(2, 7): g[2][c] = 4; g[6][c] = 4
        for r in range(2, 7): g[r][2] = 4; g[r][6] = 4
        return g
    if name == "multiple_seeds":
        # Two distinct-color seeds inside one frame — rule's
        # "single seed → fill color" tie-break is ambiguous.
        for c in range(2, 7): g[2][c] = 4; g[6][c] = 4
        for r in range(2, 7): g[r][2] = 4; g[r][6] = 4
        g[3][4] = 6; g[4][5] = 7
        return g
    return g
