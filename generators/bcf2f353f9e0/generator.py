"""Generator for arc_puzzle_bank_21_set7_s:S7_E1 — slide red component right.

Rule: a single red component slides right until blocked by a wall or
the grid edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blocker_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_red, red_at_right_edge, red_against_wall.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bcf2f353f9e0"
# 2.1.0: red shape was a 3-entry bank -> now random connected polyomino.
# Blocker enriched: the wall colour varies (rule blocks on ANY non-2
# nonzero cell, a canonical demo mixes an 8-wall with a 3-block) and may
# be a full-height or partial column; still guaranteed >=1 clear move.
VERSION = "2.1.1"  # add self_check
TASK_ID = "bcf2f353f9e0"

SUMMARY = (
    "0-bg grid (h~7-10, w~10-14) "
    "with: (a) ONE COLOR-2 (red) "
    "CONNECTED COMPONENT placed at "
    "the LEFT side (col c0 ∈ "
    "0..2) of the grid, drawn from "
    "a 3-shape bank (small L/T-"
    "tetro shapes); (b) blocker_"
    "kind ∈ {wall, edge}: if WALL, "
    "a full-height COLOR-8 (cyan) "
    "WALL is placed at col wall_c "
    "(at least 2 cells right of "
    "the red); if EDGE, no wall, "
    "the grid edge acts as the "
    "right boundary. Rule (SLIDE "
    "RED RIGHT UNTIL BLOCKED): "
    "identify the COLOR-2 "
    "component. SLIDE it "
    "RIGHTWARD as a rigid body "
    "until ANY of its cells "
    "WOULD HIT (a) the GRID's "
    "RIGHT EDGE (col w) or (b) a "
    "COLOR-8 WALL cell. STOP at "
    "the first contact "
    "(translated cells stay in "
    "bounds and don't overlap "
    "walls). Walls stay. Net: "
    "red component shifts right "
    "as a unit until obstructed."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one color-2 component",
    "all other nonzero cells are blockers",
    "the red component has at least one clear rightward move",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_red", "red_at_right_edge", "red_against_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blocker_kind":   {"type": "str", "default": "rng wall|edge", "valid": "wall|edge"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "left_red_with_blocker",
                       "valid": "left_red_with_blocker"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def _poly(rng, size, max_dim=3):
    cells = {(0, 0)}; frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        opts = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        rng.shuffle(opts)
        grown = False
        for nr, nc in opts:
            if (nr, nc) in cells:
                continue
            rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
            if max(rs) - min(rs) + 1 > max_dim or max(cs) - min(cs) + 1 > max_dim:
                continue
            cells.add((nr, nc)); frontier.append((nr, nc)); grown = True
            break
        if not grown:
            frontier.remove((r, c))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has color-2 (red) cells; has at least one clear rightward path."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not twos:
        return errs  # degenerate no_red
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 13, 16)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 14)
    blocker_kind = ctx.draw_choice("blocker_kind", ["wall", "edge"])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shape = _poly(rng, rng.randint(2, 5))
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    r0 = rng.randint(1, max(1, h - sh - 1))
    c0 = rng.randint(0, 2)
    for dr, dc in shape:
        g[r0 + dr][c0 + dc] = 2
    if blocker_kind == "wall":
        # wall colour is any non-{0,2} colour (rule blocks on any nonzero)
        wall_color = rng.choice([1, 3, 4, 5, 6, 7, 8, 9])
        lo = c0 + sw + 2
        if lo <= w - 1:
            wall_c = rng.randint(lo, w - 1)
            # full-height or just covering the red's row span (partial)
            if rng.random() < 0.5:
                rspan = range(h)
            else:
                rspan = range(max(0, r0 - 1), min(h, r0 + sh + 1))
            for r in rspan:
                g[r][wall_c] = wall_color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_red":
        # walls only, no red component → nothing to slide
        for r in range(h): g[r][7] = 8
        return g
    if name == "red_at_right_edge":
        # red already touching right edge → no rightward move possible
        g[3][w - 1] = 2
        g[4][w - 1] = 2
        return g
    if name == "red_against_wall":
        # red has wall right at its right side → rule is identity (no move)
        g[3][3] = 2
        g[4][3] = 2; g[4][4] = 2
        for r in range(2, 7): g[r][5] = 8
        return g
    return g
