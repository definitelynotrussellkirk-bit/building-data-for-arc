"""Generator for arc_puzzle_bank_fifteenth_21_bundle:easy_99_fill_main_diagonal_spans.

Place same-color pairs on slope +1 diagonals, leaving the span empty.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, length_1_pair, anti_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4f77a83eb83"
VERSION = "2.1.0"  # clean but under-diversified: 2-4 pairs, small grids, length<=5. Widen pair count (up to 8), grids, and span length for more positions/sizes (rule fills any number of same-color main-diagonal pairs).
TASK_ID = "e4f77a83eb83"

SUMMARY = (
    "0-bg grid (h~8-10, w~9-12) with 2-4 "
    "DIAGONAL PAIRS — each pair is two "
    "SAME-COLOR cells along the MAIN "
    "DIAGONAL (slope +1): pick "
    "length L ∈ {2..5}; pick start "
    "(r0, c0); endpoint at (r0+L, "
    "c0+L). PAINT only the two endpoints "
    "in the pair's color; cells (r0+k, "
    "c0+k) for k ∈ [1..L-1] are bg-0 "
    "(the diagonal span). Each pair "
    "uses a DISTINCT non-0 color drawn "
    "from {1..9}. Diagonal spans don't "
    "overlap (placement tracked in "
    "reserved set). Rule (FILL EACH "
    "MAIN-DIAGONAL SPAN BETWEEN SAME-"
    "COLOR ENDPOINTS WITH THAT COLOR): "
    "for EACH color C that appears at "
    "exactly TWO cells (r0, c0) and "
    "(r0+L, c0+L) on the SAME MAIN-"
    "DIAGONAL LINE (slope +1, equal "
    "row-step and col-step): PAINT "
    "every cell (r0+k, c0+k) for k in "
    "[1..L-1] with COLOR C. Endpoints "
    "stay. Anti-diagonal pairs and "
    "non-pair cells are unchanged. "
    "Net: each diagonal pair becomes a "
    "solid diagonal colored line."
)

INVARIANTS = [
    "background is 0",
    "same-color cells share a main-diagonal line",
    "the diagonal span between them is initially empty",
    "diagonal spans do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "length_1_pair", "anti_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|rainbow"},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "main_diagonal_pairs",
                       "valid": "main_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|rainbow|no_pairs|length_1_pair|anti_diagonal"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        target = ctx.draw_int("pairs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        target = ctx.draw_int("pairs", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        target = ctx.draw_int("pairs", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    target = min(target, 9)                      # at most 9 distinct colors
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(800):
        if placed >= target:
            break
        length = rng.randint(2, min(7, h - 1, w - 1))
        r0 = rng.randint(0, h - length - 1)
        c0 = rng.randint(0, w - length - 1)
        cells = [(r0 + k, c0 + k) for k in range(length + 1)]
        if any(p in reserved for p in cells):
            continue
        color = colors[placed]
        g[r0][c0] = color
        g[r0 + length][c0 + length] = color
        reserved.update(cells)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify non-degenerate main-diagonal endpoint-span instances."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    cells_by_color: dict[int, list[tuple[int, int]]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                cells_by_color.setdefault(v, []).append((r, c))
    if not cells_by_color:
        errs.append("no non-zero diagonal endpoint pairs")
    claimed_spans: set[tuple[int, int]] = set()
    for color, cells in sorted(cells_by_color.items()):
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times, expected exactly 2 endpoints")
            continue
        (r0, c0), (r1, c1) = sorted(cells)
        dr, dc = r1 - r0, c1 - c0
        if dr != dc or dr < 2:
            errs.append(f"color {color} endpoints are not a length>=2 main-diagonal span: {cells}")
            continue
        for k in range(1, dr):
            p = (r0 + k, c0 + k)
            if grid[p[0]][p[1]] != 0:
                errs.append(f"color {color} span interior is not empty at {p}")
            if p in claimed_spans:
                errs.append(f"diagonal spans overlap at {p}")
            claimed_spans.add(p)
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal pairs to span-fill
        return g
    if name == "length_1_pair":
        # adjacent diagonal cells → no empty span between them
        g[2][2] = 4; g[3][3] = 4
        return g
    if name == "anti_diagonal":
        # anti-diagonal pair → not slope +1, rule won't fire
        g[2][6] = 4; g[5][3] = 4
        return g
    return g
