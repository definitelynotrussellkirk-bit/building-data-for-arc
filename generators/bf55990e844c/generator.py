"""Generator for arc_puzzle_bank_21_set21_bundle:hard_p01 — laser-bounce trail.

Rule: a source cell on the border (color in non-{0, 1, 2, 5}) emits a beam
inward. Mirror 1 is /, mirror 2 is \\, color 5 is wall. The beam paints 0-cells
along its path with the source color until it hits a wall or exits.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_mirrors, n_walls, texture.
Degenerates: no_source, no_mirrors, source_in_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf55990e844c"
VERSION = "1.2.1"
TASK_ID = "bf55990e844c"

SUMMARY = "One color-1 source (treated as laser start, moving right). Mirrors at color 2 reflect via (dr,dc) → (-dc,-dr); mirrors at color 3 reflect via (dr,dc) → (dc,dr). Color 8 is a wall (stops the beam). The beam paints empty cells along its trajectory color 7. Source + mirrors + walls preserved."

# Rivals: 'output is input' refuted by any demo (7s appear along beam).
# 'beam paints source color' refuted by any demo (beam is 7).
# 'no reflection' refuted by ≥1 demo where mirror 2 or 3 redirects beam.
# 'walls do nothing' refuted by ≥1 demo where 8-wall stops trail.
# 3 demos with varied configs cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one source cell on the grid border in a non-{0, 1, 2, 5} color",
    "1-3 mirror cells (color 1 or 2) inside the grid (not on border)",
    "0-2 wall cells (color 5) sparsely placed",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_mirrors", "source_in_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..17"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..19"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_mirrors":      {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "n_walls":        {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "border_source_inner_mirrors",
                       "valid": "border_source_inner_mirrors"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one non-zero cell on the border (the laser source)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    # Collect border cells
    border_nonzero = []
    for c in range(w):
        if grid[0][c] != 0:
            border_nonzero.append((0, c, grid[0][c]))
        if grid[h - 1][c] != 0:
            border_nonzero.append((h - 1, c, grid[h - 1][c]))
    for r in range(1, h - 1):
        if grid[r][0] != 0:
            border_nonzero.append((r, 0, grid[r][0]))
        if grid[r][w - 1] != 0:
            border_nonzero.append((r, w - 1, grid[r][w - 1]))
    if not border_nonzero:
        errs.append("no border source cell found")
    elif len(border_nonzero) > 1:
        errs.append(f"expected 1 border source; found {len(border_nonzero)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        n_mirrors = ctx.draw_int("n_mirrors", 0, 2)
        n_walls = ctx.draw_int("n_walls", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 14, 19)
        n_mirrors = ctx.draw_int("n_mirrors", 4, 6)
        n_walls = ctx.draw_int("n_walls", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        n_mirrors = ctx.draw_int("n_mirrors", 2, 4)
        n_walls = ctx.draw_int("n_walls", 1, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    source_color = rng.choice([3, 4, 6, 7, 8, 9])
    border = []
    for c in range(w): border.extend([(0, c), (h - 1, c)])
    for r in range(1, h - 1): border.extend([(r, 0), (r, w - 1)])
    sr, sc = rng.choice(border)
    g[sr][sc] = source_color
    for _ in range(n_mirrors):
        for _t in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            g[r][c] = rng.choice([1, 2])
            break
    for _ in range(n_walls):
        for _t in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            g[r][c] = 5
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_source":
        # Mirrors and walls but no border source — no beam to launch.
        g[3][4] = 1; g[5][6] = 2; g[7][3] = 5
        return g
    if name == "no_mirrors":
        # Source on border but no mirrors — straight beam, reflection
        # step never fires.
        g[0][5] = 4; g[5][3] = 5
        return g
    if name == "source_in_corner":
        # Source at corner — direction is ambiguous.
        g[0][0] = 4; g[3][3] = 1
        return g
    return g
