"""Generator for arc_puzzle_bank_21_set18_s:S18_E5.

Rule: color 2 closes across rows while color 3 closes down columns.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_color_2, no_color_3, no_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26a885b7ba49"
VERSION = "1.1.2"
TASK_ID = "26a885b7ba49"
SUMMARY = "Color 2 closes across rows while color 3 closes down columns."

INVARIANTS = [
    "color 2 cells define horizontal spans",
    "color 3 cells define vertical spans",
    "vertical color-3 closure overwrites row closure where they overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_color_2", "no_color_3", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "7..9"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "7..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "row_2_col_3",
                       "valid": "row_2_col_3"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _span_overlap_cells(grid):
    """Cells where an inferred color-2 row span crosses a color-3 column span."""
    h, w = len(grid), len(grid[0])
    row_spans = []
    for r in range(h):
        cs = [c for c in range(w) if grid[r][c] == 2]
        if len(cs) >= 2:
            row_spans.append((r, min(cs), max(cs)))
    col_spans = []
    for c in range(w):
        rs = [r for r in range(h) if grid[r][c] == 3]
        if len(rs) >= 2:
            col_spans.append((c, min(rs), max(rs)))
    return [
        (r, c)
        for r, c1, c2 in row_spans
        for c, r1, r2 in col_spans
        if c1 <= c <= c2 and r1 <= r <= r2
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for row color-2 spans and column color-3 spans."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w)}
    extra = colors - {0, 2, 3}
    if extra:
        errors.append(f"unexpected colors present: {sorted(extra)}")
    row_counts = [sum(1 for c in range(w) if grid[r][c] == 2) for r in range(h)]
    col_counts = [sum(1 for r in range(h) if grid[r][c] == 3) for c in range(w)]
    rows = [r for r, n in enumerate(row_counts) if n == 2]
    cols = [c for c, n in enumerate(col_counts) if n == 2]
    if len(rows) < 2:
        errors.append(f"expected at least two rows with exactly two color-2 endpoints, found {rows}")
    if len(cols) < 2:
        errors.append(f"expected at least two columns with exactly two color-3 endpoints, found {cols}")
    bad_rows = [(r, n) for r, n in enumerate(row_counts) if n not in (0, 2)]
    bad_cols = [(c, n) for c, n in enumerate(col_counts) if n not in (0, 2)]
    if bad_rows:
        errors.append(f"malformed color-2 row endpoint counts: {bad_rows[:5]}")
    if bad_cols:
        errors.append(f"malformed color-3 column endpoint counts: {bad_cols[:5]}")
    if rows and cols and not _span_overlap_cells(grid):
        errors.append("row spans and column spans never cross; overlap-overwrite branch hidden")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    rng = ctx.draw_rng("layout")
    for _attempt in range(120):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        for r in rng.sample(range(h), 2):
            c1 = rng.randint(0, w - 5)
            c2 = rng.randint(c1 + 3, w - 1)
            g[r][c1] = 2
            g[r][c2] = 2
            used.update({(r, c1), (r, c2)})
        cols = rng.sample(range(w), 2)
        ok = True
        for c in cols:
            r1 = rng.randint(0, h - 5)
            r2 = rng.randint(r1 + 3, h - 1)
            placed_rows = []
            for r in (r1, r2):
                candidates = [r] + [(r + delta) % h for delta in (1, -1, 2, -2)]
                placed = None
                for rr in candidates:
                    if (rr, c) not in used and g[rr][c] == 0:
                        placed = rr
                        break
                if placed is None:
                    ok = False
                    break
                placed_rows.append(placed)
            if not ok or len(set(placed_rows)) != 2:
                ok = False
                break
            for rr in placed_rows:
                g[rr][c] = 3
                used.add((rr, c))
        if ok and _span_overlap_cells(g):
            return g
    raise ValueError("could not place row/column spans with an overlap")


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_color_2":
        # only column closures → no row spans
        g[1][3] = 3; g[5][3] = 3
        g[1][6] = 3; g[5][6] = 3
        return g
    if name == "no_color_3":
        # only row closures → no column spans, no overlap-overwrite case
        g[2][1] = 2; g[2][5] = 2
        g[5][2] = 2; g[5][7] = 2
        return g
    if name == "no_overlap":
        # spans in disjoint regions → overlap rule never triggers
        g[1][1] = 2; g[1][3] = 2
        g[5][5] = 3; g[7][5] = 3
        return g
    return g
