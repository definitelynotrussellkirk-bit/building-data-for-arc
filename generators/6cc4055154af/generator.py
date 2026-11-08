"""Generator for arc_puzzle_bank_fifteenth21:E105.

Rule: keep only interior components, drop border-touching ones.

Combinatorial axes (8): grid_h, grid_w, palette_kind, interior_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_border, all_interior, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6cc4055154af"
VERSION = "2.0.2"  # lintable AXES + self_check verifies border/interior branch coverage
TASK_ID = "6cc4055154af"
SUMMARY = (
    "0-bg grid (h~8-10, w~8-11) with: (a) ONE "
    "BORDER-TOUCHING COMPONENT placed flush "
    "against one of the 4 grid edges in some "
    "random non-zero color; (b) 2-3 INTERIOR "
    "COMPONENTS placed strictly inside (rows "
    "1..h-2, cols 1..w-2, with 1-cell padding "
    "from each other) in distinct non-zero "
    "colors. All components are small "
    "polyominoes (2-3 cells from a shape bank: "
    "L-tromino, S-tromino, line, domino). Rule: "
    "identify each CONNECTED COMPONENT. For "
    "EACH component, check if it has ANY cell "
    "ON the GRID BORDER. DROP (clear to 0) "
    "every border-touching component. KEEP "
    "(preserve) every strictly-interior "
    "component at its original color. Net: "
    "border-touching blobs erased; interior "
    "blobs survive."
)

INVARIANTS = [
    "background is 0",
    "components are separated",
    "at least one component touches the border",
    "at least one component is strictly interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "interior_objects": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "border_plus_interior",
                       "valid": "border_plus_interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_border|all_interior|no_objects"},
}


def _components_nonzero(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify both drop and keep branches: border-touching and interior components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    comps = _components_nonzero(grid)
    border = [comp for comp in comps if any(r in (0, h - 1) or c in (0, w - 1) for r, c in comp)]
    interior = [comp for comp in comps if all(0 < r < h - 1 and 0 < c < w - 1 for r, c in comp)]
    errs = []
    if not border:
        errs.append("no border-touching component to drop")
    if not interior:
        errs.append("no strictly interior component to keep")
    return errs


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0)],
]


def _free(g, cells, top, left):
    h, w = len(g), len(g[0])
    coords = [(top + r, left + c) for r, c in cells]
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in coords):
        return False
    for r, c in coords:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def _paint(g, cells, top, left, color):
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        interior = ctx.draw_int("interior_objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        interior = ctx.draw_int("interior_objects", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        interior = ctx.draw_int("interior_objects", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    border_shape = rng.choice(_SHAPES)
    side = rng.randrange(4)
    max_r = max(r for r, _ in border_shape)
    max_c = max(c for _, c in border_shape)
    if side == 0:
        top, left = 0, rng.randint(0, w - max_c - 1)
    elif side == 1:
        top, left = h - max_r - 1, rng.randint(0, w - max_c - 1)
    elif side == 2:
        top, left = rng.randint(0, h - max_r - 1), 0
    else:
        top, left = rng.randint(0, h - max_r - 1), w - max_c - 1
    _paint(g, border_shape, top, left, rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]))
    placed = 0
    for _ in range(400):
        if placed >= interior:
            break
        shape = rng.choice(_SHAPES)
        max_r = max(r for r, _ in shape)
        max_c = max(c for _, c in shape)
        top = rng.randint(1, h - max_r - 2)
        left = rng.randint(1, w - max_c - 2)
        if _free(g, shape, top, left):
            _paint(g, shape, top, left, rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]))
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "all_border":
        # all components touch the border → rule erases everything, output is empty
        _paint(g, [(0, 0), (0, 1), (1, 0)], 0, 1, 4)
        _paint(g, [(0, 0), (1, 0)], h - 2, w - 2, 6)
        _paint(g, [(0, 0), (0, 1)], 3, 0, 3)
        return g
    if name == "all_interior":
        # all components interior → rule keeps everything, no contrast
        _paint(g, [(0, 0), (0, 1), (1, 0)], 2, 2, 4)
        _paint(g, [(0, 0), (1, 0)], 5, 5, 6)
        _paint(g, [(0, 0), (0, 1)], 6, 7, 3)
        return g
    if name == "no_objects":
        # blank grid → rule has nothing to keep or drop
        return g
    return g
