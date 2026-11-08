"""Generator for arc_additional_puzzle_bank_volume13:H89.

Rule: dr/dc = (3-marker − 2-marker) + (6-marker − 4-marker). For each
1-cell, paint 8 at (r + dr, c + dc) if in bounds.

Combinatorial axes (8): grid_h/w, palette_kind, blob_size, marker_layout,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: missing_marker, zero_combined_delta, no_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2abfa4e4beeb"
VERSION = "2.0.1"
TASK_ID = "2abfa4e4beeb"
SUMMARY = (
    "0-bg grid (h, w ∈ 12-14) with: "
    "(a) FOUR MARKER CELLS at FIXED "
    "positions — g[0][7] = COLOR 2, "
    "g[1][10] = COLOR 3, g[2][2] = "
    "COLOR 4, g[1][0] = COLOR 6; "
    "(b) ONE COLOR-1 PLUS-SHAPED "
    "BLOB at FIXED position centered "
    "around (6, 6) — 5 cells: (5, 6), "
    "(6, 5), (6, 6), (6, 7), (7, 6) "
    "forming a +. Rule (COMPUTE TWO "
    "DELTA VECTORS: V1 = (3-MARKER "
    "POS) - (2-MARKER POS); V2 = "
    "(6-MARKER POS) - (4-MARKER "
    "POS); COMBINE V = V1 + V2; "
    "FOR EACH COLOR-1 CELL, PAINT "
    "COLOR 8 AT (R + V.R, C + V.C) "
    "IF IN-BOUNDS): LOCATE the 4 "
    "markers (one each of colors 2, "
    "3, 4, 6). COMPUTE v1 = pos(3) "
    "- pos(2), v2 = pos(6) - "
    "pos(4). LET v = v1 + v2. For "
    "EACH color-1 cell at (r, c): "
    "COMPUTE target (r+v.r, c+v.c); "
    "IF in-bounds: PAINT "
    "g[r+v.r][c+v.c] = COLOR 8 "
    "(cyan). Original cells "
    "preserved. Net: the + blob "
    "is copied to color 8 at a "
    "translated position dictated "
    "by the 4-marker vector sum."
)

INVARIANTS = [
    "exactly one 1-blob, one each of 2, 3, 4, 6 markers",
    "combined delta keeps translated 1-cells in bounds",
]

PALETTE_KINDS = ("default", "tight_blob", "wide_grid", "varied_markers")
DEGENERATE_TEXTURES = ("missing_marker", "zero_combined_delta", "no_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "5", "valid": "5"},
    "marker_layout":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, has color-1 cells, has exactly one each of marker colors 2,3,4,6."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    for color in (1, 2, 3, 4, 6):
        count = sum(grid[r][c] == color for r in range(h) for c in range(w))
        if color == 1:
            if count == 0:
                errs.append("no color-1 (blob) cells found")
        else:
            if count != 1:
                errs.append(f"expected exactly 1 marker of color {color}, got {count}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    rng = ctx.draw_rng("layout")
    plus = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
    for _ in range(80):
        g = full_grid(h, w, 0)
        # Random plus center (interior)
        br = rng.randint(2, h - 3)
        bc = rng.randint(2, w - 3)
        for dr, dc in plus:
            g[br + dr][bc + dc] = 1
        # Place 4 markers (2, 3, 4, 6) at random non-overlapping positions
        positions = {}
        ok = True
        for color in [2, 3, 4, 6]:
            placed = False
            for _ in range(40):
                r = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                positions[color] = (r, c)
                g[r][c] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        v1r = positions[3][0] - positions[2][0]
        v1c = positions[3][1] - positions[2][1]
        v2r = positions[6][0] - positions[4][0]
        v2c = positions[6][1] - positions[4][1]
        vr, vc = v1r + v2r, v1c + v2c
        # Check translated plus fits in-bounds
        bad = False
        for dr, dc in plus:
            tr, tc = br + dr + vr, bc + dc + vc
            if not (0 <= tr < h and 0 <= tc < w):
                bad = True
                break
        if bad:
            continue
        return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "missing_marker":
        # only 3 of the 4 markers — combined delta undefined
        g[0][7] = 2
        g[1][10] = 3
        g[2][2] = 4
        g[5][6] = 1
        g[6][5] = 1; g[6][6] = 1; g[6][7] = 1
        return g
    if name == "zero_combined_delta":
        # the two delta vectors cancel — net translation is (0, 0), output is identity
        g[0][7] = 2
        g[1][8] = 3
        g[2][2] = 4
        g[1][1] = 6
        g[5][6] = 1
        g[6][5] = 1; g[6][6] = 1; g[6][7] = 1
        return g
    if name == "no_blob":
        # markers but no 1-blob to translate
        g[0][7] = 2
        g[1][10] = 3
        g[2][2] = 4
        g[1][0] = 6
        return g
    return g
