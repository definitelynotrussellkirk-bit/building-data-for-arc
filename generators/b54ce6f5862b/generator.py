"""Generator for 25c199f5.

Rule: 3 horizontal sections separated by 6-cols; rule stacks non-blank
rows right-to-left into single output of section width.

Combinatorial axes (8): grid_h, section_w, n_marks_per_section,
palette_kind, anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_dividers, no_marks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b54ce6f5862b"
VERSION = "2.0.1"
TASK_ID = "b54ce6f5862b"
SUMMARY = (
    "COLOR-7 (orange) background grid "
    "(h ∈ 5-7, w = 3*sw + 2 with sw ∈ "
    "5-6) split into 3 SECTIONS of "
    "WIDTH sw separated by 2 FULL-"
    "HEIGHT COLOR-6 (MAGENTA) DIVIDER "
    "COLUMNS at cols div1=sw and "
    "div2=2*sw+1. WITHIN EACH SECTION: "
    "N_MARKS ∈ 1-5 COLOR-1 (BLUE) "
    "CELLS scattered at random "
    "positions; PLUS ONE COLOR-5 "
    "(GRAY) CELL placed in exactly "
    "ONE of the 3 sections at a "
    "random row/col. Rule (RIGHT-TO-"
    "LEFT STACK ALL NON-BLANK ROWS "
    "FROM EACH SECTION INTO A SINGLE "
    "OUTPUT GRID OF SECTION WIDTH; "
    "PER DEMOS: OVERLAY/COMBINE "
    "USING THE COLOR-5 MARKER AS "
    "ANCHOR): IDENTIFY the 3 SECTIONS "
    "(separated by 6-dividers). For "
    "EACH SECTION, EXTRACT its non-"
    "blank ROWS (rows containing any "
    "non-7 cells). STACK them right-"
    "to-left into a single output of "
    "DIMENSIONS h × sw, combining "
    "the cell values per a fixed "
    "stacking rule (e.g., last-wins, "
    "majority, or per-position OR). "
    "The single color-5 cell may "
    "act as a special marker. Net: "
    "3 sections collapse into 1 "
    "by stacking; the unique 5 "
    "may anchor the layout."
)

INVARIANTS = [
    "h in 5..7, sw in 5..6 -> w = 3*sw + 2",
    "exactly 2 full-height columns of 6 (the dividers)",
    "rest is 7-bg with scattered 1-cells and a single 5-cell",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_dividers", "no_marks", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "section_w":      {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "n_marks_per_section":{"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES)},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=7; exactly 2 full-height magenta(6) separator columns;
    ≥1 mark cell of color 1 (marker color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Check for exactly 2 full-height magenta(6) columns
    mag_cols = [c for c in range(w) if all(grid[r][c] == 6 for r in range(h))]
    if len(mag_cols) != 2:
        errs.append(f"expected exactly 2 full-height magenta(6) separator columns; found {mag_cols}")
    # Check for ≥1 mark (color 1) in the grid
    mark_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not mark_cells:
        errs.append("expected ≥1 color-1 mark cell; found none")
    # Check bg=7 exists
    seven_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 7)
    if seven_count == 0:
        errs.append("expected bg=7 cells; found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, sw_lo, sw_hi = 4, 5, 4, 5
        nm_lo, nm_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, sw_lo, sw_hi = 7, 10, 6, 7
        nm_lo, nm_hi = 2, 5
    else:
        h_lo, h_hi, sw_lo, sw_hi = 5, 7, 5, 6
        nm_lo, nm_hi = 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    sw = ctx.draw_int("section_w", sw_lo, sw_hi)
    w = 3 * sw + 2
    g = [[7] * w for _ in range(h)]
    div1 = sw
    div2 = 2 * sw + 1
    for r in range(h):
        g[r][div1] = 6
        g[r][div2] = 6
    section_starts = [0, div1 + 1, div2 + 1]
    n_marks = int(overrides.get("n_marks_per_section",
                                rng.randint(nm_lo, nm_hi)))
    n_marks = max(1, min(5, n_marks))
    for s in section_starts:
        for _ in range(n_marks):
            r = rng.randint(0, h - 1)
            c = rng.randint(s, s + sw - 1)
            if g[r][c] == 7:
                g[r][c] = 1
    s = rng.choice(section_starts)
    for _ in range(20):
        r = rng.randint(0, h - 1); c = rng.randint(s, s + sw - 1)
        if g[r][c] == 7:
            g[r][c] = 5
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 17
    g = [[7] * w for _ in range(h)]
    if name == "no_dividers":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.1:
                    g[r][c] = 1
        g[3][8] = 5
        return g
    if name == "no_marks":
        for r in range(h):
            g[r][5] = 6
            g[r][11] = 6
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
