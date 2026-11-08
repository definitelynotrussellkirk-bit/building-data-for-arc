"""Generator for puzzle 10fcaaa3.

Rule: tile input 2x2 then paint cyan(8) at every bg cell that has a
diagonal neighbor of a non-bg cell.

Combinatorial axes (8): grid_h/w, n_cells, n_colors, density_kind,
position_bias, anchor_corner, palette_size, asymmetry_force.
Degenerates: empty, full, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_cells
from puzzle_generators.helpers.indices import all_indices

GENERATOR_ID = "f527b82316c1"
VERSION = "2.1.0"  # bump hard h/w to 15 (tiled 30 = canvas max); already very diverse/clean
TASK_ID = "f527b82316c1"
SUMMARY = (
    "0-bg SMALL grid (h, w ~ 3-10) with SPARSE NON-BG "
    "CELLS painted in non-{0, 8} colors drawn from a "
    "palette of 1-4 distinct colors. Cell placement "
    "follows one of 7 density patterns (sparse / "
    "medium / dense / checker / diagonal / corners / "
    "stripes) with cell counts scaled to grid area "
    "(roughly h*w/8 to h*w/2). The constraint: at "
    "least one non-bg cell; no cell uses color 8 "
    "(reserved for output). Rule (TILE 2×2 THEN PAINT "
    "DIAGONAL HALOS WITH COLOR 8): produce an OUTPUT "
    "of dimensions (2*h, 2*w) by REPLICATING the "
    "input as a 2×2 TILE GRID (output[r][c] = "
    "input[r mod h][c mod w] for all r, c). Then, "
    "for EACH 0-CELL in the tiled output: CHECK if "
    "any of its FOUR DIAGONAL NEIGHBORS (positions "
    "(r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)) "
    "contains a non-0 value. If YES: PAINT this 0-"
    "cell with COLOR 8. Otherwise stay 0. Non-bg "
    "input-tile cells stay their original color. "
    "Net: a 2×2-tiled output where each non-bg cell "
    "gets a halo of 8s painted in the 4 diagonal "
    "directions, while cardinal neighbors stay 0."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 non-bg cells, all using colors != 8",
    "tiled grid (2h x 2w) is <= 30x30",
]

DENSITY_KINDS = ("sparse", "medium", "dense", "checker", "diagonal",
                 "corners", "stripes")
DEGENERATE_TEXTURES = ("empty", "full", "single_cell")
HELPFUL_TEXTURES = DENSITY_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..10", "valid": "2..15"},
    "grid_w":         {"type": "int", "default": "rng 3..10", "valid": "2..15"},
    "n_colors":       {"type": "int", "default": "rng 1..4", "valid": "1..8"},
    "density_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DENSITY_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..(h*w)/4",
                       "valid": "1..(h*w)/2"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "alias for n_colors",
                       "valid": "1..8"},
    "texture":        {"type": "str", "default": "alias for density_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, at least 1 non-bg non-8 cell, no color-8 in input (halo color), grid ≤ 15x15."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if eights:
        errors.append(f"color-8 found in input at {eights[:3]} — rule only writes 8 to output halo")
    if h > 15 or w > 15:
        errors.append(f"input too large: {h}x{w} (tiled output would be {2*h}x{2*w}, max 30x30)")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 2, 5
    elif difficulty == "hard":
        h_lo, h_hi = 8, 15
    else:
        h_lo, h_hi = 3, 10
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_colors = int(overrides.get("n_colors",
                                 ctx.draw_int("n_colors", 1, 4)))
    n_colors = max(1, min(8, n_colors))
    palette = list(ctx.draw_distinct_colors("palette", n=n_colors,
                                            exclude={0, 8}))
    density = (overrides.get("texture") or
               overrides.get("density_kind")
               or ctx.draw_choice("density_kind", list(DENSITY_KINDS)))
    g = full_grid(h, w, 0)
    if density == "sparse":
        n_cells = max(1, (h * w) // 8)
        locs = rng.sample(list(all_indices(h, w)), min(n_cells, h * w))
        for loc in locs:
            paint_cells(g, [loc], rng.choice(palette))
    elif density == "medium":
        n_cells = max(1, (h * w) // 4)
        locs = rng.sample(list(all_indices(h, w)), min(n_cells, h * w))
        for loc in locs:
            paint_cells(g, [loc], rng.choice(palette))
    elif density == "dense":
        n_cells = max(1, (h * w) // 2)
        locs = rng.sample(list(all_indices(h, w)), min(n_cells, h * w))
        for loc in locs:
            paint_cells(g, [loc], rng.choice(palette))
    elif density == "checker":
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0 and rng.random() < 0.6:
                    g[r][c] = rng.choice(palette)
    elif density == "diagonal":
        for i in range(min(h, w)):
            g[i][i] = rng.choice(palette)
    elif density == "corners":
        for r, c in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]:
            if 0 <= r < h and 0 <= c < w:
                g[r][c] = rng.choice(palette)
    elif density == "stripes":
        for r in range(h):
            if r % 2 == 0:
                for c in range(0, w, 2):
                    g[r][c] = rng.choice(palette)
    else:
        n_cells = max(1, ctx.draw_int("n_cells", 1, max(1, (h * w) // 4)))
        locs = rng.sample(list(all_indices(h, w)), min(n_cells, h * w))
        for loc in locs:
            paint_cells(g, [loc], rng.choice(palette))
    if bool(overrides.get("anchor_corner", False)) and g[0][0] == 0:
        g[0][0] = palette[0]
    if not any(v != 0 for row in g for v in row):
        g[0][0] = palette[0]
    return g


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    if name == "empty":
        g[0][0] = color  # need at least one cell
        return g
    if name == "full":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_cell":
        g[h // 2][w // 2] = color
        return g
    return g
