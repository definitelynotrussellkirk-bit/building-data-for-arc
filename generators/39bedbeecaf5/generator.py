"""Generator for ARC task 9dfd6313.

Rule: output is n × n. For r==c → 5. For r<c (upper triangle): take
input[c][r] (transpose); if non-zero and not 5 → keep, else 0.
For r>c (lower triangle) → 0.

Combinatorial axes: side, palette_size, lower_triangle_density,
lower_triangle_pattern (random/diagonal_only/clustered/border-only).
Degenerates: all_zero_lower (output is just diag), all_fg_lower
(output is full upper-triangle), single_cell_lower.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39bedbeecaf5"
VERSION = "1.2.1"
TASK_ID = "39bedbeecaf5"
SUMMARY = "Square n×n grid with cells in the lower triangle; rule outputs n×n with diagonal=5, lower triangle=0, upper triangle = transpose(lower) (cell (r,c) ← input[c][r] for r<c)."

# Rivals: 'output = input (identity)' refuted by any demo (output is
# upper-triangle reflection, not lower). 'fill diagonal with bg'
# refuted by any demo (diag is always 5). 'transpose entire grid'
# refuted by ≥1 demo where output's lower triangle is 0, not the
# upper input. 'use color 5 for everything' refuted by any demo with
# multiple colors visible in upper triangle.
# 4 demos with varied side + patterns cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "input is square (n × n) with n in 3..10",
    "≥1 lower-triangle cell is non-zero, non-5 so output is non-trivial",
    "diagonal output is forced to 5",
]

LOWER_PATTERNS = ("random", "diagonal_only", "clustered", "border_only", "blob")
DEGENERATE_TEXTURES = ("all_zero_lower", "all_fg_lower", "single_cell_lower")
HELPFUL_TEXTURES = LOWER_PATTERNS

AXES = {
    "side":            {"type": "int", "default": "rng 3..10", "valid": "3..14"},
    "palette_size":    {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "lower_density":   {"type": "float", "default": "rng 0.4..0.8", "valid": "0..1"},
    "lower_pattern":   {"type": "str", "default": "rng helpful",
                        "valid": "random|diagonal_only|clustered|border_only|blob"},
    "texture":         {"type": "str", "default": "alias for lower_pattern",
                        "valid": "random|diagonal_only|clustered|border_only|blob|all_zero_lower|all_fg_lower|single_cell_lower"},
}


def _cell_color(palette, r, c):
    # Alternate colors by coordinate so adjacent lower-triangle cells do not all
    # collapse into one same-color component.  This keeps object-count metrics in
    # the canonical range while preserving the triangle rule exactly.
    return palette[(r + 2 * c) % len(palette)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        s_lo, s_hi = 3, 6
    elif difficulty == "hard":
        s_lo, s_hi = 11, 14
    else:
        s_lo, s_hi = 5, 11
    n = ctx.draw_int("side", s_lo, s_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, rng)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 4)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(1, n_palette), exclude={0, 5}))
    density = float(overrides.get("lower_density",
                                  ctx.draw_rng("lower_density").uniform(0.4, 0.8)))
    pattern = (overrides.get("texture") or overrides.get("lower_pattern")
               or ctx.draw_choice("lower_pattern", list(LOWER_PATTERNS)))
    g = full_grid(n, n, 0)
    if pattern == "random":
        for r in range(1, n):
            for c in range(r):
                if rng.random() < density:
                    g[r][c] = _cell_color(palette, r, c)
    elif pattern == "diagonal_only":
        for k in range(1, n):
            g[k][k - 1] = _cell_color(palette, k, k - 1)
    elif pattern == "clustered":
        cr = rng.randint(1, n - 1); cc = rng.randint(0, n - 2)
        for r in range(1, n):
            for c in range(r):
                if abs(r - cr) + abs(c - cc) <= 2 and rng.random() < density:
                    g[r][c] = _cell_color(palette, r, c)
    elif pattern == "border_only":
        c0 = palette[0]
        for r in range(1, n):
            g[r][0] = c0
            if r > 0:
                g[n - 1][r - 1] = c0
    elif pattern == "blob":
        rr = rng.randint(1, n - 1); cc = 0
        bh = min(rr, n // 2); bw = min(rr, n // 2)
        for r in range(rr - bh + 1, rr + 1):
            for c in range(cc, cc + bw):
                if c < r:
                    g[r][c] = _cell_color(palette, r, c)
    # Force at least one non-zero lower-triangle cell.
    if not any(g[r][c] != 0 for r in range(1, n) for c in range(r)):
        g[1][0] = _cell_color(palette, 1, 0)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify normal inputs are square, lower-triangle-only, and non-trivial."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h = len(grid)
    w = len(grid[0])
    if h != w:
        errors.append(f"grid is {h}x{w} — must be square for triangle rule")
        return errors
    if h > 14 or w > 14:
        errors.append(f"grid too large: {h}x{w} > 14x14")
    if any(grid[r][c] == 5 for r in range(h) for c in range(w)):
        errors.append("input contains color 5; diagonal 5 belongs to the output only")
    upper_nonzero = [(r, c) for r in range(h) for c in range(r + 1, w) if grid[r][c] != 0]
    if upper_nonzero:
        errors.append(f"found {len(upper_nonzero)} nonzero cells above diagonal in input")
    lower_nonzero = [(r, c) for r in range(1, h) for c in range(r) if grid[r][c] != 0]
    if not lower_nonzero:
        errors.append("no nonzero lower-triangle cell; output would be diagonal-only")
    return errors

def _draw_from_degenerate(name, n, rng):
    palette = [c for c in range(1, 10) if c != 5]
    rng.shuffle(palette)
    g = full_grid(n, n, 0)
    if name == "all_zero_lower":
        return g
    if name == "all_fg_lower":
        for r in range(1, n):
            for c in range(r):
                g[r][c] = _cell_color(palette, r, c)
        return g
    if name == "single_cell_lower":
        r = rng.randint(1, n - 1)
        c = rng.randint(0, r - 1)
        g[r][c] = _cell_color(palette, r, c)
        return g
    return g
