"""Generator for arc_additional_puzzle_bank_volume23:M157 — Output count-row of colors 2,3,4.

Rule: count red(2), green(3), yellow(4) connected components. Output
single row: n2 reps of 2, then 0, then n3 reps of 3, then 0, then n4
reps of 4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n2, n3, n4,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_color, all_zero_counts, all_equal_counts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "5aeb34b3b850"
VERSION = "3.1.1"  # AXES synced to the 3.1.0 widened draws (defect-lint axis-honesty: metadata lied)
TASK_ID = "5aeb34b3b850"
SUMMARY = (
    "0-bg grid (h~8-12, w~10-14) with SEVERAL "
    "CONNECTED COMPONENTS of COLORS 2, 3, 4 — "
    "n2 (1-3) red, n3 (1-3) green, n4 (1-3) "
    "yellow blobs, each of size 1-2 cells, at "
    "scattered non-touching positions. Counts "
    "are typically distinct to avoid symmetric "
    "output. Rule: COUNT the CONNECTED "
    "COMPONENTS of EACH color: n2 = count of "
    "color-2 components, n3 = color-3, n4 = "
    "color-4. Build a SINGLE-ROW OUTPUT: n2 "
    "cells of COLOR 2, then 1 cell of COLOR 0 "
    "(separator), then n3 cells of COLOR 3, "
    "then 0 separator, then n4 cells of "
    "COLOR 4. Output dimensions: "
    "1 × (n2 + n3 + n4 + 2). Net: input has "
    "scattered red/green/yellow blobs; "
    "output is a horizontal count-row "
    "encoding."
)

INVARIANTS = [
    "between 1 and 3 components of color 2",
    "between 1 and 3 components of color 3",
    "between 1 and 3 components of color 4",
    "at least one count differs (so output isn't trivially uniform)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_color", "all_zero_counts", "all_equal_counts")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9-11 easy / 11-16 med / 14-20 hard",
                       "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "11-13 easy / 13-18 med / 16-22 hard",
                       "valid": "11..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n2":             {"type": "int", "default": "1-3 easy / 1-5 med / 1-6 hard", "valid": "1..6"},
    "n3":             {"type": "int", "default": "1-3 easy / 1-5 med / 1-6 hard", "valid": "1..6"},
    "n4":             {"type": "int", "default": "1-3 easy / 1-5 med / 1-6 hard", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "scattered_3color_blobs",
                       "valid": "scattered_3color_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output is a 1xK row encoding component counts (n2,n3,n4); widen each count
    # -> more distinct (n2,n3,n4) tuples -> more distinct outputs
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13); lo, hi = 1, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 16, 22); lo, hi = 1, 6
    else:
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 13, 18); lo, hi = 1, 5
    n2 = ctx.draw_int("n2", lo, hi); n3 = ctx.draw_int("n3", lo, hi); n4 = ctx.draw_int("n4", lo, hi)
    if n2 == n3 == n4:
        # Avoid the symmetric count-row shortcut in the default stream; the
        # explicit all_equal_counts texture still covers that degenerate case.
        n4 = n4 + 1 if n4 < hi else n4 - 1
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()
    for color, n in ((2, n2), (3, n3), (4, n4)):
        for _ in range(n):
            size = rng.randint(1, 2)
            blob = grow_blob(rng, h, w, used, size)
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "missing_color":
        # only red and green blobs (no yellow) → output has n4=0
        g[1][1] = 2; g[2][3] = 2
        g[5][5] = 3; g[6][7] = 3
        return g
    if name == "all_zero_counts":
        # blank → all counts are 0, output row degenerate
        return g
    if name == "all_equal_counts":
        # exactly 2 of each color → output row is symmetric (no asymmetry signal)
        g[1][1] = 2; g[1][3] = 2
        g[3][2] = 3; g[3][5] = 3
        g[5][4] = 4; g[5][7] = 4
        return g
    return g

def _count_components(grid, color):
    h = len(grid); w = len(grid[0]) if h else 0; seen = set(); n = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            n += 1; stack = [(r, c)]; seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
    return n


def self_check(grid, *, difficulty=None, meta=None):
    counts = [_count_components(grid, c) for c in (2, 3, 4)]
    msgs = []
    for color, n in zip((2, 3, 4), counts):
        if n < 1:
            msgs.append(f"missing color-{color} component")
    if len(set(counts)) == 1:
        msgs.append("component counts for colors 2/3/4 are all equal")
    return msgs
