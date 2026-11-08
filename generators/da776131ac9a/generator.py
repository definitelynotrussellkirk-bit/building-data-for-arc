"""Generator for puzzle 91413438.

Rule: N×N square; nz = non-bg count; z = N²-nz. Output is z*N × z*N
where each (br, bc) block is the input if (br*z + bc) < nz else bg.

Combinatorial axes (8): grid_n, nz, palette_size, palette_kind,
cell_layout, position_bias, anchor_corner, decoy_density.
Degenerates: empty_grid, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_cells
from puzzle_generators.helpers.indices import all_indices

GENERATOR_ID = "da776131ac9a"
VERSION = "1.2.0"
TASK_ID = "da776131ac9a"
SUMMARY = "Square grid; rule tiles z*N × z*N where z = N² - nz."

INVARIANTS = [
    "bg=0",
    "h == w (square)",
    "1 <= nz <= n² - 2 (so z>=2 and the rule is not identity)",
    "z*N <= 30 (output fits)",
]

CELL_LAYOUTS = ("scattered", "diagonal", "anti_diag", "row", "col",
                "corners", "blob")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "single_cell")
HELPFUL_TEXTURES = CELL_LAYOUTS

AXES = {
    "grid_n":         {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "nz":             {"type": "int", "default": "auto", "valid": "1..n²-1"},
    "palette_size":   {"type": "int", "default": "rng 1..3",
                       "valid": "1..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cell_layout":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CELL_LAYOUTS)},
    "position_bias":  {"type": "str", "default": "rng spread|center|corner",
                       "valid": "spread|center|corner"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "decoy_density":  {"type": "float", "default": "0", "valid": "0..0"},
    "texture":        {"type": "str", "default": "alias for cell_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        n_lo, n_hi = 2, 2
    elif difficulty == "hard":
        n_lo, n_hi = 4, 4
    else:
        n_lo, n_hi = 2, 4
    n = ctx.draw_int("grid_n", n_lo, n_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, rng)
    nz_lo = max(1, n * n - 30 // n)
    # z = n² - nz controls the output tiling.  z=1 makes the
    # canonical rule return a same-sized copy of the input (identity demo),
    # so the normal path keeps at least two zero cells.
    nz_hi = n * n - 2
    if nz_lo > nz_hi:
        return _draw_from_degenerate("single_cell", n, rng)
    nz = int(overrides.get("nz",
                           ctx.draw_int("nz", nz_lo, nz_hi)))
    nz = max(nz_lo, min(nz_hi, nz))
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 1,
                                               min(3, max(1, nz)))))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = list(range(1, 10))
    rng.shuffle(pool)
    palette = pool[:max(1, n_palette)]
    layout = (overrides.get("texture") or overrides.get("cell_layout")
              or ctx.draw_choice("cell_layout", list(CELL_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "corner"]))
    g = full_grid(n, n, 0)
    locs = _layout_cells(layout, n, bias, rng)[:nz]
    for loc in locs:
        paint_cells(g, [loc], rng.choice(palette))
    if bool(overrides.get("anchor_corner", False)):
        g[0][0] = palette[0]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default instances must be non-identity square tiling demos."""
    errors = []
    n = len(grid)
    if n == 0 or any(len(row) != n for row in grid):
        return ["grid is not a non-empty square"]
    if n < 2 or n > 4:
        errors.append(f"grid_n={n} outside canonical generator range 2..4")
    nz = sum(1 for row in grid for v in row if v != 0)
    area = n * n
    if not (1 <= nz <= area - 2):
        errors.append(f"nz={nz} must be in 1..n²-2 so z>=2 and output is not identity")
    z = area - nz
    if z * n > 30:
        errors.append(f"z*n={z*n} exceeds 30x30 output bound")
    if z <= 1:
        errors.append("z<=1 would make the rule an identity/same-size copy")
    return errors


def _layout_cells(layout, n, bias, rng):
    cells = list(all_indices(n, n))
    if layout == "diagonal":
        diag = [(k, k) for k in range(n)]
        rest = [c for c in cells if c not in diag]
        rng.shuffle(rest)
        return diag + rest
    if layout == "anti_diag":
        anti = [(k, n - 1 - k) for k in range(n)]
        rest = [c for c in cells if c not in anti]
        rng.shuffle(rest)
        return anti + rest
    if layout == "row":
        r = rng.randint(0, n - 1)
        chosen = [(r, c) for c in range(n)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "col":
        c = rng.randint(0, n - 1)
        chosen = [(r, c) for r in range(n)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "corners":
        corners = [(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)]
        rest = [c for c in cells if c not in corners]
        rng.shuffle(rest)
        return corners + rest
    if layout == "blob":
        cr, cc = rng.randint(0, n - 1), rng.randint(0, n - 1)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells
    rng.shuffle(cells)
    return cells


def _draw_from_degenerate(name, n, rng):
    g = full_grid(n, n, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "empty_grid":
        # nz = 0 → z = n² → output is huge (n³ × n³), violates ≤30
        # Force nz=1 instead
        g[0][0] = color
        return g
    if name == "full_grid":
        for r in range(n):
            for c in range(n):
                g[r][c] = color
        # nz = n² → z = 0 → output 0 × 0; force nz = n²-1
        g[n - 1][n - 1] = 0
        return g
    if name == "single_cell":
        g[n // 2][n // 2] = color
        return g
    return g
