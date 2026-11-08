"""Generator for puzzle ac0a08a4.

Rule: input is N×N with nz non-bg cells. Output is (N*nz)×(N*nz) where
each input cell becomes an nz×nz block of that color (or all 0 if bg).

Combinatorial axes (8): grid_n, n_cells, palette_size, cell_layout,
unique_colors, anchor_origin, decoy_palette_kind, position_bias.
Degenerates: empty_grid, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_cells
from puzzle_generators.helpers.indices import all_indices

GENERATOR_ID = "7fc158ab7b70"
VERSION = "1.1.2"
TASK_ID = "7fc158ab7b70"
SUMMARY = "Square input with non-bg cells; rule upscales each cell by nz (non-bg count)."

INVARIANTS = [
    "bg=0",
    "h == w (square input)",
    ">=2 non-bg cells (so the upscale factor is meaningful)",
    "n*nz <= 30 (output fits 30x30 limit)",
]

CELL_LAYOUTS = ("random", "diag", "anti_diag", "row", "col", "scattered", "cluster")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "single_cell")
HELPFUL_TEXTURES = CELL_LAYOUTS

AXES = {
    "grid_n":         {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "n_cells":        {"type": "int", "default": "rng 2..max_nz", "valid": "1..(n²-1)"},
    "palette_size":   {"type": "int", "default": "= n_cells",     "valid": "1..9"},
    "cell_layout":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CELL_LAYOUTS)},
    "unique_colors":  {"type": "bool", "default": "true", "valid": "true|false"},
    "position_bias":  {"type": "str", "default": "rng spread|center|edge",
                       "valid": "spread|center|edge"},
    "anchor_origin":  {"type": "bool", "default": "false", "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for cell_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify square input, meaningful nonzero count, and output size cap."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h != w:
        errs.append(f"expected square grid; got {h}×{w}")
    nz = sum(1 for row in grid for v in row if v != 0)
    if nz < 2:
        errs.append(f"expected ≥2 nonzero cells; found {nz}")
    if h * nz > 30:
        errs.append(f"upscaled output would be {h * nz}×{h * nz}, exceeding 30")
    colors = [v for row in grid for v in row if v != 0]
    if len(colors) > len(set(colors)):
        errs.append("normal examples should use unique nonzero colors")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        n_lo, n_hi = 2, 3
    elif difficulty == "hard":
        n_lo, n_hi = 4, 5
    else:
        n_lo, n_hi = 2, 5
    n = int(overrides.get("grid_n", ctx.draw_int("grid_n", n_lo, n_hi)))
    n = max(2, min(5, n))
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, rng)
    max_nz = min(n * n - 1, 30 // n, 9)
    if max_nz < 2:
        return _draw_from_degenerate("single_cell", n, rng)
    n_cells = int(overrides.get("n_cells",
                                ctx.draw_int("n_cells", 2, max_nz)))
    n_cells = max(2, min(max_nz, n_cells))
    unique_colors = bool(overrides.get("unique_colors", True))
    if unique_colors:
        palette = list(ctx.draw_distinct_colors("palette",
                                                n=n_cells, exclude={0}))
    else:
        n_pal = max(1, n_cells // 2)
        pool = list(ctx.draw_distinct_colors("palette",
                                             n=n_pal, exclude={0}))
        palette = [pool[i % n_pal] for i in range(n_cells)]
    layout = (overrides.get("texture") or overrides.get("cell_layout")
              or ctx.draw_choice("cell_layout", list(CELL_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    g = full_grid(n, n, 0)
    locs = _pick_cells(layout, n, n_cells, bias, rng)
    for color, loc in zip(palette, locs):
        paint_cells(g, [loc], color)
    if bool(overrides.get("anchor_origin", False)) and (0, 0) not in locs:
        # Preserve the nonzero count/output-size contract by moving one active cell to origin.
        old_r, old_c = locs[-1]
        g[old_r][old_c] = 0
        g[0][0] = palette[-1]
    return g


def _pick_cells(layout, n, k, bias, rng):
    all_cells = list(all_indices(n, n))
    if layout == "diag":
        cells = [(i, i) for i in range(n)]
    elif layout == "anti_diag":
        cells = [(i, n - 1 - i) for i in range(n)]
    elif layout == "row":
        r = rng.randint(0, n - 1)
        cells = [(r, c) for c in range(n)]
    elif layout == "col":
        c = rng.randint(0, n - 1)
        cells = [(r, c) for r in range(n)]
    elif layout == "scattered":
        cells = [(r, c) for (r, c) in all_cells if (r + c) % 2 == 0]
    elif layout == "cluster":
        cr = rng.randint(0, n - 1)
        cc = rng.randint(0, n - 1)
        cells = sorted(all_cells, key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
    else:  # random
        cells = list(all_cells)
        rng.shuffle(cells)
    if bias == "edge":
        cells = sorted(cells,
                       key=lambda rc: -max(rc[0], rc[1], n - 1 - rc[0], n - 1 - rc[1]))
    elif bias == "center":
        ctr = (n - 1) / 2
        cells = sorted(cells, key=lambda rc: abs(rc[0] - ctr) + abs(rc[1] - ctr))
    chosen = cells[:k]
    if len(chosen) < k:
        remaining = [cell for cell in all_cells if cell not in chosen]
        chosen.extend(remaining[:k - len(chosen)])
    return chosen


def _draw_from_degenerate(name, n, rng):
    g = full_grid(n, n, 0)
    if name == "empty_grid":
        return g
    if name == "full_grid":
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r in range(n):
            for c in range(n):
                g[r][c] = color
        return g
    if name == "single_cell":
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        g[n // 2][n // 2] = color
        return g
    return g
