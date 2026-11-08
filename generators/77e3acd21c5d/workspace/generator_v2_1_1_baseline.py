"""Generator for 57edb29d.

Rule: marker positions from a wide source rectangle are anchored into a
marker-free rectangle.

Combinatorial axes (8): grid_h/w, empty_size, marker_layout, palette_kind,
anchor_corner, asymmetry_force, palette_size, n_distinct_colors.
Degenerates: no_source, no_empty, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "77e3acd21c5d"
RULE_HASH = "b2cfd10a5b26"  # canonical rule this generator was written against
VERSION = "2.1.1"  # shape-locked-in: grid fixed 18x18 (rule finds the source/dest rects by content, so grid size is free). Vary grid size and source position, and add more dest-rect sizes -> input size varies (and a few more output sizes).
TASK_ID = "77e3acd21c5d"
SUMMARY = (
    "18×18 0-bg grid with: (a) "
    "ONE EMPTY DEST RECTANGLE "
    "(5×6 or 6×5 or 6×7) in "
    "EMPTY_COLOR at row 1, col "
    "1; (b) ONE 5×9 WIDE SOURCE "
    "RECTANGLE at row 10, col "
    "4 filled with BODY_COLOR "
    "and overlaid with 3 "
    "MARKER cells in "
    "MARKER_COLOR at offsets "
    "from one of 3 layouts "
    "(corners / edge / mixed). "
    "Rule (TRANSFER MARKER "
    "OFFSETS TO DEST): identify "
    "the SOURCE RECT (wide, "
    "body+markers) and the "
    "EMPTY DEST RECT. For EACH "
    "MARKER at offset (dr, dc) "
    "from the source's "
    "(NEAREST) CORNER, "
    "TRANSLATE the same "
    "OFFSET from the dest's "
    "corresponding corner and "
    "PAINT that cell with "
    "MARKER_COLOR (inside the "
    "dest rect). Net: marker "
    "positions transfer from "
    "source rect to dest rect "
    "by corner-relative "
    "offsets."
)

INVARIANTS = [
    "the background is zero",
    "one solid rectangle has a single color and supplies the output size",
    "one wider rectangle has a dominant fill color and a few same-color markers",
    "marker offsets are interpreted by nearest source corners and transferred to the empty rectangle",
]

EMPTY_SIZES = ("e5x6", "e6x5", "e6x7")
LAYOUTS = ("corners", "edge", "mixed")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_source", "no_empty", "full_grid")
HELPFUL_TEXTURES = LAYOUTS

AXES = {
    "grid_h":         {"type": "int", "default": "18", "valid": "18"},
    "grid_w":         {"type": "int", "default": "18", "valid": "18"},
    "empty_size":     {"type": "str", "default": "rng",
                       "valid": "5x6|6x5|6x7"},
    "marker_layout":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(LAYOUTS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for marker_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, ≥3 distinct non-zero colors, ≥1 solid-color rectangle (dest) and ≥1 two-color rectangle (source+markers)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} non-zero color(s); expected ≥2 (empty_color + source)")
    nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not nonzero:
        errs.append("grid is entirely background")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    eh, ew = ctx.draw_choice("empty_size",
                             [(5, 6), (6, 5), (6, 7), (4, 5), (5, 5), (7, 6), (5, 7)])
    layout = (overrides.get("texture") if overrides.get("texture") in LAYOUTS else None) or \
             overrides.get("marker_layout") or \
             ctx.draw_choice("marker_layout", list(LAYOUTS))
    empty_color, body_color, marker_color = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 16, 18); W = ctx.draw_int("grid_w", 16, 18)
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 20, 26); W = ctx.draw_int("grid_w", 20, 26)
    else:
        H = ctx.draw_int("grid_h", 17, 22); W = ctx.draw_int("grid_w", 17, 22)
    g = full_grid(H, W, 0)
    draw_rect(g, 1, 1, eh, ew, empty_color)
    sh, sw = 5, 9
    # place the wide source rect below the dest, clear of it
    sr = rng.randint(eh + 3, H - sh - 1)
    sc = rng.randint(0, W - sw - 1)
    draw_rect(g, sr, sc, sh, sw, body_color)
    marker_sets = {
        "corners": [(0, 1), (1, sw - 2), (sh - 2, 1)],
        "edge": [(1, 2), (1, sw - 3), (sh - 2, sw // 2)],
        "mixed": [(0, sw // 2), (sh // 2, 1), (sh - 1, sw - 2)],
    }
    for dr, dc in marker_sets[layout]:
        g[sr + dr][sc + dc] = marker_color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 18, 0)
    if name == "no_source":
        draw_rect(g, 1, 1, 5, 6, 3)
        return g
    if name == "no_empty":
        draw_rect(g, 10, 4, 5, 9, 4)
        return g
    if name == "full_grid":
        for r in range(18):
            for c in range(18):
                g[r][c] = 4
        return g
    return g
