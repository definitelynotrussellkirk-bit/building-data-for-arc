"""Generator for puzzle 2281f1f4.

Rule: row 0 holds template marker-cols. For each row r>0 with a non-bg
cell at any col NOT in template: paint 2 at every template col on row r.

Combinatorial axes (8): grid_h/w, dot_color, n_template_cols,
n_marker_rows, template_layout, marker_col, decoy_density,
asymmetry_force.
Degenerates: empty_template, full_template, no_marker_rows.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8985a4e38207"
VERSION = "2.0.1"
TASK_ID = "8985a4e38207"
SUMMARY = (
    "0-bg grid (h, w ∈ "
    "[4, 14]) with: (a) "
    "ROW-0 TEMPLATE — a "
    "set of TEMPLATE COLS "
    "(1..w/2 cells) painted "
    "DOT COLOR (any non-0 "
    "non-2 color) at row 0 "
    "using a chosen layout "
    "(scattered/left/right/"
    "even/endpoints/"
    "alternating); (b) "
    "MARKER ROWS — for "
    "1..h/2 ROWS r > 0, a "
    "MARKER cell of the "
    "same DOT COLOR is "
    "placed at a MARKER "
    "COL (chosen as last/"
    "first/random from "
    "cols NOT in the "
    "template). Rule "
    "(EXPAND MARKER ROWS "
    "AT TEMPLATE COLS WITH "
    "COLOR 2): identify the "
    "TEMPLATE COLS (non-0 "
    "cells in row 0) and "
    "the DOT COLOR. For "
    "EACH ROW r > 0: if r "
    "has ≥1 non-0 cell at "
    "any col NOT in the "
    "template (a marker), "
    "then PAINT every "
    "TEMPLATE COL of row r "
    "with COLOR 2 (red). "
    "Marker cells stay at "
    "dot color. Row 0 "
    "(template) stays. "
    "Rows without markers "
    "stay all-0. Net: each "
    "marker-row gets red "
    "dots at the template "
    "columns, marking the "
    "intersection."
)

INVARIANTS = [
    "background is 0",
    ">=1 non-bg cell in row 0 (template)",
    ">=1 row r>0 with a non-bg cell at a col NOT in template (marker)",
    "dot color != 2 (avoid conflict with rule output)",
    "marker col is NOT in template (so 'has-marker' check fires)",
]

TEMPLATE_LAYOUTS = ("scattered", "left_biased", "right_biased",
                    "even_spacing", "endpoints", "alternating")
DEGENERATE_TEXTURES = ("empty_template", "full_template", "no_marker_rows")
HELPFUL_TEXTURES = TEMPLATE_LAYOUTS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 4..14", "valid": "3..20"},
    "grid_w":            {"type": "int", "default": "rng 4..14", "valid": "3..20"},
    "dot_color":         {"type": "color", "default": "rng (≠0,2)",
                          "valid": "1..9 (≠2)"},
    "n_template_cols":   {"type": "int", "default": "rng 1..w/2",
                          "valid": "1..w-1"},
    "n_marker_rows":     {"type": "int", "default": "rng 1..h/2",
                          "valid": "1..h-1"},
    "template_layout":   {"type": "str", "default": "rng helpful",
                          "valid": "|".join(TEMPLATE_LAYOUTS)},
    "marker_col_choice": {"type": "str", "default": "rng last|first|random",
                          "valid": "last|first|random"},
    "asymmetry_force":   {"type": "bool", "default": "false", "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for template_layout",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: if row 0 has non-bg cells, their color is not 2 (rule output color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    template_vals = {grid[0][c] for c in range(w) if grid[0][c] != 0}
    if not template_vals:
        return []  # empty_template degenerate — allowed
    errs = []
    if 2 in template_vals:
        errs.append("dot color is 2 (same as rule output color — forbidden)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 5
    elif difficulty == "hard":
        h_lo, h_hi = 11, 18
    else:
        h_lo, h_hi = 4, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    dotc = int(overrides.get("dot_color",
                             ctx.draw_color("dotc", exclude={0, 2})))
    n_template = int(overrides.get("n_template_cols",
                                   ctx.draw_int("n_template_cols", 1,
                                                max(1, w // 2))))
    n_template = max(1, min(w - 2, n_template))
    n_marker_rows = int(overrides.get("n_marker_rows",
                                      ctx.draw_int("n_marker_rows", 1,
                                                   max(1, h // 2))))
    n_marker_rows = max(1, min(h - 1, n_marker_rows))
    layout = (overrides.get("texture") or overrides.get("template_layout")
              or ctx.draw_choice("template_layout",
                                 list(TEMPLATE_LAYOUTS)))
    marker_choice = overrides.get("marker_col_choice",
                                  ctx.draw_choice("marker_col_choice",
                                                  ["last", "first", "random"]))
    g = full_grid(h, w, 0)
    template_cols = _layout_template(layout, w, n_template, rng)
    template_set = set(template_cols)
    if marker_choice == "first":
        marker_col = next((c for c in range(w) if c not in template_set), w - 1)
    elif marker_choice == "random":
        non_template = [c for c in range(w) if c not in template_set]
        marker_col = rng.choice(non_template) if non_template else w - 1
    else:
        marker_col = next((c for c in range(w - 1, -1, -1)
                           if c not in template_set), w - 1)
    if marker_col in template_set:
        if w - 1 not in template_set:
            marker_col = w - 1
        else:
            marker_col = next(c for c in range(w) if c not in template_set)
    for c in template_cols:
        g[0][c] = dotc
    marker_rows = rng.sample(range(1, h), min(n_marker_rows, h - 1))
    for r in marker_rows:
        g[r][marker_col] = dotc
    return g


def _layout_template(layout, w, n, rng):
    available = list(range(w - 1))  # leave w-1 for marker_col by default
    if not available:
        return [0]
    if layout == "left_biased":
        return sorted(available[:n])
    if layout == "right_biased":
        return sorted(available[-n:])
    if layout == "even_spacing":
        step = max(1, len(available) // n)
        return sorted([available[i * step] for i in range(n) if i * step < len(available)])
    if layout == "endpoints":
        if n == 1:
            return [available[0]]
        return sorted([available[0], available[-1]] +
                      list(rng.sample(available[1:-1],
                                      max(0, min(n - 2, len(available) - 2)))))
    if layout == "alternating":
        cs = [c for c in available if c % 2 == 0]
        return sorted(cs[:n]) if cs else sorted(available[:n])
    rng.shuffle(available)
    return sorted(available[:n])


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    dotc = rng.choice([c for c in range(1, 10) if c != 2])
    if name == "empty_template":
        for r in range(1, h):
            g[r][w - 1] = dotc
        return g
    if name == "full_template":
        for c in range(w):
            g[0][c] = dotc
        for r in range(1, h):
            g[r][0] = dotc
        return g
    if name == "no_marker_rows":
        for c in range(min(3, w - 1)):
            g[0][c] = dotc
        return g
    return g
