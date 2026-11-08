"""Generator for arc_additional_puzzle_bank_volume16:E109.

2x2 windows with exactly three blue cells get a red missing corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_windows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_windows, full_2x2, mixed_color_window.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b1cf9bc21c63"
VERSION = "2.0.1"
TASK_ID = "b1cf9bc21c63"
SUMMARY = (
    "0-bg grid (h, w~7-12) "
    "with 2-5 BLUE(1) L-"
    "TROMINOES (3-cell L-"
    "shapes in 2×2 bboxes "
    "with one MISSING "
    "CORNER) placed at "
    "non-touching anchors "
    "(min Chebyshev "
    "distance 3 between "
    "anchors). EACH "
    "tromino occupies 3 "
    "of 4 cells in its "
    "2×2 bbox, with the "
    "missing corner "
    "randomly chosen "
    "from the 4 "
    "positions. Rule "
    "(FILL EACH 2×2 "
    "WINDOW WITH 3 BLUE + "
    "1 BG → COMPLETE WITH "
    "RED): scan EVERY 2×2 "
    "WINDOW in the grid. "
    "For EACH window "
    "containing EXACTLY 3 "
    "BLUE(1) CELLS AND 1 "
    "BG(0) CELL: PAINT "
    "the bg cell with "
    "COLOR 2 (red). "
    "Windows with other "
    "blue counts (0, 1, "
    "2, 4) stay unchanged. "
    "Net: each L-tromino "
    "gains a red dot in "
    "its missing corner, "
    "completing it to a "
    "blue-3 + red-1 2×2."
)

INVARIANTS = [
    "background is 0",
    "each active 2x2 window contains exactly three blue cells",
    "the fourth corner is empty before the rule runs",
    "active windows are separated so completions do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_windows", "full_2x2", "mixed_color_window")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_windows":      {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_2x2_windows",
                       "valid": "separated_2x2_windows"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 blue(1) L-tromino (2x2 window with exactly 3 blue cells and 1 bg cell)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    tromino_count = 0
    for r in range(h - 1):
        for c in range(w - 1):
            window = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
            blue = window.count(1)
            bg = window.count(0)
            if blue == 3 and bg == 1:
                tromino_count += 1
    if tromino_count < 1:
        errs.append(f"expected ≥1 2×2 window with 3 blue + 1 bg; found {tromino_count}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_windows = ctx.draw_int("n_windows", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_windows = ctx.draw_int("n_windows", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_windows = ctx.draw_int("n_windows", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_windows:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 1
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 1
        g[1][2] = 1
        g[2][1] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_windows":
        # blank → no 3-of-4 windows to complete
        return g
    if name == "full_2x2":
        # 2x2 already complete → no missing corner to fill
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 1
        return g
    if name == "mixed_color_window":
        # 2x2 with 2 blue + 1 other → not exactly 3 blue, rule won't fire
        g[1][1] = 1; g[1][2] = 1; g[2][1] = 4
        return g
    return g
