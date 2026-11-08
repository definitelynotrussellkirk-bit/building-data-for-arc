"""Generator for arc_additional_puzzle_bank_volume16:E110 — diagonal magenta endpoints recolor.

Rule: each diagonal magenta segment has its two endpoints recolored
blue.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_segments,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_segments, axis_aligned, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "820f1b7e2a6f"
VERSION = "2.1.0"
TASK_ID = "820f1b7e2a6f"
SUMMARY = (
    "0-bg grid (h, w~9-14) with "
    "2-4 DIAGONAL COLOR-6 "
    "(magenta) SEGMENTS, each a "
    "STRAIGHT 45° DIAGONAL line "
    "(slope +1 or -1) of length "
    "3-5 cells. Segments are "
    "8-conn isolated (no two "
    "segments share a "
    "neighborhood). Rule "
    "(RECOLOR DIAGONAL "
    "MAGENTA ENDPOINTS TO BLUE): "
    "for EACH diagonal magenta "
    "segment (8-connected "
    "component of length ≥3), "
    "identify its two ENDPOINT "
    "cells (the cells with only "
    "ONE same-color 8-conn "
    "neighbor). RECOLOR the two "
    "endpoint cells to COLOR 1 "
    "(blue). The INTERIOR cells "
    "of the diagonal stay "
    "magenta. Net: each diagonal "
    "magenta segment has its "
    "endpoints repainted blue, "
    "creating a blue-magenta-...-"
    "blue stripe."
)

# Rivals: 'recolor all segment cells' refuted by ≥1 demo where
# interior stays 6. 'recolor only one endpoint' refuted by ≥2 demos
# with both endpoints recolored. 'use magenta for endpoint mark'
# refuted by any demo (endpoint is 1). 'recolor axis-aligned too'
# refuted if input would have them (not generated here, but rule
# only matches diagonal connectivity).
# 4 demos with varied diagonal segments cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "magenta components are diagonal line segments",
    "diagonal segments have length at least three",
    "segments are separated so 8-connected components do not merge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_segments", "axis_aligned", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_segments":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1 (magenta)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "diagonal_segments",
                       "valid": "diagonal_segments"},
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
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_segments = ctx.draw_int("n_segments", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 20)
        w = ctx.draw_int("grid_w", 15, 20)
        n_segments = ctx.draw_int("n_segments", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 13, 16)
        n_segments = ctx.draw_int("n_segments", 3, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()
    placed_segments = 0
    # Realize the requested number of diagonal components, not merely
    # n_segments*3 magenta cells.  The previous cell-count stop accepted, e.g.,
    # three length-5 segments as "five requested segments", so hard examples
    # often under-taught the per-component endpoint rule.
    for _ in range(1200):
        if placed_segments >= n_segments:
            break
        length = rng.randint(3, min(5, h - 2, w - 2))
        slope = rng.choice([-1, 1])
        r0 = rng.randint(1, h - length - 1)
        c0 = rng.randint(length, w - 2) if slope == -1 else rng.randint(1, w - length - 1)
        cells = [(r0 + i, c0 + slope * i) for i in range(length)]
        if any(abs(r - rr) <= 1 and abs(c - cc) <= 1
               for r, c in cells for rr, cc in occupied):
            continue
        for cell in cells:
            occupied.add(cell)
            g[cell[0]][cell[1]] = 6
        placed_segments += 1
    if placed_segments < n_segments:
        g = _fallback_segments(h, w, n_segments)
    return g


def _fallback_segments(h, w, n_segments):
    """Deterministic spaced length-3 diagonals used only if random packing
    misses the exact requested component count."""
    g = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()
    placed = 0
    for r0 in range(1, max(2, h - 2), 4):
        for c0 in range(1, max(2, w - 2), 4):
            for slope in (1, -1):
                if placed >= n_segments:
                    return g
                if slope == 1:
                    cells = [(r0 + i, c0 + i) for i in range(3)]
                else:
                    cells = [(r0 + i, c0 + 2 - i) for i in range(3)]
                if any(not (1 <= r < h - 1 and 1 <= c < w - 1) for r, c in cells):
                    continue
                if any(abs(r - rr) <= 1 and abs(c - cc) <= 1
                       for r, c in cells for rr, cc in occupied):
                    continue
                for r, c in cells:
                    occupied.add((r, c))
                    g[r][c] = 6
                placed += 1
                break
    if placed < n_segments:
        raise ValueError(f"could not realize {n_segments} separated diagonal segments in {h}x{w}")
    return g


def _magenta_components(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 6 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 6:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    comps = _magenta_components(grid)
    lo, hi = (1, 3) if difficulty == "easy" else (5, 8) if difficulty == "hard" else (3, 5)
    if not (lo <= len(comps) <= hi):
        errors.append(f"expected {lo}-{hi} separated magenta diagonal segments, got {len(comps)}")
    for cells in comps:
        if len(cells) < 3:
            errors.append(f"magenta segment too short: {len(cells)}")
            continue
        rs = sorted(r for r, _ in cells)
        cs = sorted(c for _, c in cells)
        if len(set(rs)) != len(cells) or len(set(cs)) != len(cells):
            errors.append("magenta component is not a 45-degree diagonal line")
            continue
        diffs = {r - c for r, c in cells}
        sums = {r + c for r, c in cells}
        if len(diffs) != 1 and len(sums) != 1:
            errors.append("magenta component is not a straight diagonal")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_segments":
        # Empty grid — no diagonal magenta to recolor.
        return g
    if name == "axis_aligned":
        # Horizontal and vertical magenta segments — neither is a
        # diagonal, so the rule's diagonal-segment match never fires.
        for dc in range(4):
            g[2][2 + dc] = 6
        for dr in range(4):
            g[5 + dr][7] = 6
        return g
    if name == "single_cell":
        # Single magenta cells (length 1) — too short for the rule's
        # length-3+ filter, no endpoints to identify.
        g[2][2] = 6; g[5][7] = 6; g[8][3] = 6
        return g
    return g
