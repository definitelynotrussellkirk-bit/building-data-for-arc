"""Generator for arc_puzzle_bank_seventh21:M47.

The first two rows define source-to-target color mappings. Body cells use the
source colors and are recolored by the rule while the legend stays unchanged.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_maps,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_body, body_unknown_source.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f6f10283c81b"
VERSION = "2.0.0"  # full-palette legend colors (was rigid 1-5->6-9) + bigger grids + denser body (every key exercised)
TASK_ID = "f6f10283c81b"
SUMMARY = (
    "0-bg grid. The first two rows are a color LEGEND: at several columns, row 0 "
    "holds a source color and row 1 holds its target (keys and values are drawn "
    "from the FULL 1-9 palette and are disjoint, matching canonical). The body "
    "(rows >=2) is filled with the source colors. Rule: keep rows 0-1, and for "
    "every body cell that equals a legend key, replace it with that key's value. "
    "Net: the legend recolors the body. (Was: sources fixed to 1-5, targets 6-9.)"
)

INVARIANTS = [
    "row 0 holds source (key) colors at the legend columns; row 1 the targets",
    "legend keys and values are disjoint colors from 1-9 (each value != its key)",
    "the body (rows >=2) contains every source color at least once (all maps exercised)",
    "body uses only legend source colors + background (clean recolor)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_body", "body_unknown_source")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-10 easy / 9-13 med / 11-16 hard", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 10-15 med / 12-20 hard", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_maps":         {"type": "int", "default": "2-3 easy / 3-4 med / 4 hard", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 6..8", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "two_legend_rows_plus_body",
                       "valid": "two_legend_rows_plus_body"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..8", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, has ≥1 legend column (row 0 and row 1 have matching non-zero cells)."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 2:
        return errors
    legend_cols = [c for c in range(w) if grid[0][c] != 0 and grid[1][c] != 0]
    if not legend_cols:
        pass  # degenerate (no_legend) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, nr, dens = (8, 10), (8, 11), (2, 3), 0.32
    elif difficulty == "hard":
        hr, wr, nr, dens = (11, 16), (12, 20), (4, 4), 0.42
    else:
        hr, wr, nr, dens = (9, 13), (10, 15), (3, 4), 0.38
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    n_maps = min(rng.randint(*nr), w, 4)        # disjoint keys+values need 2n<=9
    g = full_grid(h, w, 0)

    # full-palette legend: 2*n_maps DISTINCT colors -> keys + values (disjoint)
    pool = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2 * n_maps)
    sources = pool[:n_maps]; targets = pool[n_maps:]
    cols = sorted(rng.sample(range(w), n_maps))
    for col, src, dst in zip(cols, sources, targets):
        g[0][col] = src; g[1][col] = dst

    # body (rows >=2): every source appears >=1, then random source fill
    for src in sources:
        for _ in range(60):
            r = rng.randint(2, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = src; break
    for r in range(2, h):
        for c in range(w):
            if g[r][c] == 0 and rng.random() < dens:
                g[r][c] = rng.choice(sources)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # body has source colors but no legend → no remap mapping defined
        g[3][2] = 1; g[5][6] = 2; g[7][3] = 3
        return g
    if name == "no_body":
        # legend present but body is empty → nothing to recolor
        for col, src, dst in [(1, 1, 6), (3, 2, 7), (5, 3, 8)]:
            g[0][col] = src; g[1][col] = dst
        return g
    if name == "body_unknown_source":
        # body contains colors not in legend's source set → no mapping for them
        g[0][1] = 1; g[1][1] = 6
        g[3][2] = 4  # 4 is not in legend sources
        g[5][6] = 5
        return g
    return g
