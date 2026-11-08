"""Generator for arc_puzzle_bank_21_set20_bundle:medium_p03 — corner-key extract.

Rule: at(0,0) = key. Find all key-color cells (excluding the corner),
crop to bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_distractors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_target_cells, key_cells_at_corner_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "923465deb4e4"
VERSION = "2.1.1"  # add self_check  # dup40%: key blob only 3-5 cells -> few distinct bbox crops. Output = bbox crop of the key-color blob. Use 4-8 cell key blobs on slightly larger grids -> more distinct output shapes/sizes.
TASK_ID = "923465deb4e4"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with: (a) cell (0,0) = KEY "
    "(some non-bg color); (b) one 3-5 cell BLOB of the KEY "
    "color placed elsewhere on the grid (away from (0,0)); "
    "(c) 1-2 DISTRACTOR blobs in different colors. Rule: "
    "read key = grid[0][0]. Clear (0,0) to 0 (temp). Find all "
    "cells in temp matching the key color. If none → output "
    "[[0]]. Else: compute bbox of those key-color cells. "
    "Output: temp cropped to that bbox (small grid containing "
    "the key blob plus any distractor cells that happen to "
    "lie inside the same bbox)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "(0,0) holds the key color",
    "≥1 key-color cell exists somewhere not at (0,0)",
    "1-2 distractor blobs in different colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_target_cells", "key_cells_at_corner_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distractors":  {"type": "int", "default": "2", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "key_at_corner",
                       "valid": "key_at_corner"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; (0,0) is the non-zero key; ≥1 key-color cell elsewhere."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    key = grid[0][0]
    if key == 0:
        errs.append("(0,0) is 0 — key must be non-zero")
    else:
        others = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == key and (r, c) != (0, 0)]
        if not others:
            errs.append(f"no key-color ({key}) cells outside (0,0)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 9, 10)
        k_lo, k_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 14)
        k_lo, k_hi = 6, 9
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 13)
        k_lo, k_hi = 4, 8
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    key = palette[0]
    distractors = palette[1:]
    g[0][0] = key
    used = {(0, 0)}
    blob = grow_blob(rng, h, w, used, rng.randint(k_lo, k_hi), max_attempts=80)
    if blob is None:
        return g
    for r, c in blob:
        g[r][c] = key
    used |= blob
    for color in distractors:
        b = grow_blob(rng, h, w, used, rng.randint(2, 3), max_attempts=40)
        if b is None:
            continue
        for r, c in b:
            g[r][c] = color
        used |= b
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_key":
        # (0,0) is bg → no key color, rule has no anchor
        for r, c in [(2, 3), (3, 3), (3, 4)]:
            g[r][c] = 4
        for r, c in [(5, 6), (5, 7)]:
            g[r][c] = 6
        return g
    if name == "no_target_cells":
        # key at (0,0) but no other cells of that color → bbox over empty set is undefined
        g[0][0] = 5
        for r, c in [(3, 3), (3, 4), (4, 4)]:
            g[r][c] = 6
        for r, c in [(6, 7), (7, 7)]:
            g[r][c] = 4
        return g
    if name == "key_cells_at_corner_only":
        # only (0,0) has the key color (no other instances) → empty target set, undefined output
        g[0][0] = 5
        return g
    return g
