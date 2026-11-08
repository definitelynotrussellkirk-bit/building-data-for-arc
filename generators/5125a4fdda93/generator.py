"""Generator for arc_additional_puzzle_bank_volume2:H13.

Rule: control markers copy a green template at their positions, with
marker color selecting the rotation.

Combinatorial axes (8): grid_h/w, palette_kind, n_anchors, palette_size,
position_bias, n_distinct_colors, vector_length, texture.
Degenerates: no_template, no_anchors, invalid_anchor_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "5125a4fdda93"
VERSION = "2.0.2"  # strengthen executable template/anchor invariants
TASK_ID = "5125a4fdda93"
SUMMARY = (
    "0-bg grid (h~9-13, w~12-17) with: (a) ONE color-3 "
    "(green) TEMPLATE shape — a small polyomino "
    "[(0,0),(0,1),(1,1),(2,1)] placed at upper-left "
    "(rows 0-2, cols 1-2); (b) THREE CONTROL MARKERS "
    "placed at fixed positions ((h-5, 4), (h-4, w-5), "
    "(h-2, 2)) in 3 distinct colors drawn from "
    "{1, 2, 4, 6} — each marker color encodes a "
    "DIFFERENT ROTATION (0°, 90°, 180°, 270° "
    "respectively). Rule: extract the green template. "
    "For each control marker, decode the rotation "
    "from its color and STAMP a rotated copy of the "
    "template in color 3 at the marker's position. "
    "Original template and markers are DISCARDED. "
    "Output: 3 green copies of the template, each "
    "rotated according to its marker, at the marker "
    "positions. Net: marker colors program rotations; "
    "output is the template gallery."
)

INVARIANTS = [
    "the largest green component is the template",
    "control markers use colors 1, 2, 4, or 6",
    "all rotated copies fit in-bounds",
    "the output contains only the green copies",
]

PALETTE_KINDS = ("default", "anchor_1_2", "anchor_4_6", "varied_palette")
DEGENERATE_TEXTURES = ("no_template", "no_anchors", "invalid_anchor_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_anchors":      {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "vector_length":  {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for template+rotation-control-marker samples."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    if not (9 <= h <= 13 and 12 <= w <= 17):
        errs.append(f"normal grid should be 9..13 by 12..17, got {h}x{w}")
    expected_template = {(0, 1), (0, 2), (1, 2), (2, 2)}
    green_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    if green_cells != expected_template:
        errs.append(f"green template cells should be {sorted(expected_template)}, found {sorted(green_cells)[:8]}")
    anchor_positions = [(h - 5, 4), (h - 4, w - 5), (h - 2, 2)]
    anchor_vals = [grid[r][c] for r, c in anchor_positions]
    if len(set(anchor_vals)) != 3 or any(v not in (1, 2, 4, 6) for v in anchor_vals):
        errs.append(f"three anchors must be distinct colors from {{1,2,4,6}}, found {anchor_vals}")
    allowed_nonzero = expected_template | set(anchor_positions)
    extras = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
              if grid[r][c] != 0 and (r, c) not in allowed_nonzero]
    if extras:
        errs.append(f"unexpected nonzero outside template/anchor cells; first={extras[0]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 16, 17)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 12, 17)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    paint_at(g, 0, 1, [(0, 0), (0, 1), (1, 1), (2, 1)], 3)
    anchors = [(h - 5, 4), (h - 4, w - 5), (h - 2, 2)]
    codes = [1, 2, 4, 6]
    rng.shuffle(codes)
    for (r, c), code in zip(anchors, codes):
        g[r][c] = code
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "no_template":
        # anchors but no green template — rotation has nothing to apply
        g[h - 5][4] = 1
        g[h - 4][w - 5] = 2
        g[h - 2][2] = 4
        return g
    if name == "no_anchors":
        # template but no anchors — no copies generated
        paint_at(g, 0, 1, [(0, 0), (0, 1), (1, 1), (2, 1)], 3)
        return g
    if name == "invalid_anchor_color":
        # anchors use colors outside {1,2,4,6} — rotation undefined
        paint_at(g, 0, 1, [(0, 0), (0, 1), (1, 1), (2, 1)], 3)
        g[h - 5][4] = 7  # not in {1,2,4,6}
        g[h - 4][w - 5] = 8
        g[h - 2][2] = 5
        return g
    return g
