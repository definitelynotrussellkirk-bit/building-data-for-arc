"""Generator for arc_puzzle_bank_21_set9_e:medium_i08 — crop blob named by corner key.

Rule: at(0,0) = key. Find the (single non-corner) blob of color `key`,
crop to its bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_distractors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key_blob, multiple_key_blobs, no_corner_key.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "acd7a04963f1"
VERSION = "2.1.0"  # dup-outputs 34%: tiny 2-4 cell key blob on small grid -> few cropped outputs. Widen grid + grow larger varied key blob (output=key-blob crop) -> distinct 49->109, flags cleared."
TASK_ID = "acd7a04963f1"
SUMMARY = (
    "0-bg grid (h, w~7-10) with: (a) cell "
    "(0, 0) holding a KEY COLOR from a "
    "3-color palette; (b) ONE KEY-COLOR BLOB "
    "(2-4 cells, connected polyomino) placed "
    "AWAY from the (0, 0) corner in the same "
    "key color; (c) 1-2 DISTRACTOR BLOBS in "
    "the other 2 palette colors (2-3 cells "
    "each, non-overlapping). Rule: READ the "
    "KEY at (0, 0). Find the UNIQUE BLOB of "
    "matching KEY COLOR that's NOT at the "
    "corner. CROP that blob to its BBOX and "
    "OUTPUT the cropped subgrid (preserving "
    "key color and shape). Distractors and "
    "the corner-key are discarded. Net: "
    "corner-key selects the target by color; "
    "output is bbox crop of the matching "
    "non-corner blob."
)

INVARIANTS = [
    "background is 0",
    "(0,0) holds the key color",
    "≥1 key-color blob away from (0,0)",
    "1-2 distractor blobs in different colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key_blob", "multiple_key_blobs", "no_corner_key")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..15"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distractors":  {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "key_at_origin",
                       "valid": "key_at_origin"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
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
    # Rule: output = bbox crop of the corner(0,0)-color cells (minus the marker).
    # Output diversity = the key blob's shape/size. v1.x grew a tiny 2-4 cell key
    # blob on a small grid -> dup 34%. Widen grid + grow a larger varied key blob.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9); ks = (3, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 11, 15); ks = (6, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 13); w = ctx.draw_int("grid_w", 8, 13); ks = (4, 8)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    key, d1, d2 = palette
    g[0][0] = key
    used = {(0, 0)}
    blob = grow_blob(rng, h, w, used, rng.randint(*ks), max_attempts=120)
    if blob:
        for r, c in blob: g[r][c] = key
        used |= blob
    for color in (d1, d2):
        b = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=40)
        if b:
            for r, c in b: g[r][c] = color
            used |= b
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_key_blob":
        # key at (0,0) but no other key-color blob → rule has nothing to crop
        g[0][0] = 4
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 6
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 3
        return g
    if name == "multiple_key_blobs":
        # two blobs of key color → ambiguous which to crop
        g[0][0] = 4
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 4
        for (r, c) in [(4, 1), (4, 2)]: g[r][c] = 6
        return g
    if name == "no_corner_key":
        # (0,0) is bg → no key, rule has no anchor
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 6
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components

    errs: list[str] = []
    key = grid[0][0]
    if key == 0:
        return ["missing nonzero corner key at (0,0)"]
    key_comps = components(grid, colors={key})
    target_comps = [comp for comp in key_comps if (0, 0) not in comp["cells"]]
    if len(target_comps) != 1:
        errs.append("expected exactly one non-corner blob matching the key color")
    elif len(target_comps[0]["cells"]) < 3:
        errs.append("key-selected blob is too small to be a useful crop witness")
    other_colors = {v for row in grid for v in row if v not in (0, key)}
    if len(other_colors) < 2:
        errs.append("expected distractor blobs in two non-key colors")
    return errs
