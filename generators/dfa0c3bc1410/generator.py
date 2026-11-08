"""Generator for arc_puzzle_bank_seventeenth21:M115 — recolor by border contact.

Rule: each blob gets recolored based on which border its cells touch:
  top → 2 (kept), left → 4, right → 6, no border → 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, all_interior, multi_border_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "dfa0c3bc1410"
VERSION = "2.0.0"
TASK_ID = "dfa0c3bc1410"
SUMMARY = (
    "0-bg grid (h~7-9, w~8-10) "
    "with 4 BLOBS at hardcoded "
    "border positions: (a) "
    "2-cell vertical bar TOUCHING "
    "TOP BORDER at column tc; "
    "(b) 2-cell vertical bar "
    "TOUCHING LEFT BORDER at row "
    "lr; (c) 1-cell bar TOUCHING "
    "RIGHT BORDER at row rr; "
    "(d) 2-3 cell INTERIOR BLOB "
    "growth in the middle. Each "
    "in a DISTINCT color from "
    "{2, 3, 5, 7, 9}. Rule "
    "(RECOLOR BY BORDER "
    "CONTACT): for EACH BLOB, "
    "check which BORDER its "
    "cells touch: (a) blob "
    "touching ROW 0 (top) → "
    "RECOLOR to COLOR 2 (red); "
    "(b) touching COL 0 (left) "
    "→ COLOR 4 (yellow); (c) "
    "touching COL w-1 (right) "
    "→ COLOR 6 (magenta); (d) "
    "fully INTERIOR (no border) "
    "→ COLOR 8 (cyan). Net: "
    "blobs recolored by which "
    "border they touch."
)

INVARIANTS = [
    "background is 0",
    "≥1 blob touching top (some cell in row 0)",
    "≥1 blob touching left (some cell in col 0)",
    "≥1 blob touching right (some cell in col w-1)",
    "≥1 fully-interior blob",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "all_interior", "multi_border_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "blobs_on_each_border",
                       "valid": "blobs_on_each_border"},
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
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 8, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([2, 3, 5, 7, 9], 4)
    tc = rng.randint(2, w - 3)
    g[0][tc] = palette[0]; g[1][tc] = palette[0]
    lr = rng.randint(2, h - 3)
    g[lr][0] = palette[1]; g[lr + 1][0] = palette[1]
    rr = rng.randint(2, h - 3)
    g[rr][w - 1] = palette[2]
    interior_used = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    for r in range(h):
        interior_used.add((r, 0)); interior_used.add((r, w - 1))
    for c in range(w):
        interior_used.add((0, c)); interior_used.add((h - 1, c))
    cells = grow_blob(rng, h, w, interior_used, rng.randint(2, 3), max_attempts=80)
    if cells:
        for r, c in cells: g[r][c] = palette[3]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no blobs to recolor.
        return g
    if name == "all_interior":
        # Every blob is fully interior — rule's recolor mapping
        # only ever fires the "no border → 8" branch; top/left/right
        # branches are never visited.
        for r, c in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        for r, c in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 6
        return g
    if name == "multi_border_blob":
        # A single blob touches multiple borders simultaneously
        # (top + left) — rule's "which border" assignment is
        # ambiguous; recolor target undefined.
        for r, c in [(0, 0), (0, 1), (1, 0)]: g[r][c] = 4
        return g
    return g
