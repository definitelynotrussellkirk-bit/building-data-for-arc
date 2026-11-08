"""Generator for 41ace6b5.

Rule: nxn grid with row of 2s as divider; odd cols have alternating 8s;
rule normalizes alternating bars around the divider.

Combinatorial axes (8): n, sep_position, density_top, density_bottom,
density_2, palette_kind, anchor_corner, asymmetry_force.
Degenerates: no_divider, full_8s, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "982fefa4fff9"
VERSION = "2.0.1"
TASK_ID = "982fefa4fff9"
SUMMARY = (
    "Square n×n grid (n~7-11) with: "
    "(a) ONE FULL-ROW COLOR-2 (red) "
    "DIVIDER ROW at row sep "
    "(interior, 2..n-3) with random "
    "density (some cells = 2, "
    "others = 0); (b) COLOR-8 (cyan) "
    "CELLS scattered in ODD COLUMNS "
    "(c = 1, 3, 5, ...) above and "
    "below the divider at random "
    "densities. Rule (NORMALIZE "
    "ALTERNATING BARS): identify "
    "the DIVIDER ROW (the row with "
    "color-2 cells). For EACH ODD "
    "COLUMN, count the 8-cells "
    "ABOVE and BELOW the divider. "
    "NORMALIZE — paint a FULL "
    "ALTERNATING BAR pattern: paint "
    "every cell in odd columns "
    "(except divider row) with "
    "COLOR 8, then leave even "
    "columns 0. Or apply "
    "task-specific normalization "
    "based on the divider partition. "
    "Divider row stays color 2. "
    "Net: scattered odd-col 8s "
    "normalize into alternating "
    "vertical bars."
)

INVARIANTS = [
    "input is square nxn (n in [7, 11])",
    "exactly one row contains a 2 (the divider)",
    "the divider is interior (rows 2..n-3)",
    "odd columns have 8s above and below the divider",
]

SEP_POSITIONS = ("center", "upper", "lower", "rng")
DEGENERATE_TEXTURES = ("no_divider", "full_8s", "full_grid")
HELPFUL_TEXTURES = SEP_POSITIONS

AXES = {
    "n":              {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "sep_position":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(SEP_POSITIONS)},
    "density_top":    {"type": "float", "default": "rng 0.4..0.6", "valid": "0.2..0.8"},
    "density_bottom": {"type": "float", "default": "rng 0.4..0.6", "valid": "0.2..0.8"},
    "density_2":      {"type": "float", "default": "0.5", "valid": "0.3..0.7"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for sep_position",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 row contains a color-2 cell; that row is interior (not row 0 or last)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h = len(grid)
    rows_with_2 = [r for r in range(h) if any(v == 2 for v in grid[r])]
    if not rows_with_2:
        return []  # degenerate — allowed
    errs = []
    if len(rows_with_2) != 1:
        errs.append(f"expected exactly 1 row with color-2 divider; found {len(rows_with_2)}: {rows_with_2}")
    else:
        r = rows_with_2[0]
        if r == 0 or r == h - 1:
            errs.append(f"divider row {r} is at border (expected interior)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n_lo, n_hi = 5, 7
    elif difficulty == "hard":
        n_lo, n_hi = 11, 14
    else:
        n_lo, n_hi = 7, 11
    n = ctx.draw_int("n", n_lo, n_hi)
    sep_pos = (overrides.get("texture") or
               overrides.get("sep_position")
               or ctx.draw_choice("sep_position", list(SEP_POSITIONS)))
    if sep_pos == "center":
        sep = n // 2
    elif sep_pos == "upper":
        sep = max(2, n // 3)
    elif sep_pos == "lower":
        sep = min(n - 3, 2 * n // 3)
    else:
        sep = rng.randint(2, n - 3)
    sep = max(2, min(sep, n - 3))
    g = full_grid(n, n, 0)
    d2 = float(overrides.get("density_2", 0.5))
    for c in range(n):
        if rng.random() < d2:
            g[sep][c] = 2
    d_top = float(overrides.get("density_top",
                                rng.uniform(0.3, 0.7)))
    d_bot = float(overrides.get("density_bottom",
                                rng.uniform(0.3, 0.7)))
    for c in range(1, n, 2):
        for r in range(n):
            if r == sep:
                continue
            density = d_top if r < sep else d_bot
            if rng.random() < density:
                g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    n = 9
    g = full_grid(n, n, 0)
    if name == "no_divider":
        for c in range(1, n, 2):
            for r in range(n):
                if rng.random() < 0.5:
                    g[r][c] = 8
        return g
    if name == "full_8s":
        for r in range(n):
            for c in range(n):
                g[r][c] = 8
        return g
    if name == "full_grid":
        for r in range(n):
            for c in range(n):
                g[r][c] = 2
        return g
    return g
