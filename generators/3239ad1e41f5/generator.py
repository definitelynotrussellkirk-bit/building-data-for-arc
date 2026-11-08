"""Generator for 84db8fc4.

Rule: find 0-regions. If region touches grid border → 2; else → 5.
Non-zero cells unchanged.

Combinatorial axes (8): grid_h/w, fill_density, palette_kind,
palette_size, n_interior_holes, n_border_holes, anchor_corner,
asymmetry_force.
Degenerates: all_zeros, all_filled, only_interior.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3239ad1e41f5"
VERSION = "1.2.0"
TASK_ID = "3239ad1e41f5"
SUMMARY = "Mixed grid; rule paints 0-regions: 2 if border, 5 if interior."

INVARIANTS = [
    ">=1 0-region adjacent to outer border",
    ">=1 0-region strictly interior",
    "no 2 or 5 in input (rule writes them for output)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("all_zeros", "all_filled", "only_interior")
HELPFUL_TEXTURES = ("balanced", "border_heavy", "interior_heavy", "scattered")

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "grid_w":            {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "fill_density":      {"type": "float", "default": "rng 0.4..0.7",
                          "valid": "0.2..0.9"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "n_interior_holes":  {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_border_holes":    {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "rng helpful",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """≥1 border-adjacent zero region AND ≥1 strictly interior zero region; no 2 or 5 in input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # No 2 or 5 in input (rule writes them for output)
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (2, 5):
                errs.append(f"input contains color {grid[r][c]} at ({r},{c}) (reserved for rule output)")
                return errs
    # BFS from border to find border-reachable zero cells
    border_zero = set()
    queue = []
    visited = set()
    for c in range(w):
        if grid[0][c] == 0:
            queue.append((0, c)); visited.add((0, c)); border_zero.add((0, c))
        if grid[h-1][c] == 0:
            queue.append((h-1, c)); visited.add((h-1, c)); border_zero.add((h-1, c))
    for r in range(h):
        if grid[r][0] == 0:
            queue.append((r, 0)); visited.add((r, 0)); border_zero.add((r, 0))
        if grid[r][w-1] == 0:
            queue.append((r, w-1)); visited.add((r, w-1)); border_zero.add((r, w-1))
    idx = 0
    while idx < len(queue):
        r, c = queue[idx]; idx += 1
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in visited and grid[nr][nc]==0:
                visited.add((nr,nc)); queue.append((nr,nc)); border_zero.add((nr,nc))
    has_border = bool(border_zero)
    has_interior = any(grid[r][c]==0 and (r,c) not in border_zero for r in range(h) for c in range(w))
    if not has_border:
        errs.append("no zero region adjacent to outer border")
    if not has_interior:
        errs.append("no strictly interior zero region")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 11, 8, 11
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 13, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 9, 14, 9, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 7, 8]
    elif palette_kind == "small":
        pool = [1, 3]
    else:
        pool = [1, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 4)))
    palette = pool[:max(1, n_palette)]
    density = float(overrides.get("fill_density",
                                  ctx.draw_rng("fill_density")
                                  .uniform(0.4, 0.7)))
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)
    n_interior = int(overrides.get("n_interior_holes",
                                   ctx.draw_int("n_interior_holes", 1, 3)))
    n_border = int(overrides.get("n_border_holes",
                                 ctx.draw_int("n_border_holes", 1, 3)))
    placed_interior = 0
    for _ in range(20):
        if placed_interior >= n_interior:
            break
        r = rng.randint(2, h - 3)
        c = rng.randint(2, w - 3)
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if (rr, cc) != (r, c) and g[rr][cc] == 0:
                    g[rr][cc] = rng.choice(palette)
        g[r][c] = 0
        placed_interior += 1
    placed_border = 0
    for _ in range(n_border * 5):
        if placed_border >= n_border:
            break
        choice = rng.choice([(0, rng.randint(0, w - 1)),
                            (h - 1, rng.randint(0, w - 1)),
                            (rng.randint(0, h - 1), 0),
                            (rng.randint(0, h - 1), w - 1)])
        r, c = choice
        g[r][c] = 0
        placed_border += 1
    return g


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 3, 4, 6, 7, 8, 9])
    if name == "all_zeros":
        return g
    if name == "all_filled":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "only_interior":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        g[h // 2][w // 2] = 0
        return g
    return g
