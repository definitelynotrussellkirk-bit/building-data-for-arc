"""Generator for arc_puzzle_bank_21_set7_s:S7_M5 — slide objects to the wall, keep the farthest.

REAL rule (verified from canonical Racket): COLOR-8 cells are immovable WALLS.
Every other (non-8) connected object is slid RIGHT until it hits a blocker
(another non-bg cell or the grid edge). The object that travels the FARTHEST
(ties: topmost, then leftmost, then lowest color) is selected, and the OUTPUT
is a blank grid containing ONLY that object at its final slid position, in its
original color. Output size == input size.

The previous body drew a 6-panel color-9 gallery ("find the matching pair"),
which is a DIFFERENT task — the slide rule ran on it but the distribution was
wrong (9-dividers treated as slideable columns). This rewrite builds the real
distribution: a color-8 wall (right edge) plus several non-8 objects placed in
separate row bands so each slides independently toward the wall; the leftmost
(farthest-travelling) object is the answer.

Degenerates: no_wall, no_objects, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "65ff8a28f79a"
VERSION = "3.0.1"  # WRONG-TASK rewrite: drew 6-panel 9-divider gallery; real rule slides non-8 objects right toward color-8 walls and outputs the farthest-travelling one. Now: color-8 wall + non-8 objects in separate row bands, varied shapes/positions/sizes.
TASK_ID = "65ff8a28f79a"

SUMMARY = (
    "0-bg grid with a COLOR-8 (maroon) WALL down the right edge and several "
    "non-8 connected OBJECTS (distinct colors, random small polyominoes) placed "
    "in separate row bands at varied starting columns. Rule: slide every non-8 "
    "object RIGHT until blocked; the object that travels the FARTHEST (ties: "
    "topmost / leftmost / lowest color) is emitted ALONE at its final position "
    "on a blank grid, in its colour. Output size == input size."
)

INVARIANTS = [
    "background is 0",
    "at least one color-8 wall cell is present",
    ">=1 non-8 object; objects occupy separate row bands (independent slides)",
    "objects are left of the wall so they can slide right",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_wall", "no_objects", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 13..20", "valid": "8..30"},
    "n_objects":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "row_bands_left_of_wall",
                       "valid": "row_bands_left_of_wall"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-8 wall cell; ≥1 non-{0,8} object cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    has_obj = any(grid[r][c] not in (0, 8) for r in range(h) for c in range(w))
    if not has_8:
        errs.append("no color-8 wall cells found")
    if not has_obj:
        errs.append("no non-{0,8} object cells found")
    return errs


_NON8 = [1, 2, 3, 4, 5, 6, 7, 9]


def _rand_poly(rng, maxh, maxw, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= k:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen and 0 <= nr < maxh and 0 <= nc < maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 11, 14); n = ctx.draw_int("n_objects", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 16); w = ctx.draw_int("grid_w", 18, 28); n = ctx.draw_int("n_objects", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 7, 12); w = ctx.draw_int("grid_w", 13, 22); n = ctx.draw_int("n_objects", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    wall_c = w - 1
    for r in range(h):
        g[r][wall_c] = 8
    # objects in separate row bands -> each slides toward the wall independently
    n = max(1, min(n, h // 2))
    band_h = h // n
    colors = rng.sample(_NON8, min(n, len(_NON8)))
    for i, color in enumerate(colors):
        band_top = i * band_h
        band_bot = band_top + band_h - 1  # leaves >=1 row gap when band_h>obj_h
        max_ph = max(1, band_h - 1)
        poly = _rand_poly(rng, rng.randint(1, max_ph), rng.randint(1, 3),
                          rng.randint(2, 4))
        ph = max(r for r, _ in poly) + 1
        pw = max(c for _, c in poly) + 1
        if ph > (band_bot - band_top + 1) or pw > wall_c - 1:
            poly = [(0, 0)]; ph = pw = 1
        r0 = band_top + rng.randint(0, max(0, (band_bot - band_top) - ph + 1))
        c0 = rng.randint(0, max(0, wall_c - 1 - pw))
        for dr, dc in poly:
            if g[r0 + dr][c0 + dc] == 0:
                g[r0 + dr][c0 + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 13
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][w - 1] = 8
    if name == "no_wall":
        # remove the wall -> objects slide to the grid edge
        for r in range(h):
            g[r][w - 1] = 0
        g[2][2] = 3; g[2][3] = 3
        g[5][4] = 4
        return g
    if name == "no_objects":
        # only the wall -> nothing to slide
        return g
    if name == "single_object":
        g[3][2] = 4; g[4][2] = 4
        return g
    return g
