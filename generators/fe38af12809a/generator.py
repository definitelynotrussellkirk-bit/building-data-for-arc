"""Generator for arc_additional_puzzle_bank_volume11:M72 -- red-distance ring.

Rule: a top-row code gives Manhattan radius 1 or 3; zeros/red cells at
that radius become 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, radius,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_code, no_red_seed, code_radius_too_large.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fe38af12809a"
VERSION = "2.2.0"  # wider grids, clipped rings (seed anywhere below row 0), broader body decor colors + counts
TASK_ID = "fe38af12809a"
SUMMARY = (
    "0-bg grid with: (a) one CODE cell in row 0 with value 1 or 3 "
    "(the Manhattan radius k); (b) one RED (color-2) SEED cell "
    "anywhere below row 0 — the radius-k Manhattan diamond around it "
    "may run off the grid edges (a clipped/partial ring); (c) "
    "scattered decoration cells in colors {1,3,4..9} (never 2, never "
    "in row 0, never exactly on the ring). Rule: find the first 1/2/3 "
    "cell in row 0 → k. Find the first color-2 seed. For each cell, "
    "if its value is 0 OR 2 AND its Manhattan distance from the seed "
    "equals k, set it to 8. Other cells preserved."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one CODE cell in row 0 with value 1 or 3 (the radius k)",
    "exactly one color-2 SEED cell in rows 1+ (so it's not confused with the code)",
    "the radius-k ring may be clipped by grid edges (partial diamond allowed)",
    "at least one in-bounds ring cell is 0/2 (the transformation is never trivial)",
    "decoration cells are never color 2, never in row 0, never exactly on the ring",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "no_red_seed", "code_radius_too_large")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-9 easy / 9-14 med / 13-20 hard", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "6-9 easy / 9-14 med / 13-20 hard", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "radius":         {"type": "choice", "default": "rng {1,3}", "valid": "1 or 3"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "code_row0_with_red_seed",
                       "valid": "code_row0_with_red_seed"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_code|no_red_seed|code_radius_too_large"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        n_decor = ctx.draw_int("n_decor", 0, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 20)
        w = ctx.draw_int("grid_w", 13, 20)
        n_decor = ctx.draw_int("n_decor", 4, 10)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        n_decor = ctx.draw_int("n_decor", 2, 6)
    # k is the code value, read from row 0; only 1 or 3 are usable (radius 2 would be
    # a color-2 code, which the seed-finder would mistake for the seed). Offer radius 3
    # whenever distance-3 cells can land in-bounds.
    radius_choices = [1, 3] if max(h, w) >= 6 else [1]
    radius = ctx.draw_choice("radius", radius_choices)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    code_col = rng.randint(0, w - 1)
    g[0][code_col] = radius

    # Seed may sit ANYWHERE below row 0 — the Manhattan diamond is allowed to run off
    # the edges (a clipped ring), which multiplies distinct outputs. Require the seed
    # to keep >=1 in-bounds ring cell that is 0 (so the transformation is never trivial).
    seed_spots = [(r, c) for r in range(1, h) for c in range(w)]
    rng.shuffle(seed_spots)
    sr, sc = seed_spots[0]
    for (cr, cc) in seed_spots:
        ring = [(cr + dr, cc + dc) for dr in range(-radius, radius + 1)
                for dc in (radius - abs(dr), -(radius - abs(dr)))]
        if any(0 <= rr < h and 0 <= ccc < w and g[rr][ccc] == 0 for rr, ccc in ring):
            sr, sc = cr, cc
            break
    g[sr][sc] = 2

    placed_decor = 0
    for _ in range(n_decor * 6):
        if placed_decor >= n_decor:
            break
        r = rng.randint(1, h - 1)            # decor never in row 0 (would shift k)
        c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        # Never sit exactly on the ring (the rule would convert 0/2 there; keep clean).
        if abs(r - sr) + abs(c - sc) == radius:
            continue
        # Body decor may be 1 or 3 (k only reads ROW 0) but never 2 (a second red seed).
        g[r][c] = rng.choice([1, 3, 4, 5, 6, 7, 8, 9])
        placed_decor += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_code":
        # row 0 empty → no radius code, ring undefined
        g[4][4] = 2
        return g
    if name == "no_red_seed":
        # code present but no red seed → no center for the ring
        g[0][1] = 3
        return g
    if name == "code_radius_too_large":
        # radius too large → ring extends beyond grid (mostly out-of-bounds)
        g[0][1] = 3
        g[1][1] = 2   # red seed near edge — ring at distance 3 mostly out
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    h,w=len(grid),len(grid[0]); msgs=[]
    codes=[(c,v) for c,v in enumerate(grid[0]) if v in (1,3)]
    seeds=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if r>0 and v==2]
    if len(codes)!=1: msgs.append(f"expected exactly one row-0 radius code, got {len(codes)}")
    if len(seeds)!=1: msgs.append(f"expected exactly one red seed below row 0, got {len(seeds)}")
    if len(codes)==1 and len(seeds)==1:
        radius=codes[0][1]; sr,sc=seeds[0]
        ring=[(sr+dr, sc+dc) for dr in range(-radius,radius+1) for dc in {radius-abs(dr), -(radius-abs(dr))}]
        if not any(0<=r<h and 0<=c<w and grid[r][c] in (0,2) for r,c in ring): msgs.append("ring must have at least one in-bounds convertible cell")
        for r,row in enumerate(grid):
            for c,v in enumerate(row):
                if r>0 and v not in (0,2) and abs(r-sr)+abs(c-sc)==radius: msgs.append("decor must not sit on the ring"); return msgs
    return msgs
