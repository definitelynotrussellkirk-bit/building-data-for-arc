"""Generator for arc_additional_puzzles_21_set22_bundle:E148 -- connect 2 aligned cells.

Rule: exactly two non-0 cells. If they share a row, draw the horizontal
segment between them; otherwise draw a vertical segment at the first
cell's column spanning their row range. The line takes the first cell's
color, on a blank grid.

This generator places two same-color cells aligned in a row or column.

Combinatorial axes: grid size, the two endpoints (row or column aligned),
and the color.
Degenerates: one_cell, no_cells, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70a3e6be3283"
VERSION = "2.0.0"  # diversity: two aligned same-color endpoints -> connecting line (was fixed ~27)
TASK_ID = "70a3e6be3283"
SUMMARY = (
    "0-bg grid (size varies) with two non-0 cells aligned in a row or "
    "column. Rule: connect them with a segment (horizontal if same row, "
    "else vertical at the first cell's column) in the first cell's color, on "
    "a blank grid. The grid size, endpoints and color vary freely (was a "
    "fixed setup, ~27 distinct). Output is a single line, so distinct "
    "OUTPUTS are bounded; distinct INPUTS are large."
)

INVARIANTS = [
    "exactly two non-0 endpoints aligned in a row or column",
    "the output is the connecting segment in the first cell's color",
    "the endpoints are separated so the segment is non-trivial",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("one_cell", "no_cells", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..22"},
    "axis":           {"type": "str", "default": "rng", "valid": "row|col"},
    "color":          {"type": "color", "default": "rng !0", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "two_aligned", "valid": "two_aligned"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|one_cell|no_cells|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    axis = overrides.get("axis") or rng.choice(["row", "col"])

    if difficulty == "easy":
        hr, wr = (8, 11), (8, 12)
    elif difficulty == "hard":
        hr, wr = (14, 20), (16, 22)
    else:
        hr, wr = (10, 15), (11, 17)

    color = rng.randint(1, 9)
    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        if axis == "row":
            r = rng.randint(0, h - 1)
            c1, c2 = sorted(rng.sample(range(w), 2))
            if c2 - c1 < 2:
                continue
            g[r][c1] = color; g[r][c2] = color
        else:
            c = rng.randint(0, w - 1)
            r1, r2 = sorted(rng.sample(range(h), 2))
            if r2 - r1 < 2:
                continue
            g[r1][c] = color; g[r2][c] = color
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    g[3][2] = 4; g[3][8] = 4
    if name == "one_cell":
        g[3][8] = 0
        return g
    if name == "no_cells":
        return full_grid(10, 12, 0)
    if name == "full_grid":
        return full_grid(10, 12, 4)
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the two-endpoint line task."""
    errors: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    pts: list[tuple[int, int, int]] = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not isinstance(v, int) or not 0 <= v <= 9:
                errors.append("grid values must be ARC digits 0..9")
            if v != 0:
                pts.append((r, c, v))
    if len(pts) != 2:
        errors.append(f"normal sample must contain exactly two endpoints, found {len(pts)}")
        return sorted(set(errors))
    (r1, c1, color1), (r2, c2, color2) = pts
    if color1 != color2:
        errors.append("the two endpoints must have the same color")
    if r1 != r2 and c1 != c2:
        errors.append("endpoints must be row- or column-aligned")
    if abs(r1 - r2) + abs(c1 - c2) < 2:
        errors.append("endpoints must be separated by at least one interior cell")
    return sorted(set(errors))
