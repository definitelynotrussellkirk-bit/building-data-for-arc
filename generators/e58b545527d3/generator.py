"""Generator for arc_puzzle_bank_21_set21_bundle:medium_p06 — fill enclosed region by seed color.

Rule: 1-2 hollow color-8 frames; each strictly contains a single seed cell
of another color; output fills the non-edge-touching enclosed bg region
with the seed color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_seed, frame_open.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "e58b545527d3"
VERSION = "3.0.0"  # rule fills ANY number of enclosed frame interiors; v2.1.0 capped hard n at 2 only because the SMALL grid over-packed. Enlarge hard grid (11-14 x 15-19) so n=3 places reliably, and widen frame sizes 4-6 (bigger interiors). More frames/sizes/colors.
TASK_ID = "e58b545527d3"

SUMMARY = (
    "0-bg grid (h~7-9, w~"
    "11-13) with 1-2 "
    "HOLLOW RECTANGULAR "
    "COLOR-8 (cyan) FRAMES "
    "— each a rectangle "
    "outline of width × "
    "height 4-5 (interior "
    "is 0). EACH FRAME "
    "strictly CONTAINS "
    "EXACTLY ONE SEED CELL "
    "at a random INTERIOR "
    "position (inside the "
    "frame, not on the "
    "border) in a SEED "
    "COLOR distinct from "
    "0 and 8. Frames are "
    "placed at non-"
    "touching positions "
    "(≥1-cell padding). "
    "Rule (FILL EACH "
    "ENCLOSED INTERIOR "
    "WITH ITS SEED'S "
    "COLOR): For EACH "
    "COLOR-8 FRAME: find "
    "the bg-0 cells "
    "strictly INSIDE the "
    "frame's border (the "
    "enclosed region NOT "
    "border-reachable). "
    "IDENTIFY the SEED — "
    "the lone non-0 non-"
    "8 cell inside the "
    "frame's interior; "
    "its color is C. "
    "PAINT every BG-0 "
    "cell in the interior "
    "with COLOR C. The "
    "frame border stays "
    "at 8. The seed stays "
    "at C. Net: each "
    "frame's interior "
    "becomes solid in the "
    "seed's color."
)

INVARIANTS = [
    "background is 0",
    "1-2 hollow rectangular color-8 frames at distinct positions",
    "each frame strictly contains exactly one seed cell in some non-{0, 8} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seed", "frame_open")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "8..19"},
    "n":              {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "frame_with_seed",
                       "valid": "frame_with_seed"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frame|no_seed|frame_open"},
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
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 1, 1)
    elif difficulty == "hard":
        # Enlarged grid (vs v2.1.0's 9-11 x 13-15) so three 4-6 frames each with
        # a 1-cell halo place reliably; rule fills any number of interiors.
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 15, 19)
        n = ctx.draw_int("n", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n", 1, 2)
    rng = ctx.draw_rng("layout")

    for outer in range(60):
        g = full_grid(h, w, 0)
        ok = True
        for _ in range(n):
            placed = False
            for _ in range(120):
                # r0=randint(1, h-fh-1) needs h-fh-1 >= 1 (h >= fh+2); a 6-tall frame
                # on the fixed 7-tall easy grid collapsed the range. Cap to the grid.
                fh = rng.choice([f for f in (4, 5, 6) if f <= h - 2])
                fw = rng.choice([f for f in (4, 5, 6) if f <= w - 2])
                r0 = rng.randint(1, h - fh - 1); c0 = rng.randint(1, w - fw - 1)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, 8)
                seed_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
                ir = rng.randint(r0 + 1, r0 + fh - 2)
                ic = rng.randint(c0 + 1, c0 + fw - 2)
                g[ir][ic] = seed_color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # Loose seed but no frame — rule's "fill enclosed" has
        # no enclosure to fill.
        g[3][5] = 4
        return g
    if name == "no_seed":
        # Frame but no seed inside — rule's "fill with seed
        # color" has no source; rule's fill never fires.
        draw_frame(g, 1, 2, 5, 7, 8)
        return g
    if name == "frame_open":
        # Frame missing one wall (3-walled) — rule's "enclosed
        # region" is connected to the outside; fill leaks out
        # or never fires.
        for c in range(2, 8): g[1][c] = 8
        for r in range(1, 6): g[r][2] = 8; g[r][7] = 8
        g[3][5] = 4
        return g
    return g
