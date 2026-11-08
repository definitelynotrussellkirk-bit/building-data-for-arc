"""Generator for puzzle 913fb3ed.

Rule: sparse cells of {2, 3, 8} on bg=0. Output paints 1-cell ring of
paired colors around each: 3→6, 2→1, 8→4.

Combinatorial axes (8): grid_h/w, n_cells, color_distribution,
position_bias, min_separation, anchor_corner, asymmetry_force,
palette_subset.
Degenerates: no_cells, full_grid, single_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "c920aa05c47e"
VERSION = "1.1.0"
TASK_ID = "c920aa05c47e"
SUMMARY = "Cells of {2,3,8}; rule paints color-paired rings around each."

INVARIANTS = [
    "bg = 0",
    "cells use colors from {2, 3, 8}",
    ">=1 cell placed (rule has work)",
    "cells separated >=3 cells apart so rings don't overlap",
]

POSITION_BIASES = ("scattered", "clustered", "row_aligned", "diagonal",
                   "corners")
COLOR_DISTRIBUTIONS = ("uniform", "mostly_3", "mostly_2", "mostly_8",
                       "all_three")
DEGENERATE_TEXTURES = ("no_cells", "full_grid", "single_color")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":             {"type": "int", "default": "rng 8..18", "valid": "5..28"},
    "grid_w":             {"type": "int", "default": "rng 8..18", "valid": "5..28"},
    "n_cells":            {"type": "int", "default": "rng 3..8", "valid": "1..15"},
    "color_distribution": {"type": "str", "default": "rng helpful",
                           "valid": "|".join(COLOR_DISTRIBUTIONS)},
    "position_bias":      {"type": "str", "default": "rng helpful",
                           "valid": "|".join(POSITION_BIASES)},
    "min_separation":     {"type": "int", "default": "3", "valid": "3..6"},
    "anchor_corner":      {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "palette_subset":     {"type": "str", "default": "all", "valid": "all|two"},
    "texture":            {"type": "str", "default": "alias for position_bias",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 9
    elif difficulty == "hard":
        h_lo, h_hi = 18, 28
    else:
        h_lo, h_hi = 8, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_cells = int(overrides.get("n_cells",
                                ctx.draw_int("n_cells", 3, 8)))
    n_cells = max(1, min(15, n_cells))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    color_dist = overrides.get("color_distribution",
                               ctx.draw_choice("color_distribution",
                                               list(COLOR_DISTRIBUTIONS)))
    palette_subset = overrides.get("palette_subset", "all")
    if palette_subset == "two":
        palette = rng.sample([2, 3, 8], 2)
    else:
        palette = [2, 3, 8]
    min_sep = int(overrides.get("min_separation", 3))
    g = full_grid(h, w, 0)
    placed = []
    candidates = _candidate_positions(bias, h, w, rng)
    for r, c in candidates:
        if len(placed) >= n_cells:
            break
        if not (1 <= r <= h - 2 and 1 <= c <= w - 2):
            continue
        if any(abs(r - pr) < min_sep and abs(c - pc) < min_sep
               for pr, pc in placed):
            continue
        col = _pick_color(color_dist, palette, rng)
        g[r][c] = col
        placed.append((r, c))
    if not placed:
        g[h // 2][w // 2] = palette[0]
    return g


def _candidate_positions(bias, h, w, rng):
    if bias == "clustered":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        cells = [(r, c) for r in range(h) for c in range(w)]
        cells.sort(key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
        return cells
    if bias == "row_aligned":
        r = h // 2
        return [(r, c) for c in range(1, w - 1, 4)]
    if bias == "diagonal":
        return [(i, i) for i in range(1, min(h, w) - 1, 3)]
    if bias == "corners":
        return [(2, 2), (2, w - 3), (h - 3, 2), (h - 3, w - 3)]
    cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(cells)
    return cells


def _pick_color(distribution, palette, rng):
    if distribution == "mostly_3" and 3 in palette:
        return 3 if rng.random() < 0.7 else rng.choice(palette)
    if distribution == "mostly_2" and 2 in palette:
        return 2 if rng.random() < 0.7 else rng.choice(palette)
    if distribution == "mostly_8" and 8 in palette:
        return 8 if rng.random() < 0.7 else rng.choice(palette)
    return rng.choice(palette)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_cells":
        return g
    if name == "full_grid":
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                if (r + c) % 4 == 0:
                    g[r][c] = rng.choice([2, 3, 8])
        return g
    if name == "single_color":
        for r in range(2, h - 2, 4):
            for c in range(2, w - 2, 4):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    h, w = len(grid), len(grid[0])
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not cells:
        errs.append("expected at least one source cell")
    bad = [(r, c, v) for r, c, v in cells if v not in {2, 3, 8}]
    if bad:
        errs.append("source cells must use only colors {2,3,8}")
    if any(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in cells):
        errs.append("source cells must stay off the border so 1-cell rings fit")
    pts = [(r, c) for r, c, _ in cells]
    for i, (r1, c1) in enumerate(pts):
        for r2, c2 in pts[i + 1:]:
            if abs(r1 - r2) < 3 and abs(c1 - c2) < 3:
                errs.append("source cells are too close; their rings can overlap")
                return errs
    return errs
