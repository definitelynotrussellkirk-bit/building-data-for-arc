"""Generator for arc_puzzle_bank_nineteenth21:M133 — sort and pack components by area.

Rule: sort blobs by descending area, pack horizontally with 1-col gap.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "9e21d782f5e6"
VERSION = "1.2.1"
TASK_ID = "9e21d782f5e6"
SUMMARY = "N (2..4) distinct-color blobs of strictly distinct sizes; output packs them horizontally by descending area."

# Rivals: 'pack by color order' refuted by ≥2 demos where color order
# and size order disagree. 'pack ascending' refuted by ≥1 demo with
# top-left blob = the largest. 'keep colors in original positions'
# refuted by any demo (output is a compact pack). 'output a fixed
# horizontal arrangement' refuted by ≥2 demos with different N.
# 4 demos with mixed blob counts + decorrelated color-vs-size cover all.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "3 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|tied_sizes|single_blob|no_blobs"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; ≥2 distinct-color 4-connected blobs with strictly distinct sizes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    seen = [[False] * w for _ in range(h)]
    blobs = []  # list of (color, size)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                blobs.append((color, len(cells)))
    if len(blobs) < 2:
        errs.append(f"fewer than 2 blobs: found {len(blobs)}")
        return errs
    sizes = [s for _, s in blobs]
    if len(set(sizes)) < len(sizes):
        errs.append(f"blob sizes are not all distinct: {sorted(sizes)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 6, 7, 9
        n_lo, n_hi = 2, 3
        size_pool = range(1, 5)
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 8, 10, 11, 14
        n_lo, n_hi = 3, 4
        size_pool = range(1, 8)
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 9, 8, 12
        n_lo, n_hi = 2, 4
        size_pool = range(1, 7)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_blobs = ctx.draw_int("n_blobs", n_lo, n_hi)
    rng = ctx.draw_rng("layout")
    # Retry the whole instance up to 20 times so we always emit the
    # full n_blobs (v1.1.0 silently skipped failed blobs).
    for _attempt in range(20):
        g = full_grid(h, w, 0)
        sizes = rng.sample(list(size_pool), n_blobs)
        palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blobs)
        used: set[tuple[int, int]] = set()
        ok = True
        for size, color in zip(sizes, palette):
            cells = grow_blob(rng, h, w, used, size, max_attempts=80)
            if cells is None:
                ok = False
                break
            for r, c in cells:
                g[r][c] = color
            used |= cells
        if ok:
            return g
    # Last-ditch: emit whatever we have (preserves prior behaviour).
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # equal-area blobs → desc-sort order ambiguous
        g[0][0] = 3; g[1][0] = 3
        g[0][3] = 5; g[1][3] = 5
        for r, c in [(4, 1), (4, 2), (5, 1)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → trivial pack
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → nothing to sort or pack
        return g
    return g
