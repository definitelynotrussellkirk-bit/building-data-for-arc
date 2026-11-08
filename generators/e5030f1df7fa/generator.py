"""Generator for arc_additional_puzzle_bank_volume16:E111 — Fill ring centers with red.

Rule: hollow 3×3 yellow rings have their centers filled red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, solid_squares, centers_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "e5030f1df7fa"
VERSION = "2.2.0"  # keep the skip-branch distractors and enlarge easy grids enough to reliably place two hollow rings
TASK_ID = "e5030f1df7fa"
SUMMARY = (
    "0-bg grid (h, w~8-13) with "
    "2-4 ISOLATED HOLLOW 3×3 "
    "COLOR-4 (yellow) RINGS at "
    "scattered positions, each "
    "with ≥4 cell separation from "
    "the others (no overlap of "
    "3×3 windows). Each ring is "
    "an 8-cell outline (3×3 - "
    "center) with a 0 center "
    "cell. Rule (FILL RING "
    "CENTERS WITH COLOR 2): "
    "identify each HOLLOW 3×3 "
    "RING (8-cell color-4 frame "
    "with 0 center). For EACH "
    "ring, PAINT the CENTER CELL "
    "(at (r0+1, c0+1)) with "
    "COLOR 2 (red). The 8 ring "
    "cells stay color 4. Net: "
    "each yellow ring gets a "
    "red dot painted in its "
    "center."
)

# Rivals: 'fill every 3x3 region center' refuted by ≥1 demo with
# non-ring 3x3 regions (no fill). 'fill ring center with yellow'
# refuted by any demo (center is 2/red). 'fill all rings everywhere'
# refuted by ≥1 demo with a single ring.
# 3 demos with varied ring counts + a distractor or two cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "target windows are exact hollow 3x3 yellow rings",
    "ring centers start empty",
    "rings are separated so their windows do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "solid_squares", "centers_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_3x3_rings",
                       "valid": "spaced_3x3_rings"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


# Yellow shapes that are NOT a hollow 3x3 ring -> rule must NOT fill them.
_YELLOW_NONRING = [
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)],  # solid 3x3
    [(0, 0), (0, 1), (1, 0), (1, 1)],                                          # 2x2
    [(0, 0), (0, 1), (0, 2)],                                                  # h-line
    [(0, 0), (1, 0), (2, 0)],                                                  # v-line
    [(0, 0), (1, 0), (1, 1)],                                                  # L
]
_DECOY = [
    [(0, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1), (1, 0)],
]


def _free(g, cells, top, left, halo=1):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        r, c = top + dr, left + dc
        if not (0 <= r < h and 0 <= c < w):
            return False
        for ar in range(r - halo, r + halo + 1):
            for ac in range(c - halo, c + halo + 1):
                if 0 <= ar < h and 0 <= ac < w and g[ar][ac] != 0:
                    return False
    return True


def _place(g, rng, cells, color, tries=120):
    h, w = len(g), len(g[0])
    mr = max(dr for dr, _ in cells)
    mc = max(dc for _, dc in cells)
    for _ in range(tries):
        top = rng.randint(0, h - mr - 1)
        left = rng.randint(0, w - mc - 1)
        if _free(g, cells, top, left):
            for dr, dc in cells:
                g[top + dr][left + dc] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_rings = ctx.draw_int("n_rings", 2, 2)
        n_ynr = 0; n_decoy = ctx.draw_int("n_decoy", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 13, 16)
        n_rings = ctx.draw_int("n_rings", 3, 4)
        n_ynr = ctx.draw_int("n_ynr", 1, 2); n_decoy = ctx.draw_int("n_decoy", 1, 2)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 9, 13)
        n_rings = ctx.draw_int("n_rings", 2, 4)
        n_ynr = ctx.draw_int("n_ynr", 0, 2); n_decoy = ctx.draw_int("n_decoy", 0, 2)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    ring = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    placed = 0
    for _ in range(200):
        if placed >= n_rings:
            break
        if _place(g, rng, ring, 4):
            placed += 1
    if placed == 0:
        draw_rect_outline(g, 1, 1, 3, 3, 4)
    # yellow non-ring distractors -> rule must skip (no center to fill)
    for _ in range(n_ynr):
        _place(g, rng, rng.choice(_YELLOW_NONRING), 4)
    # non-yellow decoys -> rule ignores (matches canonical's color-6 decoy)
    for _ in range(n_decoy):
        color = rng.choice([1, 2, 3, 5, 6, 7, 8, 9])
        _place(g, rng, rng.choice(_DECOY), color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no ring centers to fill
        return g
    if name == "solid_squares":
        # solid 3x3 yellow squares (no hole) → no center to fill
        for r in range(3):
            for c in range(3): g[1 + r][1 + c] = 4
        for r in range(3):
            for c in range(3): g[5 + r][5 + c] = 4
        return g
    if name == "centers_already_filled":
        # 3x3 ring with center already non-bg → fill precondition fails
        draw_rect_outline(g, 1, 1, 3, 3, 4)
        g[2][2] = 6
        draw_rect_outline(g, 5, 5, 3, 3, 4)
        g[6][6] = 7
        return g
    return g

def _ring_topleft_positions(grid):
    h, w = len(grid), len(grid[0])
    out = []
    border = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    for r in range(h - 2):
        for c in range(w - 2):
            if grid[r + 1][c + 1] == 0 and all(grid[r + dr][c + dc] == 4 for dr, dc in border):
                out.append((r, c))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid must be non-empty and rectangular"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid rows must have equal width"]
    rings = _ring_topleft_positions(grid)
    min_rings = 3 if difficulty == "hard" else 2
    if len(rings) < min_rings:
        errs.append(f"expected at least {min_rings} hollow yellow rings, found {len(rings)}")
    centers = {(r + 1, c + 1) for r, c in rings}
    if any(grid[r][c] != 0 for r, c in centers):
        errs.append("ring centers must start empty")
    return errs
