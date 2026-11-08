"""Generator for arc_additional_puzzles_21_set17_bundle:E113.

Rule: row 0 holds a legend (its non-0 cells, in column order). A fixed
3x3 template at rows 2-4, cols 1-3 uses some symbols; sorted ascending,
the i-th distinct symbol maps to the i-th legend color. Output is the
remapped 3x3 template.

This generator lays out a legend in row 0 and a 3x3 template using exactly
those symbols, on a 0-padded grid.

Combinatorial axes: the legend colors, the template symbols/arrangement,
and grid size.
Degenerates: no_legend, single_symbol, full_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9da7d24a9190"
VERSION = "2.0.0"  # diversity: random legend + 3x3 template symbol remap (was fixed ~24)
TASK_ID = "9da7d24a9190"
SUMMARY = (
    "0-padded grid (size varies). Row 0 is a LEGEND (non-0 cells in column "
    "order); a fixed 3x3 template (rows 2-4, cols 1-3) uses some symbols. "
    "Rule: the i-th smallest distinct template symbol maps to the i-th "
    "legend color; output is the remapped 3x3 template. The legend colors, "
    "template symbols/arrangement and grid size vary freely (was a fixed "
    "setup, ~24 distinct). Output is 3x3, so distinct OUTPUTS are bounded; "
    "distinct INPUTS are large."
)

INVARIANTS = [
    "row 0 holds the legend; the template is the fixed 3x3 at rows 2-4 cols 1-3",
    "the legend has at least as many colors as the template has distinct symbols",
    "the i-th sorted symbol maps to the i-th legend color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "single_symbol", "full_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "5..9"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "5..10"},
    "n_symbols":      {"type": "int", "default": "varies", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "legend_template", "valid": "legend_template"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|single_symbol|full_template"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, kr = (5, 6), (5, 7), (2, 3)
    elif difficulty == "hard":
        hr, wr, kr = (7, 9), (7, 10), (4, 6)
    else:
        hr, wr, kr = (5, 8), (5, 9), (2, 5)

    for _attempt in range(40):
        K = rng.randint(*kr)
        symbols = rng.sample(range(1, 10), K)          # the K distinct template symbols
        legend = rng.sample(range(1, 10), K)             # i-th sorted symbol -> unique legend[i]
        h = rng.randint(*hr); w = rng.randint(*wr)
        if w < 4 or w < K:
            continue
        g = full_grid(h, w, 0)
        # legend in row 0, columns 0..K-1
        for i in range(K):
            g[0][i] = legend[i]
        # 3x3 template at rows 2-4 cols 1-3, every symbol present, rest 0/symbol
        cells = [(r, c) for r in range(3) for c in range(3)]
        rng.shuffle(cells)
        used = list(symbols)
        rng.shuffle(used)
        for idx, (r, c) in enumerate(cells):
            if idx < K:
                g[2 + r][1 + c] = used[idx]
            else:
                g[2 + r][1 + c] = rng.choice([0] + symbols)
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 6, 0)
    g[0][0] = 3; g[0][1] = 4
    for r in range(3):
        for c in range(3):
            g[2 + r][1 + c] = (5 if (r + c) % 2 == 0 else 6)
    if name == "no_legend":
        g[0][0] = 0; g[0][1] = 0
        return g
    if name == "single_symbol":
        for r in range(3):
            for c in range(3):
                g[2 + r][1 + c] = 5
        return g
    if name == "full_template":
        for r in range(3):
            for c in range(3):
                g[2 + r][1 + c] = 5 if (r * 3 + c) % 2 == 0 else 6
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    legend = [v for v in grid[0] if v != 0]
    syms = {grid[r][c] for r in range(2, 5) for c in range(1, 4) if grid[r][c] != 0}
    errs: list[str] = []
    if len(legend) < len(syms): errs.append("legend shorter than distinct template symbols")
    if len(legend) != len(set(legend)): errs.append("legend colors must be unique")
    if len(syms) < 2: errs.append("template should use at least two symbols")
    return errs
