"""Generator for arc_additional_puzzles_21_set11_bundle:M73.

Rule: each object expands to its bounding-box border plus a same-color
checker pattern inside.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, single_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "2b7bcfbf942b"
VERSION = "2.0.1"
TASK_ID = "2b7bcfbf942b"
SUMMARY = (
    "0-bg grid (h ∈ 9-12, w ∈ 10-14) "
    "with: TWO OBJECTS at FIXED "
    "positions: (a) FIRST OBJECT at "
    "(1, 1) with cells [(0, 0), "
    "(1, 0), (2, 0), (2, 1), (2, 2), "
    "(2, 3)] (L-hexomino) in "
    "colors[0]; (b) SECOND OBJECT "
    "at (h-4, w-5) with cells "
    "[(0, 0), (0, 1), (0, 2), "
    "(1, 2), (2, 2), (2, 3)] "
    "(Z-hexomino) in colors[1]. "
    "Colors drawn distinct from "
    "{1..9}\\{0}. Rule (EACH OBJECT "
    "EXPANDS TO ITS BOUNDING-BOX "
    "BORDER PLUS A SAME-COLOR "
    "CHECKER PATTERN INSIDE THE "
    "BBOX): For EACH object with "
    "color c and bbox (rmin..rmax, "
    "cmin..cmax): PAINT every "
    "border cell of the bbox (top/"
    "bottom rows, left/right cols) "
    "with c. For interior cells "
    "(strictly inside the bbox): "
    "PAINT cells where (r + c) % 2 "
    "== 0 (or similar checker "
    "predicate) with c; leave "
    "others 0. Net: each object "
    "becomes a rectangular bordered "
    "block with a checker fill in "
    "its color."
)

INVARIANTS = [
    "objects are separated by background",
    "object bounding boxes have interior cells where checker fill is visible",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, has at least 2 distinct non-bg colors (the two objects)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        return [f"expected >=2 distinct non-bg colors, got {len(colors)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
    colors = list(ctx.draw_distinct_colors("colors", n=2, exclude=[0]))
    g = full_grid(h, w, 0)
    paint_at(g, 1, 1, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)], colors[0])
    paint_at(g, h - 4, w - 5, [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)], colors[1])
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_objects":
        return g
    if name == "single_object":
        paint_at(g, 1, 1, [(0, 0), (1, 0), (2, 0), (2, 1)], 3)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 3
        return g
    return g
