"""Generator for ce8d95cc.

Rule: grid with full nonzero rows and constant nonzero columns is
compressed by representative rows and columns.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
size.
Degenerates: no_lines, no_columns, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "174d775fd42f"
# 2.1.0: was a fully fixed 7x7 with lines at rows/cols 2,5 (shape-locked in
#        AND out). Now randomize grid size, the number (1-3) and positions of
#        horizontal divider rows AND vertical divider cols, each with its own
#        color (matches real train, which uses per-divider colors). Output
#        compressed-lattice shape now varies.
VERSION = "2.1.1"
TASK_ID = "174d775fd42f"
SUMMARY = (
    "Fixed 7×7 0-bg grid with: (a) TWO FULL "
    "HORIZONTAL DIVIDER ROWS at rows 2 and 5, "
    "each painted entirely in a SINGLE "
    "non-zero hline_color; (b) TWO VERTICAL "
    "DIVIDER COLUMNS at cols 2 and 5, each "
    "containing the same COLOR (v1 for col 2, "
    "v2 for col 5) at ALL non-divider rows "
    "(rows 0, 1, 3, 4, 6). hline_color, v1, "
    "and v2 are 3 distinct non-zero colors. "
    "Other cells are 0. Rule: DETECT the FULL "
    "NONZERO horizontal DIVIDER ROWS and the "
    "CONSTANT vertical DIVIDER COLUMNS. "
    "COMPRESS the 7×7 grid into a "
    "REPRESENTATIVE smaller grid: keep only "
    "ONE REPRESENTATIVE ROW per group between "
    "horizontal dividers, and ONE "
    "REPRESENTATIVE COL per group between "
    "vertical dividers. The dividers themselves "
    "are stripped; output is the "
    "intersection-cells matrix. Net: input is "
    "a divider-decorated grid; output is its "
    "compressed form (group representatives "
    "only)."
)

INVARIANTS = [
    "background is color 0",
    "horizontal divider rows are fully nonzero",
    "vertical divider columns have one nonzero color across non-divider rows",
    "row and col colors are distinct and non-zero",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_lines", "no_columns", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7", "valid": "7"},
    "grid_w":         {"type": "int", "default": "7", "valid": "7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "size":           {"type": "str", "default": "7x7", "valid": "7x7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one full nonzero row and at least one full nonzero col."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_lines", "no_columns", "full_grid"):
        return errs
    full_rows = [r for r in range(h) if all(grid[r][c] != 0 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] != 0 for r in range(h))]
    if not full_rows:
        errs.append("no full nonzero horizontal divider rows found")
    if not full_cols:
        errs.append("no full nonzero vertical divider columns found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(7, 9)
        n_h, n_v = rng.randint(1, 2), rng.randint(1, 2)
    elif difficulty == "hard":
        h = rng.randint(12, 18); w = rng.randint(12, 18)
        n_h, n_v = rng.randint(2, 3), rng.randint(2, 3)
    else:
        h = rng.randint(9, 14); w = rng.randint(9, 14)
        n_h, n_v = rng.randint(1, 3), rng.randint(1, 3)

    # Pick distinct interior divider rows/cols, keeping >=1 blank band
    # before/after/between dividers so the rule emits band representatives.
    # Interior positions chosen from 1..h-2 / 1..w-2 with >=2 gap between
    # consecutive dividers, and not touching row0/last (so leading/trailing
    # band rows exist).
    def _pick_dividers(n, lim):
        # candidate interior positions, leaving row 0 and row lim-1 as bands
        cands = list(range(2, lim - 2))
        rng.shuffle(cands)
        picked = []
        for p in sorted(cands):
            if all(abs(p - q) >= 2 for q in picked):
                picked.append(p)
            if len(picked) >= n:
                break
        return sorted(picked)

    h_rows = _pick_dividers(n_h, h)
    v_cols = _pick_dividers(n_v, w)
    # Guarantee at least one of each.
    if not h_rows:
        h_rows = [h // 2]
    if not v_cols:
        v_cols = [w // 2]

    # Distinct colors: one per horizontal divider + one per vertical divider.
    n_colors = len(h_rows) + len(v_cols)
    pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    colors = pool[:n_colors]
    h_colors = colors[:len(h_rows)]
    v_colors = colors[len(h_rows):]

    g = full_grid(h, w, 0)
    # Horizontal divider rows: fully nonzero (single color each).
    for hr, hc in zip(h_rows, h_colors):
        for c in range(w):
            g[hr][c] = hc
    # Vertical divider cols: single color across all NON-divider rows.
    for vc, vcolor in zip(v_cols, v_colors):
        for r in range(h):
            if r not in h_rows:
                g[r][vc] = vcolor
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_lines":
        for r in range(7):
            g[r][2] = 2
        return g
    if name == "no_columns":
        for r in (2, 5):
            for c in range(7):
                g[r][c] = 1
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 2
        return g
    return g
