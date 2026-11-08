"""Generator for additional_scaffolded:H4 — Marker extends right by count of 6-objects.

Rule: n = count of color-6 connected components. Marker = first cell of
color 2. From marker (mr, mc), paint cells (mr, mc+1)..(mr, mc+n) with 3
(only where original is 0).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_six,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_six_objects, marker_at_right_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "1ae37a953518"
VERSION = "2.0.1"
TASK_ID = "1ae37a953518"
SUMMARY = (
    "0-bg grid (h~8-10, w~8-10) with: (a) 1-4 NON-"
    "TOUCHING COLOR-6 BLOBS placed in the upper rows "
    "(rows 0..h-3, leaving the bottom row for the "
    "marker) — each blob is a 1-2 cell 4-connected "
    "component grown via grow_blob with a used-set "
    "track to avoid touching neighbors; (b) ONE "
    "COLOR-2 MARKER at fixed BOTTOM-LEFT position "
    "(h-1, 0). The marker has enough horizontal "
    "clearance for the extension to fit within the "
    "grid (col 0..w-1). Rule (EXTEND MARKER RIGHT BY "
    "COUNT OF 6-BLOBS, PAINT COLOR 3): COUNT n = "
    "number of 4-CONNECTED color-6 COMPONENTS. find "
    "the color-2 marker at position (mr, mc). PAINT "
    "the cells (mr, mc+1), (mr, mc+2), ..., (mr, "
    "mc+n) with COLOR 3, but ONLY where the original "
    "cell is bg-0 (don't overwrite 6-cells). 6-blobs "
    "and the marker stay unchanged. Net: a horizontal "
    "color-3 bar of length n appears to the right of "
    "the 2-marker, encoding the count of 6-blobs as "
    "an extension length."
)

INVARIANTS = [
    "between 1 and 4 non-touching 6-blobs (4-connectivity)",
    "exactly one 2-marker placed in bottom-left, with enough room to extend",
    "extension stays within grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_six_objects", "marker_at_right_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_six":          {"type": "int", "default": "rng 1..4",  "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "blobs_top_marker_bottom",
                       "valid": "blobs_top_marker_bottom"},
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
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        n_six = ctx.draw_int("n_six", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_six = ctx.draw_int("n_six", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_six = ctx.draw_int("n_six", 1, 4)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()
    placed = 0
    for _ in range(n_six * 5):
        if placed >= n_six:
            break
        size = rng.randint(1, 2)
        blob = grow_blob(rng, h - 2, w, used, size)
        if blob is None: continue
        used |= blob
        for r, c in blob:
            g[r][c] = 6
        placed += 1
    mc = 0
    g[h - 1][mc] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-6 blob and exactly 1 color-2 marker."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c6 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    c2 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not c6:
        errs.append("no color-6 blob cells found")
    if len(c2) != 1:
        errs.append(f"expected exactly 1 color-2 marker, found {len(c2)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # 6-blobs but no color-2 marker → rule has no anchor to extend
        g[1][1] = 6; g[2][2] = 6
        g[4][5] = 6; g[5][6] = 6
        return g
    if name == "no_six_objects":
        # marker present but no 6-objects → n=0, rule extends by zero (identity)
        g[h - 1][0] = 2
        return g
    if name == "marker_at_right_edge":
        # marker at right side → extension would go off-grid
        g[1][1] = 6; g[2][2] = 6; g[3][3] = 6
        g[h - 1][w - 1] = 2  # cannot extend right
        return g
    return g
