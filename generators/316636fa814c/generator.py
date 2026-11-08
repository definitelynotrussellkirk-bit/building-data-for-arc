"""Generator for 4093f84a.

Rule: full gray row or column expands outward by counting colored
dots on each side.

Combinatorial axes (8): grid_h/w, orientation, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_dots.
Degenerates: no_bar, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "316636fa814c"
VERSION = "1.2.1"
TASK_ID = "316636fa814c"
SUMMARY = "Full gray(5) row or column bar; per row/col, extend gray by side dot count; output is binary 0/5 (dot colors discarded)."

# Rivals: 'preserve dot colors' refuted by any demo (output uses only
# 0 and 5). 'extend by fixed count' refuted by ≥2 demos with different
# per-row counts. 'extend only on one side' refuted by ≥1 demo with
# dots on both sides extending both directions. 'extend by row index'
# refuted by ≥2 demos where same row index has different counts.
# 4 demos with varied dot distributions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "color 5 forms one full-width row or full-height column bar",
    "all nonzero non-gray side cells are counted by row or column",
    "the bar splits the grid into two sides each holding dot markers",
    "non-bar cells use colors other than 0 or 5",
]

ORIENTATIONS = ("vertical", "horizontal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_bar", "no_dots", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..14"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_dots":         {"type": "int", "default": "rng 4..8", "valid": "1..16"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    palette_kind = overrides.get("palette_kind") or \
                   ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < 3:
        pool = pool + [c for c in [1, 2, 3, 4, 6, 7, 8, 9] if c not in pool]
    dot_colors = pool[:3]
    if difficulty == "easy":
        h = rng.randint(12, 14)
        w = rng.randint(12, 14)
        n_bar = 1
        dot_lo, dot_hi = 4, 6
    elif difficulty == "hard":
        h = rng.randint(14, 16)
        w = rng.randint(14, 16)
        n_bar = rng.randint(1, 2)
        dot_lo, dot_hi = 8, 14
    else:
        h = 14
        w = 14
        n_bar = rng.randint(1, 2)
        dot_lo, dot_hi = 4, 8
    n_dots = int(overrides.get("n_dots", ctx.draw_int("n_dots", dot_lo, dot_hi)))
    n_dots = max(2, min(16, n_dots))
    g = full_grid(h, w, 0)
    if orientation == "vertical":
        # Pick n_bar contiguous columns for the gray bar.
        c1 = rng.randint(3, max(3, w - 3 - n_bar))
        for r in range(h):
            for cc in range(c1, c1 + n_bar):
                g[r][cc] = 5
        _scatter_side_dots_vertical(g, rng, c1, n_bar, n_dots, dot_colors)
    else:
        r1 = rng.randint(3, max(3, h - 3 - n_bar))
        for c in range(w):
            for rr in range(r1, r1 + n_bar):
                g[rr][c] = 5
        _scatter_side_dots_horizontal(g, rng, r1, n_bar, n_dots, dot_colors)
    return g


def _scatter_side_dots_vertical(g, rng, c1, n_bar, n_dots, dot_colors):
    """Place a bounded number of colored side dots around a vertical gray bar."""
    h, w = len(g), len(g[0])
    left = [(r, c) for r in range(h) for c in range(0, c1)]
    right = [(r, c) for r in range(h) for c in range(c1 + n_bar, w)]
    slots = []
    if left:
        slots.append(rng.choice(left))
    if right:
        slots.append(rng.choice(right))
    rest = [s for s in (left + right) if s not in set(slots)]
    rng.shuffle(rest)
    slots.extend(rest[:max(0, n_dots - len(slots))])
    for i, (r, c) in enumerate(slots[:n_dots]):
        g[r][c] = dot_colors[i % len(dot_colors)]


def _scatter_side_dots_horizontal(g, rng, r1, n_bar, n_dots, dot_colors):
    """Place a bounded number of colored side dots around a horizontal gray bar."""
    h, w = len(g), len(g[0])
    top = [(r, c) for r in range(0, r1) for c in range(w)]
    bot = [(r, c) for r in range(r1 + n_bar, h) for c in range(w)]
    slots = []
    if top:
        slots.append(rng.choice(top))
    if bot:
        slots.append(rng.choice(bot))
    rest = [s for s in (top + bot) if s not in set(slots)]
    rng.shuffle(rest)
    slots.extend(rest[:max(0, n_dots - len(slots))])
    for i, (r, c) in enumerate(slots[:n_dots]):
        g[r][c] = dot_colors[i % len(dot_colors)]


def self_check(grid, *, difficulty=None, meta=None):
    """Color-5 must form a full bar and the side-dot count should stay canonical-scale."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    full_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if bool(full_rows) == bool(full_cols):
        errs.append(f"expected exactly one orientation of full gray bar, rows={len(full_rows)} cols={len(full_cols)}")
    dots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if not (2 <= len(dots) <= 16):
        errs.append(f"expected 2..16 side dots, got {len(dots)}")
    if full_cols:
        left = [1 for r, c in dots if c < min(full_cols)]
        right = [1 for r, c in dots if c > max(full_cols)]
        if not left or not right:
            errs.append("vertical bar should have dots on both sides")
    if full_rows:
        top = [1 for r, c in dots if r < min(full_rows)]
        bot = [1 for r, c in dots if r > max(full_rows)]
        if not top or not bot:
            errs.append("horizontal bar should have dots on both sides")
    return errs


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 5)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_bar":
        g[3][2] = 1
        g[5][7] = 2
        return g
    if name == "no_dots":
        for c in range(10):
            g[5][c] = 5
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 5
        return g
    return g
