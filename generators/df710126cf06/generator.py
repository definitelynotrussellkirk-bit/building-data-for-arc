"""Generator for arc_additional_puzzle_bank_volume6:E39.

Bend cells of green L-triominoes are recolored red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_l_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l, straight_lines, length_4_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df710126cf06"
VERSION = "2.1.0"  # add executable L-triomino invariants
TASK_ID = "df710126cf06"
SUMMARY = (
    "0-bg grid (h, w~7-12) "
    "with 2-5 GREEN "
    "(COLOR-3) L-TRIOMINOES "
    "— each a 3-cell L-"
    "shape in one of 4 "
    "ORIENTATIONS (NE/NW/"
    "SE/SW), placed at "
    "non-touching positions "
    "(≥3-cell separation). "
    "L-triominoes have a "
    "clear BEND CELL — the "
    "corner cell where two "
    "arms meet (4-conn "
    "degree 2 in the "
    "tromino). Rule "
    "(RECOLOR L-TRIOMINO "
    "BEND CELLS TO RED): "
    "For EACH GREEN L-"
    "TROMINO of 3 cells: "
    "identify the BEND "
    "CELL (corner of the L "
    "— the cell where both "
    "arms meet, with 2 "
    "non-zero neighbors in "
    "the tromino). "
    "RECOLOR that cell to "
    "COLOR-2 (red). The "
    "two arm cells stay "
    "green. Net: each L-"
    "tromino's corner pixel "
    "turns red; arms "
    "stay green."
)

INVARIANTS = [
    "background is 0",
    "target green components are size-3 L-triominoes",
    "components are separated by background",
    "all four L orientations can appear",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l", "straight_lines", "length_4_l")
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
    shapes = [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 1), (1, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
    ]
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_l_shapes:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        for dr, dc in rng.choice(shapes):
            g[r + dr][c + dc] = 3
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 3
        g[2][1] = 3
        g[2][2] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_l":
        # blank → no L-triominoes, no bend cells to recolor
        return g
    if name == "straight_lines":
        # 3-cell straight lines (no bend) → "L-triomino" precondition fails
        for c in [1, 2, 3]: g[2][c] = 3
        for r in [4, 5, 6]: g[r][6] = 3
        return g
    if name == "length_4_l":
        # 4-cell L → not 3-cell L, rule won't identify a single bend
        for r, c in [(1, 1), (1, 2), (2, 1), (3, 1)]: g[r][c] = 3
        return g
    return g

def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bend_count(cells):
    s = set(cells)
    bends = 0
    for r, c in cells:
        deg = sum((r + dr, c + dc) in s
                  for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        if deg == 2:
            bends += 1
    return bends


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    colors = {v for row in grid for v in row}
    if not colors <= {0, 3}:
        errors.append("normal sample may contain only background 0 and green 3")
    comps = _color_components(grid, 3)
    min_expected = 4 if difficulty == "hard" else 2
    if len(comps) < min_expected:
        errors.append(f"normal sample must contain at least {min_expected} green L-triominoes")
    for cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        if len(cells) != 3 or max(rs) - min(rs) + 1 != 2 or max(cs) - min(cs) + 1 != 2:
            errors.append("each green component must be a size-3 2x2 L-triomino")
            break
        if _bend_count(cells) != 1:
            errors.append("each L-triomino must have exactly one bend cell")
            break
    return errors
