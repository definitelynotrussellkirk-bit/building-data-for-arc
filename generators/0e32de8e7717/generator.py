"""Generator for arc_additional_puzzles_21_set16_bundle:E111 — Iteratively complete 2x2 blocks.

Rule: scan 2x2 windows; whenever 3 of 4 cells are same non-zero,
fill the 4th. Iterate until stable.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l, length_2_l, full_squares.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0e32de8e7717"
VERSION = "1.3.0"  # 1.2.0->1.3.0: guarantee the requested number of fillable L/2x2-completion triggers
TASK_ID = "0e32de8e7717"
SUMMARY = "2-3 L-shaped 3-cell groups of distinct colors, well separated."

INVARIANTS = [
    "2-3 L-shapes (3 cells of the same color forming an L)",
    "each L's missing 4th cell is 0 (the corner to fill)",
    "shapes well-separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l", "length_2_l", "full_squares")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "separated_l_triominoes",
                       "valid": "separated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

LSHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        ns_lo, ns_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        ns_lo, ns_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 6, 11)
        w = ctx.draw_int("grid_w", 8, 13)
        ns_lo, ns_hi = 2, 4
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n_shapes = rng.randint(ns_lo, ns_hi)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_shapes)
    placed = []
    for color in palette:
        if not _place_l(g, rng, color, placed):
            # The sampled grid sizes always have enough 2x2 windows for the
            # requested count; failing closed here is better than silently
            # emitting a one-shape example that hides the iterative-completion
            # rule.  self_check catches this if future axes make it impossible.
            raise RuntimeError("could not place requested L completion trigger")
    return g


def _place_l(g, rng, color, placed):
    h, w = len(g), len(g[0])
    # First preserve the old pedagogical spacing.  If the sampled anchors are too
    # tight for the requested hard/default count, relax the anchor gap while still
    # requiring the 2x2 trigger window itself to be empty before painting.
    for min_sep in (4, 3, 2, 1, 0):
        choices = []
        for shape in LSHAPES:
            for r0 in range(h - 1):
                for c0 in range(w - 1):
                    choices.append((shape, r0, c0))
        rng.shuffle(choices)
        for shape, r0, c0 in choices:
            if min_sep and any(abs(r0 - pr) < min_sep and abs(c0 - pc) < min_sep
                               for pr, pc in placed):
                continue
            if any(g[r0 + dr][c0 + dc] != 0 for dr in range(2) for dc in range(2)):
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            placed.append((r0, c0))
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_l":
        # blank → no L-shapes to complete
        return g
    if name == "length_2_l":
        # 2-cell groups → not 3-of-4, rule won't fire
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(4, 4), (5, 4)]: g[r][c] = 6
        return g
    if name == "full_squares":
        # 2x2 already complete → no missing 4th to fill
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
        return g
    return g


def _fillable_windows(grid):
    out = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            vals = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
            nz = [v for v in vals if v != 0]
            if len(nz) == 3 and len(set(nz)) == 1 and vals.count(0) == 1:
                out.append((r, c, nz[0]))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    wins = _fillable_windows(grid)
    if difficulty == "easy":
        allowed = (2, 3)
    elif difficulty == "hard":
        allowed = (3, 4, 5)
    else:
        allowed = (2, 3, 4)
    if len(wins) not in allowed:
        errors.append(f"expected {allowed} fillable 2x2 windows, found {len(wins)}")
    colors = [color for _r, _c, color in wins]
    if len(colors) != len(set(colors)):
        errors.append("fillable L triggers should use distinct colors")
    allowed_cells = set()
    for r, c, color in wins:
        cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
        if sum(1 for rr, cc in cells if grid[rr][cc] == color) != 3:
            errors.append("each trigger window must contain exactly three cells of its color")
            break
        allowed_cells.update((rr, cc) for rr, cc in cells if grid[rr][cc] != 0)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0 and (r, c) not in allowed_cells:
                errors.append("all nonzero cells must belong to a fillable L trigger")
                return errors
    return errors
