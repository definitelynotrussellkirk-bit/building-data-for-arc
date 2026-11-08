"""Generator for arc_puzzle_bank_eleventh21:E74.

Complete the missing cardinal arm of each partial plus.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, full_plus, missing_two_arms.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa22818fb880"
VERSION = "2.1.1"
TASK_ID = "aa22818fb880"

SUMMARY = (
    "0-bg grid (h~8-11, w~8-11) with 2-4 isolated PARTIAL "
    "PLUS motifs. Each plus: a center cell + 3 same-color "
    "cardinal arm cells (up, down, left, right minus one). "
    "The missing 4th arm cell is bg (0), in-bounds, and the "
    "remaining 3 arms are all the same color. Different pluses "
    "use distinct colors; motifs isolated by ≥2 bg cells on "
    "all sides. Rule: scan every cell. For each non-bg cell, "
    "count how many of its 4 cardinal neighbors have the same "
    "color. If exactly 3 → identify the missing cardinal "
    "direction and paint that neighbor with the cell's color "
    "(if in bounds and currently 0). Net effect: complete each "
    "partial plus by filling its missing arm."
)

# Rivals: 'complete only first plus' refuted by ≥1 demo with ≥2 pluses
# (all completed). 'use a fixed fill color' refuted by ≥2 demos with
# different plus colors. 'fill the cell with bg' refuted by any demo.
# 'add an extra cell beyond the missing arm' refuted by any demo
# (output is exactly the completed plus).
# 3 demos with varied plus counts + colors + missing-arm directions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each motif has a center and exactly three same-color cardinal arms",
    "the missing in-bounds arm cell is initially zero",
    "partial plus motifs are isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "full_plus", "missing_two_arms")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_motifs":       {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_partial_pluses",
                       "valid": "isolated_partial_pluses"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 2), min(h, r + 3)):
        for cc in range(max(0, c - 2), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 6, 8)
        target = ctx.draw_int("n_motifs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        target = ctx.draw_int("n_motifs", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        target = ctx.draw_int("n_motifs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    placed = 0
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for _ in range(180):
        if placed >= target:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if not _clear(g, r, c):
            continue
        color = colors[placed]
        missing = rng.choice(deltas)
        g[r][c] = color
        for dr, dc in deltas:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = color
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r][c]
            if color == 0:
                continue
            same = [(dr, dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if grid[r + dr][c + dc] == color]
            if len(same) == 3:
                centers.append((r, c, color))
                missing = [d for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if d not in same][0]
                if grid[r + missing[0]][c + missing[1]] != 0:
                    errors.append("missing plus arm cell must be zero")
    min_centers = 3 if difficulty == "hard" else 1 if difficulty == "easy" else 2
    if len(centers) < min_centers:
        errors.append(f"expected at least {min_centers} partial-plus motifs, got {len(centers)}")
    colors = [color for _, _, color in centers]
    if len(colors) != len(set(colors)):
        errors.append("partial plus motifs must use distinct colors")
    # Every non-zero cell should belong to exactly one center+3-arm motif.
    covered = set()
    for r, c, color in centers:
        covered.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if grid[r + dr][c + dc] == color:
                covered.add((r + dr, c + dc))
    nonzero = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    if nonzero != covered:
        errors.append("all nonzero cells must be explained by isolated partial plus motifs")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # blank → no partial pluses to complete
        return g
    if name == "full_plus":
        # complete 5-cell plus → no missing arm to fill, rule is identity
        cr, cc = 3, 3
        g[cr][cc] = 4
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            g[cr + dr][cc + dc] = 4
        return g
    if name == "missing_two_arms":
        # only 2 arms present → "exactly three" precondition fails
        cr, cc = 3, 3
        g[cr][cc] = 4
        g[cr - 1][cc] = 4; g[cr][cc + 1] = 4
        return g
    return g
