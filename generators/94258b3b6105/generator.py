"""Generator for arc_puzzle_bank_21_set9_s:S9_M2.

Rule: 9-walled rect-frame contains a single seed. Cells inside the
room at odd BFS-distance from seed (through 0-cells, blocked by 9s)
get color 8. Seed stays. Walls stay.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seed, no_walls, multiple_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94258b3b6105"
VERSION = "1.2.1"  # add self_check
TASK_ID = "94258b3b6105"
SUMMARY = "Color-9 rectangular frame on a 0-bg grid, with a single color-2 seed inside the frame's interior. Rule does 4-connected BFS from the seed through cells of value {0, 2}, then paints all cells at ODD Manhattan-walk-distance from seed with color 8. Seed stays 2, walls stay 9, even-distance cells stay 0."

# Rivals: 'output is input' refuted by any demo (interior fills in
# checkerboard of 8s). 'paint all 0 cells' refuted by any demo with
# even-distance 0 cells. 'paint walls too' refuted by any demo
# (walls stay 9). 'parity is rows not BFS' refuted by an irregular
# wall layout. 3 demos with ≥3 distinct seed positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one closed 9-rect-outline frame",
    "exactly one seed (color 2) inside the room interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seed", "no_walls", "multiple_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "1", "valid": "1"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "interior_seed",
                       "valid": "interior_seed"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥4 color-9 frame cells; exactly 1 color-2 seed."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    n9 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 9)
    n2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if n9 < 8:  # minimum 4×4 frame has 12 cells; 7×7 outer → 24
        errs.append(f"expected ≥8 color-9 frame cells; got {n9}")
    if n2 != 1:
        errs.append(f"expected exactly 1 color-2 seed; got {n2}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(7, 9)
        margin = 1
    elif difficulty == "hard":
        h = rng.randint(11, 15); w = rng.randint(11, 15)
        margin = rng.randint(1, 2)
    else:
        h = rng.randint(8, 11); w = rng.randint(8, 11)
        margin = 1
    g = full_grid(h, w, 0)
    r1 = margin
    c1 = margin
    r2 = h - 1 - margin
    c2 = w - 1 - margin
    # Allow some randomness in frame size as long as interior ≥ 3x3.
    if r2 - r1 > 4:
        r1 += rng.randint(0, 1)
        r2 -= rng.randint(0, 1)
    if c2 - c1 > 4:
        c1 += rng.randint(0, 1)
        c2 -= rng.randint(0, 1)
    for c in range(c1, c2 + 1):
        g[r1][c] = 9; g[r2][c] = 9
    for r in range(r1, r2 + 1):
        g[r][c1] = 9; g[r][c2] = 9
    sr = rng.randint(r1 + 1, r2 - 1)
    sc = rng.randint(c1 + 1, c2 - 1)
    g[sr][sc] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    r1, c1 = 1, 1
    r2, c2 = h - 2, w - 2
    if name == "no_seed":
        # walls present but no seed → BFS source undefined, no odd-distance cells
        for c in range(c1, c2 + 1):
            g[r1][c] = 9; g[r2][c] = 9
        for r in range(r1, r2 + 1):
            g[r][c1] = 9; g[r][c2] = 9
        return g
    if name == "no_walls":
        # seed without surrounding walls → BFS escapes the room, parity meaningless
        g[h // 2][w // 2] = 2
        return g
    if name == "multiple_seeds":
        # two seeds in the room → odd-distance is computed from each, results conflict
        for c in range(c1, c2 + 1):
            g[r1][c] = 9; g[r2][c] = 9
        for r in range(r1, r2 + 1):
            g[r][c1] = 9; g[r][c2] = 9
        g[3][3] = 2
        g[5][5] = 2
        return g
    return g
