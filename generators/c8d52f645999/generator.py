"""Generator for arc_puzzle_bank_fourteenth21:M97 — extract guide-colored blob.

Rule: at(0,0) = key. Find the (single non-corner) blob of color `key`,
crop to its bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_corner_key, no_key_blob, multiple_key_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "c8d52f645999"
VERSION = "1.2.1"  # distinct 77: output = the key-colored blob cropped, but blob was only 3-5 cells -> few shapes. Now larger blobs (3-8 by difficulty) on bigger grids + separate the blob from the (0,0) corner key (so it stays a distinct non-corner component) -> more distinct crops."
TASK_ID = "c8d52f645999"
SUMMARY = "Key at (0,0) + a key-color blob away from corner + 1 distractor."

INVARIANTS = [
    "background is 0",
    "(0,0) holds the key color",
    "≥1 key-color blob away from (0,0)",
    "≥1 distractor blob in another color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corner_key", "no_key_blob", "multiple_key_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "key_at_origin_with_blob",
                       "valid": "key_at_origin_with_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
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
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 8, 10); b_lo, b_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14); b_lo, b_hi = 5, 8
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 9, 12); b_lo, b_hi = 4, 7
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    key, distractor = palette
    g[0][0] = key
    # keep the key blob OFF the corner key cell (and its 8-neighbors) so it stays a
    # distinct non-corner component the rule can crop.
    used = {(r, c) for r in range(2) for c in range(2)}
    blob = grow_blob(rng, h, w, used, rng.randint(b_lo, b_hi), max_attempts=120)
    if blob:
        for r, c in blob: g[r][c] = key
        used |= blob
    dist = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=60)
    if dist:
        for r, c in dist: g[r][c] = distractor
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_corner_key":
        # (0,0) is bg → no key, rule has no anchor
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 6)]: g[r][c] = 6
        return g
    if name == "no_key_blob":
        # key at (0,0) but no other key-color blob → rule has nothing to crop
        g[0][0] = 4
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 6
        return g
    if name == "multiple_key_blobs":
        # two blobs of key color → ambiguous which to crop
        g[0][0] = 4
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Cell (0,0) must hold the key color; a non-corner key-color blob must exist elsewhere."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 2 or w < 2:
        msgs.append("grid too small")
        return msgs
    key = grid[0][0]
    if key == 0:
        msgs.append("(0,0) is background (must be the key color)")
        return msgs
    # Check that there's at least one key-color cell not at (0,0)
    key_others = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == key and (r, c) != (0, 0)]
    if not key_others:
        msgs.append(f"no key-color ({key}) blob outside (0,0) for the rule to crop")
    # Check there's at least one distractor (different non-bg color)
    others = {grid[r][c] for r in range(h) for c in range(w)
              if grid[r][c] != 0 and grid[r][c] != key}
    if not others:
        msgs.append("no distractor blob in a different color")
    return msgs
