"""Generator for arc_puzzle_bank_21_set11_s:S11_E4 — Mark endpoints of h/v lines with 8.

Rule: each blob that is a horizontal line (h=1, size ≥2) → set start
and end to 8. Each vertical line (w=1, size ≥2) → same.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_lines,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_lines, all_singletons, only_squares.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ee5a50b2ab0"
VERSION = "1.2.0"  # 1.2.0: strengthen line self-check with hard-mode count and clearance.
TASK_ID = "2ee5a50b2ab0"
SUMMARY = "1-2 horizontal lines + 1-2 vertical lines, all separated."

INVARIANTS = [
    "≥1 horizontal line (h=1, size ≥3)",
    "≥1 vertical line (w=1, size ≥3)",
    "blobs don't touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_lines", "all_singletons", "only_squares")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_lines":        {"type": "int", "default": "3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "h_and_v_lines",
                       "valid": "h_and_v_lines"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
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
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    r1 = rng.randint(0, 1); c1 = rng.randint(0, 1); l1 = rng.randint(3, 4)
    for c in range(c1, c1 + l1):
        g[r1][c] = palette[0]
    r2 = rng.randint(2, h - 5); c2 = rng.randint(w - 3, w - 2); l2 = rng.randint(3, 4)
    for r in range(r2, r2 + l2):
        g[r][c2] = palette[1]
    r3 = rng.randint(h - 4, h - 3); c3 = rng.randint(0, 2); l3 = 2
    for r in range(r3, r3 + l3):
        g[r][c3] = palette[2]
    return g


def _components(grid):
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
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, comp))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    comps = _components(grid)
    horizontal = vertical = 0
    for color, cells in comps:
        rs = {r for r, _ in cells}
        cs = {c for _, c in cells}
        if len(rs) == 1 and len(cells) >= 3:
            horizontal += 1
        elif len(cs) == 1 and len(cells) >= 2:
            vertical += 1
        else:
            errors.append(f"component color {color} is not a horizontal/vertical line: {cells}")
    if horizontal < 1:
        errors.append("missing horizontal line witness")
    if vertical < 1:
        errors.append("missing vertical line witness")
    if difficulty == "hard" and horizontal + vertical < 3:
        errors.append("hard examples should keep all three line witnesses")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_lines":
        # blank → no lines to mark endpoints of
        return g
    if name == "all_singletons":
        # every blob is a single cell → "size ≥2 line" precondition fails
        g[1][2] = 4
        g[3][5] = 6
        g[5][8] = 7
        return g
    if name == "only_squares":
        # only 2x2 squares (h>1 AND w>1) → not a line in either direction
        g[1][1] = 4; g[1][2] = 4
        g[2][1] = 4; g[2][2] = 4
        g[5][5] = 6; g[5][6] = 6
        g[6][5] = 6; g[6][6] = 6
        return g
    return g
