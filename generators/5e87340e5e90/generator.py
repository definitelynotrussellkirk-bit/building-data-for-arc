"""Generator for puzzle 90347967.

Rule: rotate every non-bg cell 180° around a gray(5) pivot.

Combinatorial axes (8): grid_h/w, n_cells, palette_size, palette_kind,
pivot_position_kind, cell_layout, position_bias, asymmetry_force.
Degenerates: no_pivot, multiple_pivots, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5e87340e5e90"
VERSION = "2.1.0"
TASK_ID = "5e87340e5e90"
SUMMARY = (
    "0-bg grid (h, w~9-16) with: "
    "(a) ONE COLOR-5 (gray) "
    "PIVOT cell at position "
    "(cr, cc) — biased to "
    "center/off_center/edge/"
    "corner; (b) 4-10 SPARSE "
    "COLORED CELLS in 2-5 "
    "DISTINCT colors from a "
    "palette (warm/cool/broad/"
    "small), placed in cell "
    "layouts (scattered/blob/"
    "diag/row/col/checker) "
    "such that every cell's "
    "180° image around the "
    "pivot is in-bounds. Rule "
    "(ROTATE 180° AROUND GRAY "
    "PIVOT): identify the "
    "GRAY PIVOT (cr, cc). For "
    "EACH NON-BG, NON-PIVOT "
    "CELL at (r, c), COMPUTE "
    "its 180° MIRROR position "
    "(2cr - r, 2cc - c). "
    "PAINT the mirror "
    "position with the SAME "
    "COLOR. The pivot stays "
    "color 5. Originals stay. "
    "Net: each colored cell "
    "gets a same-color twin "
    "via 180° rotation around "
    "the gray pivot."
)

INVARIANTS = [
    "background is 0",
    "exactly one gray(5) cell (pivot)",
    ">=2 non-bg cells of other colors",
    "every non-bg cell's 180° image around pivot is in-bounds",
]

PIVOT_POSITIONS = ("center", "off_center", "edge", "corner")
CELL_LAYOUTS = ("scattered", "blob", "diag", "row", "col", "checker")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("no_pivot", "multiple_pivots", "no_cells")
HELPFUL_TEXTURES = PIVOT_POSITIONS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 9..16", "valid": "7..20"},
    "grid_w":             {"type": "int", "default": "rng 9..16", "valid": "7..20"},
    "n_cells":            {"type": "int", "default": "rng 4..10", "valid": "2..20"},
    "palette_size":       {"type": "int", "default": "rng 2..5", "valid": "1..7"},
    "palette_kind":       {"type": "str", "default": "rng helpful",
                           "valid": "warm|cool|broad|small"},
    "pivot_position_kind": {"type": "str", "default": "rng helpful",
                            "valid": "center|off_center|edge|corner"},
    "cell_layout":        {"type": "str", "default": "rng helpful",
                           "valid": "scattered|blob|diag|row|col|checker"},
    "asymmetry_force":    {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for pivot_position_kind",
                           "valid": "center|off_center|edge|corner|no_pivot|multiple_pivots|no_cells"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 7, 10
    elif difficulty == "hard":
        h_lo, h_hi = 14, 20
    else:
        h_lo, h_hi = 9, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_cells = int(overrides.get("n_cells",
                                ctx.draw_int("n_cells", 4, 10)))
    n_cells = max(2, min(20, n_cells))
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
                                  ctx.draw_int("palette_size", 2, 5)))
    palette = pool[:max(1, n_palette)]
    pivot_kind = (overrides.get("texture") or
                  overrides.get("pivot_position_kind")
                  or ctx.draw_choice("pivot_position_kind",
                                     list(PIVOT_POSITIONS)))
    cr, cc = _pick_pivot(pivot_kind, h, w, rng)
    g = full_grid(h, w, 0)
    g[cr][cc] = 5
    cell_layout = overrides.get("cell_layout",
                                ctx.draw_choice("cell_layout",
                                                list(CELL_LAYOUTS)))
    candidates = _layout_candidates(cell_layout, h, w, cr, cc, rng)
    placed = 0
    for r, c in candidates:
        if placed >= n_cells:
            break
        if g[r][c] != 0:
            continue
        nr, nc = 2 * cr - r, 2 * cc - c
        if not (0 <= nr < h and 0 <= nc < w):
            continue
        if (r, c) == (cr, cc) or (nr, nc) == (cr, cc):
            continue
        # The training input should contain ONE side of each 180° orbit.  If a
        # later source cell is placed on the mirror of an earlier source cell,
        # the canonical rule overwrites one color with the other and the demo
        # teaches a conflict instead of “copy this cell to its empty twin”.
        if g[nr][nc] != 0:
            continue
        g[r][c] = palette[placed % len(palette)]
        placed += 1
    if placed < 2:
        placed = _fill_safe_fallback_cells(g, cr, cc, palette, placed)
    return g


def _fill_safe_fallback_cells(g, cr, cc, palette, placed):
    """Add enough one-sided source cells to keep the default path teachable.

    The previous fallback painted the cells immediately above and below the
    pivot.  Those two cells are mirror images of each other, so the input
    already contained the answer and hid the 180°-copy operation.  This helper
    only selects cells whose mirror partner is still background.
    """
    h, w = len(g), len(g[0])
    for r in range(h):
        for c in range(w):
            if placed >= 2:
                return placed
            if g[r][c] != 0 or (r, c) == (cr, cc):
                continue
            nr, nc = 2 * cr - r, 2 * cc - c
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if (nr, nc) == (cr, cc) or (nr, nc) == (r, c):
                continue
            if g[nr][nc] != 0:
                continue
            g[r][c] = palette[placed % len(palette)]
            placed += 1
    return placed


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the normal training distribution."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    msgs = []
    pivots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if len(pivots) != 1:
        return [f"expected exactly one gray pivot, found {len(pivots)}"]
    cr, cc = pivots[0]
    sources = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    if len(sources) < 2:
        msgs.append("expected at least two non-pivot source cells")
    for r, c, v in sources:
        nr, nc = 2 * cr - r, 2 * cc - c
        if not (0 <= nr < h and 0 <= nc < w):
            msgs.append("source mirror is out of bounds")
            continue
        if (nr, nc) == (r, c):
            msgs.append("source lies on the pivot center orbit")
        elif grid[nr][nc] != 0:
            msgs.append("source mirror cell is pre-filled")
    return sorted(set(msgs))


def _pick_pivot(kind, h, w, rng):
    if kind == "center":
        return h // 2, w // 2
    if kind == "off_center":
        return rng.randint(h // 3, 2 * h // 3), rng.randint(w // 3, 2 * w // 3)
    if kind == "edge":
        return rng.choice([1, h - 2]), w // 2
    if kind == "corner":
        return 2, 2
    return h // 2, w // 2


def _layout_candidates(layout, h, w, cr, cc, rng):
    cells = [(r, c) for r in range(h) for c in range(w)]
    if layout == "blob":
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells
    if layout == "diag":
        diag = [(k, k) for k in range(min(h, w))]
        rest = [c for c in cells if c not in diag]
        rng.shuffle(rest)
        return diag + rest
    if layout == "row":
        r = max(0, cr - 1)
        chosen = [(r, c) for c in range(w)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "col":
        c = max(0, cc - 1)
        chosen = [(r, c) for r in range(h)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "checker":
        even = [(r, c) for (r, c) in cells if (r + c) % 2 == 0]
        odd = [(r, c) for (r, c) in cells if (r + c) % 2 != 0]
        rng.shuffle(even); rng.shuffle(odd)
        return even + odd
    rng.shuffle(cells)
    return cells


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_pivot":
        g[1][1] = rng.choice([1, 2, 3, 4])
        g[h - 2][w - 2] = rng.choice([6, 7, 8, 9])
        return g
    if name == "multiple_pivots":
        g[1][1] = 5; g[h - 2][w - 2] = 5
        g[2][2] = 1
        return g
    if name == "no_cells":
        g[h // 2][w // 2] = 5
        return g
    return g
