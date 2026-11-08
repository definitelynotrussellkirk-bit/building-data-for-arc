"""Generator for 32e9702f.

Rule: per row, find leftmost/rightmost non-bg col; cells in
[max(0, left-1), right) get value of cell to right; everything else → 5.

Combinatorial axes (8): grid_h/w, n_active_rows, run_length_kind,
palette_size, position_bias, run_layout, palette_kind, asymmetry.
Degenerates: empty_grid, all_rows_filled, single_cell_per_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "adc0c2fa01fd"
VERSION = "1.1.0"
TASK_ID = "adc0c2fa01fd"
SUMMARY = "Rows with non-bg run; rule shifts run right + fills 5."

INVARIANTS = [
    "background is 0",
    ">=2 rows have a horizontal segment of >=2 non-bg cells (single color)",
    "rest of grid is all 0",
    "no color 5 in input (rule writes 5 for output)",
]

RUN_LAYOUTS = ("contiguous", "left_biased", "right_biased", "centered",
               "varied_length")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("empty_grid", "all_rows_filled", "single_cell_per_row")
HELPFUL_TEXTURES = RUN_LAYOUTS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "grid_w":           {"type": "int", "default": "rng 7..14", "valid": "6..18"},
    "n_active_rows":    {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "run_length_kind":  {"type": "str", "default": "rng small|medium|large",
                         "valid": "small|medium|large"},
    "palette_size":     {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":    {"type": "str", "default": "rng spread|center|edge",
                         "valid": "spread|center|edge"},
    "run_layout":       {"type": "str", "default": "rng helpful",
                         "valid": "|".join(RUN_LAYOUTS)},
    "palette_kind":     {"type": "str", "default": "rng helpful",
                         "valid": "|".join(PALETTE_KINDS)},
    "texture":          {"type": "str", "default": "alias for run_layout",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 7, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 16, 13, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 12, 7, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_active = int(overrides.get("n_active_rows",
                                 ctx.draw_int("n_active_rows", 2, 5)))
    n_active = max(2, min(h, n_active))
    length_kind = overrides.get("run_length_kind",
                                ctx.draw_choice("run_length_kind",
                                                ["small", "medium", "large"]))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 7, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 4)))
    palette = pool[:max(1, n_palette)]
    layout = (overrides.get("texture") or overrides.get("run_layout")
              or ctx.draw_choice("run_layout", list(RUN_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    g = full_grid(h, w, 0)
    rows = list(range(h))
    rng.shuffle(rows)
    placed = 0
    for r in rows[:n_active]:
        length = _draw_length(length_kind, w, rng)
        c0 = _row_position(layout, bias, w, length, rng)
        c0 = max(0, min(w - length, c0))
        if layout == "varied_length":
            length = rng.randint(2, max(2, w - 2))
            c0 = max(0, min(w - length, c0))
        color = rng.choice(palette)
        for i in range(length):
            g[r][c0 + i] = color
        placed += 1
    if placed < 2:
        for r in range(min(2, h)):
            for c in range(min(3, w)):
                g[r][c] = palette[0]
    return g


def _draw_length(kind, w, rng):
    if kind == "small":
        return rng.randint(2, min(3, w - 1))
    if kind == "medium":
        return rng.randint(3, min(5, w - 1))
    if kind == "large":
        return rng.randint(4, min(8, w - 1))
    return rng.randint(2, min(4, w - 1))


def _row_position(layout, bias, w, length, rng):
    if layout == "left_biased":
        return 0
    if layout == "right_biased":
        return w - length
    if layout == "centered":
        return (w - length) // 2
    if bias == "center":
        return (w - length) // 2 + rng.randint(-1, 1)
    if bias == "edge":
        return rng.choice([0, w - length])
    return rng.randint(0, max(0, w - length))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    if name == "empty_grid":
        return g
    if name == "all_rows_filled":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_cell_per_row":
        for r in range(h):
            g[r][rng.randint(0, w - 1)] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    active = 0
    for r, row in enumerate(grid):
        nz = [c for c, v in enumerate(row) if v != 0]
        if not nz:
            continue
        active += 1
        if len(nz) < 2:
            msgs.append(f"row {r} has a single-cell run")
        if nz != list(range(nz[0], nz[-1] + 1)):
            msgs.append(f"row {r} non-bg cells are not contiguous: {nz}")
        vals = {row[c] for c in nz}
        if len(vals) != 1:
            msgs.append(f"row {r} run is not single-color: {sorted(vals)}")
    if active < 2:
        msgs.append(f"expected at least two active rows, found {active}")
    if any(v == 5 for row in grid for v in row):
        msgs.append("input must not contain output fill color 5")
    return msgs
