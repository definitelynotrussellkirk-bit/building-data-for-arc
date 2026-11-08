"""Generator for arc_puzzle_bank_twentyfirst_21_bundle:easy_147_bridge_one_cell_vertical_gaps.

Rule: one-cell vertical gaps between matching colors are filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, gaps,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, gap_already_filled, mismatched_endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f45070496ffc"
VERSION = "2.1.0"  # add lone-cell + mismatched-endpoint DISTRACTORS (canonical has them; was matching-pairs-only)
TASK_ID = "f45070496ffc"
SUMMARY = (
    "0-bg grid (h~8-13, w~7-11). Contains: (a) matching VERTICAL ENDPOINT PAIRS "
    "— two same-color cells at (r,c) and (r+2,c) with exactly one bg cell between; "
    "(b) DISTRACTORS the rule leaves alone — lone single cells (no vertical "
    "partner) and mismatched endpoint pairs (x 0 y, x!=y). All structures have a "
    ">=2-row vertical clearance so none interfere. Rule: for interior (r,c), if "
    "input[r][c]==0 AND input[r-1][c]!=0 AND input[r-1][c]==input[r+1][c] -> set "
    "output[r][c]=input[r-1][c]. Net: only the MATCHING 1-cell gaps fill; lone "
    "cells and mismatched pairs stay. (Canonical includes such distractors; prior "
    "version emitted matching pairs only.)"
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 matching x 0 x vertical pair (so output != input)",
    "endpoint/distractor colors are nonzero",
    "every structure has a >=2-row same-column clearance (no accidental cross-fill)",
    "no horizontal pairs (rule is vertical-only)",
    "distractors (lone cells, mismatched x 0 y pairs) are NOT filled by the rule",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "gap_already_filled", "mismatched_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..24"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "3..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "gaps":           {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "vertical_pair",
                       "valid": "vertical_pair"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|gap_already_filled|mismatched_endpoints"},
}


def _free(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def _free_v(g, cells):
    """1-cell ring buffer PLUS a 2-row same-column clearance above/below each
    structure, so no two structures ever sit close enough to form an unintended
    vertical gap (matching or otherwise)."""
    if not _free(g, cells):
        return False
    h = len(g)
    by_col = {}
    for r, c in cells:
        by_col.setdefault(c, []).append(r)
    cellset = set(cells)
    for c, rs in by_col.items():
        for rr in range(min(rs) - 2, max(rs) + 3):
            if 0 <= rr < h and (rr, c) not in cellset and g[rr][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("gaps", 3, 3); n_distract = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 10, 12)
        target = ctx.draw_int("gaps", 4, 6); n_distract = 3
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 7, 11)
        target = ctx.draw_int("gaps", 3, 5); n_distract = 2
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # (a) matching x 0 x pairs -> these are the cells the rule fills
    placed = 0
    for _ in range(200):
        if placed >= target:
            break
        r = rng.randint(0, h - 3); c = rng.randrange(w)
        if _free_v(g, [(r, c), (r + 2, c)]):
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            g[r][c] = color; g[r + 2][c] = color
            placed += 1

    # (b) distractors the rule must leave alone: lone cells + mismatched pairs
    dplaced = 0
    for _ in range(200):
        if dplaced >= n_distract:
            break
        kind = rng.choice(["lone", "lone", "mismatch"])
        c = rng.randrange(w)
        if kind == "lone":
            r = rng.randrange(h)
            if _free_v(g, [(r, c)]):
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                dplaced += 1
        else:  # mismatched endpoints x 0 y (x != y) -> gap NOT filled
            r = rng.randint(0, h - 3)
            if _free_v(g, [(r, c), (r + 2, c)]):
                x = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                y = rng.choice([v for v in range(1, 10) if v != x])
                g[r][c] = x; g[r + 2][c] = y
                dplaced += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify matching one-cell vertical gaps and non-interfering distractors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    vals = [v for row in grid for v in row]
    if 0 not in vals:
        errs.append("no background cells")
    if any(v < 0 or v > 9 for v in vals):
        errs.append("color outside ARC 0..9 palette")
    fillable = []
    for r in range(1, h - 1):
        for c in range(w):
            if grid[r][c] == 0 and grid[r - 1][c] != 0 and grid[r - 1][c] == grid[r + 1][c]:
                fillable.append((r, c, grid[r - 1][c]))
    if not fillable:
        errs.append("no matching x 0 x vertical gap; rule would be a no-op")
    # The generator spaces structures with a one-cell ring and a two-row same-column
    # clearance. Horizontal/diagonal touching makes accidental extra objects; adjacent
    # vertical touching can create non-canonical fill opportunities.
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            for dr, dc, label in ((0, 1, "horizontal touch"), (1, 0, "vertical adjacency"),
                                  (1, 1, "diagonal touch"), (1, -1, "diagonal touch")):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                    errs.append(label)
                    break
    # A filled gap texture should not appear in normal samples: every matching
    # endpoint pair must have a zero bridge cell so the transformation is visible.
    for r in range(1, h - 1):
        for c in range(w):
            if grid[r][c] != 0 and grid[r - 1][c] == grid[r + 1][c] != 0:
                errs.append("matching endpoints already have a non-background bridge cell")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 11, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # scattered single cells, no vertical pairs → rule has no targets
        for r, c, v in [(1, 2, 4), (4, 5, 5), (7, 7, 6)]:
            g[r][c] = v
        return g
    if name == "gap_already_filled":
        # vertical pairs but the gap is already non-bg → rule no-op for those
        g[1][2] = 3; g[2][2] = 5; g[3][2] = 3
        g[5][5] = 6; g[6][5] = 7; g[7][5] = 6
        return g
    if name == "mismatched_endpoints":
        # different-color vertical endpoints → "same color" condition never matches
        g[1][2] = 3; g[3][2] = 5
        g[5][5] = 6; g[7][5] = 7
        return g
    return g
