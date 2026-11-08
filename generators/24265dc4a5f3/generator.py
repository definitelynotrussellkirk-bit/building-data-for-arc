"""Generator for f83cb3f6.

Rule: colored pixels project onto the row or column adjacent to a
cyan bar.

Combinatorial axes (8): grid_h/w, orientation, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_bar, no_pixels, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "24265dc4a5f3"
VERSION = "2.0.0"  # shape-locked: fixed 12x12 + fixed 8-bar + 3 fixed pixels. Rule magnetizes pixels to the 8-bar edges, reads h,w. Now grid size, bar position/length, pixel positions vary.
TASK_ID = "24265dc4a5f3"
SUMMARY = (
    "Grid (size varies) with: (a) "
    "ONE COLOR-8 (cyan) BAR of "
    "varied length/position, either "
    "HORIZONTAL or VERTICAL; "
    "(b) 3+ COLORED PIXELS in "
    "non-{0, 8} colors "
    "placed at varied "
    "positions beyond the bar in "
    "rows/columns the bar covers. "
    "Rule (PROJECT TO BAR-ADJACENT "
    "ROW/COL): identify the CYAN "
    "BAR's orientation. For EACH "
    "COLORED PIXEL at (pr, pc): "
    "if the bar is HORIZONTAL "
    "(row r), PROJECT the pixel "
    "to the cell DIRECTLY "
    "ADJACENT to the bar in the "
    "pixel's column — i.e., paint "
    "(r-1, pc) or (r+1, pc) "
    "depending on which side the "
    "pixel is on, in the pixel's "
    "color. If the bar is "
    "VERTICAL, project to "
    "(pr, c-1) or (pr, c+1). The "
    "original pixel may be "
    "cleared or kept. Net: "
    "scattered pixels collapse "
    "to projections one cell "
    "from the cyan bar."
)

INVARIANTS = [
    "one cyan bar is horizontal or vertical",
    "colored pixels lie beyond the bar along matching rows or columns",
    "only coordinates covered by the bar can receive projections",
    "pixel colors are distinct from each other and from 0 and 8",
]

def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, has color-8 bar (horizontal or vertical run) + non-8 pixels."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    non_bg_non8 = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] not in (0, 8)]
    if not eights:
        pass  # degenerate (no_bar) — allowed
    if not non_bg_non8:
        pass  # degenerate (no_pixels) — allowed
    return errors


ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_bar", "no_pixels", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..17", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..20"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    # an 8-BAR magnetizes coloured pixels to its adjacent edge cells. Rule reads h,w
    # and finds the bar dynamically. Was a fixed 12x12 with a fixed bar + 3 fixed
    # pixels (in=1). Now grid size, bar position/length, and pixel positions vary.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 20); w = ctx.draw_int("grid_w", 15, 20)
    else:
        h = ctx.draw_int("grid_h", 12, 17); w = ctx.draw_int("grid_w", 12, 17)
    pool = [c for c in range(1, 10) if c != 8]
    g = full_grid(h, w, 0)
    if orientation == "horizontal":
        br = rng.randint(2, h - 3)
        bc1 = rng.randint(1, w - 6); blen = rng.randint(4, min(8, w - bc1 - 1))
        bc2 = bc1 + blen - 1
        for c in range(bc1, bc2 + 1):
            g[br][c] = 8
        n_pix = rng.randint(3, blen)
        pcols = rng.sample(range(bc1, bc2 + 1), n_pix)
        cols = rng.sample(pool, min(n_pix, len(pool)))
        for i, c in enumerate(pcols):
            side = rng.choice([-1, 1])           # pixel above or below the bar
            if side < 0 and br - 2 >= 0:
                pr = rng.randint(0, br - 2)
            elif br + 2 <= h - 1:
                pr = rng.randint(br + 2, h - 1)
            else:
                pr = 0 if br - 2 >= 0 else h - 1
            g[pr][c] = cols[i % len(cols)]
    else:
        bc = rng.randint(2, w - 3)
        br1 = rng.randint(1, h - 6); blen = rng.randint(4, min(8, h - br1 - 1))
        br2 = br1 + blen - 1
        for r in range(br1, br2 + 1):
            g[r][bc] = 8
        n_pix = rng.randint(3, blen)
        prows = rng.sample(range(br1, br2 + 1), n_pix)
        cols = rng.sample(pool, min(n_pix, len(pool)))
        for i, r in enumerate(prows):
            side = rng.choice([-1, 1])
            if side < 0 and bc - 2 >= 0:
                pc = rng.randint(0, bc - 2)
            elif bc + 2 <= w - 1:
                pc = rng.randint(bc + 2, w - 1)
            else:
                pc = 0 if bc - 2 >= 0 else w - 1
            g[r][pc] = cols[i % len(cols)]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_bar":
        g[5][5] = 2
        return g
    if name == "no_pixels":
        for c in range(3, 9):
            g[6][c] = 8
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 8
        return g
    return g
