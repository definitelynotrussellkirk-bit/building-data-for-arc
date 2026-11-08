"""Generator for arc_additional_puzzle_bank_volume6:M39.

Colored objects slide rightward until they pack against a gray wall.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_wall, no_objects, objects_at_wall.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e5ead55c33e7"
VERSION = "2.0.0"  # objects were only 1-2 cells on even rows; canonical packs richer shapes (2x2, L, triominoes). Widen to a polyomino bank with free separated placement left of the wall (rule slides any color-2/3/4 object rightward to pack). More sizes/shapes/positions.
TASK_ID = "e5ead55c33e7"
SUMMARY = "Colored objects slide rightward until they pack against a gray wall."

INVARIANTS = [
    "background is 0",
    "there is a full-height gray wall column",
    "movable objects are colors 2, 3, or 4 and start left of the wall",
    "objects have clear space to move right before settling",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_wall", "no_objects", "objects_at_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 9..15", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "wall_with_left_objects",
                       "valid": "wall_with_left_objects"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],   # 2x2
    [(0, 0), (0, 1), (0, 2)],            # row triomino
    [(0, 0), (1, 0), (2, 0)],            # col triomino
    [(0, 0), (1, 0), (1, 1)],            # L
    [(0, 0), (0, 1), (1, 1)],            # corner
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)],  # P-pentomino
]


def _free_at(g, cells, top, left, wall):
    """Cells + their 8-neighbours must be bg, in-bounds, and left of wall."""
    h = len(g)
    for r, c in cells:
        rr, cc = top + r, left + c
        if not (0 <= rr < h and 0 <= cc < wall):     # stay strictly left of wall
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                ar, ac = rr + dr, cc + dc
                if 0 <= ar < h and 0 <= ac <= wall and g[ar][ac] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_objects = ctx.draw_int("n_objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_objects = ctx.draw_int("n_objects", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n_objects = ctx.draw_int("n_objects", 3, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    wall = w - 1
    for r in range(h):
        g[r][wall] = 5
    colors = [2, 3, 4]
    placed = 0
    for _ in range(400):
        if placed >= n_objects:
            break
        shape = rng.choice(_SHAPES)
        mr = max(r for r, _ in shape)
        mc = max(c for _, c in shape)
        top = rng.randint(0, h - mr - 1)
        left = rng.randint(0, max(0, wall - mc - 1))
        if not _free_at(g, shape, top, left, wall):
            continue
        color = colors[placed % len(colors)]
        for r, c in shape:
            g[top + r][left + c] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    wall = w - 1
    if name == "no_wall":
        # objects without gray wall → nothing to pack against
        g[1][2] = 2; g[1][3] = 2
        g[3][1] = 3
        return g
    if name == "no_objects":
        # wall alone → nothing to slide
        for r in range(h):
            g[r][wall] = 5
        return g
    if name == "objects_at_wall":
        # objects already touching wall → slide is identity
        for r in range(h):
            g[r][wall] = 5
        g[1][wall - 1] = 2; g[1][wall - 2] = 2
        g[3][wall - 1] = 3
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    wall_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if wall_cols != [w - 1]:
        errs.append(f"expected one full-height gray wall at right edge, got {wall_cols}")
    movable = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] in (2, 3, 4)]
    lo, hi = (2, 2) if difficulty == "easy" else ((4, 6) if difficulty == "hard" else (3, 4))
    # Object count is color-component count, not cell count.
    seen = set(); comps = 0
    for r, c, v in movable:
        if (r, c) in seen:
            continue
        comps += 1; stack = [(r, c)]; seen.add((r, c))
        while stack:
            rr, cc = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == v and (nr, nc) not in seen:
                    seen.add((nr, nc)); stack.append((nr, nc))
    if not (lo <= comps <= hi):
        errs.append(f"expected {lo}..{hi} movable color-components, got {comps}")
    if any(c >= w - 1 for _, c, _ in movable):
        errs.append("movable objects must stay strictly left of the wall")
    if movable and max(c for _, c, _ in movable) >= w - 2:
        errs.append("movable objects should have at least one blank column before the wall")
    return errs
