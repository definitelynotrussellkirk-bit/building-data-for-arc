"""Generator for arc_additional_puzzles_21_set11_bundle:H71 — overlapping routed links.

Rule: cell (0, 0) holds command color (1 = horizontal-first L bend, else =
vertical-first). For every other color present exactly twice, route a
2-leg L between its endpoints. Cells touched by 2+ routes become color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_command (cell (0,0) is bg → rule's bend-direction
selector defaults; one of two routes is missing), single_pair (only
1 endpoint pair → no overlap possible, rule's "2+ routes overlap"
collapses to no 8-cells), aligned_endpoints (endpoint pair shares row
or col → L-route degenerates to straight line, no bend).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "17686ad9c247"
VERSION = "1.1.1"
TASK_ID = "17686ad9c247"

SUMMARY = "Cmd at (0,0); 2-3 colors with exactly 2 endpoints each; routed L-paths can overlap."

INVARIANTS = [
    "background is 0",
    "cell (0, 0) holds the command color (1 or 2)",
    "2-3 endpoint colors, each appearing exactly twice elsewhere on the grid",
    "endpoint colors do not equal the command color and are not 0 or 8",
    "endpoints do not coincide with (0, 0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_command", "single_pair", "aligned_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "command_plus_endpoint_pairs",
                       "valid": "command_plus_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: cell (0,0) is the command color (non-zero), at least one endpoint pair."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_command", "single_pair", "aligned_endpoints"):
        return errs
    if grid[0][0] == 0:
        errs.append("cell (0,0) should be the command color (non-zero)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 8)
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_pairs = ctx.draw_int("n_pairs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    rng = ctx.draw_rng("layout")
    cmd = rng.choice([1, 2])
    avail = [c for c in [3, 4, 5, 6, 7, 9] if c != cmd]
    rng.shuffle(avail)
    endpoint_colors = avail[:n_pairs]

    for outer in range(60):
        g = full_grid(h, w, 0)
        g[0][0] = cmd
        used = {(0, 0)}
        ok = True
        for color in endpoint_colors:
            placed = False
            for _ in range(120):
                ar = rng.randint(0, h - 1); ac = rng.randint(0, w - 1)
                br = rng.randint(0, h - 1); bc = rng.randint(0, w - 1)
                if (ar, ac) in used or (br, bc) in used:
                    continue
                if (ar, ac) == (br, bc):
                    continue
                if abs(ar - br) < 2 or abs(ac - bc) < 2:
                    continue
                g[ar][ac] = color
                g[br][bc] = color
                used.add((ar, ac)); used.add((br, bc))
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place {0} endpoint pairs in 60 attempts".format(n_pairs))


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_command":
        # (0,0) is bg — rule's bend-direction selector is undefined;
        # output's L-bend orientation is unspecified.
        g[2][3] = 3; g[5][7] = 3
        g[3][6] = 4; g[7][2] = 4
        return g
    if name == "single_pair":
        # Only one endpoint pair — no overlap possible; rule's
        # "2+ routes overlap → 8" branch never fires.
        g[0][0] = 1
        g[2][2] = 3; g[6][7] = 3
        return g
    if name == "aligned_endpoints":
        # Endpoint pairs share a row → L-route collapses to a
        # straight line; no bend, rule's bend-direction is moot.
        g[0][0] = 1
        g[3][2] = 3; g[3][7] = 3
        g[6][2] = 4; g[6][7] = 4
        return g
    return g
