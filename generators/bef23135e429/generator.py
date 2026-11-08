"""Generator for arc_puzzle_bank_21_set9_s:S9_H1.

Rule: a single 2-marker and a single 3-marker; color-7 cells form a
connected region around them. Each 7-cell gets recolored 2/3 by which
marker is closer (BFS distance through 7-cells only); ties become 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_path, markers_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bef23135e429"
VERSION = "1.2.1"
TASK_ID = "bef23135e429"

SUMMARY = "One color-2 + one color-3 single-cell markers + color-7 path cells; rule recolors each 7 to whichever marker is closer (BFS distance through 7-cells); equal distances → 8."

# Rivals: 'flood-fill from each marker' refuted by ≥1 demo where ties
# appear as 8. 'use Manhattan distance, ignore path' refuted by ≥1
# demo where path detours around obstacles. 'recolor everything as
# 2/3 alternating' refuted by ≥2 demos with clear distance-based
# boundaries. 'erase 7s' refuted by any demo (7s become 2 or 3 or 8).
# 4 demos with varied marker positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-2 cell and one color-3 cell (single cells)",
    "color-7 cells form a connected region adjacent to both markers",
    "markers are at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_path", "markers_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_7_cells":      {"type": "int", "default": "rng 4..8", "valid": "2..16"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "two_markers_in_7_region",
                       "valid": "two_markers_in_7_region"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _grow_region(rng, h, w, target_size, start):
    """Grow a 4-connected region of target_size starting from start cell."""
    cells = {start}
    frontier = [start]
    while len(cells) < target_size and frontier:
        r, c = rng.choice(frontier)
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(deltas)
        added = False
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells:
                cells.add((nr, nc))
                frontier.append((nr, nc))
                added = True
                break
        if not added:
            frontier.remove((r, c))
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-2 cell, one color-3 cell, and some color-7 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    c2 = [(r, c) for r in range(len(grid)) for c in range(w) if grid[r][c] == 2]
    c3 = [(r, c) for r in range(len(grid)) for c in range(w) if grid[r][c] == 3]
    c7 = [(r, c) for r in range(len(grid)) for c in range(w) if grid[r][c] == 7]
    if len(c2) != 1:
        errs.append(f"expected exactly 1 color-2 cell; found {len(c2)}")
    if len(c3) != 1:
        errs.append(f"expected exactly 1 color-3 cell; found {len(c3)}")
    if not c7:
        errs.append("no color-7 path cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 11)
        n_7 = ctx.draw_int("n_7", 3, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 18)
        n_7 = ctx.draw_int("n_7", 10, 18)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 14)
        n_7 = ctx.draw_int("n_7", 6, 10)

    g = full_grid(h, w, 0)
    # Place two distinct marker positions.
    r2, c2 = rng.randint(0, h - 1), rng.randint(0, w - 1)
    while True:
        r3, c3 = rng.randint(0, h - 1), rng.randint(0, w - 1)
        if (r2, c2) != (r3, c3):
            break
    # Grow a 7-region connecting them (start from a midpoint).
    mr = (r2 + r3) // 2; mc = (c2 + c3) // 2
    region = _grow_region(rng, h, w, n_7, (mr, mc))
    # Force the markers' positions to be in the region for BFS through them
    region.add((r2, c2))
    region.add((r3, c3))
    # Ensure path connectivity from (r2,c2) to (r3,c3) — extend the region
    # by walking towards each marker if not already connected.
    def bfs_reachable(start, goal):
        seen = {start}; queue = [start]
        while queue:
            cur = queue.pop(0)
            if cur == goal: return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = cur[0] + dr, cur[1] + dc
                if (nr, nc) in region and (nr, nc) not in seen:
                    seen.add((nr, nc)); queue.append((nr, nc))
        return False
    if not bfs_reachable((r2, c2), (r3, c3)):
        # Add a straight L-path between them.
        cur_r, cur_c = r2, c2
        while cur_r != r3:
            cur_r += 1 if r3 > cur_r else -1
            region.add((cur_r, cur_c))
        while cur_c != c3:
            cur_c += 1 if c3 > cur_c else -1
            region.add((cur_r, cur_c))
    # Paint region as 7, then overwrite markers.
    for r, c in region:
        g[r][c] = 7
    g[r2][c2] = 2
    g[r3][c3] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_markers":
        for r, c in [(3, 3), (3, 4), (4, 3), (4, 4)]: g[r][c] = 7
        return g
    if name == "no_path":
        g[2][2] = 2; g[6][8] = 3
        return g
    if name == "markers_overlap":
        g[3][5] = 2; g[3][5] = 3  # only 3 survives
        for r, c in [(3, 4), (3, 6)]: g[r][c] = 7
        return g
    return g
