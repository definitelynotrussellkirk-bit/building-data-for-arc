"""Generator for arc_puzzle_bank_21_more:easy_b07 — Fill 0 between matching pair.

Rule: 0-cell with same non-zero value horizontally adjacent on both
sides (or vertically) → fill with that value. Horizontal precedence.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_triplets,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_triplets, gap_too_wide, no_distractor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf1bc9d143b8"
VERSION = "2.1.0"  # out_shapes 9: grid 5..7 x 7..9. Output=same dims; widen to valid (4..10 x 6..12).
TASK_ID = "bf1bc9d143b8"
SUMMARY = (
    "0-bg grid (h~5-7, w~7-9) with 2-3 HORIZONTAL endpoint "
    "TRIPLETS: each is a (color, 0, color) pattern in some "
    "row at consecutive cols (c, c+1, c+2). Plus 1-2 "
    "isolated DISTRACTOR cells that have no matching "
    "neighbor. Different triplets use varied non-bg colors. "
    "Rule: for each (r, c) with input == 0, check: HORIZONTAL "
    "match — (r, c-1) and (r, c+1) are equal non-bg → fill "
    "(r, c) with that color. Else VERTICAL match — (r-1, c) "
    "and (r+1, c) are equal non-bg → fill with that color. "
    "Horizontal precedence (if both match with different "
    "colors, horizontal wins)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "≥1 horizontal (a,0,a) triplet for some non-bg a",
    "1-2 distractor isolated cells (no matching neighbor)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_triplets", "gap_too_wide", "no_distractor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_triplets":     {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "row_triplets_plus_distractor",
                       "valid": "row_triplets_plus_distractor"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _fillable_centers(grid):
    h, w = len(grid), len(grid[0])
    centers = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if 0 < c < w - 1 and grid[r][c - 1] != 0 and grid[r][c - 1] == grid[r][c + 1]:
                centers.add((r, c))
            if 0 < r < h - 1 and grid[r - 1][c] != 0 and grid[r - 1][c] == grid[r + 1][c]:
                centers.add((r, c))
    return centers


def _place_safe_distractor(grid, rng, palette, protected):
    """Place a singleton that does not erase/create any fillable center."""
    h, w = len(grid), len(grid[0])
    before = _fillable_centers(grid)
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 0 and (r, c) not in protected]
    rng.shuffle(candidates)
    for r, c in candidates:
        colors = list(palette)
        rng.shuffle(colors)
        for color in colors:
            if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == color
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            grid[r][c] = color
            if _fillable_centers(grid) == before:
                return True
            grid[r][c] = 0
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 6, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
    else:
        h = ctx.draw_int("grid_h", 4, 10)
        w = ctx.draw_int("grid_w", 6, 12)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used_rows = set()
    protected = set()
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    for _ in range(rng.randint(2, 3)):
        for _ in range(40):
            r = rng.randint(0, h - 1)
            if r in used_rows:
                continue
            c = rng.randint(0, w - 3)
            if any(g[r][cc] != 0 for cc in (c, c + 1, c + 2)):
                continue
            color = rng.choice(palette)
            g[r][c] = color; g[r][c + 2] = color
            protected.update({(r, c), (r, c + 1), (r, c + 2)})
            used_rows.add(r)
            break
    _place_safe_distractor(g, rng, palette, protected)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    centers = _fillable_centers(grid)
    horizontal = []
    for r, c in centers:
        if 0 < c < len(grid[0]) - 1 and grid[r][c - 1] != 0 and grid[r][c - 1] == grid[r][c + 1]:
            horizontal.append((r, c))
    min_triplets = 2
    if len(horizontal) < min_triplets:
        errors.append(f"expected at least {min_triplets} horizontal (a,0,a) triplets")
    endpoints = set()
    for r, c in horizontal:
        endpoints.add((r, c - 1)); endpoints.add((r, c + 1))
    distractors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                   if v != 0 and (r, c) not in endpoints]
    if not distractors:
        errors.append("expected at least one non-interfering distractor singleton")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_triplets":
        # only distractor singletons → no (a,0,a) patterns to fill
        g[1][2] = 4
        g[3][5] = 6
        return g
    if name == "gap_too_wide":
        # pair separated by 2+ zeros → not adjacent triplets, rule doesn't fire
        g[2][1] = 4
        g[2][5] = 4  # gap of 3 zeros, not 1
        return g
    if name == "no_distractor":
        # only triplets without distractor → no contrast for "isolated" cells
        g[1][1] = 4; g[1][3] = 4
        g[3][2] = 6; g[3][4] = 6
        return g
    return g
