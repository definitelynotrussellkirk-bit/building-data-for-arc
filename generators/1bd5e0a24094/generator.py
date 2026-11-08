"""Generator for puzzle ad7e01d0.

Rule: output is (ih*ih × iw*iw). For each meta-cell (r/ih, c/iw), if
input has 5 there, output's local cell is the input value; else 0.

Combinatorial axes (8): grid_h/w, n_fives, fg_color, fg_density,
five_layout, fg_layout, palette_size, position_bias.
Degenerates: no_fives, all_fives, all_fg.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1bd5e0a24094"
VERSION = "1.1.1"
TASK_ID = "1bd5e0a24094"
SUMMARY = "Small grid with 5s; rule meta-self-tiles where 5s appear."

INVARIANTS = [
    "ih, iw in [3, 5]",
    ">=1 cell of color 5 in input (so meta-tiling has output)",
    ">=1 cell of a non-5, non-0 color (so tile content is visible)",
    "ih*ih and iw*iw <= 25 (output fits ARC limit)",
]

FIVE_LAYOUTS = ("scattered", "diagonal", "row", "col", "corners", "center")
FG_LAYOUTS = ("scattered", "diagonal", "blob", "stripes", "checker", "frame")
DEGENERATE_TEXTURES = ("no_fives", "all_fives", "all_fg")
HELPFUL_TEXTURES = FIVE_LAYOUTS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "grid_w":         {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "n_fives":        {"type": "int", "default": "rng 2..4", "valid": "1..15"},
    "fg_color":       {"type": "color", "default": "rng (≠0,5)",
                       "valid": "1..9 (≠5)"},
    "five_layout":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(FIVE_LAYOUTS)},
    "fg_layout":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(FG_LAYOUTS)},
    "fg_density":     {"type": "float", "default": "rng 0.3..0.6",
                       "valid": "0..1"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for five_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 3
    elif difficulty == "hard":
        h_lo, h_hi = 5, 5
    else:
        h_lo, h_hi = 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_fives = int(overrides.get("n_fives", ctx.draw_int("n_fives", 2, 4)))
    n_fives = max(1, min(h * w - 1, n_fives))
    fg_color = int(overrides.get("fg_color",
                                 ctx.draw_color("fg_color", exclude={0, 5})))
    n_palette = int(overrides.get("palette_size", 1))
    pool = [c for c in range(1, 10) if c not in (0, 5, fg_color)]
    rng.shuffle(pool)
    palette = [fg_color] + pool[:max(0, n_palette - 1)]
    five_layout = (overrides.get("texture") or overrides.get("five_layout")
                   or ctx.draw_choice("five_layout", list(FIVE_LAYOUTS)))
    fg_layout = overrides.get("fg_layout",
                              ctx.draw_choice("fg_layout", list(FG_LAYOUTS)))
    density = float(overrides.get("fg_density",
                                  ctx.draw_rng("fg_density")
                                  .uniform(0.3, 0.6)))
    g = full_grid(h, w, 0)
    five_cells = _layout_cells(five_layout, h, w, n_fives, rng)
    for r, c in five_cells:
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = 5
    if not any(g[r][c] == 5 for r in range(h) for c in range(w)):
        g[0][0] = 5
    _add_fg(g, fg_layout, h, w, palette, density, rng)
    if not any(g[r][c] not in (0, 5) for r in range(h) for c in range(w)):
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0:
                    g[r][c] = palette[0]
                    return g
    return g


def _layout_cells(layout, h, w, n, rng):
    if layout == "diagonal":
        return [(k, k) for k in range(min(h, w, n))]
    if layout == "row":
        r = rng.randint(0, h - 1)
        return [(r, c) for c in range(min(w, n))]
    if layout == "col":
        c = rng.randint(0, w - 1)
        return [(r, c) for r in range(min(h, n))]
    if layout == "corners":
        cs = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        return cs[:n]
    if layout == "center":
        cr, cc = h // 2, w // 2
        all_cells = [(r, c) for r in range(h) for c in range(w)]
        all_cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return all_cells[:n]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    return cells[:n]


def _add_fg(g, layout, h, w, palette, density, rng):
    if layout == "diagonal":
        for k in range(min(h, w)):
            r, c = k, w - 1 - k
            if g[r][c] == 0:
                g[r][c] = rng.choice(palette)
        return
    if layout == "blob":
        cr = rng.randint(0, h - 1)
        cc = rng.randint(0, w - 1)
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and abs(r - cr) + abs(c - cc) <= 2 \
                        and rng.random() < density:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "stripes":
        for r in range(h):
            color = rng.choice(palette)
            for c in range(w):
                if g[r][c] == 0 and rng.random() < density and r % 2 == 0:
                    g[r][c] = color
        return
    if layout == "checker":
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and (r + c) % 2 == 0:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "frame":
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and (r in (0, h - 1) or c in (0, w - 1)):
                    g[r][c] = rng.choice(palette)
        return
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 and rng.random() < density:
                g[r][c] = rng.choice(palette)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-5 cell; >=1 non-zero non-5 cell; grid 3-5 cells square."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    if not (3 <= h <= 5):
        errs.append(f"expected grid height in [3,5], got {h}")
    if not (3 <= w <= 5):
        errs.append(f"expected grid width in [3,5], got {w}")
    c5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    fg = any(grid[r][c] not in (0, 5) for r in range(h) for c in range(w))
    if not c5:
        errs.append("no color-5 cells (meta-tiling trigger)")
    if not fg:
        errs.append("no foreground (non-0, non-5) cells")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_fives":
        color = rng.choice([c for c in range(1, 10) if c != 5])
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.4:
                    g[r][c] = color
        return g
    if name == "all_fives":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    if name == "all_fg":
        color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        g[0][0] = 5
        return g
    return g
