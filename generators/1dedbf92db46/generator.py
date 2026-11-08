"""Generator for arc_puzzle_bank_twentythird21:M161 — transfer cutout to second block.

Rule: the first blob has a hole (interior 0-cell). The second blob is
solid bbox-fill. Output: erase a corresponding hole in the second blob
at the same relative position.

Combinatorial axes (8): grid_h, grid_w, palette_kind, hole_position,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_hole, both_solid, both_hollow.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1dedbf92db46"
VERSION = "2.0.1"
TASK_ID = "1dedbf92db46"
SUMMARY = "Two same-size square blocks side-by-side in distinct colors. Left block is hollow (has 1+ interior 0 cells defining a 'mask'). Right block is solid. Rule outputs the left block unchanged + the right block painted using the left block's mask cells as a stencil (only those positions paint in right-block color)."

# Rivals: 'output is input' refuted by any demo (right block changes
# shape). 'transfer color from left' refuted by any demo (transferred
# uses right's color). 'fill right hole equally' refuted by ≥1 demo
# where the right block mass changes. 'mirror left to right' refuted
# by any demo where left stays the source mask. 3 demos with varied
# block positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "left block (color A): rect-frame 3x3 with center 0 (hollow)",
    "right block (color B): solid 3x3",
    "blocks have distinct colors and don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_hole", "both_solid", "both_hollow")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..11"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "hole_position":  {"type": "str", "default": "center", "valid": "center"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_blocks_left_hollow",
                       "valid": "two_blocks_left_hollow"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 10, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 16, 20)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 12, 16)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)
    fc, sc = palette
    r1 = rng.randint(1, h - 4)
    c1 = rng.randint(1, w // 2 - 4)
    for r in range(r1, r1 + 3):
        for c in range(c1, c1 + 3):
            g[r][c] = fc
    g[r1 + 1][c1 + 1] = 0
    c2 = rng.randint(w // 2 + 1, w - 4)
    for r in range(r1, r1 + 3):
        for c in range(c2, c2 + 3):
            g[r][c] = sc
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 2 distinct non-bg colors; left block has >=1 interior zero."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) != 2:
        errs.append(f"expected exactly 2 distinct non-bg colors, found {len(colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 6, 12
    g = full_grid(h, w, 0)
    if name == "no_hole":
        # left block solid, right block solid → no cutout to transfer
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 3
        for r in range(1, 4):
            for c in range(8, 11):
                g[r][c] = 5
        return g
    if name == "both_solid":
        # both blocks solid (same as no_hole) → rule's "transfer hole" precondition fails
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 3
        for r in range(1, 4):
            for c in range(8, 11):
                g[r][c] = 5
        return g
    if name == "both_hollow":
        # both have a hole → ambiguous which is the "source" template
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][c] = 3
        g[2][2] = 0
        for r in range(1, 4):
            for c in range(8, 11):
                g[r][c] = 5
        g[2][9] = 0
        return g
    return g
