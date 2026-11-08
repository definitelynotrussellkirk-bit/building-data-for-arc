"""Generator for arc_puzzle_bank_21_set7:easy_g03.

Rule: rows with nonzero cells contain a strict majority color that
controls the row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_majority, no_active_rows, single_color_rows.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8a610ee504e"
VERSION = "1.1.1"
TASK_ID = "c8a610ee504e"
SUMMARY = "Rows with nonzero cells contain a strict majority color that controls the row."

INVARIANTS = [
    "nonempty rows have a strict nonzero majority color",
    "some rows may remain empty",
    "background is zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_majority", "no_active_rows", "single_color_rows")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rows":         {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "rows", "valid": "rows"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "3_majority_2_minor",
                       "valid": "3_majority_2_minor"},
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
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 8)
        n = min(ctx.draw_int("n_rows", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = min(ctx.draw_int("n_rows", 4, 5), h)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 6, 10)
        n = min(ctx.draw_int("n_rows", 2, 5), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = list(range(h))
    rng.shuffle(rows)
    for r in rows[:n]:
        major, minor = ctx.draw_distinct_colors(f"row_{r}_colors", n=2, exclude={0})
        cols = list(range(w))
        rng.shuffle(cols)
        for c in cols[:3]:
            g[r][c] = major
        for c in cols[3:5]:
            g[r][c] = minor
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "tied_majority":
        # row has equal counts of two colors → no strict majority winner
        for c, color in zip(range(0, 6, 2), [4] * 3):
            g[2][c] = color
        for c, color in zip(range(1, 6, 2), [6] * 3):
            g[2][c] = color
        return g
    if name == "no_active_rows":
        # empty grid — predicate "rows with nonzero cells" matches nothing
        return g
    if name == "single_color_rows":
        # rows have a single non-zero color only → no minor cells, ratio undefined
        for c in range(3):
            g[1][c] = 5
        for c in range(2, 5):
            g[3][c] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Each non-empty row must have a strict majority (>50%) nonzero color."""
    msgs = []
    from collections import Counter
    h = len(grid)
    w = len(grid[0]) if h else 0
    active = False
    for r in range(h):
        row = [grid[r][c] for c in range(w) if grid[r][c] != 0]
        if not row:
            continue
        active = True
        counts = Counter(row)
        total = sum(counts.values())
        best_count = max(counts.values())
        if best_count * 2 <= total:
            msgs.append(f"row {r} has no strict majority nonzero color: counts={dict(counts)}")
    if not active:
        msgs.append("no active (non-empty) rows found")
    return msgs
