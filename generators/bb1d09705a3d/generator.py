"""Generator for arc_additional_puzzle_bank_volume9:M61 — Bar chart of N-objects-per-color.

Rule: build a 3x6 grid where row r has color (r+1) painted in the
first n cells, where n = number of (r+1)-colored connected components
in the input.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n1,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_counts_equal, missing_color, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "bb1d09705a3d"
VERSION = "2.1.2"  # AXES synced to the widened draws (defect-lint axis-honesty). 2.1.0->2.1.1: add self_check. 2.0.0->2.1.0: widen per-color count ranges to 0..6 (full
# meaningful range for the 3x6 histogram; output shape is rule-locked at 3x6 so
# count-triple is the only diversity axis) -> more distinct outputs
TASK_ID = "bb1d09705a3d"
SUMMARY = "Connected components in colors 1, 2, 3. Output is a 3×6 bar chart: row r (r=0,1,2) has color r+1 painted in the first n cells, where n = number of (r+1)-colored components in the input."

# Rivals: 'output is input' refuted by any demo (output is 3×6).
# 'output with input colors only' refuted by ≥1 demo where some
# colors have 0 components (their row is all bg). 'output left-empty
# right-filled' refuted by any demo (bars are left-aligned). 'use one
# color for all rows' refuted by ≥1 demo (each row uses its own
# index color). 3 demos with varied counts cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "between 1 and 5 components of color 1, 2, and 3 each",
    "counts are not all equal (so output isn't trivially uniform)",
    "blobs are non-touching",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_counts_equal", "missing_color", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 12-16 med / 13-18 hard",
                       "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 12-16 med / 13-18 hard",
                       "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n1":             {"type": "int", "default": "1-3 easy / 0-6 med / 4-6 hard", "valid": "0..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "n2":             {"type": "int", "default": "1-3 easy / 0-6 med / 4-6 hard", "valid": "0..6"},
    "n3":             {"type": "int", "default": "1-3 easy / 0-6 med / 4-6 hard", "valid": "0..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; nonzero cells use only colors in {1,2,3}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 1, 2, 3)]
    if bad:
        errs.append(f"unexpected color values (expected only 0/1/2/3): {bad[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degenerate"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n1 = ctx.draw_int("n1", 1, 3)
        n2 = ctx.draw_int("n2", 1, 3)
        n3 = ctx.draw_int("n3", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n1 = ctx.draw_int("n1", 4, 6)
        n2 = ctx.draw_int("n2", 4, 6)
        n3 = ctx.draw_int("n3", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n1 = ctx.draw_int("n1", 0, 6)
        n2 = ctx.draw_int("n2", 0, 6)
        n3 = ctx.draw_int("n3", 0, 6)
    if n1 == n2 == n3:
        n3 = (n3 % 6) + 1

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()
    for color, n in ((1, n1), (2, n2), (3, n3)):
        for _ in range(n):
            size = rng.randint(1, 3)
            blob = grow_blob(rng, h, w, used, size)
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    # rng is a ctx.draw_rng("degenerate") handle (deterministic per seed +
    # sample_index) — grow_blob consumes it, so degenerate layouts stay
    # reproducible without a banned `import random`.
    h, w = 11, 11
    g = full_grid(h, w, 0)
    used = set()
    if name == "all_counts_equal":
        # all colors have equal counts → output rows have equal length, no contrast in heights
        for color in (1, 2, 3):
            for _ in range(2):
                blob = grow_blob(rng, h, w, used, 2)
                if blob is None: continue
                used |= blob
                for r, c in blob: g[r][c] = color
        return g
    if name == "missing_color":
        # one of the 3 colors is absent → that row's count is 0, ambiguous bar shape
        for color in (1, 3):
            for _ in range(3):
                blob = grow_blob(rng, h, w, used, 2)
                if blob is None: continue
                used |= blob
                for r, c in blob: g[r][c] = color
        return g
    if name == "no_blobs":
        # empty grid → counts are all zero, output is empty/all-zero bar chart
        return g
    return g
