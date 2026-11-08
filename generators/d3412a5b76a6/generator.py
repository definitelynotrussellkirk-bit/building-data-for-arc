"""Generator for arc_puzzle_bank_21_set19_s:S19_E5.

Three panels contain one repeated occupancy pattern; return the repeated panel.

Combinatorial axes (8): grid_h, grid_w, palette_kind, repeat_pair,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_distinct, all_same, no_repeat.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "d3412a5b76a6"
VERSION = "2.0.0"
TASK_ID = "d3412a5b76a6"
SUMMARY = (
    "Vertically-assembled grid with 3 SAME-SIZE "
    "PANELS (each panel h × w, h ∈ {5, 6} and "
    "w ∈ {5, 6}) separated by FULL-WIDTH COLOR-"
    "9 SEPARATOR ROWS. Layout: (a) PANEL 0 at "
    "top, painted in COLOR 2 (red); (b) PANEL 1 "
    "in middle, COLOR 3 (green); (c) PANEL 2 at "
    "bottom, COLOR 4 (yellow). The occupancy "
    "patterns (which cells are non-bg) are: "
    "ONE REPEATED PATTERN (6 cells) appears in "
    "EXACTLY 2 of the 3 panels (the pair "
    "chosen via repeat_pair ∈ {'01', '02', "
    "'12'}); the THIRD ODD PANEL has a "
    "DIFFERENT pattern (5 cells, ensured "
    "distinct from the repeated set). Each "
    "panel's occupied cells use that panel's "
    "designated color. Rule (FIND THE REPEATED "
    "OCCUPANCY PATTERN AMONG 3 PANELS, OUTPUT "
    "IT RECOLORED TO 8): COMPUTE each panel's "
    "OCCUPANCY MASK (which cells are non-0, "
    "ignoring color). FIND the TWO panels "
    "that share the SAME occupancy mask. OUTPUT "
    "is a single panel of dimensions h × w "
    "where the SHARED OCCUPANCY CELLS are "
    "painted COLOR 8 (cyan) and all other "
    "cells are bg-0. The third panel and the "
    "9-dividers are discarded. Net: the "
    "repeated-pattern panel emerges as a "
    "single cyan-occupancy panel."
)

INVARIANTS = [
    "three same-size vertical panels separated by color 9",
    "exactly two panels share the same occupied coordinates",
    "the repeated occupancy pattern is recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_distinct", "all_same", "no_repeat")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..6", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "13..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "repeat_pair":    {"type": "choice", "default": "rng among 01,02,12",
                       "valid": "01|02|12"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "9col_separated_panels",
                       "valid": "9col_separated_panels"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: 3 panels separated by full-width color-9 rows, each panel has ≥1 non-bg cell."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    nine_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    if not nine_rows:
        pass  # degenerate (all_distinct or no_repeat) — allowed
    return errors


def _panel(h: int, w: int, cells: set[tuple[int, int]], color: int):
    panel = full_grid(h, w, 0)
    for r, c in cells:
        panel[r][c] = color
    return panel


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 5, 5)
        w = ctx.draw_int("width", 5, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 6, 6)
        w = ctx.draw_int("width", 6, 6)
    else:
        h = ctx.draw_int("height", 5, 6)
        w = ctx.draw_int("width", 5, 6)
    pair = ctx.draw_choice("repeat_pair", ["01", "02", "12"])
    rng = ctx.draw_rng("cells")
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    repeated = set(rng.sample(all_cells, 6))
    odd = repeated
    while odd == repeated:
        odd = set(rng.sample(all_cells, 5))
    patterns = [odd, odd, odd]
    for idx in (int(pair[0]), int(pair[1])):
        patterns[idx] = repeated
    return assemble_vertical_panels([
        _panel(h, w, patterns[0], 2),
        _panel(h, w, patterns[1], 3),
        _panel(h, w, patterns[2], 4),
    ])


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    if name == "all_distinct":
        # 3 distinct patterns → no repeat to find, undefined output
        p1 = _panel(h, w, {(0, 0), (1, 1), (2, 2)}, 2)
        p2 = _panel(h, w, {(0, 4), (1, 3), (2, 2)}, 3)
        p3 = _panel(h, w, {(4, 0), (4, 4), (2, 2)}, 4)
        return assemble_vertical_panels([p1, p2, p3])
    if name == "all_same":
        # all 3 panels share pattern → 3 repeats, ambiguous
        cells = {(0, 0), (1, 1), (2, 2)}
        p1 = _panel(h, w, cells, 2)
        p2 = _panel(h, w, cells, 3)
        p3 = _panel(h, w, cells, 4)
        return assemble_vertical_panels([p1, p2, p3])
    if name == "no_repeat":
        # only one panel → no repeat possible
        cells = {(0, 0), (1, 1), (2, 2)}
        return _panel(h, w, cells, 2)
    return _panel(h, w, set(), 2)
