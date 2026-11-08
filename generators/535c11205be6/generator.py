"""Generator for arc_puzzle_bank_twentieth21:H139 — recolor body shapes by size rank.

Rule: row 0 holds a PALETTE (its non-zero cells, left-to-right). The BODY (rows
1..h-1) holds connected shapes; sort them by size DESCENDING and recolor the
i-th largest with palette[i]. Output = the body recolored (dims (h-1) x w).

The old docstring called this a "multi-motif gallery pack" and the generator
just scattered motifs across the whole grid with NO row-0 palette and NO
distinct-size body shapes — so the rule's palette was whatever random cells
landed in row 0 (fragile / wrong distribution). Now: a deliberate row-0 palette
of K distinct colors + K body shapes of DISTINCT sizes in rows 1..h-1.

Combinatorial axes: palette size/colors/order, body shape sizes (-> rank), the
shapes themselves, grid size, positions.
Degenerates: no_palette, single_shape, equal_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "535c11205be6"
VERSION = "3.1.0"  # WRONG-TASK: rule reads row 0 as a PALETTE and recolors the body shapes by size rank. Old gen scattered motifs with no palette row / no distinct sizes. Now deliberate row-0 palette (K distinct colours) + K body shapes of DISTINCT sizes.
TASK_ID = "535c11205be6"
SUMMARY = (
    "0-bg grid (size varies). ROW 0 holds a PALETTE: K distinct non-0 colors at "
    "K columns (left-to-right palette order). The BODY (rows 1..h-1) holds K "
    "connected shapes of DISTINCT sizes (random polyominoes), separated, in "
    "distinct colors. Rule: sort the body shapes by size descending and recolor "
    "the i-th largest with palette[i]; output the recolored body (dims "
    "(h-1) x w). The palette, the body shape sizes and the shapes all vary."
)

INVARIANTS = [
    "row 0 holds K distinct palette colors (one per body shape)",
    "the body (rows 1..h-1) holds K connected shapes of distinct sizes",
    "body shapes are separated (distinct components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_palette", "single_shape", "equal_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "n":              {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "palette_row_plus_body",
                       "valid": "palette_row_plus_body"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, n):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (1 <= rr < h and 0 <= cc < w):      # body stays in rows >= 1
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 12); k = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 14, 18); k = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 12, 15); k = ctx.draw_int("n", 3, 4)

    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k)
    body_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k)
    sizes = sorted(rng.sample(range(1, 9), k), reverse=True)  # place big shapes first
    pcols = sorted(rng.sample(range(w), k))
    for _layout_attempt in range(40):
        g = full_grid(h, w, 0)
        # row-0 palette (left-to-right order)
        for col, color in zip(pcols, palette):
            g[0][col] = color
        placed = 0
        for sz, col in zip(sizes, body_colors):
            cells = _poly(rng, sz)
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            ok = False
            for _ in range(200):
                top = rng.randint(1, h - sh)
                left = rng.randint(0, w - sw)
                if _free(g, top, left, cells):
                    for dr, dc in cells:
                        g[top + dr][left + dc] = col
                    placed += 1
                    ok = True
                    break
            if not ok:
                break
        if placed == k:
            return g
    return _fallback_layout(h, w, pcols, palette, sizes, body_colors)


def _fallback_layout(h, w, pcols, palette, sizes, body_colors):
    """Guaranteed K body components if random polyomino packing exhausts retries."""
    g = full_grid(h, w, 0)
    for col, color in zip(pcols, palette):
        g[0][col] = color
    for i, (sz, color) in enumerate(zip(sizes, body_colors)):
        row = min(1 + 2 * i, h - 1)
        left = 1 if sz + 1 < w else 0
        for c in range(left, min(w, left + sz)):
            g[row][c] = color
    return g


def _body_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 1 <= ny < h and 0 <= nx < w and (ny, nx) not in seen and grid[ny][nx] == color:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    palette_cells = [(c, v) for c, v in enumerate(grid[0]) if v != 0]
    k = len(palette_cells)
    if k < 2:
        errors.append("row 0 must contain at least two palette colors")
    if len({v for _, v in palette_cells}) != k:
        errors.append("row 0 palette colors must be distinct")
    comps = _body_components(grid)
    sizes = [len(comp) for comp in comps]
    if len(comps) != k:
        errors.append(f"body component count {len(comps)} must match palette count {k}")
    if len(sizes) != len(set(sizes)):
        errors.append(f"body component sizes must be distinct, found {sizes}")
    # Components should be separated by at least one background cell, including diagonals.
    occupied = {cell for comp in comps for cell in comp}
    for r, c in occupied:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nb = (r + dr, c + dc)
                if nb in occupied and grid[nb[0]][nb[1]] != grid[r][c]:
                    errors.append("body components touch or diagonally kiss")
                    return errors
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 11, 0)
    if name == "no_palette":
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 4
        return g
    if name == "single_shape":
        g[0][2] = 6
        for r, c in [(3, 3), (3, 4)]:
            g[r][c] = 5
        return g
    if name == "equal_sizes":
        g[0][1] = 2; g[0][5] = 3
        for r, c in [(3, 1), (3, 2)]:
            g[r][c] = 5
        for r, c in [(6, 6), (6, 7)]:
            g[r][c] = 5
        return g
    return g
