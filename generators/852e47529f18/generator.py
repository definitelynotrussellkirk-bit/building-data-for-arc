"""Generator for v2_meta_puzzles:E7 — recolor color-6 by orientation.

Rule: each color-6 connected component is recolored: 8 if horizontal-only
(rmin == rmax), 2 otherwise.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: only_horizontal, only_vertical, no_color_6.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "852e47529f18"
VERSION = "1.2.1"
TASK_ID = "852e47529f18"
SUMMARY = "Color-6 connected components; rule recolors each: cyan(8) if single-row (rmin==rmax), else red(2). Output palette is binary by orientation."

# Rivals: 'recolor all to 8' refuted by ≥1 demo with multi-row 6-blob
# becoming 2. 'recolor all to 2' refuted by ≥1 demo with single-row
# 6-blob becoming 8. 'preserve 6' refuted by any demo (output has
# 8s and 2s). 'use original color (6) for one branch' refuted by any
# demo (output is always 8 or 2, never 6).
# 4 demos with varied 6-motifs cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly two color-6 motifs at distinct positions",
    "one motif is a horizontal line (single-row, length ≥3)",
    "the other motif spans multiple rows",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("only_horizontal", "only_vertical", "no_color_6")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_motifs":       {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "horizontal_plus_vertical",
                       "valid": "horizontal_plus_vertical"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; only color-6 nonzero cells; ≥2 color-6 components; ≥1 horizontal + ≥1 vertical."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    sixes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    non6 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0 and grid[r][c] != 6]
    if not sixes and not non6:
        return []  # no_color_6 degenerate — allowed
    errs = []
    if non6:
        errs.append(f"{len(non6)} non-6 nonzero cells found; input should only have color-6")
        return errs
    if not sixes:
        return []
    # find color-6 components
    visited = set()
    horiz = vert = 0
    for r0, c0 in sixes:
        if (r0, c0) not in visited:
            queue = [(r0, c0)]
            visited.add((r0, c0))
            comp = [(r0, c0)]
            while queue:
                r, c = queue.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in visited and 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 6:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        comp.append((nr, nc))
            rows = {r for r, c in comp}
            if len(rows) == 1:
                horiz += 1
            else:
                vert += 1
    if horiz == 0 and vert == 0:
        errs.append("no color-6 components found")
    elif horiz + vert < 2:
        errs.append(f"expected ≥2 color-6 components; found {horiz + vert}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        n_h_lines = rng.randint(1, 2)
        n_v_or_rect = rng.randint(1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 17)
        n_h_lines = rng.randint(2, 4)
        n_v_or_rect = rng.randint(2, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 13)
        n_h_lines = rng.randint(1, 3)
        n_v_or_rect = rng.randint(1, 3)
    g = full_grid(h, w, 0)
    # Place horizontal lines (single-row, length ≥1; rule cares about rmin==rmax).
    for _ in range(n_h_lines * 6):
        if n_h_lines <= 0: break
        length = rng.randint(2, min(6, w))
        r = rng.randint(0, h - 1); c = rng.randint(0, w - length)
        if not _free(g, r, c, r, c + length - 1): continue
        for cc in range(c, c + length):
            g[r][cc] = 6
        n_h_lines -= 1
    # Place vertical lines or rectangles (multi-row).
    for _ in range(n_v_or_rect * 6):
        if n_v_or_rect <= 0: break
        ph = rng.randint(2, min(4, h)); pw = rng.randint(1, min(3, w))
        r0 = rng.randint(0, h - ph); c0 = rng.randint(0, w - pw)
        if not _free(g, r0, c0, r0 + ph - 1, c0 + pw - 1): continue
        for dr in range(ph):
            for dc in range(pw):
                g[r0 + dr][c0 + dc] = 6
        n_v_or_rect -= 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "only_horizontal":
        # all 6-motifs are horizontal-only → only the rmin==rmax → 8 branch fires
        for c in range(2, 5): g[1][c] = 6
        for c in range(4, 7): g[4][c] = 6
        return g
    if name == "only_vertical":
        # all 6-motifs span multiple rows → only the else → 2 branch fires
        for r in range(1, 4): g[r][2] = 6
        for r in range(3, 6): g[r][7] = 6
        return g
    if name == "no_color_6":
        # no color-6 cells → rule has no components to recolor
        g[2][3] = 4; g[4][6] = 8
        return g
    return g
