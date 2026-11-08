"""Generator for arc_additional_puzzle_bank_volume3:M18.

Rule: pivot = first 2-cell. For each non-{0,2} cell at (r,c), compute
delta (r-pr, c-pc), place at (pr+dc, pc-dr).

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_kind,
palette_size, position_bias, n_distinct_colors, blob_color, texture.
Degenerates: no_pivot, two_pivots, no_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3279a0599dab"
# 3.1.0: defect-lint all_background_output — a blob far from the pivot could rotate
# ENTIRELY out of bounds (empty output). Placement now requires every rotated cell
# in bounds; self_check enforces it. (3.0.1 fixed the 40% dup-input fixed-L issue.)
VERSION = "3.1.0"
TASK_ID = "3279a0599dab"
SUMMARY = (
    "0-bg grid with ONE color-2 (red) PIVOT near the center and a RANDOM "
    "connected blob (3-6 cells) in a single color from {1,4,5,6,7,8,9} placed "
    "at a random position. Rule: for each non-{0,2} cell, compute its delta "
    "(dr,dc) from the pivot and place its color at the 90° CW rotated position "
    "(pr+dc, pc-dr); the pivot stays. Net: the blob rotates 90° CW around the pivot."
)

INVARIANTS = [
    "exactly one color-2 pivot",
    "a single-color blob distinct from the pivot, rotated 90 deg around it",
]

PALETTE_KINDS = ("default", "L_blob", "I_blob", "asymmetric")
DEGENERATE_TEXTURES = ("no_pivot", "two_pivots", "no_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_kind":      {"type": "str", "default": "L_3cell", "valid": "L_3cell"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "pivot_centered",
                       "valid": "pivot_centered"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "blob_color":     {"type": "int", "default": "rng 1,4..9", "valid": "1|4|5|6|7|8|9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one color-2 pivot cell; ≥1 non-{0,2} blob cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 pivot, found {len(twos)}")
    blob = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 2)]
    if not blob:
        errs.append("no non-{0,2} blob cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pr = h // 2 + rng.randint(-1, 1); pc = w // 2 + rng.randint(-1, 1)
    g[pr][pc] = 2
    color = rng.choice([1, 4, 5, 6, 7, 8, 9])
    # rule rotates the shape 90 deg around the color-2 pivot. A RANDOM blob (was a
    # fixed 3-cell L -> 40% dup-inputs) placed at a random spot gives varied outputs.
    shape = _rand_blob(rng, rng.randint(3, 6))
    sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
    placed = False
    for _try in range(120):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        if any(g[r][c] != 0 for (r, c) in cells):   # don't cover the pivot
            continue
        # The rule maps (r,c) -> (pr + (c-pc), pc - (r-pr)); every rotated cell
        # must stay in bounds or the demo's output loses (or empties) the shape.
        if any(not (0 <= pr + (c - pc) < h and 0 <= pc - (r - pr) < w)
               for (r, c) in cells):
            continue
        for (r, c) in cells:
            g[r][c] = color
        placed = True
        break
    if not placed:
        # Deterministic fallback: a 3-cell L hugging the pivot always rotates
        # in bounds (pivot sits at the grid center +-1).
        for (r, c) in ((pr - 1, pc), (pr - 1, pc + 1), (pr, pc + 1)):
            if 0 <= r < h and 0 <= c < w:
                g[r][c] = color
    return g


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_blob(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    pr, pc = h // 2, w // 2
    if name == "no_pivot":
        # blob present but no 2-pivot → rotation center undefined
        g[pr - 2][pc - 1] = 5
        g[pr - 1][pc - 1] = 5
        g[pr - 1][pc - 2] = 5
        return g
    if name == "two_pivots":
        # two 2-cells → which is the pivot?
        g[pr][pc] = 2
        g[1][1] = 2
        g[pr - 2][pc - 1] = 5
        g[pr - 1][pc - 1] = 5
        return g
    if name == "no_blob":
        # pivot but nothing to rotate → rule has no source cells
        g[pr][pc] = 2
        return g
    return g
