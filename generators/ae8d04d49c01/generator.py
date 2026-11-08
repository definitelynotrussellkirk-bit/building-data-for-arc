"""Generator for 6a980be1.

Rule: a sparse spec is expanded into a full periodic stripe pattern.
The top-left cell holds the FILL color fc. Full green(3) interior rows
(or cols) set the orientation and become full 3-lines. A red(2) row (or
col) shows >=2 periodic red blocks; the rule reads the first block's
width and the period, then tiles the whole grid: stripe columns (in the
red phase) get fc, the red rows get 2 inside stripes, green rows become
full 3, everything else 0.

This generator emits the sparse spec: corner fc, 1-2 full green rows, and
one red row carrying periodic red blocks; the rule fills the rest.

Combinatorial axes: orientation (h/v), grid size, fill color, the green
row(s), the red row, the block width and period.
Degenerates: no_bars, no_stripe, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ae8d04d49c01"
VERSION = "2.0.1"  # diversity: random size/orientation/positions/period/width/color (was fixed 11x12 ~13)
TASK_ID = "ae8d04d49c01"
SUMMARY = (
    "0-bg grid (size varies). A FILL color fc at (0,0); 1-2 full green(3) "
    "interior rows; one red(2) row carrying >=2 periodic red blocks (width "
    "w, period p). Rule: read the block width + period and tile the whole "
    "grid into a periodic stripe pattern -- stripe columns filled with fc, "
    "red rows -> 2 inside stripes, green rows -> full 3, else 0. Built "
    "horizontally then optionally transposed. The orientation, grid size, "
    "fill color, green/red positions, block width and period all vary "
    "freely (was a fixed 11x12 layout, ~13 distinct)."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the top-left cell is the (non-{0,2,3}) fill color",
    "full green(3) rows (or cols after transpose) set the orientation",
    "one red(2) line carries >=2 periodic blocks giving width + period",
]

ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_bars", "no_stripe", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..22"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "horizontal|vertical"},
    "n_green":        {"type": "int", "default": "varies", "valid": "1..2"},
    "block_width":    {"type": "int", "default": "varies", "valid": "1..3"},
    "period":         {"type": "int", "default": "varies", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "frame_color":    {"type": "color", "default": "rng !{0,2,3}", "valid": "1|4|5|6|7|8|9"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "horizontal|vertical|no_bars|no_stripe|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) is fill color (not 0, 2, 3), color-3 present, color-2 present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_bars", "no_stripe", "full_grid"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    fc = grid[0][0]
    if fc in (0, 2, 3):
        errs.append(f"top-left fill color {fc} must not be 0, 2, or 3")
    has_3 = any(grid[r][c] == 3 for r in range(h) for c in range(w))
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_3:
        errs.append("no color-3 (green) orientation rows found")
    if not has_2:
        errs.append("no color-2 (red) stripe-spec row found")
    return errs


def _transpose(g):
    return [list(row) for row in zip(*g)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS
                   else None) or overrides.get("orientation") or \
        rng.choice(list(ORIENTATIONS))
    fc = rng.choice([1, 4, 5, 6, 7, 8, 9])

    if difficulty == "easy":
        hr, wr, gr, rwr, gpr = (8, 11), (9, 13), (1, 1), (1, 2), (1, 2)
    elif difficulty == "hard":
        hr, wr, gr, rwr, gpr = (11, 18), (13, 22), (1, 2), (1, 3), (2, 3)
    else:
        hr, wr, gr, rwr, gpr = (9, 14), (11, 17), (1, 2), (1, 3), (1, 3)

    h = rng.randint(*hr); w = rng.randint(*wr)
    rw = rng.randint(*rwr); period = rw + rng.randint(*gpr)
    # need >=2 blocks inside interior cols [1, w-2]: rc1 + period <= w-2
    if w - 2 - period < 1:
        period = max(2, w - 3)
    rc1 = rng.randint(1, max(1, w - 2 - period))

    n_green = rng.randint(*gr)
    rows = rng.sample(range(1, h - 1), min(n_green + 1, h - 2))
    green_rows = rows[:n_green]
    red_row = rows[n_green]

    g = full_grid(h, w, 0)
    g[0][0] = fc
    for gr_ in green_rows:
        for c in range(1, w - 1):
            g[gr_][c] = 3
    for c in range(1, w - 1):
        if c >= rc1 and ((c - rc1) % period) < rw:
            g[red_row][c] = 2

    if orientation == "vertical":
        g = _transpose(g)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 12, 0)
    if name == "no_bars":
        g[0][0] = 1
        return g
    if name == "no_stripe":
        for c in range(11):
            g[5][c] = 3
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(12):
                g[r][c] = 3
        return g
    return g
