"""Generator for arc_puzzle_bank_fourth_21_bundle:easy_24_bridge_single_horizontal_gaps.

Rule: isolated 6-0-6 horizontal gaps are bridged with 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_gaps,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_gaps, gaps_too_long, vertical_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b01ab48322ab"
VERSION = "1.2.0"  # count bridgeable gaps explicitly + stronger self_check
TASK_ID = "b01ab48322ab"
SUMMARY = "Isolated 6-0-6 horizontal gaps are bridged with 8."

INVARIANTS = [
    "background is 0",
    "target motifs are exactly 6-0-6 in a row",
    "neighboring cells beyond each motif are not 6",
    "at least one bridgeable gap is present",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_gaps", "gaps_too_long", "vertical_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_gaps":         {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "isolated_horizontal_gaps",
                       "valid": "isolated_horizontal_gaps"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _bridgeable_gaps(grid):
    h, w = len(grid), len(grid[0])
    gaps = []
    for r in range(h):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and grid[r][c - 1] == 6 and grid[r][c + 1] == 6:
                if (c - 2 < 0 or grid[r][c - 2] != 6) and (c + 2 >= w or grid[r][c + 2] != 6):
                    gaps.append((r, c))
    return gaps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify isolated horizontal 6-0-6 bridge motifs are present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs: list[str] = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    bad = sorted({v for row in grid for v in row if v not in (0, 6)})
    if bad:
        errs.append(f"unexpected colors outside {{0,6}}: {bad}")
    gaps = _bridgeable_gaps(grid)
    lo, hi = (2, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else (2, 5))
    if not (lo <= len(gaps) <= hi):
        errs.append(f"expected {lo}..{hi} isolated horizontal gaps, got {len(gaps)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        n_gaps = ctx.draw_int("n_gaps", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_gaps = ctx.draw_int("n_gaps", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n_gaps = ctx.draw_int("n_gaps", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(240):
        if placed >= n_gaps:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(1, w - 2)
        area = {(r, x) for x in range(c - 2, c + 3) if 0 <= x < w}
        if reserved & area:
            continue
        g[r][c - 1] = 6
        g[r][c + 1] = 6
        reserved |= area
        placed += 1
    if placed < n_gaps:
        raise ValueError(f"could not place {n_gaps} isolated 6-0-6 gaps")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_gaps":
        # only single 6-cells, never (6,0,6) → rule fires zero times
        g[2][3] = 6; g[5][7] = 6; g[6][1] = 6
        return g
    if name == "gaps_too_long":
        # 6-0-0-6 (gap of 2) → predicate "single zero between" fails, rule does nothing
        g[2][1] = 6; g[2][4] = 6   # gap of 2 zeros at cols 2,3
        g[5][3] = 6; g[5][7] = 6   # gap of 3
        return g
    if name == "vertical_only":
        # 6-0-6 vertical (above-below) → rule only checks horizontal, predicate fails
        g[1][3] = 6; g[3][3] = 6
        g[2][7] = 6; g[4][7] = 6
        return g
    return g
