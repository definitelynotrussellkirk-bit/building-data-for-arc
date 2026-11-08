"""Generator for next_b:hard_10 — palette recolor components left-to-right.

Rule: row 0 holds a palette of non-{0, 2} colors. Color-2 components
sorted by (col, row) ascending get recolored to the palette colors
in order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_palette, no_components, equal_leftmosts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "258e1a721c75"
VERSION = "2.0.1"
TASK_ID = "258e1a721c75"

SUMMARY = (
    "0-bg grid (h~9-11, w~12-14) with: (a) ROW 0 = PALETTE — "
    "3 distinct non-{0, 2} cells scattered at distinct columns "
    "of row 0, in their natural left-to-right order; (b) "
    "BELOW row 0: exactly 3 isolated 4-connected COMPONENTS "
    "all in color 2 (red), each a 3-4 cell motif with "
    "distinct leftmost columns. Rule: extract palette = row 0 "
    "non-{0,2} values in scan order (left to right). Extract "
    "color-2 components, sort by (leftmost_col asc, then top "
    "row asc). For each component in sorted order, recolor "
    "its cells to the corresponding palette color (1st "
    "component → 1st palette color, etc.). Row 0 cells "
    "preserved."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "row 0 holds a palette of 3 distinct non-{0,2} colors at distinct columns",
    "exactly 3 color-2 components below row 0, at strictly distinct leftmost columns",
    "components are 4-connected and isolated by ≥1 bg cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_palette", "no_components", "equal_leftmosts")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "row0_palette_components_below",
                       "valid": "row0_palette_components_below"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has ≥1 non-{0,2} palette cell; ≥1 color-2 component cell below."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    palette = [grid[0][c] for c in range(w) if grid[0][c] not in (0, 2)]
    if not palette:
        return errors  # degenerate no_palette — allowed
    comps = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 2]
    if not comps:
        errors.append("row 0 has palette but no color-2 cells in body (rows 1+)")
    return errors


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


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
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 17)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], 3)
    for outer in range(40):
        g = full_grid(h, w, 0)
        cols = rng.sample(range(0, w), 3)
        for c, color in zip(cols, palette):
            g[0][c] = color
        leftmosts = []
        ok = True
        for _ in range(3):
            placed = False
            for _ in range(60):
                shape = rng.choice(_SHAPES)
                sh = max(r for r, _ in shape) + 1
                sw = max(c for _, c in shape) + 1
                r0 = rng.randint(2, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                shape_left = min(c for _, c in shape)
                lc = c0 + shape_left
                if lc in leftmosts: continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = 2
                leftmosts.append(lc); placed = True; break
            if not placed:
                ok = False; break
        if ok and len(set(leftmosts)) == 3:
            return g
    raise ValueError("could not place 3 color-2 components at distinct cols")


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_palette":
        # Row 0 empty — rule has no recolor target colors.
        for dr, dc in _SHAPES[0]: g[3 + dr][2 + dc] = 2
        for dr, dc in _SHAPES[0]: g[3 + dr][6 + dc] = 2
        return g
    if name == "no_components":
        # Palette but no color-2 components — rule has nothing to recolor.
        g[0][2] = 4; g[0][6] = 5; g[0][10] = 6
        return g
    if name == "equal_leftmosts":
        # All color-2 components share leftmost column — sort order ambiguous.
        g[0][2] = 4; g[0][6] = 5; g[0][10] = 6
        for dr, dc in _SHAPES[0]: g[3 + dr][3 + dc] = 2
        for dr, dc in _SHAPES[0]: g[6 + dr][3 + dc] = 2
        return g
    return g
