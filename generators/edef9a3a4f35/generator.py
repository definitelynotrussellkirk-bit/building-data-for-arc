"""Generator for arc_puzzle_bank_fifth21:E33.

Rule: each isolated cell moves one step down-right unless blocked by the edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_blocked_cell, all_at_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "edef9a3a4f35"
VERSION = "2.1.0"  # add occupied-blocked chains (cell blocked by another cell, not just the edge)
TASK_ID = "edef9a3a4f35"

SUMMARY = (
    "0-bg grid with K (3-7) singleton non-zero cells, each in some "
    "color (1-9). The cells are placed so most have an empty cell at "
    "(r+1, c+1) (where they'd move) but ≥1 cell sits at the right or "
    "bottom edge — its (r+1, c+1) would be out of bounds, so it stays. "
    "Rule: scan all non-zero cells. For each, if (r+1, c+1) is in "
    "bounds AND empty in the input, write the value to (r+1, c+1) on a "
    "fresh output canvas. Otherwise, write it to (r, c) on the output. "
    "Output is a fresh 0-bg grid with the moved/staying cells."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "all active cells are singletons (each its own connected component)",
    ">=1 cell moves (down-right neighbor in-bounds AND empty)",
    ">=1 cell is BLOCKED: either at the right/bottom edge, OR its down-right "
    "neighbor is another cell (occupied) -> it stays put",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_blocked_cell", "all_at_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "markers":        {"type": "int", "default": "rng 3..8", "valid": "1..12"},
    "n_chain":        {"type": "int", "default": "rng 0..2", "valid": "0..3",
                       "doc": "occupied-blocked diagonal pairs (A blocked by B)"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_with_blocked_cell",
                       "valid": "scattered_with_blocked_cell"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 9)
        target = ctx.draw_int("markers", 3, 4)
        n_chain = ctx.draw_int("n_chain", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 11, 16)
        target = ctx.draw_int("markers", 5, 8)
        n_chain = ctx.draw_int("n_chain", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        target = ctx.draw_int("markers", 4, 6)
        n_chain = ctx.draw_int("n_chain", 0, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved_in: set[tuple[int, int]] = set()
    reserved_out: set[tuple[int, int]] = set()
    rcolor = lambda: rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    # one edge-blocked cell (stays because down-right is out of bounds)
    blocked = (rng.randrange(h), w - 1) if rng.randrange(2) else (h - 1, rng.randrange(w))
    g[blocked[0]][blocked[1]] = rcolor()
    reserved_in.add(blocked); reserved_out.add(blocked)

    # occupied-blocked chains: A at (br-1,bc-1) is blocked by B at (br,bc);
    # A stays at its cell, B moves to (br+1,bc+1). Exercises the
    # 'down-right neighbor occupied -> stay' branch (not just the edge).
    for _ in range(n_chain * 30):
        if n_chain <= 0:
            break
        br = rng.randint(1, h - 2); bc = rng.randint(1, w - 2)
        a = (br - 1, bc - 1); b = (br, bc); bdst = (br + 1, bc + 1)
        if any(p in reserved_in for p in (a, b, bdst)):
            continue
        if a in reserved_out or bdst in reserved_out:
            continue
        g[a[0]][a[1]] = rcolor(); g[b[0]][b[1]] = rcolor()
        reserved_in.update((a, b))
        reserved_out.update((a, bdst))   # A stays at a; B moves to bdst
        n_chain -= 1

    placed = sum(1 for r in range(h) for c in range(w) if g[r][c])
    for _ in range(300):
        if placed >= target:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        src = (r, c)
        dst = (r + 1, c + 1)
        if src in reserved_in or dst in reserved_in or dst in reserved_out:
            continue
        g[r][c] = rcolor()
        reserved_in.add(src)
        reserved_out.add(dst)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # blank → no cells to move, rule has no effect
        return g
    if name == "no_blocked_cell":
        # all cells away from right/bottom edge → all move, no anchor stays
        g[1][1] = 4; g[3][3] = 6; g[5][5] = 3
        return g
    if name == "all_at_edge":
        # all cells at right/bottom edge → all blocked, none move
        g[1][w - 1] = 4
        g[3][w - 1] = 6
        g[h - 1][2] = 3
        g[h - 1][5] = 8
        return g
    return g
