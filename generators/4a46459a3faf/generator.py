"""Generator for dce56571.

Rule: bg=8. Single non-8 color C with count cells. Output is 8-bg
grid with horizontal C-bar centered at middle row, length=count.

Combinatorial axes (8): grid_h/w, color, count, cell_layout,
position_bias, palette_size, decoy_density, asymmetry.
Degenerates: no_color, full_color, count_too_large.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a46459a3faf"
VERSION = "2.1.0"
TASK_ID = "4a46459a3faf"
SUMMARY = (
    "COLOR-8 (cyan) bg grid "
    "(h~6-12, w~11-18) with a "
    "SINGLE non-8 COLOR C at "
    "'count' scattered cells "
    "(count ≥ 2, ≤ w). "
    "Cell placement uses one "
    "of 8 LAYOUTS (scattered/"
    "blob/diagonal/row/col/"
    "checker/frame/corners) "
    "with position_bias "
    "(spread/center/edge). "
    "Rule (CENTER 'count'-"
    "LENGTH HORIZONTAL BAR "
    "ON BG=8): identify the "
    "SINGLE NON-8 COLOR C "
    "and COUNT = total cells "
    "of C. EMIT a FRESH h×w "
    "GRID filled with 8. "
    "PAINT a HORIZONTAL BAR "
    "of LENGTH 'count' in "
    "color C CENTERED at "
    "the MIDDLE ROW (h//2), "
    "starting at col "
    "(w - count)//2. Net: "
    "scattered count of C "
    "cells reduces to a "
    "centered horizontal bar "
    "of length count in "
    "color C."
)

INVARIANTS = [
    "background is 8 (rule's bg)",
    ">=2 cells of single non-8 color (count = bar length)",
    "count <= w (bar fits horizontally)",
    "exactly one non-8 color in input (rule's find-first picks unambiguously)",
]

CELL_LAYOUTS = ("scattered", "blob", "diagonal", "row", "col",
                "checker", "frame", "corners")
DEGENERATE_TEXTURES = ("no_color", "full_color", "count_too_large")
HELPFUL_TEXTURES = CELL_LAYOUTS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 11..18", "valid": "9..22"},
    "color":          {"type": "color", "default": "rng (≠8)", "valid": "1..9 (≠8)"},
    "count":          {"type": "int", "default": "rng 2..w", "valid": "1..w"},
    "cell_layout":    {"type": "str", "default": "rng helpful",
                       "valid": "compact|spread|diagonal|mixed"},
    "position_bias":  {"type": "str", "default": "rng spread|center|edge",
                       "valid": "spread|center|edge"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "asymmetry":      {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for cell_layout",
                       "valid": "compact|spread|diagonal|mixed|no_color|full_color|count_too_large"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 7, 9, 12
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 16, 16, 22
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 12, 11, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    color = int(overrides.get("color",
                              rng.choice([1, 2, 3, 4, 5, 6, 7, 9])))
    max_count = w
    count = int(overrides.get("count",
                              ctx.draw_int("count", 2, max(2, max_count))))
    count = max(2, min(max_count, count))
    layout = (overrides.get("texture") or overrides.get("cell_layout")
              or ctx.draw_choice("cell_layout", list(CELL_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "center", "edge"]))
    g = full_grid(h, w, 8)
    cells = _layout_cells(layout, h, w, bias, rng)
    for r, c in cells[:count]:
        g[r][c] = color
    return _avoid_identity(g, color, count, rng)


def _target_grid(h, w, color, count):
    out = full_grid(h, w, 8)
    center_r = h // 2
    start = (w - count) // 2
    for c in range(start, start + count):
        out[center_r][c] = color
    return out


def _avoid_identity(g, color, count, rng):
    """Keep the same color-count but avoid input==canonical output demos."""
    h = len(g); w = len(g[0]) if h else 0
    if g != _target_grid(h, w, color, count):
        return g
    center_r = h // 2
    start = (w - count) // 2
    bar = {(center_r, c) for c in range(start, start + count)}
    # Move one painted cell out of the target bar while preserving count.
    src = (center_r, start)
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if (r, c) not in bar]
    rng.shuffle(candidates)
    if candidates:
        dst = candidates[0]
        g[src[0]][src[1]] = 8
        g[dst[0]][dst[1]] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=8, exactly one non-8 color, count>=2, fits, not identity."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    # Count colors
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w))
    non_bg = {c: n for c, n in counts.items() if c != 8}
    if len(non_bg) == 0:
        # degenerate (no_color) — skip
        return errors
    if len(non_bg) > 1:
        errors.append(f"expected 1 non-8 color, found {len(non_bg)}: {list(non_bg)}")
    if non_bg:
        color, count = next(iter(non_bg.items()))
        if count < 2:
            errors.append(f"count={count} < 2 (bar length must be >= 2)")
        if count > w:
            errors.append(f"count={count} > w={w} (bar would overflow)")
        if grid == _target_grid(h, w, color, count):
            errors.append("input already equals the centered count-bar output")
    return errors


def _layout_cells(layout, h, w, bias, rng):
    cells = [(r, c) for r in range(h) for c in range(w)]
    if layout == "blob":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells
    if layout == "diagonal":
        diag = [(k, k) for k in range(min(h, w))]
        rest = [c for c in cells if c not in diag]
        rng.shuffle(rest)
        return diag + rest
    if layout == "row":
        r = rng.randint(0, h - 1)
        chosen = [(r, c) for c in range(w)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "col":
        c = rng.randint(0, w - 1)
        chosen = [(r, c) for r in range(h)]
        rest = [cc for cc in cells if cc not in chosen]
        rng.shuffle(rest)
        return chosen + rest
    if layout == "corners":
        corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        rest = [c for c in cells if c not in corners]
        rng.shuffle(rest)
        return corners + rest
    if layout == "checker":
        even = [(r, c) for (r, c) in cells if (r + c) % 2 == 0]
        odd = [(r, c) for (r, c) in cells if (r + c) % 2 != 0]
        rng.shuffle(even); rng.shuffle(odd)
        return even + odd
    if layout == "frame":
        border = [(r, c) for (r, c) in cells
                  if r in (0, h - 1) or c in (0, w - 1)]
        interior = [(r, c) for (r, c) in cells if (r, c) not in border]
        rng.shuffle(border); rng.shuffle(interior)
        return border + interior
    rng.shuffle(cells)
    return cells


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 8)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    if name == "no_color":
        return g
    if name == "full_color":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "count_too_large":
        # count > w (bar would overflow)
        for c in range(w):
            g[0][c] = color
        g[1][0] = color
        return g
    return g
