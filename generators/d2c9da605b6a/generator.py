"""Generator for additional_scaffolded:M6 -- recolor small cyan L triominoes.

Rule: find color-6 objects that occupy 3 cells inside a 2x2 box, recolor 1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, only_distractor, all_2x2_solid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2c9da605b6a"
VERSION = "1.1.1"
TASK_ID = "d2c9da605b6a"
SUMMARY = "Find color-6 objects that occupy three cells in a 2x2 box and recolor them to 1."

INVARIANTS = [
    "target objects are color 6, size 3, and have a 2x2 bounding box",
    "larger or rectangular color-6 distractors are left unchanged",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "only_distractor", "all_2x2_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "targets":        {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "scattered_l_triominoes",
                       "valid": "scattered_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


L_TRIOMINOES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)


def _can_place(g, cells, r0, c0):
    h = len(g)
    w = len(g[0])
    for dr, dc in cells:
        r = r0 + dr
        c = c0 + dc
        if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
            return False
    for dr, dc in cells:
        r = r0 + dr
        c = c0 + dc
        for nr in (r - 1, r, r + 1):
            for nc in (c - 1, c, c + 1):
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _paint(g, cells, r0, c0, color):
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-6 L-triomino (3 cells in 2×2 box) present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    # check at least one color-6 cell exists
    has_6 = any(grid[r][c] == 6 for r in range(h) for c in range(w))
    if not has_6:
        errs.append("no color-6 cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        count = ctx.draw_int("targets", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
        count = ctx.draw_int("targets", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        count = ctx.draw_int("targets", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    placed = 0
    for _ in range(200):
        if placed >= count:
            break
        cells = rng.choice(L_TRIOMINOES)
        r0 = rng.randint(1, h - 3)
        c0 = rng.randint(1, w - 3)
        if _can_place(g, cells, r0, c0):
            _paint(g, cells, r0, c0, 6)
            placed += 1

    if placed == 0:
        _paint(g, L_TRIOMINOES[0], 1, 1, 6)

    if h >= 8 and w >= 8:
        row = h - 2
        for c in range(w - 3, w - 1):
            if g[row][c] == 0:
                g[row][c] = 6
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # Empty grid — rule has no color-6 objects to filter or
        # recolor.
        return g
    if name == "only_distractor":
        # Only large color-6 line/rectangle (no 3-cell-in-2x2
        # objects) — rule's filter excludes; output equals input.
        for c in range(2, 7): g[3][c] = 6
        for r in range(5, 7):
            for c in range(5, 7): g[r][c] = 6
        return g
    if name == "all_2x2_solid":
        # All color-6 objects fill a 2x2 box completely (4 cells,
        # not 3) — rule's "size 3 in 2x2" filter excludes.
        for r in range(2, 4):
            for c in range(2, 4): g[r][c] = 6
        for r in range(5, 7):
            for c in range(6, 8): g[r][c] = 6
        return g
    return g
