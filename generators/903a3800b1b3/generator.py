"""Generator for puzzle ba26e723.

Rule: `(rule! (lambda (g) (cellmap g (r c v) (if (and (= v 4) (zero? (mod c 3))) 6 v))))`.
Yellow(4) cells at columns where col % 3 == 0 become magenta(6); other
cells unchanged.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * bg_color               — bg color (≠ 4, ≠ 6)
  * yellow_count           — total yellow cells planted
  * yellow_layout          — random / cluster / column / row / diagonal /
                             scattered
  * trigger_col_density    — fraction of yellows that fall on col%3==0
                             (must be ≥1; 1.0 means all yellows trigger,
                             0.5 means half)
  * decor_palette_size     — extra non-yellow non-magenta colors
  * caller-opt-in degenerates: no_yellows, only_trigger_cols
                               (output ambiguous), single_yellow
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "903a3800b1b3"
VERSION = "2.0.1"
TASK_ID = "903a3800b1b3"
SUMMARY = (
    "Grid (h×w, h=3..15, w=6..15) with bg color ∉ {4, 6} and "
    "scattered color-4 (yellow) cells in various layouts "
    "(random, cluster, column, row, diagonal, scattered). "
    "Optional decor cells in other colors. At least one yellow "
    "cell sits at a column where col % 3 == 0. Rule: for each "
    "cell, if color == 4 AND column index % 3 == 0, recolor to "
    "6 (magenta). Otherwise keep original. Output: yellows in "
    "trigger columns become magenta; yellows elsewhere stay 4."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "bg color ∉ {4, 6}",
    "≥1 yellow(4) cell at a column where col % 3 == 0",
    "≥1 yellow at a non-trigger col (so rule's selectivity is visible)",
]

YELLOW_LAYOUTS = (
    "random", "cluster", "column", "row", "diagonal", "scattered",
)
DEGENERATE_TEXTURES = ("no_yellows", "only_trigger_cols", "single_yellow")
HELPFUL_TEXTURES = YELLOW_LAYOUTS

AXES = {
    "grid_h":              {"type": "int",   "default": "rng 3..15", "valid": "3..18"},
    "grid_w":              {"type": "int",   "default": "rng 6..15", "valid": "6..18"},
    "bg_color":            {"type": "color", "default": "rng (≠4,6)", "valid": "0..9 (≠4,6)"},
    "yellow_count":        {"type": "int",   "default": "rng 3..h*w/3", "valid": "1..h*w"},
    "yellow_layout":       {"type": "str",   "default": "rng helpful",
                            "valid": "|".join(YELLOW_LAYOUTS)},
    "trigger_col_density": {"type": "float", "default": "rng 0.3..0.8",
                            "valid": "0.1..1.0"},
    "decor_palette_size":  {"type": "int",   "default": "rng 0..3", "valid": "0..6"},
    "texture":             {"type": "str",   "default": "alias for yellow_layout",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 yellow(4) at col%3==0 and >=1 yellow at col%3!=0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_yellows", "only_trigger_cols", "single_yellow"):
        return errs
    trigger = any(grid[r][c] == 4 and c % 3 == 0 for r in range(h) for c in range(w))
    non_trigger = any(grid[r][c] == 4 and c % 3 != 0 for r in range(h) for c in range(w))
    if not trigger:
        errs.append("no yellow(4) cell at col%3==0 (trigger)")
    if not non_trigger:
        errs.append("no yellow(4) cell at col%3!=0 (non-trigger)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 3, 7, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 15, 12, 15
    else:
        h_lo, h_hi, w_lo, w_hi = 3, 15, 6, 15

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    bg = int(overrides.get("bg_color",
                           ctx.draw_color("bg_color", exclude={4, 6})))
    layout = (overrides.get("texture")
              or overrides.get("yellow_layout")
              or ctx.draw_choice("yellow_layout", list(YELLOW_LAYOUTS)))
    n_yellows = int(overrides.get(
        "yellow_count",
        ctx.draw_int("yellow_count", 3, max(3, (h * w) // 3))))
    trigger_density = float(overrides.get(
        "trigger_col_density",
        ctx.draw_rng("trigger_col_density").uniform(0.3, 0.8)))
    n_decor = int(overrides.get("decor_palette_size",
                                ctx.draw_int("decor_palette_size", 0, 3)))

    g = full_grid(h, w, bg)
    decor_palette = [c for c in range(10) if c not in {bg, 4, 6}]
    rng.shuffle(decor_palette)
    decor_palette = decor_palette[:max(0, n_decor)]
    if decor_palette:
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.20:
                    g[r][c] = rng.choice(decor_palette)

    trigger_cols = [c for c in range(w) if c % 3 == 0]
    other_cols = [c for c in range(w) if c % 3 != 0]
    n_trigger = max(1, int(n_yellows * trigger_density))
    n_other = max(0, n_yellows - n_trigger)

    placed = 0
    target_cells = _yellow_layout_cells(layout, h, w, n_yellows, rng)
    used = set()
    # Place yellows in trigger cols first (≥1 must land in col%3==0).
    trigger_candidates = [(r, c) for (r, c) in target_cells if c in trigger_cols]
    other_candidates = [(r, c) for (r, c) in target_cells if c in other_cols]
    rng.shuffle(trigger_candidates)
    rng.shuffle(other_candidates)
    for (r, c) in trigger_candidates[:n_trigger]:
        g[r][c] = 4; used.add((r, c)); placed += 1
    for (r, c) in other_candidates[:n_other]:
        if (r, c) not in used:
            g[r][c] = 4; placed += 1

    if not any(g[r][c] == 4 and (c % 3 == 0)
               for r in range(h) for c in range(w)):
        target_col = rng.choice(trigger_cols) if trigger_cols else 0
        target_row = rng.randint(0, h - 1)
        g[target_row][target_col] = 4
    return g


def _yellow_layout_cells(layout, h, w, n, rng):
    cells = [(r, c) for r in range(h) for c in range(w)]
    if layout == "cluster":
        cr = rng.randint(0, h - 1); cc = rng.randint(0, w - 1)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells[:n * 2]  # extra so trigger split has options
    if layout == "column":
        c = rng.randint(0, w - 1)
        col = [(r, c) for r in range(h)]
        return col + cells[:n - len(col)]
    if layout == "row":
        r = rng.randint(0, h - 1)
        row = [(r, c) for c in range(w)]
        return row + cells[:n - len(row)]
    if layout == "diagonal":
        diag = [(k, k) for k in range(min(h, w))]
        return diag + cells[:n - len(diag)]
    if layout == "scattered":
        scat = [(r, c) for r in range(0, h, 2) for c in range(0, w, 2)]
        rng.shuffle(scat)
        return scat[:n * 2]
    rng.shuffle(cells)
    return cells[:n * 2]


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the col%3-trigger signal collapses.

    no_yellows         — no 4s; rule is no-op (output == input).
    only_trigger_cols  — every yellow lands in col%3==0 → output looks
                          like "all yellows became magenta."
    single_yellow      — one yellow in a trigger col; minimal signal.
    """
    bg = rng.choice([0, 1, 2, 3, 5, 7, 8, 9])
    g = full_grid(h, w, bg)
    if name == "no_yellows":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.3:
                    g[r][c] = rng.choice([1, 2, 3, 5, 7, 8, 9])
        return g
    if name == "only_trigger_cols":
        cols = [c for c in range(w) if c % 3 == 0]
        for c in cols:
            for r in range(h):
                if rng.random() < 0.5:
                    g[r][c] = 4
        return g
    if name == "single_yellow":
        cols = [c for c in range(w) if c % 3 == 0]
        if cols:
            g[rng.randint(0, h - 1)][rng.choice(cols)] = 4
        return g
    return g
