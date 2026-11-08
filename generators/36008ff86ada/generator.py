"""Generator for arc_puzzle_bank_twentyfirst21:E147 — stamp 2x2 proto at each color-9 marker.

Rule: a 2x2 proto block at the top-left corner (rows 0-1, cols 0-1). The
interior of the grid (rows 2..h-2, cols 2..w-2) has color-9 markers; the
proto is pasted at each marker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_proto, no_markers, marker_at_border.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36008ff86ada"
VERSION = "1.2.0"  # +self_check
TASK_ID = "36008ff86ada"

SUMMARY = "2x2 colored proto in top-left + 1-3 color-9 markers in the interior."

INVARIANTS = [
    "background is 0",
    "rows 0-1, cols 0-1 hold a 2x2 colored proto pattern (some non-zero cells)",
    "1-3 color-9 markers in the interior (rows 2..h-2, cols 2..w-2)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_proto", "no_markers", "marker_at_border")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "proto_topleft_markers_interior",
                       "valid": "proto_topleft_markers_interior"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-9 marker in interior, some non-zero proto cells in top-left."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    # Check for color-9 markers in interior (rows 2..h-2, cols 2..w-2)
    has_marker = any(grid[r][c] == 9
                     for r in range(2, h - 1) for c in range(2, w - 1))
    if not has_marker:
        errs.append("no color-9 marker cells in interior (rows 2..h-2, cols 2..w-2)")
    # Check for proto cells in top-left 2x2
    has_proto = any(grid[r][c] != 0 for r in range(min(2, h)) for c in range(min(2, w)))
    if not has_proto:
        errs.append("no nonzero proto cells in top-left 2x2 block")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n = ctx.draw_int("n_markers", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n = ctx.draw_int("n_markers", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n = ctx.draw_int("n_markers", 1, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    proto_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    # 2-3 cells in the 2x2 proto
    proto_cells = rng.sample([(0, 0), (0, 1), (1, 0), (1, 1)], rng.randint(2, 3))
    for r, c in proto_cells:
        g[r][c] = proto_color
    # markers in interior
    placed = 0
    for _ in range(120):
        if placed >= n: break
        r = rng.randint(2, h - 2); c = rng.randint(2, w - 2)
        if g[r][c] != 0: continue
        # require some isolation
        if any(g[r + dr][c + dc] != 0 for dr in range(-1, 2) for dc in range(-1, 2)
               if 0 <= r + dr < h and 0 <= c + dc < w):
            continue
        g[r][c] = 9
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_proto":
        # Markers present but no proto in top-left — rule has nothing to stamp.
        g[4][4] = 9
        return g
    if name == "no_markers":
        # Proto present but no markers — rule has no anchor positions.
        g[0][0] = 3; g[0][1] = 3; g[1][0] = 3
        return g
    if name == "marker_at_border":
        # Marker at row/col h-1 — proto would overflow grid bounds.
        g[0][0] = 3; g[0][1] = 3; g[1][0] = 3
        g[h - 1][w - 1] = 9
        return g
    return g
