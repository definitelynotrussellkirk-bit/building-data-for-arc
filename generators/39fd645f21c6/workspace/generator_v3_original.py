"""Generator for arc_puzzle_bank_21_set13_s:S13_M2 — blue seed selects feature-matching object.

Rule: a blue seed object's area, hole count, and symmetry class select
matching objects.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seed, no_match, multiple_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "39fd645f21c6"
VERSION = "3.0.1"  # distinct=85: only 2 seed shapes (L/T) + fixed same-shape match + fixed plus/ring decoys at fixed spots. Now seed = RANDOM polyomino (size 3-6), 1-2 MATCH copies (identical shape -> identical area/holes/symmetry triple) in distinct colors, 1-2 DECOYS forced to a DIFFERENT area (guaranteed non-match), all scattered at random separated spots + varied grid.
TASK_ID = "39fd645f21c6"

SUMMARY = (
    "0-bg grid (h~10-13, w~13-16) with: (a) one BLUE(1) seed "
    "object (L or T shape); (b) one non-blue object with the "
    "same SHAPE as the blue seed (in a different color); (c) "
    "1-2 DECOY objects in other colors with different shapes "
    "(plus, ring). Rule: extract components. Find the blue "
    "seed. Compute its feature triple (area, hole-count, "
    "symmetry-class). For each non-blue object: if its "
    "feature triple matches the seed's → recolor its cells to "
    "8 (cyan). Else leave unchanged. Net: matching objects "
    "become cyan; decoys keep their original color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "there is exactly one blue seed object",
    "one non-blue object shares the seed's feature triple (area, holes, symmetry)",
    "other objects differ by area, holes, or symmetry class",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seed", "no_match", "multiple_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "rng 13..16", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_shape":     {"type": "str", "default": "rng l|t", "valid": "l|t"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "blue_seed_with_distractors",
                       "valid": "blue_seed_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one blue (color-1) seed object; ≥2 total nonzero colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if blues == 0:
        pass  # degenerate (no_seed) — allowed
    return errors


L_3 = [(0, 0), (1, 0), (1, 1)]
T_DOWN = [(0, 0), (0, 1), (0, 2), (1, 1)]
PLUS_5 = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
RING_8 = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 15, 16)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 13, 16)
    rng = ctx.draw_rng("layout")
    for _attempt in range(40):
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        # seed = random polyomino; MATCH copies share its exact shape (=> same
        # area/holes/symmetry triple); DECOYS use a different cell-count (=> the
        # area component of the triple differs => guaranteed non-match).
        seed_shape = _rand_poly(rng, rng.randint(3, 6))
        seed_area = len(seed_shape)
        n_match = rng.randint(1, 2)
        n_decoy = rng.randint(1, 2)
        colors = [c for c in [2, 3, 4, 5, 6, 7, 9]]
        rng.shuffle(colors)
        # color 1 (blue) = seed; matches/decoys take distinct non-blue, non-8 colors
        match_colors = colors[:n_match]
        decoy_colors = colors[n_match:n_match + n_decoy]
        jobs = [(seed_shape, 1)]
        jobs += [(seed_shape, mc) for mc in match_colors]
        for dc in decoy_colors:
            da = seed_area
            for _ in range(20):
                da = rng.randint(3, 7)
                if da != seed_area:
                    break
            jobs.append((_rand_poly(rng, da if da != seed_area else seed_area + 1), dc))
        ok = True
        for shape, color in jobs:
            if not _place(g, occ, rng, shape, color):
                ok = False
                break
        if ok:
            return g
    return g


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _place(g, occ, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
    for _ in range(60):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        # require footprint + 1-cell halo free => separate 4-connected components
        if all(0 <= r < h and 0 <= c < w and not occ[r][c]
               for (cr, cc) in cells
               for r in (cr - 1, cr, cr + 1) for c in (cc - 1, cc, cc + 1)):
            for (r, c) in cells:
                g[r][c] = color; occ[r][c] = True
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "no_seed":
        # no blue object → no seed feature triple to match
        paint_at(g, 1, 1, L_3, 4)
        paint_at(g, h - 4, 1, PLUS_5, 6)
        paint_at(g, h - 4, w - 4, RING_8, 7)
        return g
    if name == "no_match":
        # blue seed exists but no other object shares its feature triple
        paint_at(g, 1, 1, L_3, 1)
        paint_at(g, h - 4, 1, PLUS_5, 6)
        paint_at(g, h - 4, w - 4, RING_8, 7)
        return g
    if name == "multiple_matches":
        # multiple non-blue objects match the seed → ambiguous selection
        paint_at(g, 1, 1, L_3, 1)
        paint_at(g, 1, 7, L_3, 4)   # match #1
        paint_at(g, h - 4, 1, L_3, 6)   # match #2 (same shape!)
        return g
    return g
