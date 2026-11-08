"""Generator for arc_puzzle_bank_21_set10_s:S10_E6 — 2-cell same-color pairs at even row/col distance → midpoint = 8.

Rule: for each color appearing exactly twice, if cells are in same
row with even col-distance OR same col with even row-distance, set
the midpoint to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, alignment,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, odd_distance_pairs, diagonal_pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b4955d9456f7"
VERSION = "2.0.1"
TASK_ID = "b4955d9456f7"
SUMMARY = (
    "0-bg grid (h~5-7, w~7-9) with 1-2 COLORS "
    "each appearing EXACTLY TWICE as ALIGNED "
    "PAIRS — same-row pair with EVEN "
    "col-distance ≥2 OR same-col pair with "
    "EVEN row-distance ≥2. Plus 1 DISTRACTOR "
    "ISOLATED CELL in another color. Rule: for "
    "EACH COLOR appearing EXACTLY TWICE, check "
    "if its 2 cells are SAME-ROW with EVEN "
    "col-distance OR SAME-COL with EVEN "
    "row-distance. If yes, COMPUTE the "
    "MIDPOINT and PAINT it with COLOR 8 "
    "(cyan). Net: each even-distance aligned "
    "pair gets a cyan dot at its midpoint."
)

INVARIANTS = [
    "≥1 color with 2 cells aligned in same row or col, even distance ≥2",
    "1-2 distractor isolated cells of other colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "odd_distance_pairs", "diagonal_pairs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "alignment":      {"type": "str", "default": "rng row|col|both", "valid": "row|col|both"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "even_distance_pairs",
                       "valid": "even_distance_pairs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color appears exactly twice in the same row or column with even spacing."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Collect per-color cell positions
    color_cells: dict[int, list[tuple[int, int]]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                color_cells.setdefault(v, []).append((r, c))
    found_pair = False
    for color, cells in color_cells.items():
        if len(cells) >= 2:
            # Check any 2-cell subset aligned h/v with even distance
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    r1, c1 = cells[i]; r2, c2 = cells[j]
                    if r1 == r2:  # same row
                        dist = abs(c2 - c1)
                        if dist >= 2 and dist % 2 == 0:
                            found_pair = True
                    elif c1 == c2:  # same col
                        dist = abs(r2 - r1)
                        if dist >= 2 and dist % 2 == 0:
                            found_pair = True
    if not found_pair:
        errs.append("expected ≥1 color with 2 cells in same row/col at even distance ≥2; found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pal = rng.sample([2, 3, 4, 5, 6, 7, 9], 3)
    r1 = rng.randint(0, h - 1)
    c1 = rng.randint(0, w - 5)
    distance = 2 * rng.randint(1, (w - c1 - 1) // 2)
    g[r1][c1] = pal[0]
    g[r1][c1 + distance] = pal[0]
    c2 = rng.randint(0, w - 1)
    r2 = rng.randint(0, h - 3)
    rdist = 2 * rng.randint(1, (h - r2 - 1) // 2)
    if g[r2][c2] == 0 and g[r2 + rdist][c2] == 0:
        g[r2][c2] = pal[1]
        g[r2 + rdist][c2] = pal[1]
    g[0][0] = pal[2] if g[0][0] == 0 else g[0][0]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # only singletons → no 2-cell pairs to find midpoints of
        g[2][3] = 4
        g[4][7] = 6
        return g
    if name == "odd_distance_pairs":
        # pairs aligned but odd distance → no integer midpoint, rule won't fire
        g[2][1] = 4; g[2][4] = 4  # distance 3 (odd)
        return g
    if name == "diagonal_pairs":
        # pairs on diagonal → "same row or col" precondition fails
        g[1][1] = 4; g[3][5] = 4
        g[5][8] = 6
        return g
    return g
