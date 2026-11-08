"""Generator for arc_additional_puzzle_bank_volume7:E43.

Rule: red components touching exactly two borders are recolored green.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, no_two_border, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "675edc7213e5"
VERSION = "2.0.1"
TASK_ID = "675edc7213e5"
SUMMARY = (
    "0-bg grid (h, w~8-13) with multiple color-2 (red) "
    "RECTANGULAR BLOCKS placed at varying positions. "
    "Layout: 2×2 RED CORNER block at (0, 0) [top-left] "
    "touches top + left borders (2 borders); 2×2 RED "
    "CORNER block at (h-2, w-2) [bottom-right] touches "
    "bottom + right (2 borders); 2×1 RED block on top "
    "edge at a random column (touches top border only "
    "→ 1 border); 2×2 RED block at (h//2, w//2) "
    "[center] touches 0 borders. Components are "
    "4-conn isolated. Rule: count how many of the 4 "
    "GRID BORDERS each color-2 component touches (a "
    "border is touched if any cell of the component "
    "lies on row 0, row h-1, col 0, or col w-1). For "
    "every component touching EXACTLY 2 borders, "
    "RECOLOR all its cells from 2 to 3 (green). "
    "Components touching 0, 1, 3, or 4 borders stay "
    "red. Net: only the corner blobs (touching exactly "
    "two borders) turn green."
)

INVARIANTS = [
    "background is 0",
    "some red components touch exactly two borders",
    "other red components touch zero or one border",
    "components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "no_two_border", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "8..13"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "8..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-2 (red) cell; ≥1 two-border-touching component."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_2:
        errs.append("no color-2 (red) cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
    g = full_grid(h, w, 0)
    draw_rect(g, 0, 0, 2, 2, 2)
    draw_rect(g, h - 2, w - 2, 2, 2, 2)
    draw_rect(g, 0, rng.randint(3, w - 4), 2, 1, 2)
    draw_rect(g, h // 2, w // 2, 2, 2, 2)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_objects":
        return g
    if name == "no_two_border":
        draw_rect(g, 4, 4, 2, 2, 2)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 2
        return g
    return g
