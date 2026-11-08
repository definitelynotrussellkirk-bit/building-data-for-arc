"""Generator for puzzle 137f0df0.

Rule: gray(5) cells define a set of occupied rows (br) and cols (bc).
Empty cells are recolored by their relation to those rows/cols: cells in
an interior gap between gray rows/cols become 2 (the cross-hatch), cells
in an exterior gap become 1. The canonical puzzles use a GRID of small
gray blocks (multiple gray rows and cols), not a single 2x2 rectangle.

This generator places a grid of small gray blocks at regular intervals so
that br/bc each contain several rows/cols, producing the rich multi-band
cross-hatch the rule generates.

Combinatorial axes: grid size, block size, block-grid dimensions, gap
widths, offsets.
Degenerates: no_grays, single_gray, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0eb2cb95521b"
VERSION = "1.2.1"  # +self_check
TASK_ID = "0eb2cb95521b"
SUMMARY = "Grid of small gray(5) blocks defining multiple occupied rows/cols; rule cross-hatches gaps with red/blue."

INVARIANTS = [
    "background is 0",
    "gray(5) blocks arranged in a regular grid (>=2 block rows and >=2 block cols)",
    "at least one interior gap between block rows and between block cols",
    "blocks do not touch the grid edge on all sides",
]

DEGENERATE_TEXTURES = ("no_grays", "single_gray", "full_grid")

AXES = {
    "n_block_rows":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "n_block_cols":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "block_h":        {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "block_w":        {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "gap_r":          {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "gap_c":          {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture":        {"type": "str", "default": "n/a (degenerates only)",
                       "valid": "|".join(DEGENERATE_TEXTURES)},
}


def _block_starts(n_blocks, block, gap, lead):
    """Return the start index of each block given a leading offset, block
    size and uniform gap between blocks."""
    return [lead + i * (block + gap) for i in range(n_blocks)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        nb_r, nb_c = (2, 2), (2, 2)
    elif difficulty == "hard":
        nb_r, nb_c = (3, 4), (3, 4)
    else:
        nb_r, nb_c = (2, 3), (2, 3)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], 10, rng)

    for _attempt in range(40):
        bh = rng.randint(1, 2)            # block height
        bw = rng.randint(1, 2)            # block width
        nbr = ctx.draw_int("n_block_rows", *nb_r)
        nbc = ctx.draw_int("n_block_cols", *nb_c)
        gap_r = rng.randint(1, 3)         # gap between block rows
        gap_c = rng.randint(1, 3)         # gap between block cols
        lead_r = rng.randint(0, 2)
        lead_c = rng.randint(0, 2)
        trail_r = rng.randint(0, 2)
        trail_c = rng.randint(0, 2)

        row_starts = _block_starts(nbr, bh, gap_r, lead_r)
        col_starts = _block_starts(nbc, bw, gap_c, lead_c)
        h = row_starts[-1] + bh + trail_r
        w = col_starts[-1] + bw + trail_c
        if h < 5 or w < 5 or h > 22 or w > 22:
            continue

        g = full_grid(h, w, 0)
        for rs in row_starts:
            for cs in col_starts:
                for r in range(rs, rs + bh):
                    for c in range(cs, cs + bw):
                        g[r][c] = 5
        return g

    # fallback: simple 2x2 block grid
    g = full_grid(7, 7, 0)
    for r in (1, 4):
        for c in (1, 4):
            g[r][c] = 5
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid has gray (5) cells; at least 2 distinct rows and 2 distinct cols contain gray."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    h, w = len(grid), len(grid[0])
    gray_rows = {r for r in range(h) for c in range(w) if grid[r][c] == 5}
    gray_cols = {c for c in range(w) for r in range(h) if grid[r][c] == 5}
    if not gray_rows:
        errors.append("no gray (5) cells found")
    elif len(gray_rows) < 2:
        errors.append(f"only {len(gray_rows)} row(s) contain gray; need >=2 for interior gaps")
    if len(gray_cols) < 2:
        errors.append(f"only {len(gray_cols)} col(s) contain gray; need >=2 for interior gaps")
    return errors


def _draw_from_degenerate(name, size, rng):
    g = full_grid(size, size, 0)
    if name == "no_grays":
        return g
    if name == "single_gray":
        g[size // 2][size // 2] = 5
        return g
    if name == "full_grid":
        for r in range(size):
            for c in range(size):
                g[r][c] = 5
        return g
    return g
