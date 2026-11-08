"""Generator for additional_scaffolded:E2 — color-3 beacons paint diagonal halos.

Rule: color-3 beacon cells paint their diagonal neighbors with color 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_beacons,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_beacons, beacons_at_corner, multi_cell_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f819e4f14fa6"
VERSION = "1.3.1"  # add executable invariant self_check for normal beacon fields
TASK_ID = "f819e4f14fa6"
SUMMARY = "Isolated color-3 beacon cells on a 0-bg grid. Rule: every 0-cell that is a DIAGONAL (Chebyshev distance 1, Manhattan distance 2) neighbor of a 3-cell becomes color 7. Cardinal neighbors stay 0; beacons themselves stay 3. Out-of-bounds diagonals are ignored."

# Rivals: 'output is input' refuted by any demo (at least one 7).
# 'paint cardinal too' refuted by any demo with a beacon whose
# cardinal neighbor stays 0. 'paint with color 3' refuted by any
# demo (always 7). 'paint only one diagonal' refuted by any demo
# where multiple diagonals fill in. 3 demos with ≥3 interior beacons
# cover the diagonal-only rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "input contains isolated color-3 beacon cells",
    "at least one beacon is interior and at least one may be near an edge",
    "beacons are spaced enough that their halos remain readable",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_beacons", "beacons_at_corner", "multi_cell_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..11", "valid": "3..18"},
    "grid_w":         {"type": "int", "default": "rng 6..11", "valid": "3..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_beacons":      {"type": "int", "default": "rng 3..7", "valid": "1..20"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_color3_singletons",
                       "valid": "spaced_color3_singletons"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_beacons|beacons_at_corner|multi_cell_blobs"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        h = rng.randint(5, 9); w = rng.randint(5, 9)
        n_beacons = rng.randint(2, 4)
    elif difficulty == "hard":
        h = rng.randint(14, 24); w = rng.randint(14, 24)
        n_beacons = rng.randint(10, 20)
    else:
        h = rng.randint(9, 16); w = rng.randint(9, 16)
        n_beacons = rng.randint(4, 10)
    g = full_grid(h, w, 0)
    cells: list[tuple[int, int]] = [(rng.randint(1, h - 2), rng.randint(1, w - 2))]
    for _ in range(160):
        if len(cells) >= n_beacons:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if (r, c) in cells:
            continue
        if any(abs(r - rr) <= 1 and abs(c - cc) <= 1 for rr, cc in cells):
            continue
        cells.append((r, c))
    for r, c in cells:
        g[r][c] = 3
    return g



def _diag_neighbors(r: int, c: int, h: int, w: int) -> list[tuple[int, int]]:
    return [
        (r + dr, c + dc)
        for dr in (-1, 1)
        for dc in (-1, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the normal path: isolated color-3 beacons on
    a zero background, with at least one interior beacon and readable diagonal
    halo opportunities. Degenerate override textures are intentionally exempt."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    colors = {int(v) for row in grid for v in row}
    if colors - {0, 3}:
        errs.append(f"unexpected colors in input: {sorted(colors - {0, 3})}")
    beacons = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if int(v) == 3]
    if not beacons:
        errs.append("no color-3 beacons")
        return errs
    interior = [(r, c) for r, c in beacons if 0 < r < h - 1 and 0 < c < w - 1]
    if not interior:
        errs.append("no interior beacon; all halos are edge-clipped")
    # Normal examples should use singleton beacons separated by at least a one-cell Chebyshev moat;
    # otherwise the diagonal-only rule is visually confounded by adjacent color-3 blobs/merged halos.
    close_pairs = []
    for i, (r, c) in enumerate(beacons):
        for rr, cc in beacons[i + 1:]:
            if abs(r - rr) <= 1 and abs(c - cc) <= 1:
                close_pairs.append(((r, c), (rr, cc)))
    if close_pairs:
        errs.append(f"beacons are not isolated/spaced: {close_pairs[:3]}")
    if not any(len(_diag_neighbors(r, c, h, w)) == 4 for r, c in beacons):
        errs.append("no beacon has all four diagonal halo targets in bounds")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_beacons":
        # blank → no halos to paint
        return g
    if name == "beacons_at_corner":
        # beacons at corners → 3 of 4 diagonal neighbors are out of bounds
        g[0][0] = 3
        g[h - 1][w - 1] = 3
        return g
    if name == "multi_cell_blobs":
        # 3-color cells form blobs (not isolated singletons) → halos overlap/merge
        g[2][2] = 3; g[2][3] = 3   # adjacent
        g[5][5] = 3; g[6][5] = 3
        return g
    return g
