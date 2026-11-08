"""Generator for arc_additional_puzzles_21_set20_bundle:E136.

Rule: find full row OR full col of 8s. Mirror each non-{0,8} cell across
that line.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_cells_to_mirror, cells_on_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c1e45a501ca9"
VERSION = "1.3.0"  # add executable guide-axis/mirror-side invariants for assigned random audit. branch-coverage poison: rule mirrors across a full-COL OR full-ROW 8-divider, but gen only ever drew a vertical column -> row-divider branch never exercised. Now randomize orientation + divider position; widen grid toward valid caps.
TASK_ID = "c1e45a501ca9"
SUMMARY = "A full row or column of 8s acts as a mirror guide; isolated colored cells appear only on the source side."

INVARIANTS = [
    "exactly 1 full-height col of 8s (or full-width row)",
    "left/upper side has 2-3 isolated non-{0,8} cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_cells_to_mirror", "cells_on_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "left_of_divider",
                       "valid": "left_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..7"},
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
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 5, 9)
        w = ctx.draw_int("grid_w", 8, 13)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    # Rule branches on divider orientation: a full COLUMN of 8s -> mirror across
    # that column; else a full ROW of 8s -> mirror across that row. v1.1.0 only
    # ever drew a vertical column divider, so the row-divider branch was NEVER
    # exercised. Now pick orientation at random and seed cells on one side.
    orient = rng.choice(["col", "row"])
    n_seed = rng.randint(2, 4)
    if orient == "col":
        # divider in left half so left-seed mirrors (mc = 2*gc - c) stay in bounds
        gc = rng.randint(1, max(1, (w - 1) // 2))
        for r in range(h):
            g[r][gc] = 8
        for _ in range(n_seed):
            for _ in range(30):
                r = rng.randint(0, h - 1); c = rng.randint(0, gc - 1)
                if g[r][c] == 0:
                    g[r][c] = rng.choice(palette); break
    else:
        gr = rng.randint(1, max(1, (h - 1) // 2))
        for c in range(w):
            g[gr][c] = 8
        for _ in range(n_seed):
            for _ in range(30):
                r = rng.randint(0, gr - 1); c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = rng.choice(palette); break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    msgs = []
    full_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    full_rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    if len(full_cols) + len(full_rows) != 1:
        msgs.append(f"expected exactly one full 8 guide row/col, found rows={full_rows}, cols={full_cols}")
        return msgs
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)]
    if len(seeds) < 2:
        msgs.append(f"expected at least two colored cells to mirror, found {len(seeds)}")
    if full_cols:
        gc = full_cols[0]
        for r, c, v in seeds:
            if c >= gc:
                msgs.append("colored source cell appears on/after the vertical guide")
            mc = 2 * gc - c
            if not (0 <= mc < w):
                msgs.append("vertical mirror target is out of bounds")
            elif grid[r][mc] != 0:
                msgs.append("vertical mirror target is already occupied")
    else:
        gr = full_rows[0]
        for r, c, v in seeds:
            if r >= gr:
                msgs.append("colored source cell appears on/after the horizontal guide")
            mr = 2 * gr - r
            if not (0 <= mr < h):
                msgs.append("horizontal mirror target is out of bounds")
            elif grid[mr][c] != 0:
                msgs.append("horizontal mirror target is already occupied")
    return sorted(set(msgs))


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # cells without an 8-divider → rule has no mirror axis
        g[1][2] = 4; g[3][3] = 6
        return g
    if name == "no_cells_to_mirror":
        # divider but empty side → nothing to reflect
        gc = w // 2
        for r in range(h):
            g[r][gc] = 8
        return g
    if name == "cells_on_both_sides":
        # cells already on both sides → mirror would overwrite existing cells
        gc = w // 2
        for r in range(h):
            g[r][gc] = 8
        g[1][2] = 4; g[3][3] = 6
        g[2][gc + 1] = 5; g[4][gc + 2] = 7
        return g
    return g
