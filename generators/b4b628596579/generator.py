"""Generator for b4b628596579 — broadcast the top row to every row.

Rule (verified): output = a grid where EVERY row is replaced by the FIRST row
of the input ((make-list (rows g) (first g))). So the canonical task is: each
input row is a different CYCLIC SHIFT of one base color sequence, and the
output normalizes all rows to row 0's pattern.

To exercise this meaningfully the input rows must DIFFER from row 0 (otherwise
the task is identity), and row 0 must carry a rich color pattern (it alone
determines the entire output). The generator builds a base sequence of colors,
makes row 0 = the base, and fills every other row with an INDEPENDENT cyclic
shift of the base (>=1 shift so the row differs from row 0).

Combinatorial axes (8): grid_h, grid_w, base_palette, n_colors, period,
row_shift, palette_kind, position_bias.
Degenerates: all_same_rows, single_row, blank.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b4b628596579"
VERSION = "2.1.0"  # richer row-0 palette + executable cyclic-shift self_check.
TASK_ID = "b4b628596579"
SUMMARY = (
    "Dense color grid (h~4-9, w~6-12) where each ROW is a CYCLIC SHIFT of one "
    "base color sequence: row 0 = the base sequence (a length-w row drawn from "
    "a rich 4-9 color non-0 palette by default), and every other row is an "
    "independent non-zero cyclic shift of the base (so it differs from row 0). "
    "Rule: replace every row with row 0 (broadcast the top row to all rows). "
    "The output is therefore w-wide and entirely row-0's pattern repeated; its "
    "diversity comes from the base sequence in row 0."
)

INVARIANTS = [
    "every row is a cyclic shift of one base color sequence",
    "row 0 is the base sequence (it alone determines the output)",
    "at least one non-row-0 row differs from row 0 (task is non-identity)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_same_rows", "single_row", "blank")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":      {"type": "int", "default": "rng 4..7", "valid": "2..16"},
    "grid_w":      {"type": "int", "default": "rng 6..10", "valid": "3..18"},
    "n_colors":    {"type": "int", "default": "rng 4..9", "valid": "2..9"},
    "period":      {"type": "int", "default": "not used; row0 is shuffled rich palette", "valid": "varied"},
    "row_shift":   {"type": "str", "default": "per-row cyclic shift", "valid": "varied"},
    "palette_kind":{"type": "str", "default": "rng helpful",
                    "valid": "default|warm|cool|varied"},
    "base_palette":{"type": "str", "default": "distinct non-0", "valid": "varied"},
    "position_bias":{"type": "str", "default": "cyclic_shift_rows",
                     "valid": "cyclic_shift_rows"},
    "texture":     {"type": "str", "default": "alias for palette_kind",
                    "valid": "default|warm|cool|varied|all_same_rows|single_row|blank"},
}


def _shift(seq, k):
    k %= len(seq)
    return seq[k:] + seq[:k]


def _palette_pool(kind):
    if kind == "warm":
        return [2, 3, 4, 6, 9]
    if kind == "cool":
        return [1, 5, 7, 8]
    if kind == "default":
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]
    return [1, 2, 3, 4, 5, 6, 7, 8, 9]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal samples: rich non-zero row 0, every later row is a non-identity cyclic shift."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    base = list(grid[0])
    if any(v == 0 for row in grid for v in row):
        errors.append("normal broadcast task should use a dense non-zero color grid")
    if len(set(base)) < 4:
        errors.append(f"row 0 uses only {len(set(base))} distinct colors; expected a rich canonical palette")

    def is_shift(row):
        return any(_shift(base, k) == list(row) for k in range(w))

    for r, row in enumerate(grid[1:], start=1):
        if not is_shift(row):
            errors.append(f"row {r} is not a cyclic shift of row 0")
        elif list(row) == base:
            errors.append(f"row {r} equals row 0; normal path should not be identity")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 3, 5)
        w = ctx.draw_int("grid_w", 6, 8)
        nc_lo, nc_hi = 4, 7
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 10, 16)
        nc_lo, nc_hi = 7, 9
    else:
        h = ctx.draw_int("grid_h", 4, 8)
        w = ctx.draw_int("grid_w", 7, 12)
        nc_lo, nc_hi = 6, 9
    rng = ctx.draw_rng("layout")

    n_colors = int(overrides.get("n_colors",
                                     ctx.draw_int("n_colors", nc_lo, min(nc_hi, 9))))
    n_colors = max(2, min(9, w, n_colors))
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = list(_palette_pool(palette_kind))
    if len(pool) < n_colors:
        pool += [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in pool]
    palette = rng.sample(pool, n_colors)

    # Build row 0 from the full selected palette so the output carries the
    # canonical high-palette signal (the previous random tile often used only
    # 2-3 colors and was flagged as distribution drift).
    base = palette[:]
    while len(base) < w:
        base.append(rng.choice(palette))
    rng.shuffle(base)

    g = full_grid(h, w, 0)
    g[0] = base[:]
    distinct_period = len(set(base))
    for r in range(1, h):
        # pick a shift that makes this row differ from row 0 when possible
        if distinct_period > 1:
            k = rng.randint(1, w - 1)
            row = _shift(base, k)
            tries = 0
            while row == base and tries < w:
                k = rng.randint(1, w - 1)
                row = _shift(base, k)
                tries += 1
        else:
            row = base[:]
        g[r] = row
    return g


def _draw_from_degenerate(name, rng):
    if name == "blank":
        return full_grid(4, 8, 0)
    if name == "single_row":
        return [[1, 2, 3, 4, 5, 1, 2, 3]]
    if name == "all_same_rows":
        base = [3, 1, 4, 1, 5, 2]
        return [base[:] for _ in range(5)]
    return full_grid(4, 8, 0)
