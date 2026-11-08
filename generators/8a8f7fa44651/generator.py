"""Generator for arc_puzzle_bank_21_set22_bundle:easy_p05 — diagonal dominoes extend at open ends.

Rule: each separated same-color diagonal domino extends one cell at
its open ends.

Combinatorial axes (8): grid_h, grid_w, palette_kind, domino_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dominoes, axis_aligned, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a8f7fa44651"
VERSION = "2.1.1"
TASK_ID = "8a8f7fa44651"
SUMMARY = (
    "0-bg grid (h, w ~8-11) with 2-4 ISOLATED diagonal "
    "DOMINOES — each is 2 same-color cells at diagonal "
    "adjacency: (r, c) and (r+1, c±1). Different dominoes "
    "use distinct colors and have ≥2-cell buffer. Rule: for "
    "each cell (r, c), for each diagonal direction (dr, dc) "
    "∈ {(1,1),(1,-1),(-1,1),(-1,-1)}: if input[r][c] is a "
    "non-bg color c0, input[r+dr][c+dc] is also c0 (forming "
    "a domino in that direction), input[r+2dr][c+2dc] is 0 "
    "(open end), and (r-dr, c-dc) is NOT c0 (so r,c is the "
    "outer end) → set output[r+2dr][c+2dc] = c0. Net effect: "
    "each diagonal domino grows by 1 cell at its OPEN END "
    "(the end not next to a same-color neighbor)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each object is exactly one diagonal same-color domino",
    "dominoes are separated so extensions do not collide",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dominoes", "axis_aligned", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "domino_count":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "= domino_count", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_diagonal_dominoes",
                       "valid": "scattered_diagonal_dominoes"},
    "n_distinct_colors": {"type": "int", "default": "= domino_count", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each non-bg color has at most 2 cells (no over-sized groups)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    counts: dict[int, int] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return []  # no_dominoes degenerate — allowed
    errs = []
    for color, cnt in counts.items():
        if cnt > 2:
            errs.append(f"color {color}: {cnt} cells (expected at most 2 for a domino)")
    return errs


def _clear_wide(grid, cells):
    h = len(grid)
    w = len(grid[0])
    for r, c in cells:
        for rr in range(max(0, r - 2), min(h, r + 3)):
            for cc in range(max(0, c - 2), min(w, c + 3)):
                if grid[rr][cc] != 0:
                    return False
    return True


def _clear_with_margin(grid, cells, margin=1):
    h = len(grid)
    w = len(grid[0])
    for r, c in cells:
        for rr in range(max(0, r - margin), min(h, r + margin + 1)):
            for cc in range(max(0, c - margin), min(w, c + margin + 1)):
                if grid[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        domino_count = ctx.draw_int("domino_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        domino_count = ctx.draw_int("domino_count", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        domino_count = ctx.draw_int("domino_count", 2, 4)
    rng = ctx.draw_rng("layout")
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], domino_count)
    for _ in range(80):
        grid = _place_extendable_dominoes(h, w, colors, rng)
        if grid is not None:
            return grid
    raise ValueError("could not place isolated diagonal dominoes with two open ends")


def _place_extendable_dominoes(h, w, colors, rng):
    grid = full_grid(h, w, 0)
    candidates = []
    for r in range(h):
        for c in range(w):
            for dr, dc in ((1, 1), (1, -1)):
                r2, c2 = r + dr, c + dc
                before = (r - dr, c - dc)
                after = (r2 + dr, c2 + dc)
                if (0 <= r2 < h and 0 <= c2 < w
                        and 0 <= before[0] < h and 0 <= before[1] < w
                        and 0 <= after[0] < h and 0 <= after[1] < w):
                    candidates.append(((r, c), (r2, c2), before, after))
    rng.shuffle(candidates)
    placed = 0
    for cand in candidates:
        if placed >= len(colors):
            break
        cells = cand[:2]
        extension_cells = cand[2:]
        # Reserve the two-cell input domino PLUS its two output extension cells.
        # The old radius-2 site check made the requested 4-6 hard dominoes
        # impossible in many 11x11 seeds; a one-cell margin is enough to keep
        # both inputs and their future extensions from colliding while preserving
        # the intended separated-domino pedagogy.
        if not _clear_with_margin(grid, cells + extension_cells, margin=1):
            continue
        color = colors[placed]
        for r, c in cells:
            grid[r][c] = color
        placed += 1
    if placed != len(colors):
        return None
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_dominoes":
        # Empty grid — no diagonal domino to extend.
        return g
    if name == "axis_aligned":
        # Same-color cells but they're horizontally/vertically adjacent,
        # not diagonal — rule's diagonal-domino filter never matches.
        g[2][2] = 4; g[2][3] = 4
        g[5][7] = 6; g[6][7] = 6
        return g
    if name == "single_cell":
        # Singletons only — no domino, just isolated cells.
        g[2][2] = 4; g[5][5] = 6; g[7][7] = 7
        return g
    return g
