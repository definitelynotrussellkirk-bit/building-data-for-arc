"""Generator for arc_additional_puzzle_bank_volume3:H20.

Rule: pivot = first 2-cell. For each 1-cell, rotate around pivot by
4 quarter-turns and paint at all rotation positions in bounds.

Combinatorial axes (8): grid_n, palette_kind, n_ones,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pivot, no_ones, ones_outside_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ba0c6a5828f9"
VERSION = "2.1.2"  # 2.1.1->2.1.2: require at least one missing in-bounds rotation copy, preventing identity demos. 2.1.0->2.1.1: add self_check. 2.0.0->2.1.0: pivot placed anywhere (not just center),
# 2-5 color-1 cells scattered grid-wide (not a tiny 2x3 corner), wider +
# non-square grids. Rule skips out-of-bounds rotation images, so all valid.
# in/out shapes 3 -> many; uniq_out up.
TASK_ID = "ba0c6a5828f9"
SUMMARY = (
    "Square grid (n×n, n=7-9) with: (a) "
    "ONE COLOR-2 (red) PIVOT CELL at the "
    "exact CENTER (n//2, n//2); (b) 2-3 "
    "COLOR-1 (blue) MARKER CELLS placed in "
    "the UPPER-LEFT quadrant (rows "
    "pr-2..pr-1, cols pc-2..pc) near the "
    "pivot, NOT at pivot position. All "
    "1-cells stay in-bounds under 4-fold "
    "rotation. Rule (4-FOLD ROTATIONAL "
    "COPY): use the COLOR-2 CELL as the "
    "ROTATION PIVOT (pr, pc). For EACH "
    "COLOR-1 CELL at (r, c), APPLY all 4 "
    "QUARTER-TURNS around the pivot — i.e., "
    "compute the 4 positions: (r, c), "
    "(2pc-c, ...), and their 90°/180°/270° "
    "images. PAINT each rotation image with "
    "COLOR 1, as long as it stays in "
    "bounds. The pivot stays color-2. Net: "
    "each blue cell creates 4 rotated "
    "copies around the red pivot."
)

INVARIANTS = [
    "exactly one 2-cell (pivot)",
    "2-5 color-1 cells (not at the pivot)",
    "out-of-bounds rotation images are simply skipped by the rule",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pivot", "no_ones", "ones_outside_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_ones":         {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "pivot_anywhere",
                       "valid": "pivot_anywhere"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pivot|no_ones|ones_outside_grid"},
}


def _orbit(r, c, pr, pc, h, w):
    """In-bounds 90-degree rotation orbit around the pivot, matching the Racket rule."""
    dr, dc = r - pr, c - pc
    for rr, cc in (
        (pr + dr, pc + dc),
        (pr + dc, pc - dr),
        (pr - dr, pc - dc),
        (pr - dc, pc + dr),
    ):
        if 0 <= rr < h and 0 <= cc < w:
            yield rr, cc


def _has_visible_completion(grid, twos=None, ones=None):
    """True iff the oracle will paint at least one new color-1 cell."""
    h, w = len(grid), len(grid[0])
    twos = twos if twos is not None else [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    ones = ones if ones is not None else [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(twos) != 1 or not ones:
        return False
    pr, pc = twos[0]
    for r, c in ones:
        for rr, cc in _orbit(r, c, pr, pc, h, w):
            if grid[rr][cc] == 0:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: one pivot, marker cells, and at least one missing orbit cell to fill."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1, 2)]
    if bad:
        r, c, v = bad[0]
        errs.append(f"unexpected color {v} at ({r},{c}); expected only 0/1/2")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(twos) != 1:
        errs.append(f"expected exactly 1 pivot (color-2), got {len(twos)}")
    if not ones:
        errs.append("no color-1 cells found")
    if not errs and not _has_visible_completion(grid, twos, ones):
        errs.append("no missing in-bounds rotation copy; oracle output would equal input")
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
        n_ones_hi = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        n_ones_hi = 5
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_ones_hi = 5
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # pivot anywhere with at least a little room around it
    pr = rng.randint(1, h - 2)
    pc = rng.randint(1, w - 2)
    g[pr][pc] = 2
    # Place one marker whose orbit has at least one missing in-bounds copy.  The
    # rule otherwise sometimes leaves scattered edge markers unchanged, producing
    # identity demos.  Keep the rest random but avoid filling that whole orbit.
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if (r, c) != (pr, pc)]
    active_candidates = [p for p in candidates
                         if any((rr, cc) != p for rr, cc in _orbit(p[0], p[1], pr, pc, h, w))]
    active = rng.choice(active_candidates)
    g[active[0]][active[1]] = 1
    active_orbit = set(_orbit(active[0], active[1], pr, pc, h, w)) - {active}
    candidates = [p for p in candidates if p != active and p not in active_orbit]
    rng.shuffle(candidates)
    n_ones = rng.randint(2, n_ones_hi)
    placed = 1
    for r, c in candidates:
        if placed >= n_ones:
            break
        if g[r][c] == 0:
            g[r][c] = 1
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    n = 8
    g = full_grid(n, n, 0)
    if name == "no_pivot":
        # no 2-cell → rotation center is undefined, rule has nothing to rotate around
        g[2][2] = 1
        g[2][3] = 1
        return g
    pr = n // 2; pc = n // 2
    g[pr][pc] = 2
    if name == "no_ones":
        # pivot exists but no 1-cells → nothing to rotate
        return g
    if name == "ones_outside_grid":
        # 1-cell placed where one of its rotation images is out-of-bounds
        g[0][0] = 1
        return g
    return g
