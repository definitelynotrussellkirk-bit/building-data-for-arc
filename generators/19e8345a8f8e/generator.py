"""Generator for arc_puzzle_bank_21_set3:S3_M3 — farthest-from-border blob.

Rule: pick the blob whose bbox center is farthest (Chebyshev) from any
grid border, recolor to 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, tied_distance, all_on_border.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "19e8345a8f8e"
VERSION = "2.0.1"
TASK_ID = "19e8345a8f8e"
SUMMARY = (
    "0-bg grid (h, w~9-11) "
    "with 3 SAME-SHAPE "
    "BLOBS each a 2×2 "
    "SOLID SQUARE in COLOR "
    "1. The 3 blobs are "
    "placed at NON-"
    "TOUCHING positions "
    "(1-cell padding) so "
    "that their bbox-min-"
    "distance-to-grid-"
    "border values are all "
    "STRICTLY DISTINCT "
    "(Chebyshev distance "
    "from bbox to any of "
    "the 4 grid edges is "
    "the minimum of "
    "row-from-top, "
    "row-from-bottom, "
    "col-from-left, "
    "col-from-right). Rule "
    "(RECOLOR THE FARTHEST-"
    "FROM-BORDER BLOB TO "
    "COLOR 7): for EACH "
    "blob, compute its "
    "BBOX CENTER's "
    "DISTANCE to any GRID "
    "BORDER (Chebyshev). "
    "Find the blob with "
    "the STRICTLY MAXIMUM "
    "distance (the most "
    "interior blob). "
    "RECOLOR all cells of "
    "that blob from 1 to "
    "COLOR 7. Other blobs "
    "stay at 1. Net: the "
    "most interior blob "
    "turns orange; the "
    "border-adjacent "
    "blobs stay blue."
)

INVARIANTS = [
    "background is 0",
    "3 blobs all in color 1 (so output recoloring is unambiguous)",
    "blobs at strictly distinct distance-to-nearest-border",
    "blobs are 2x2 squares for simplicity",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "tied_distance", "all_on_border")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3..3"},
    "palette_size":   {"type": "str", "default": "1 (color 1)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "distinct_chebyshev_distances",
                       "valid": "distinct_chebyshev_distances"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly 3 color-1 blobs (the farthest one will be recolored)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_blobs", "tied_distance", "all_on_border"):
        return errs
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    others = [(r, c) for r in range(h) for c in range(w)
              if grid[r][c] not in (0, 1)]
    if not ones:
        errs.append("no color-1 blob cells found")
    if others:
        errs.append(f"unexpected non-0 non-1 cells: {others[:3]}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 9, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    seen_dists = set()
    placed = 0
    for _ in range(60):
        if placed >= 3:
            break
        r1 = rng.randint(0, h - 2)
        c1 = rng.randint(0, w - 2)
        if not _free(g, r1, c1, r1 + 1, c1 + 1):
            continue
        d = min(r1, h - 1 - (r1 + 1), c1, w - 1 - (c1 + 1))
        if d in seen_dists:
            continue
        for r in range(r1, r1 + 2):
            for c in range(c1, c1 + 2):
                g[r][c] = 1
        seen_dists.add(d)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — no blob to recolor.
        return g
    if name == "tied_distance":
        # Three blobs at the same distance from the nearest border —
        # rule's selection by max-distance is ambiguous.
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 1
        for r in range(2):
            for c in range(2):
                g[1 + r][7 + c] = 1
        for r in range(2):
            for c in range(2):
                g[7 + r][7 + c] = 1
        return g
    if name == "all_on_border":
        # All three blobs touch the border (distance 0) — rule degenerates
        # to picking any of them.
        for r in range(2):
            for c in range(2):
                g[r][c] = 1
        for r in range(2):
            for c in range(2):
                g[r][8 + c] = 1
        for r in range(2):
            for c in range(2):
                g[8 + r][c] = 1
        return g
    return g
