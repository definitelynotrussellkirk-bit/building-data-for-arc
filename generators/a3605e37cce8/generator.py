"""Generator for 6b:m40 — drop whole blobs to bottom.

Rule: each blob slides down as a unit until its bbox bottom row hits
the grid bottom.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, blobs_at_bottom, overlapping_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "a3605e37cce8"
VERSION = "2.0.1"
TASK_ID = "a3605e37cce8"
SUMMARY = (
    "0-bg grid (h~8-11, w~10-13) with 2-3 "
    "BLOBS of 2-4 cells each (4-connected, "
    "grown via grow_blob), each in a "
    "DISTINCT non-0 color drawn from {1..9}. "
    "Blobs are constrained: (a) STRICTLY IN "
    "THE UPPER ROWS (rows h-3 and below are "
    "marked `used` to keep blobs out of the "
    "bottom 3 rows so gravity has somewhere "
    "to drop); (b) DISJOINT COLUMN RANGES — "
    "each blob's column span (cmin..cmax) is "
    "tracked, and new blobs are required not "
    "to overlap any existing column range "
    "(so dropping doesn't cause collisions). "
    "Bottom rows start empty. Rule (DROP EACH "
    "BLOB AS A UNIT TO THE BOTTOM — EACH "
    "BLOB SLIDES DOWN UNTIL ITS BBOX-BOTTOM "
    "ROW HITS THE GRID BOTTOM): for EACH "
    "4-connected non-bg blob: COMPUTE its "
    "bbox top-left (r1, c1) and bbox-bottom "
    "row r2. COMPUTE the DROP DELTA = (h-1) "
    "- r2 (how many rows the blob can slide "
    "before its bbox-bottom hits the grid "
    "bottom). SHIFT every cell of the blob "
    "DOWN by DROP DELTA rows (cells move "
    "from (r, c) to (r + delta, c)). The "
    "ORIGINAL blob positions become bg-0; "
    "the shifted positions take on the "
    "blob's color. Other blobs in disjoint "
    "columns are dropped independently. Net: "
    "each blob falls as a rigid unit until "
    "its lowest cell sits on the bottom row."
)

INVARIANTS = [
    "background is 0",
    "blobs all in upper half, bottom row is empty",
    "blobs occupy disjoint col ranges (so dropping doesn't collide)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "blobs_at_bottom", "overlapping_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "upper_half_disjoint_columns",
                       "valid": "upper_half_disjoint_columns"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one non-bg blob; bottom row is all 0 (blobs
    are in upper rows with drop room); no blobs on the bottom row."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    nonbg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonbg:
        errs.append("no non-bg cells (no blobs)")
        return errs
    # Bottom row should be empty (blobs need drop room)
    if any(grid[h - 1][c] != 0 for c in range(w)):
        errs.append("bottom row is not empty; blobs should be in upper rows")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_blobs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_blobs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    for r in range(max(0, h - 3), h):
        for c in range(w):
            used.add((r, c))
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    cols_used: list[range] = []
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=20)
            if cells is None: continue
            cs = [c for _, c in cells]; cmin, cmax = min(cs), max(cs)
            if any(set(range(cmin, cmax + 1)) & set(cu) for cu in cols_used):
                continue
            for r, c in cells: g[r][c] = color
            used |= cells
            cols_used.append(range(cmin, cmax + 1))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → nothing to drop, identity
        return g
    if name == "blobs_at_bottom":
        # blobs already at bottom → drop is identity
        g[h - 2][2] = 4; g[h - 1][2] = 4
        g[h - 1][7] = 6; g[h - 2][7] = 6
        return g
    if name == "overlapping_columns":
        # two blobs share the same column → drop would collide / stack ambiguously
        g[1][3] = 4; g[1][4] = 4
        g[2][3] = 6; g[2][4] = 6
        return g
    return g
