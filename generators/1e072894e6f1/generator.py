"""Generator for arc_additional_puzzle_bank_volume9:M60.

Rule: for each non-bg color with exactly 2 cells (sorted by reading
order), draw an L-path (horizontal then vertical) connecting them; the
output is just those paths on a blank grid.

Combinatorial axes: grid size, the number of color pairs, their colors,
and their endpoint positions.
Degenerates: no_pairs, single_pair, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e072894e6f1"
VERSION = "2.0.1"  # diversity: random N color pairs (colors/positions) + grid (was 3 fixed pairs)
TASK_ID = "1e072894e6f1"
SUMMARY = (
    "0-bg grid (size varies). 2-4 distinct COLORS, each with EXACTLY 2 "
    "cells at distinct positions (differing in both row and column so "
    "the connector bends). Rule: for each color, sort its two cells by "
    "reading order and draw an L-PATH from the first — horizontal along "
    "its row to the second's column, then vertical to the second — in "
    "that color; the output is just those paths on a blank grid. The "
    "grid size, the number of pairs, their colors and their endpoint "
    "positions all vary freely (was 3 fixed pairs + grid padding)."
)

INVARIANTS = [
    "2-4 distinct colors",
    "each color has exactly 2 cells at distinct positions",
    "each pair's cells differ in both row and column",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pairs", "single_pair", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_pairs|single_pair|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, npr = (8, 10), (9, 11), (2, 2)
    elif difficulty == "hard":
        hr, wr, npr = (12, 16), (12, 16), (3, 4)
    else:
        hr, wr, npr = (9, 12), (10, 13), (2, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        n = rng.randint(*npr)
        colors = rng.sample(range(1, 10), n)
        used = set()
        g = full_grid(h, w, 0)
        ok = True
        for col in colors:
            placed = False
            for _t in range(60):
                r1 = rng.randint(0, h - 1); c1 = rng.randint(0, w - 1)
                r2 = rng.randint(0, h - 1); c2 = rng.randint(0, w - 1)
                # different row AND col so the L bends, and a visible length.
                if r1 == r2 or c1 == c2:
                    continue
                if abs(r1 - r2) + abs(c1 - c2) < 3:
                    continue
                if (r1, c1) in used or (r2, c2) in used:
                    continue
                used.add((r1, c1)); used.add((r2, c2))
                g[r1][c1] = col; g[r2][c2] = col
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 distinct non-bg colors, each appearing exactly 2 times."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 2:
        errs.append(f"expected >=2 distinct non-bg colors, found {len(counts)}")
    bad = [c for c, n in counts.items() if n != 2]
    if bad:
        errs.append(f"colors not appearing exactly twice: {bad}")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 10, 0)
    if name == "no_pairs":
        return g
    if name == "single_pair":
        g[2][2] = 9; g[5][7] = 9
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(10):
                g[r][c] = 9
        return g
    return g
