"""Generator for 1be83260.

Rule: a marker slot provides colors for a clean dice-mask slot in a
tiled output.

Combinatorial axes (8): grid_h/w, base_color, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_markers, no_clean, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ba241e7c5f9"
VERSION = "2.0.1"  # was hardcoded 2x2 of SOLID 5x5 slots, base=1, fixed 11x11 -> output was solid color blocks (the clean dice-MASK did nothing) + shape-locked. Rule detects slot geometry dynamically (runs); canonical is 3x2 of NON-SQUARE 7x5 dice-masked slots, base=2. Now vary nr/nc (incl non-square), th/tw (non-square), base color, and use a real base-border+holes mask so each output tile shows the masked SHAPE.
TASK_ID = "1ba241e7c5f9"
SUMMARY = "Marker slot provides colors for a clean dice-mask slot in a tiled output."

INVARIANTS = [
    "nonzero rows and columns form two 5x5 slot bands in each direction",
    "one slot contains marker colors at dice-pip positions",
    "one clean slot contains only the base mask color",
    "the clean mask determines which output positions receive marker-slot colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "no_clean", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng", "valid": "11..23"},
    "grid_w":         {"type": "int", "default": "rng", "valid": "11..23"},
    "base_color":     {"type": "int", "default": "rng", "valid": "1..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # The rule detects slot geometry dynamically (nr x nc bands of th x tw slots),
    # so vary all of it (incl NON-SQUARE arrangement and slots), like the canonical
    # 3x2 of 7x5. Cap tiles <= 6 so each output meta-tile gets a distinct color.
    if difficulty == "easy":
        nr, nc = 2, 2
    elif difficulty == "hard":
        nr, nc = ctx.draw_choice("arrange", [(3, 2), (2, 3), (3, 2), (2, 3), (2, 2)])
    else:
        nr, nc = ctx.draw_choice("arrange", [(2, 2), (2, 3), (3, 2)])
    # slot dims must fit the dice-pip read positions 1+2*(n-1): th >= 2*nr, tw >= 2*nc
    th = max(2 * nr + 1, ctx.draw_int("th", 5, 7))
    tw = max(2 * nc + 1, ctx.draw_int("tw", 5, 7))
    base = ctx.draw_color("base_color", exclude={0})
    n_tiles = nr * nc
    palette = ctx.draw_distinct_colors("marker_colors",
                                       n=min(n_tiles, 8), exclude={0, base})
    markers = [palette[i % len(palette)] for i in range(n_tiles)]
    # shared mask: a base BORDER (guarantees every slot row/col has a nonzero cell,
    # so the rule reads full th/tw bands) + random interior holes -> the output
    # tiles show this masked SHAPE (not a solid block) in each tile's marker color.
    mask = [[True] * tw for _ in range(th)]
    for r in range(1, th - 1):
        for c in range(1, tw - 1):
            if rng.random() < 0.4:
                mask[r][c] = False
    height = nr * th + (nr - 1)
    width = nc * tw + (nc - 1)
    g = full_grid(height, width, 0)
    marker_slot = (ctx.draw_int("ms_r", 0, nr - 1), ctx.draw_int("ms_c", 0, nc - 1))
    for ri in range(nr):
        for ci in range(nc):
            r0 = ri * (th + 1)
            c0 = ci * (tw + 1)
            for rr in range(th):
                for cc in range(tw):
                    if mask[rr][cc]:
                        g[r0 + rr][c0 + cc] = base
            if (ri, ci) == marker_slot:
                # marker colors at the dice-pip positions the rule reads per tile
                for oi in range(nr):
                    for oj in range(nc):
                        g[r0 + 1 + 2 * oi][c0 + 1 + 2 * oj] = markers[oi * nc + oj]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is nonempty, rectangular, and has nonzero cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not nonzero:
        errs.append("grid is empty (all zeros)")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_markers":
        for rs in [0, 6]:
            for cs in [0, 6]:
                for r in range(rs, rs + 5):
                    for c in range(cs, cs + 5):
                        g[r][c] = 1
        return g
    if name == "no_clean":
        for rs in [0, 6]:
            for cs in [0, 6]:
                for r in range(rs, rs + 5):
                    for c in range(cs, cs + 5):
                        g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 1
        return g
    return g
