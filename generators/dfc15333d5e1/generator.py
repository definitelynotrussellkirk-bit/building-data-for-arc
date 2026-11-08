"""Generator for arc_puzzle_bank_sixteenth_21_bundle:easy_110_keep_centers_of_three_cell_lines.

Rule: each separated 3-cell horizontal/vertical line collapses to its
center cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, lines, texture.
Degenerates: no_lines, single_cells, four_plus_cell_line.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dfc15333d5e1"
VERSION = "2.1.0"  # enforce distinct line colors; add self_check
TASK_ID = "dfc15333d5e1"

SUMMARY = (
    "0-bg grid (h~8-11, w~9-13) with 3-5 "
    "SEPARATED 3-CELL STRAIGHT LINES, each "
    "either HORIZONTAL (cells at (r, c..c+2)) "
    "or VERTICAL (cells at (r..r+2, c)), each "
    "in a DISTINCT non-zero color (random "
    "from 1..9). Lines are 4-conn isolated "
    "with ≥1-cell gap between them (guard "
    "neighborhood enforced during placement). "
    "Rule: identify EACH 3-CELL STRAIGHT LINE "
    "(connected component that is exactly 3 "
    "cells in a row or column). COLLAPSE each "
    "line to its CENTER CELL ONLY — keep the "
    "middle cell of the 3, ERASE the two "
    "endpoint cells to BG (0). Endpoint "
    "cells: for a horizontal line at "
    "(r, c..c+2), erase (r, c) and (r, c+2); "
    "for vertical, erase (r, c) and (r+2, c). "
    "Net: each 3-line shrinks to its single "
    "center-cell dot in the same color."
)

INVARIANTS = [
    "background is 0",
    "each component is a straight line of exactly three cells",
    "lines may be horizontal or vertical",
    "components are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_lines", "single_cells", "four_plus_cell_line")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "lines":          {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "= lines", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_3_cell_lines",
                       "valid": "scattered_3_cell_lines"},
    "n_distinct_colors": {"type": "int", "default": "= lines", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_lines|single_cells|four_plus_cell_line'},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("lines", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        target = ctx.draw_int("lines", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        target = ctx.draw_int("lines", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    for _ in range(500):
        if placed >= target:
            break
        vertical = rng.randrange(2) == 0
        if vertical:
            r0 = rng.randint(0, h - 3)
            c0 = rng.randrange(w)
            cells = [(r0 + i, c0) for i in range(3)]
        else:
            r0 = rng.randrange(h)
            c0 = rng.randint(0, w - 3)
            cells = [(r0, c0 + i) for i in range(3)]
        guard = {
            (rr, cc)
            for r, c in cells
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
        }
        if guard & reserved:
            continue
        if placed >= len(colors):
            break
        color = colors[placed]
        for r, c in cells:
            g[r][c] = color
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_lines":
        # Empty grid — rule has no 3-cell lines to collapse.
        return g
    if name == "single_cells":
        # Components of size 1, not 3-cell lines — rule's
        # "exactly three cells" filter excludes them.
        g[2][2] = 4; g[5][7] = 6; g[7][3] = 7
        return g
    if name == "four_plus_cell_line":
        # 4-cell straight lines instead of 3-cell — rule's
        # length-3 filter excludes them; nothing collapses.
        for c in range(2, 6): g[3][c] = 4
        for r in range(5, 9): g[r][8] = 6
        return g
    return g



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _is_three_line(cells):
    if len(cells) != 3:
        return False
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if len(rows) == 1 and len(cols) == 3:
        return cols[-1] - cols[0] == 2
    if len(cols) == 1 and len(rows) == 3:
        return rows[-1] - rows[0] == 2
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for separated 3-cell line inputs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    problems = []
    comps = _components(grid)
    if difficulty == "easy":
        lo, hi = 2, 3
    elif difficulty == "hard":
        lo, hi = 5, 8
    else:
        lo, hi = 3, 5
    if not (lo <= len(comps) <= hi):
        problems.append(f"expected {lo}..{hi} line components, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        problems.append("3-cell line colors are not distinct")
    for color, cells in comps:
        if color == 0:
            problems.append("zero-colored component found")
        if not _is_three_line(cells):
            problems.append("component is not a straight 3-cell line")
    occupied = {cell for _, cells in comps for cell in cells}
    for r, c in occupied:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nb = (r + dr, c + dc)
            if nb in occupied and grid[nb[0]][nb[1]] != grid[r][c]:
                problems.append("line components touch each other")
    return sorted(set(problems))
