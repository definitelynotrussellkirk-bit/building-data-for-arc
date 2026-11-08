"""Generator for arc_additional_puzzle_bank_volume19:E130.

Red L-triominoes receive a green missing fourth corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_l_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l, full_squares, length_4_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8e034e635c60"
VERSION = "2.0.1"
TASK_ID = "8e034e635c60"
SUMMARY = (
    "0-bg grid (h, w~7-12) with 2-5 SEPARATED "
    "COLOR-2 (red) L-TRIOMINOES, each fitting in "
    "a 2x2 box with EXACTLY ONE CORNER MISSING "
    "(3 cells of color 2 painted in 3 of the 4 "
    "corners of a 2x2 window, the 4th corner is "
    "0). The missing corner varies per L "
    "(top-left, top-right, bottom-left, "
    "bottom-right). L-triominoes are spaced "
    "with ≥3-cell padding so they remain "
    "isolated. Rule: for every 3-cell L-triomino "
    "of color 2, IDENTIFY the single MISSING "
    "CORNER (the 4th cell of its 2x2 bbox that "
    "is 0). FILL that missing corner with "
    "COLOR 3 (green). The original 3 red cells "
    "STAY red. Net: each red L gains a green "
    "completion-corner, forming a 2-color 2x2 "
    "square."
)

INVARIANTS = [
    "background is 0",
    "target red components are exact 3-cell Ls in a 2x2 box",
    "the missing fourth corner starts empty",
    "L components are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l", "full_squares", "length_4_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_l_shapes":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_l_triominoes",
                       "valid": "separated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 red (color-2) cell present for L-triomino detection."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_l", "full_squares", "length_4_l"):
        return errs
    if not any(grid[r][c] == 2 for r in range(h) for c in range(w)):
        errs.append("no red (color-2) L-triomino cells found")
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
        n_l_shapes = ctx.draw_int("n_l_shapes", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_l_shapes = ctx.draw_int("n_l_shapes", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_l_shapes = ctx.draw_int("n_l_shapes", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_l_shapes:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 2
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 2
        g[1][2] = 2
        g[2][1] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_l":
        # blank → no L-triominoes to complete
        return g
    if name == "full_squares":
        # 2x2 already full → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 2
        return g
    if name == "length_4_l":
        # 4-cell shape → not a 3-cell L-triomino, rule won't fire
        for r, c in [(1, 1), (1, 2), (2, 1), (3, 1)]:
            g[r][c] = 2
        return g
    return g
