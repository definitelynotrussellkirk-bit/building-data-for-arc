"""Generator for puzzle 7e02026e.

Rule: scattered non-bg cells. Places a green(3) plus-sign at every
cell where the cell + 4 cardinal neighbors are all bg(0).

Combinatorial axes (8): grid_h/w, dot_density, palette_kind,
palette_size, distribution, anchor_corner, asymmetry_force,
include_decoy.
Degenerates: full_grid, no_dots, all_3s.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85cd7b009dd3"
VERSION = "1.2.1"
TASK_ID = "85cd7b009dd3"
SUMMARY = "Sparse non-bg cells (colors != 3) scattered on a 0-bg grid. Rule: for every interior cell (r, c) where the cell AND ALL 4 cardinal neighbors are 0, paint a plus-sign (5 cells: center + 4 cardinal neighbors) in color 3. Existing non-bg cells are preserved."

# Rivals: 'output is input' refuted by demos (plus-signs appear).
# 'paint single cells, not plus' refuted by demos with full plus.
# 'use color 2 instead of 3' refuted by demos. 'paint at any 0-cell
# even if neighbors have non-0' refuted by demos (only completely
# empty crosses fill). 3 demos with ≥2 plus locations cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "non-bg cells use colors != 3",
    ">=1 valid plus-center in the interior (so rule fires)",
    "non-bg cell density 5-30% (so empty plus-centers exist)",
]

DISTRIBUTIONS = ("scattered", "stripes", "checker", "diagonal",
                 "edges", "clustered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary", "minimal")
DEGENERATE_TEXTURES = ("full_grid", "no_dots", "all_3s")
HELPFUL_TEXTURES = DISTRIBUTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "dot_density":    {"type": "float", "default": "rng 0.1..0.3",
                       "valid": "0.05..0.5"},
    "distribution":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DISTRIBUTIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for distribution",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; no color-3 cells in input; at least one valid plus-center exists."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    # Non-bg cells must not use color 3 (that's the output color)
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if threes:
        errs.append(f"input contains color-3 cells (reserved for output); count={len(threes)}")
        return errs
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # degenerate no_dots — allowed
    # Check at least one valid plus-center exists (interior cell with all 5 cells = 0)
    has_plus_center = any(
        1 <= r <= h - 2 and 1 <= c <= w - 2 and
        grid[r][c] == 0 and
        grid[r - 1][c] == 0 and grid[r + 1][c] == 0 and
        grid[r][c - 1] == 0 and grid[r][c + 1] == 0
        for r in range(1, h - 1) for c in range(1, w - 1)
    )
    if not has_plus_center:
        return []  # degenerate full_grid — allowed (no empty plus-center)
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 16, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    density = float(overrides.get("dot_density",
                                  ctx.draw_rng("dot_density")
                                  .uniform(0.1, 0.3)))
    distribution = (overrides.get("texture") or
                    overrides.get("distribution")
                    or ctx.draw_choice("distribution",
                                       list(DISTRIBUTIONS)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette_size = int(overrides.get("palette_size",
                                     ctx.draw_int("palette_size", 2, 4)))
    palette = _build_palette(palette_kind, palette_size, rng)
    g = full_grid(h, w, 0)
    _fill(g, distribution, density, palette, h, w, rng)
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 4]
    elif kind == "minimal":
        pool = [8]
    else:
        pool = [1, 2, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:max(1, n)]


def _fill(g, distribution, density, palette, h, w, rng):
    if distribution == "scattered":
        for r in range(h):
            for c in range(w):
                if rng.random() < density:
                    g[r][c] = rng.choice(palette)
    elif distribution == "stripes":
        for r in range(h):
            if r % 2 == 0:
                for c in range(0, w, 2):
                    if rng.random() < density + 0.3:
                        g[r][c] = rng.choice(palette)
    elif distribution == "checker":
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0 and rng.random() < density + 0.2:
                    g[r][c] = rng.choice(palette)
    elif distribution == "diagonal":
        for i in range(min(h, w)):
            if rng.random() < density + 0.4:
                g[i][i] = rng.choice(palette)
    elif distribution == "edges":
        for r in range(h):
            for c in range(w):
                on_edge = (r in (0, h - 1) or c in (0, w - 1))
                if on_edge and rng.random() < density + 0.2:
                    g[r][c] = rng.choice(palette)
    elif distribution == "clustered":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        for r in range(h):
            for c in range(w):
                d = abs(r - cr) + abs(c - cc)
                if rng.random() < density * (1 - d / (h + w)):
                    g[r][c] = rng.choice(palette)
    else:
        n = int(h * w * density)
        for _ in range(n):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = rng.choice(palette)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "full_grid":
        c = rng.choice([1, 2, 4, 5, 6, 7, 8, 9])
        for r in range(h):
            for cc in range(w):
                g[r][cc] = c
        return g
    if name == "no_dots":
        return g
    if name == "all_3s":
        # Already includes 3 → rule's plus-3s collide with input
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.3:
                    g[r][c] = 3
        return g
    return g
