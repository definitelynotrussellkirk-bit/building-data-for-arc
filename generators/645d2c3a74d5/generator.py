"""Generator for arc_additional_puzzles_21_set3:E16.

Rule: cell (r,c)=0 with all 4 diagonal neighbors = 1 → set to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_patterns,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_patterns, partial_x, center_already_8.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "645d2c3a74d5"
VERSION = "2.1.0"
TASK_ID = "645d2c3a74d5"
SUMMARY = "Several X-patterns of color-1 cells on a 0-bg grid. Each X consists of 4 color-1 cells at the diagonal neighbors of an interior cell (the center stays 0). Rule paints color 8 at every interior 0-cell whose 4 diagonal neighbors are ALL color 1. Non-X 1-cells (with diagonals missing) stay 1; their adjacent 0s stay 0."

# Rivals: 'output is input' refuted by demos with ≥1 X. 'fill X
# diagonals with 8' refuted by demos preserving 1s. 'fill cardinal
# neighbors instead of diagonals' refuted by demos where cardinal
# 1-neighbor 0s stay 0. 'use color 9 instead of 8' refuted by demos.
# 3 demos with ≥2 X-patterns + some non-X 1s cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "≥2 X-patterns: 4 diagonal cells of value 1 around a 0 center",
    "patterns don't overlap",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied")
DEGENERATE_TEXTURES = ("no_patterns", "partial_x", "center_already_8")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_patterns":     {"type": "int", "default": "2", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(6, 8); w = rng.randint(7, 10)
        n_x = rng.randint(1, 2); n_decoy = rng.randint(0, 1)
    elif difficulty == "hard":
        h = rng.randint(12, 17); w = rng.randint(13, 18)
        n_x = rng.randint(4, 7); n_decoy = rng.randint(3, 6)
    else:
        h = rng.randint(8, 12); w = rng.randint(10, 14)
        n_x = rng.randint(2, 4); n_decoy = rng.randint(1, 3)
    g = full_grid(h, w, 0)
    placed = []  # X centers

    def can_place_x(r, c):
        if g[r][c] != 0:
            return False
        if any(abs(r - pr) <= 2 and abs(c - pc) <= 2 for pr, pc in placed):
            return False
        return all(g[r + dr][c + dc] == 0
                   for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)])

    def place_x(r, c):
        g[r - 1][c - 1] = 1; g[r - 1][c + 1] = 1
        g[r + 1][c - 1] = 1; g[r + 1][c + 1] = 1
        placed.append((r, c))

    for _ in range(80):
        if len(placed) >= n_x:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if not can_place_x(r, c):
            continue
        place_x(r, c)
    # Deterministic scan fallback: the random spacing loop could leave easy
    # boards with zero true X-centers on small grids, turning the rule into a
    # no-op. Keep placing non-overlapping centers until the declared target is
    # reached or the grid is genuinely saturated.
    if len(placed) < n_x:
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                if len(placed) >= n_x:
                    break
                if can_place_x(r, c):
                    place_x(r, c)
            if len(placed) >= n_x:
                break
    # Add decoy 1-cells in non-X positions
    for _ in range(n_decoy * 6):
        if n_decoy <= 0:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0 or (r, c) in placed:
            continue
        # Avoid creating a complete X by accident or corrupting a real X center:
        # this 1 would complete any X-center's 4-diagonal-1 condition.
        completes_x = False
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            cr, cc = r + dr, c + dc
            if not (1 <= cr < h - 1 and 1 <= cc < w - 1):
                continue
            if (cr, cc) in placed:
                continue  # this center is already a real X
            # Check if 3 other diagonals of (cr, cc) are already 1
            count = 0
            for ddr, ddc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                tr = cr + ddr; tc = cc + ddc
                if (tr, tc) == (r, c):
                    continue
                if 0 <= tr < h and 0 <= tc < w and g[tr][tc] == 1:
                    count += 1
            if count == 3:
                completes_x = True; break
        if completes_x:
            continue
        g[r][c] = 1
        n_decoy -= 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_patterns":
        # empty grid — no X-patterns to detect
        return g
    if name == "partial_x":
        # only 3 diagonal cells of an X → predicate "all 4 diagonals = 1" fails
        g[1][1] = 1; g[1][3] = 1; g[3][1] = 1
        return g
    if name == "center_already_8":
        # complete X but center is already 8 → rule's effect is invisible
        g[1][1] = 1; g[1][3] = 1; g[3][1] = 1; g[3][3] = 1
        g[2][2] = 8
        return g
    return g
def _x_centers(grid):
    h, w = len(grid), len(grid[0])
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            if all(grid[r + dr][c + dc] == 1
                   for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]):
                centers.append((r, c))
    return centers


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(v not in (0, 1) for row in grid for v in row):
        errors.append("input should contain only 0 background and color-1 diagonals")
    centers = _x_centers(grid)
    if not centers:
        errors.append("no complete X-pattern centers")
    if difficulty in (None, "hard") and len(centers) < 2:
        errors.append(f"expected at least two X-pattern centers, got {len(centers)}")
    return errors
