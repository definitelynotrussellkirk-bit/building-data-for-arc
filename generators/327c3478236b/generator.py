"""Generator for arc_puzzle_bank_21_set9_s:S9_M3 — anchor-vector copy.

Rule: 3 = src anchor, 4 = dst anchor, 2 = template. Output: empty grid
+ template translated by (dst-src) painted in 8 + dst itself painted 4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchors, no_template, src_equals_dst.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "327c3478236b"
VERSION = "2.0.2"
TASK_ID = "327c3478236b"
SUMMARY = (
    "0-bg grid (h ∈ 8-11, w ∈ 9-12) "
    "with: (a) ONE COLOR-3 SRC ANCHOR "
    "at a random position in the UPPER-"
    "LEFT region (rows 0..h//3, cols "
    "0..w//2); (b) ONE COLOR-4 DST "
    "ANCHOR at a random position in "
    "the MIDDLE-RIGHT region (rows "
    "h//3..2h//3, cols w//2..w-1) — "
    "guarantees src and dst are "
    "distinct; (c) ONE COLOR-2 "
    "TEMPLATE BLOB — a 3-4 cell "
    "irregular blob built by "
    "grow_blob random walk, placed at "
    "a random non-overlapping position. "
    "Rule (COMPUTE THE VECTOR FROM "
    "SRC-3 TO DST-4, TRANSLATE THE "
    "COLOR-2 TEMPLATE BY THAT VECTOR; "
    "PAINT THE TRANSLATED COPY AS "
    "COLOR 8 ON A FRESH GRID, "
    "PRESERVING DST-4): FIND the "
    "COLOR-3 SRC cell at (sr, sc) "
    "and the COLOR-4 DST cell at "
    "(dr, dc); COMPUTE the vector "
    "v = (dr - sr, dc - sc). "
    "PRODUCE a fresh same-size grid "
    "of 0s. For EACH COLOR-2 "
    "template cell at (r, c): "
    "PAINT g[r + v.r][c + v.c] = "
    "COLOR 8 (cyan). ALSO PAINT "
    "the DST cell at (dr, dc) = "
    "COLOR 4 (preserving the "
    "anchor). Net: template gets "
    "translated by anchor-to-"
    "anchor vector, recolored to "
    "cyan, with dst anchor "
    "preserved as a 4-marker."
)

INVARIANTS = [
    "background is 0",
    "exactly one 3-cell, exactly one 4-cell, ≥2 2-cells in a connected blob",
    "translated cells are in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchors", "no_template", "src_equals_dst")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "blob_size":      {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "src_dst_with_template",
                       "valid": "src_dst_with_template"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_anchors|no_template|src_equals_dst"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one color-3 src, one color-4 dst, ≥2 color-2 template cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    for color, name, count_req in [(3, "src", 1), (4, "dst", 1)]:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if len(cells) != count_req:
            errs.append(f"expected {count_req} color-{color} ({name}) cell(s), found {len(cells)}")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(twos) < 2:
        errs.append(f"only {len(twos)} color-2 template cell(s) (need >=2)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    src = (rng.randint(0, h // 3), rng.randint(0, w // 2))
    # The src/dst sampling bands touch at (h//3, w//2); resample to
    # prevent the dst marker from overwriting the src marker.
    for _ in range(40):
        dst = (rng.randint(h // 3, 2 * h // 3), rng.randint(w // 2, w - 1))
        if dst != src:
            break
    else:
        dst = ((src[0] + 1) % h, min(w - 1, max(w // 2, src[1] + 1)))
    g[src[0]][src[1]] = 3
    g[dst[0]][dst[1]] = 4
    used.add(src); used.add(dst)
    blob = grow_blob(rng, h, w, used, rng.randint(3, 4), max_attempts=80)
    if blob is None:
        return g
    for r, c in blob:
        g[r][c] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_anchors":
        # template only, no 3 or 4 anchors → no translation vector
        g[3][3] = 2; g[3][4] = 2; g[4][3] = 2
        return g
    if name == "no_template":
        # anchors but no 2-template → nothing to translate
        g[1][1] = 3
        g[5][6] = 4
        return g
    if name == "src_equals_dst":
        # both anchors at the same cell → vector is zero, rule is identity
        g[3][3] = 3
        g[3][3] = 4   # overwrites the 3 → ambiguous anchor
        g[5][5] = 2; g[5][6] = 2; g[6][5] = 2
        return g
    return g
