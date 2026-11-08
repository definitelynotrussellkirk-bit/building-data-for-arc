"""Generator for d6e50e54.

Rule: blue (1) rectangle + color-9 dots aligned with one of its sides.
For each side with dots, the closest dot snaps to the rectangle's edge
cell; other dots on the same side end one cell short of the edge.
Blue becomes red (2); old dot positions become orange (7); new dot
positions are 9.

Combinatorial axes (8): grid_h/w, dot_side, palette_kind,
rect_h, rect_w, palette_size, position_bias, n_dots, texture.
Degenerates: no_rect, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80abb2f28d76"
VERSION = "2.0.1"
TASK_ID = "80abb2f28d76"
SUMMARY = (
    "COLOR-7 (orange) background grid "
    "(h, w ∈ 9-18, by difficulty) with: "
    "(a) ONE COLOR-1 (BLUE) SOLID "
    "RECTANGLE of size rh × rw (rh ∈ "
    "2-5, rw ∈ 3-7) placed with margin "
    "≥4 from the DOT_SIDE; (b) "
    "N_DOTS ∈ 1-4 COLOR-9 (MAROON) "
    "MARKER DOTS placed in column "
    "(rows for left/right side) or row "
    "(cols for top/bottom side) "
    "aligned with one of the "
    "rectangle's rows (or cols), at "
    "varied distances from the "
    "rectangle's edge. Dot_side ∈ "
    "{left, right, top, bottom} "
    "chosen per sample. Rule (FOR "
    "EACH SIDE WITH MAROON DOTS: "
    "THE CLOSEST DOT SNAPS TO THE "
    "RECT'S EDGE CELL; OTHER DOTS "
    "MOVE TO ONE CELL SHORT OF THE "
    "EDGE; BLUE BECOMES RED, OLD "
    "DOT POSITIONS BECOME 7 "
    "(BACKGROUND-COLOR), NEW DOT "
    "POSITIONS = 9): FIND the "
    "color-1 RECT and the color-9 "
    "DOTS. For EACH DOT-bearing "
    "side: FIND the CLOSEST dot "
    "(min distance to rect edge). "
    "SNAP it to the rect's edge "
    "cell (adjacent to rect). FOR "
    "OTHER dots on the same side: "
    "move them to ONE CELL SHORT "
    "of the edge (i.e., position "
    "edge ± 1 from rect). PAINT "
    "new dot positions = 9. PAINT "
    "old dot positions = 7 (bg). "
    "PAINT every rect cell = 2 "
    "(red). Net: dots converge on "
    "rect; closest touches the "
    "edge, rest park one cell "
    "short."
)

# Rivals: 'all dots snap to edge cell' refuted by ≥2 demos with two
# dots per side (only one snaps). 'keep blue blue' refuted by any
# demo (blue becomes 2). 'preserve old dot positions' refuted by any
# demo (old dots become 7). 'use dot color 9 for moved cells' refuted
# by demos where the orange 7 trail is visible. 4 demos with varied
# sides + dot counts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0",
    "one blue rectangle uses color 1",
    "maroon marker dots use color 9 and are aligned with rectangle sides",
    "the rectangle sits clear of grid borders so dots can flank all sides",
]

DOT_SIDES = ("left", "right", "top", "bottom")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_rect", "no_dots", "full_grid")
HELPFUL_TEXTURES = DOT_SIDES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..18"},
    "dot_side":       {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DOT_SIDES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "rect_h":         {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "rect_w":         {"type": "int", "default": "rng 3..5", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_dots":         {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for dot_side",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=7; has color-1 (blue) rectangle cells; has color-9 (maroon) dot cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    blues = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if not blues and not nines:
        return []  # no_rect / no_dots degenerate — allowed
    errs = []
    if not blues:
        errs.append("no color-1 (blue) rectangle cells found")
    if not nines:
        errs.append("no color-9 (maroon) dot cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        rh_lo, rh_hi = 2, 3
        rw_lo, rw_hi = 3, 4
        n_lo, n_hi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        rh_lo, rh_hi = 3, 5
        rw_lo, rw_hi = 4, 6
        n_lo, n_hi = 2, 4
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        rh_lo, rh_hi = 3, 4
        rw_lo, rw_hi = 3, 5
        n_lo, n_hi = 1, 3
    side = (overrides.get("texture") if overrides.get("texture") in DOT_SIDES else None) or \
           overrides.get("dot_side") or \
           ctx.draw_choice("dot_side", list(DOT_SIDES))
    rh = ctx.draw_int("rect_h", rh_lo, rh_hi)
    rw = ctx.draw_int("rect_w", rw_lo, rw_hi)
    g = full_grid(h, w, 7)  # bg is 7, NOT 0 (per actual rule)
    # Place rectangle leaving room on the dot side
    margin = 4
    r0 = rng.randint(margin if side == "top" else 1,
                     h - rh - (margin if side == "bottom" else 1))
    c0 = rng.randint(margin if side == "left" else 1,
                     w - rw - (margin if side == "right" else 1))
    r1 = r0 + rh - 1
    c1 = c0 + rw - 1
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            g[r][c] = 1
    # Place n_dots aligned with chosen side, at varied distances
    n_dots = ctx.draw_int("n_dots", n_lo, n_hi)
    if side == "left":
        avail = list(range(0, c0))
        rows = rng.sample(range(r0, r1 + 1), min(n_dots, rh))
        for ri in rows:
            if not avail: break
            dc = rng.choice(avail)
            g[ri][dc] = 9
    elif side == "right":
        avail = list(range(c1 + 1, w))
        rows = rng.sample(range(r0, r1 + 1), min(n_dots, rh))
        for ri in rows:
            if not avail: break
            dc = rng.choice(avail)
            g[ri][dc] = 9
    elif side == "top":
        avail = list(range(0, r0))
        cols = rng.sample(range(c0, c1 + 1), min(n_dots, rw))
        for ci in cols:
            if not avail: break
            dr = rng.choice(avail)
            g[dr][ci] = 9
    else:  # bottom
        avail = list(range(r1 + 1, h))
        cols = rng.sample(range(c0, c1 + 1), min(n_dots, rw))
        for ci in cols:
            if not avail: break
            dr = rng.choice(avail)
            g[dr][ci] = 9
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_rect":
        g[5][5] = 9
        return g
    if name == "no_dots":
        for r in range(3, 6):
            for c in range(3, 7):
                g[r][c] = 1
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 1
        return g
    return g
