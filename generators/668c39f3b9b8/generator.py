"""Generator for 3b:m16 — shift all blobs by direction key.

Rule: a single direction-key cell at a grid corner determines the
shift direction. All non-key blobs shift by 1 cell in that direction.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_blobs, blob_blocking_shift.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "668c39f3b9b8"
VERSION = "1.2.0"  # lock direction key to canonical control colors and keep shifted blobs in bounds
TASK_ID = "668c39f3b9b8"
SUMMARY = "Single canonical direction-key color + 2 blobs in interior."

INVARIANTS = [
    "background is 0",
    "exactly one corner key cell (e.g. (h-1, 0))",
    "2-3 distinct-color blobs in interior, none touching the corner",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_blobs", "blob_blocking_shift")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "corner_key_plus_interior_blobs",
                       "valid": "corner_key_plus_interior_blobs"},
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # The canonical rule reads the direction from the unique singleton among
    # colors 1..4.  The old generator sampled the key from 1..9, so many normal
    # rows had no valid control color (or an accidental body singleton became
    # the control).  Use a real control color and body colors outside 1..4.
    key = rng.choice([1, 2, 3, 4])
    drdc = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}[key]
    g[h - 1][0] = key
    used = {(h - 1, 0), (h - 1, 1), (h - 2, 0)}
    dr, dc = drdc
    if dr < 0:
        used.update((0, c) for c in range(w))
    if dr > 0:
        used.update((h - 1, c) for c in range(w))
    if dc < 0:
        used.update((r, 0) for r in range(h))
    if dc > 0:
        used.update((r, w - 1) for r in range(h))
    for color in rng.sample([5, 6, 7, 8, 9], 2):
        cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=80)
        if cells:
            for r, c in cells: g[r][c] = color
            used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_key":
        # blobs without corner direction-key → no shift direction
        g[3][3] = 4; g[3][4] = 4; g[4][3] = 4
        g[5][6] = 6; g[5][7] = 6
        return g
    if name == "no_blobs":
        # corner key alone with no blobs → nothing to shift
        g[h - 1][0] = 5
        return g
    if name == "blob_blocking_shift":
        # blob touches the row/col where shift would push another blob → collision
        g[h - 1][0] = 5  # shift up
        g[3][3] = 4; g[3][4] = 4
        g[2][3] = 6  # blocks the upward shift of the 4-blob
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    h, w = len(grid), len(grid[0])
    counts = {color: sum(row.count(color) for row in grid) for color in (1, 2, 3, 4)}
    controls = [color for color, count in counts.items() if count == 1]
    key = grid[h - 1][0]
    if key not in (1, 2, 3, 4):
        msgs.append(f"bottom-left key must be a canonical control color 1..4, found {key}")
    if controls != [key]:
        msgs.append(f"expected exactly the key as singleton among colors 1..4; got {controls}, key={key}")
    body = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
            if v != 0 and not (r == h - 1 and c == 0)]
    if len({v for _r, _c, v in body}) < 2:
        msgs.append("expected two distinct shifted body-blob colors")
    if key in (1, 2, 3, 4):
        dr, dc = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}[key]
        for r, c, _v in body:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                msgs.append(f"body cell {(r, c)} would shift out of bounds for key {key}")
                break
    return msgs
