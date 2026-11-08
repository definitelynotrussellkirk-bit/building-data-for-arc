"""Generator for arc_puzzle_bank_fifteenth21:M102 — keep nearest blob to 9-anchor.

Rule: a 9-anchor + multiple non-9 blobs. Keep only the blob whose
center is closest to the anchor (Manhattan distance, distinct distances).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor, no_blobs, all_equidistant.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.selfcheck import components as _components

GENERATOR_ID = "ed658816cdb6"
VERSION = "3.0.1"  # add executable invariant coverage for anchor count and distinct blob distances.
TASK_ID = "ed658816cdb6"
SUMMARY = (
    "0-bg grid (h~9-13, w~10-14) with: (a) "
    "ONE COLOR-9 (maroon) ANCHOR cell at a "
    "random interior position; (b) 2-4 BLOBS "
    "in DISTINCT colors (sampled from "
    "[1..8]) of size 2-5 cells each. Each "
    "blob is at a STRICTLY DISTINCT Manhattan "
    "distance from the anchor (the min "
    "cell-to-anchor distance differs for "
    "every blob; no ties, so 'nearest' is "
    "unambiguous). Rule: identify the COLOR-9 "
    "ANCHOR and the non-9 BLOBS (color-keyed "
    "4-connected components). For each blob, "
    "COMPUTE its MIN Manhattan distance to "
    "the anchor cell. KEEP only the BLOB with "
    "the SMALLEST distance, repainted in its "
    "original color on a BLANK grid; the "
    "anchor and all other blobs are ERASED to "
    "BG (0). Net: output is ONLY the nearest "
    "blob to where the 9-anchor was (no 9 in "
    "the output)."
)

INVARIANTS = [
    "background is 0",
    "exactly one 9-cell (the anchor) in the INPUT (erased in the output)",
    ">=2 distinct-color blobs at strictly distinct Manhattan distances (no ties)",
    "each blob is a single color-keyed 4-connected component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_blobs", "all_equidistant")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "blob_size":      {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "= n_blobs", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "anchor_plus_distinct_distance_blobs",
                       "valid": "anchor_plus_distinct_distance_blobs"},
    "n_distinct_colors": {"type": "int", "default": "= n_blobs", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_anchor|no_blobs|all_equidistant'},
}


def _man(p, cells):
    return min(abs(p[0] - r) + abs(p[1] - c) for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        n_blobs = ctx.draw_int("n_blobs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        n_blobs = ctx.draw_int("n_blobs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    anchor = (rng.randint(2, h - 3), rng.randint(2, w - 3))
    g[anchor[0]][anchor[1]] = 9
    used = {anchor}
    # blob colors: distinct, non-9, non-bg (1..8). The rule keys components by
    # color so blobs may touch without merging; distinct distances make the
    # "nearest" selection unambiguous.
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], n_blobs)
    distances = set()
    placed = 0
    for color in palette:
        for _ in range(50):
            cells = grow_blob(rng, h, w, used, rng.randint(2, 5), max_attempts=20)
            if cells is None:
                continue
            d = _man(anchor, cells)
            if d in distances or d == 0:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            distances.add(d)
            placed += 1
            break
    # Guarantee >=2 blobs so "keep the nearest" is a real selection. On a tight
    # grid where grow_blob/distinct-distance placement failed, drop in small
    # 2-cell blobs at fresh distinct distances.
    fallback_colors = [c for c in (1, 2, 3, 4, 5, 6, 7, 8) if c not in palette[:placed]]
    fi = 0
    while placed < 2 and fi < len(fallback_colors):
        color = fallback_colors[fi]; fi += 1
        for _ in range(80):
            cells = grow_blob(rng, h, w, used, 2, max_attempts=30)
            if cells is None:
                continue
            d = _man(anchor, cells)
            if d in distances or d == 0:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            distances.add(d)
            placed += 1
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one 9-anchor, at least two blobs, and no nearest-distance tie."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    errors: list[str] = []
    if len(anchors) != 1:
        return [f"expected exactly one 9-anchor, got {len(anchors)}"]
    comps = _components(grid, colors={1, 2, 3, 4, 5, 6, 7, 8})
    if len(comps) < 2:
        errors.append(f"expected at least two non-anchor blobs, got {len(comps)}")
    anchor = anchors[0]
    distances = [min(abs(anchor[0] - r) + abs(anchor[1] - c) for r, c in comp["cells"])
                 for comp in comps]
    if len(distances) != len(set(distances)):
        errors.append("two blobs have the same Manhattan distance to the anchor")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_anchor":
        # blobs but no 9-anchor → no reference point for nearest selection
        g[2][2] = 4; g[2][3] = 4
        g[6][7] = 6; g[6][8] = 6
        return g
    if name == "no_blobs":
        # anchor only → nothing to keep or remove
        g[5][5] = 9
        return g
    if name == "all_equidistant":
        # all blobs at same distance from anchor → ambiguous nearest
        g[5][5] = 9
        g[2][5] = 4  # distance 3
        g[5][2] = 6  # distance 3
        g[5][8] = 7  # distance 3
        return g
    return g
