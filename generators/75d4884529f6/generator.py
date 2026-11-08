"""Generator for 98c475bf.

Rule: paired row markers between side borders expand into fixed line
glyphs.

Combinatorial axes (8): grid_h/w, marker_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, border.
Degenerates: no_borders, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75d4884529f6"
VERSION = "2.0.1"  # shape-locked in/out: fixed 12x20, fixed marker rows [3,5,8]. Rule (connect paired row-markers between side borders) reads h/w generically. Vary grid size, marker count (1-4) and marker rows.
TASK_ID = "75d4884529f6"
SUMMARY = "Paired row markers between side borders expand into line glyphs. Grid size, marker count and marker rows vary."

INVARIANTS = [
    "the first cell defines the side-border color",
    "valid marker rows have identical non-border colors at columns 1 and w-2",
    "marker colors come from the supported glyph palette",
    "border color is distinct from marker glyph colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_borders", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "20", "valid": "20"},
    "marker_count":   {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "border":         {"type": "color", "default": "rng !{0,1,2,3,6,7}",
                       "valid": "4|5|8|9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 non-zero cell at col 0 (border), ≥1 marker row with paired non-border cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    # Col 0 should be the side-border (all same color)
    border_color = grid[0][0]
    if border_color == 0:
        errs.append("col-0 border has value 0 (expected non-zero border color)")
    # Has ≥1 row with identical non-0 markers at col 1 and col w-2
    has_marker_row = any(
        grid[r][1] != 0 and grid[r][1] == grid[r][w - 2]
        for r in range(h) if w >= 4
    )
    if not has_marker_row:
        errs.append("no row found with matching non-zero markers at col 1 and col w-2")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        mc_lo, mc_hi = 1, 2; h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 14, 18)
    elif difficulty == "hard":
        mc_lo, mc_hi = 3, 4; h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 18, 24)
    else:
        mc_lo, mc_hi = 1, 3; h = ctx.draw_int("grid_h", 12, 18); w = ctx.draw_int("grid_w", 16, 22)
    marker_count = ctx.draw_int("marker_count", mc_lo, min(mc_hi, h - 2))
    border = ctx.draw_color("border", exclude={0, 1, 2, 3, 6, 7})
    colors = rng.sample([c for c in (6, 7, 2, 1, 3, 4, 5, 9) if c != border], marker_count)
    rows = rng.sample(range(h), marker_count)
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = border
        g[r][w - 1] = border
    for row, color in zip(rows, colors):
        g[row][1] = color
        g[row][w - 2] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 20, 0)
    if name == "no_borders":
        g[3][1] = 2; g[3][18] = 2
        return g
    if name == "no_markers":
        for r in range(12):
            g[r][0] = 5; g[r][19] = 5
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(20):
                g[r][c] = 5
        return g
    return g
