"""Generator for arc_puzzle_bank_21_set13_bundle:easy_m05.

The grid has exactly two nonzero colors with unequal frequencies. The rarer
color is recolored to the more frequent color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, dominant_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: monochrome, equal_freq, three_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "73ab3e5ab7dc"
VERSION = "1.2.0"
TASK_ID = "73ab3e5ab7dc"
SUMMARY = "Two compact nonzero color components with a strict frequency winner and loser."

INVARIANTS = [
    "background is 0",
    "exactly two nonzero colors appear",
    "one color appears strictly more often than the other",
    "each nonzero color forms one compact 4-connected component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("monochrome", "equal_freq", "three_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "dominant_count": {"type": "int", "default": "rng 4..8", "valid": "2..20"},
    "rare_count":     {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_colors_unequal_freq",
                       "valid": "two_colors_unequal_freq"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 9)
        dominant_count = ctx.draw_int("dominant_count", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        dominant_count = ctx.draw_int("dominant_count", 6, 8)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
        dominant_count = ctx.draw_int("dominant_count", 4, 8)
    rare_count = min(ctx.draw_int("rare_count", 1, 3), dominant_count - 1)
    dominant, rare = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Canonical examples show one compact component per color, not many
    # disconnected singleton dots.  Keeping the two colors connected preserves
    # the frequency rule while matching the task's visual distribution.
    _place_blob(g, dominant, dominant_count, rng)
    _place_blob(g, rare, rare_count, rng)
    return g


def _place_blob(g, color, n, rng):
    """Paint n cells as one 4-connected component in currently empty cells."""
    h, w = len(g), len(g[0])
    n = max(1, min(n, sum(1 for row in g for v in row if v == 0)))
    for _ in range(250):
        empties = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        if not empties:
            break
        start = rng.choice(empties)
        cells = {start}
        while len(cells) < n:
            cand = []
            for r, c in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 0 and (nr, nc) not in cells:
                        cand.append((nr, nc))
            if not cand:
                break
            cells.add(rng.choice(cand))
        if len(cells) == n:
            for r, c in cells:
                g[r][c] = color
            return cells
    # Extremely rare fallback: greedily fill a connected component from the
    # first empty cell.  The requested grids have ample space, so this path is
    # mainly a defensive guard for unusual overrides.
    empties = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
    if not empties:
        return set()
    cells = {empties[0]}
    while len(cells) < n:
        cand = []
        for r, c in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 0 and (nr, nc) not in cells:
                    cand.append((nr, nc))
        if not cand:
            break
        cells.add(cand[0])
    for r, c in cells:
        g[r][c] = color
    return cells


def _component_count(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = 0
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            comps += 1
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Verify two nonzero colors with frequency imbalance invariants for 73ab3e5ab7dc."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    nz = [v for v in flat if v != 0]
    if not nz:
        errs.append("no non-zero cells")
        return errs
    nz_colors = {v for v in nz}
    if len(nz_colors) != 2:
        errs.append(f"{len(nz_colors)} non-zero colors (expected exactly 2)")
    elif len(nz_colors) == 2:
        c1, c2 = sorted(nz_colors)
        n1, n2 = nz.count(c1), nz.count(c2)
        if n1 == n2:
            errs.append(f"colors {c1} and {c2} appear equal times ({n1}) — need strict majority")
        for color in (c1, c2):
            comps = _component_count(grid, color)
            if comps != 1:
                errs.append(f"color {color} has {comps} components; expected one compact component")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "monochrome":
        # only one nonzero color → no rare color to recolor
        for r, c in [(1, 1), (1, 2), (3, 4), (5, 6)]:
            g[r][c] = 4
        return g
    if name == "equal_freq":
        # two colors at equal frequency → no winner/loser
        for r, c in [(1, 1), (2, 3), (4, 5)]:
            g[r][c] = 4
        for r, c in [(0, 0), (3, 7), (5, 2)]:
            g[r][c] = 6
        return g
    if name == "three_colors":
        # three nonzero colors → "exactly two" precondition fails
        for r, c in [(1, 1), (2, 3), (4, 5)]:
            g[r][c] = 4
        for r, c in [(0, 0), (3, 7)]:
            g[r][c] = 6
        for r, c in [(5, 2)]:
            g[r][c] = 7
        return g
    return g
