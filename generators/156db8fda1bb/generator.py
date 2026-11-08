"""Generator for aa18de87.

Rule: for each row, find leftmost & rightmost non-bg cells; fill all 0s
strictly between them with 2.

Combinatorial axes (8): grid_h/w, color, n_active_rows,
endpoint_separation, intermediate_density, palette_size,
position_bias, asymmetry.
Degenerates: empty_rows, full_rows, single_endpoint_per_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "156db8fda1bb"
VERSION = "2.0.1"
TASK_ID = "156db8fda1bb"
SUMMARY = (
    "0-bg grid (h~5-10, w~"
    "8-14) with 3+ "
    "ACTIVE ROWS each "
    "containing 2-many "
    "NON-BG CELLS in a "
    "SINGLE color C "
    "(from {1..9}\\{0, 2})"
    " arranged via one "
    "of 5 ROW PATTERNS "
    "(scattered/"
    "endpoints_only/"
    "ascending/many_"
    "cells/alternating). "
    "Endpoint separation "
    "(near/medium/far) "
    "and intermediate "
    "density (0..0.4) "
    "vary. Leftmost and "
    "rightmost non-bg "
    "cells in each "
    "active row are ≥2 "
    "cols apart. Rule "
    "(FILL BETWEEN ROW "
    "EXTREMES WITH 2): "
    "For EACH ROW r: "
    "find the LEFTMOST "
    "(c_min) and "
    "RIGHTMOST (c_max) "
    "non-bg cells. For "
    "EACH cell (r, c) "
    "with c_min < c < "
    "c_max AND g[r][c] "
    "== 0: PAINT "
    "g[r][c] = 2 (red). "
    "Existing non-bg "
    "cells stay. Net: "
    "each row gets red "
    "interior filling "
    "between its "
    "extreme non-bg "
    "cells."
)

INVARIANTS = [
    "background is 0",
    ">=3 rows have >=2 non-zero cells with separation >=2",
    "color used is not 2 (rule fills with 2)",
    "row's leftmost and rightmost non-bg cells differ by >=2 cols",
]

ROW_PATTERNS = ("scattered", "endpoints_only", "ascending", "many_cells",
                "alternating")
DEGENERATE_TEXTURES = ("empty_rows", "full_rows", "single_endpoint_per_row")
HELPFUL_TEXTURES = ROW_PATTERNS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 5..10", "valid": "4..14"},
    "grid_w":              {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "color":               {"type": "color", "default": "rng (≠0,2)",
                            "valid": "1..9 (≠2)"},
    "n_active_rows":       {"type": "int", "default": "rng 3..h", "valid": "1..h"},
    "endpoint_separation": {"type": "str", "default": "rng near|medium|far",
                            "valid": "near|medium|far"},
    "intermediate_density": {"type": "float", "default": "rng 0..0.4",
                             "valid": "0..0.7"},
    "row_pattern":         {"type": "str", "default": "rng helpful",
                            "valid": "scattered|endpoints_only|ascending|many_cells|alternating"},
    "palette_size":        {"type": "int", "default": "1", "valid": "1..3"},
    "texture":             {"type": "str", "default": "alias for row_pattern",
                            "valid": "scattered|endpoints_only|ascending|many_cells|alternating|empty_rows|full_rows|single_endpoint_per_row"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify default demos visibly exercise the row-gap fill rule."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if any(v == 2 for row in grid for v in row):
        errors.append("input already contains fill color 2")
    active_rows = 0
    fillable_rows = 0
    for r in range(h):
        nz = [c for c in range(w) if grid[r][c] != 0]
        if len(nz) >= 2 and max(nz) - min(nz) >= 2:
            active_rows += 1
            if any(grid[r][c] == 0 for c in range(min(nz) + 1, max(nz))):
                fillable_rows += 1
    if active_rows < 3:
        errors.append(f"expected at least 3 active rows, found {active_rows}")
    if fillable_rows < 3:
        errors.append(f"expected at least 3 rows with a zero gap to fill, found {fillable_rows}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 6, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 14, 12, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 10, 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    color = int(overrides.get("color",
                              ctx.draw_color("color", exclude={0, 2})))
    n_palette = int(overrides.get("palette_size", 1))
    palette_pool = [c for c in range(1, 10) if c not in (0, 2, color)]
    rng.shuffle(palette_pool)
    palette = [color] + palette_pool[:max(0, n_palette - 1)]
    n_active = int(overrides.get("n_active_rows",
                                 ctx.draw_int("n_active_rows", 3,
                                              max(3, h - 1))))
    n_active = max(3, min(h, n_active))
    pattern = (overrides.get("texture") or overrides.get("row_pattern")
               or ctx.draw_choice("row_pattern", list(ROW_PATTERNS)))
    sep = overrides.get("endpoint_separation",
                        ctx.draw_choice("endpoint_separation",
                                        ["near", "medium", "far"]))
    density = float(overrides.get("intermediate_density",
                                  ctx.draw_rng("intermediate_density")
                                  .uniform(0.0, 0.4)))
    g = full_grid(h, w, 0)
    rows = list(range(h))
    rng.shuffle(rows)
    chosen_rows = rows[:n_active]
    for r in chosen_rows:
        _fill_row(g, r, w, pattern, sep, density, palette, rng)
    for r in chosen_rows:
        if not _row_has_fillable_gap(g[r]):
            _force_fillable_row(g, r, w, palette, rng)
    return g


def _row_has_fillable_gap(row):
    nz = [c for c, v in enumerate(row) if v != 0]
    return (len(nz) >= 2
            and nz[-1] - nz[0] >= 2
            and any(row[c] == 0 for c in range(nz[0] + 1, nz[-1])))


def _force_fillable_row(g, r, w, palette, rng):
    for c in range(w):
        g[r][c] = 0
    c1 = rng.randint(0, w - 3)
    c2 = rng.randint(c1 + 2, w - 1)
    g[r][c1] = rng.choice(palette)
    g[r][c2] = rng.choice(palette)


def _fill_row(g, r, w, pattern, sep, density, palette, rng):
    target_sep = {"near": 3, "medium": w // 2, "far": w - 2}[sep]
    target_sep = max(2, min(w - 1, target_sep))
    if pattern == "endpoints_only":
        c1 = rng.randint(0, max(0, w - target_sep - 1))
        c2 = c1 + target_sep
        if c2 < w:
            g[r][c1] = rng.choice(palette)
            g[r][c2] = rng.choice(palette)
        return
    if pattern == "ascending":
        c1 = 0
        c2 = max(target_sep, w - 1)
        if c2 < w:
            g[r][c1] = rng.choice(palette)
            g[r][c2] = rng.choice(palette)
        return
    if pattern == "alternating":
        for c in range(0, w, 2):
            if rng.random() < density + 0.3:
                g[r][c] = rng.choice(palette)
        return
    if pattern == "many_cells":
        n = rng.randint(3, max(3, w // 2))
        cs = sorted(rng.sample(range(w), min(n, w)))
        if len(cs) >= 2 and cs[-1] - cs[0] >= 2:
            for c in cs:
                g[r][c] = rng.choice(palette)
        return
    n = rng.randint(2, 3)
    cs = sorted(rng.sample(range(w), min(n, w)))
    if cs[-1] - cs[0] >= 2:
        for c in cs:
            g[r][c] = rng.choice(palette)
        for c in range(cs[0] + 1, cs[-1]):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 3, 4, 5, 6, 7, 8, 9])
    if name == "empty_rows":
        return g
    if name == "full_rows":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_endpoint_per_row":
        for r in range(h):
            g[r][rng.randint(0, w - 1)] = color
        return g
    return g
