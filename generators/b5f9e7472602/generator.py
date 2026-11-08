"""Generator for 14b:hard_97 — cast border rays and mark matching intersections.

Rule: row 0 holds column codes; col 0 holds row codes. For each
interior cell (r, c), if vc = (0, c) equals hc = (r, 0) (both non-bg,
non-5), and the vertical ray (0, c)→(r, c) and horizontal ray
(r, 0)→(r, c) are both clear of color-5, mark cell with vc.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_top_codes, no_left_codes, no_matching_codes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b5f9e7472602"
VERSION = "1.4.0"  # guarantee a clear positive ray-match witness; add self_check
TASK_ID = "b5f9e7472602"

SUMMARY = "Top row + left col hold codes; rule marks interior cells where row code = col code AND rays from edges are clear of walls."

# Rivals: 'mark all matching code intersections' refuted by ≥1 demo
# where a 5-wall blocks a ray and the intersection stays bg. 'use
# wall color for marks' refuted by any demo (marks use code color).
# 'mark only first match' refuted by ≥1 demo with ≥2 matches.
# 4 demos with varied codes + at least 1 with walls cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "row 0 cols 1+ hold 2-3 non-{0,5} codes at distinct columns",
    "col 0 rows 1+ hold 2-3 non-{0,5} codes at distinct rows",
    "at least one (row, col) pair has matching codes (so output has at least one mark)",
    "0-2 interior 5-walls (single cells)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_top_codes", "no_left_codes", "no_matching_codes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "row0_col0_codes",
                       "valid": "row0_col0_codes"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
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
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 7, 8, 7, 8
        n_codes_lo, n_codes_hi = 2, 3
        n_walls_lo, n_walls_hi = 0, 1
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 14, 11, 14
        n_codes_lo, n_codes_hi = 3, 5
        n_walls_lo, n_walls_hi = 2, 4
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 11, 8, 11
        n_codes_lo, n_codes_hi = 2, 4
        n_walls_lo, n_walls_hi = 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    palette = [1, 2, 3, 4, 6, 7, 8, 9]
    for outer in range(40):
        g = full_grid(h, w, 0)
        n_top = rng.randint(n_codes_lo, n_codes_hi)
        n_left = rng.randint(n_codes_lo, n_codes_hi)
        top_codes = [rng.choice(palette) for _ in range(n_top)]
        left_codes = [rng.choice(palette) for _ in range(n_left)]
        if not (set(top_codes) & set(left_codes)):
            continue
        top_cols = rng.sample(range(1, w), min(n_top, w - 1))
        left_rows = rng.sample(range(1, h), min(n_left, h - 1))
        for c, code in zip(top_cols, top_codes): g[0][c] = code
        for r, code in zip(left_rows, left_codes): g[r][0] = code
        # Optional interior 5-walls.
        n_walls = rng.randint(n_walls_lo, n_walls_hi)
        for _ in range(n_walls):
            wr = rng.randint(1, h - 1); wc = rng.randint(1, w - 1)
            if g[wr][wc] == 0:
                g[wr][wc] = 5
        matching_pairs = [(r, c) for r, hc in zip(left_rows, left_codes)
                          for c, vc in zip(top_cols, top_codes) if hc == vc]
        if matching_pairs:
            # Walls are useful negative evidence, but a purely random wall pass could
            # block every matching intersection.  Clear one matching pair's two rays
            # so every default instance has at least one positive witness.
            r, c = rng.choice(matching_pairs)
            for rr in range(1, r + 1):
                if g[rr][c] == 5:
                    g[rr][c] = 0
            for cc in range(1, c + 1):
                if g[r][cc] == 5:
                    g[r][cc] = 0
            return g
    raise ValueError("could not realize matching codes in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_top_codes":
        # Left col codes but row 0 is empty — rule has no column codes
        # to compare against; intersection set is empty.
        g[2][0] = 4; g[5][0] = 6
        return g
    if name == "no_left_codes":
        # Row 0 codes but col 0 is empty — rule has no row codes; no
        # marks produced.
        g[0][2] = 4; g[0][5] = 6
        return g
    if name == "no_matching_codes":
        # Codes on both axes but no overlap — rule's match step finds
        # zero (row, col) pairs.
        g[0][2] = 4; g[0][5] = 6
        g[2][0] = 7; g[5][0] = 8
        return g
    return g

def _has_clear_match_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    for r in range(1, h):
        for c in range(1, w):
            vc = grid[0][c]
            hc = grid[r][0]
            if vc == hc and vc not in (0, 5):
                if all(grid[rr][c] != 5 for rr in range(1, r + 1)) and \
                   all(grid[r][cc] != 5 for cc in range(1, c + 1)):
                    return True
    return False


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    msgs = []
    top = [grid[0][c] for c in range(1, w) if grid[0][c] not in (0, 5)]
    left = [grid[r][0] for r in range(1, h) if grid[r][0] not in (0, 5)]
    if len(top) < 2:
        msgs.append(f"expected at least two top-row codes, got {len(top)}")
    if len(left) < 2:
        msgs.append(f"expected at least two left-column codes, got {len(left)}")
    if not (set(top) & set(left)):
        msgs.append("top-row and left-column codes must share at least one color")
    if not _has_clear_match_for_self_check(grid):
        msgs.append("expected at least one matching code pair with both rays clear of 5-walls")
    return msgs
