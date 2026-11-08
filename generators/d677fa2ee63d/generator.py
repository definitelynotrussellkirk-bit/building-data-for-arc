"""Generator for arc_puzzle_bank_twentieth21:H140 — legend stamp expansion.

Rule (verified against canonical): the TOP 3 rows hold a LEGEND of 3 prototype panels
(split column-wise, separated by single columns). Each proto has a CENTER colour at
its local (1,1) plus a small same-colour SUPPORT pattern. An all-8 divider row
separates the legend from the BODY (rows 4+). The body holds single colour markers.
The rule stamps each body marker with its colour's proto support pattern (relative to
the marker). Output = the body region (rows 4+) with every marker expanded.

This generator builds that real structure: a 3-panel legend + 8-divider + a body of
colour markers drawn from the legend colours.

Combinatorial axes: panel width, proto support patterns, body marker count, colours.
Degenerates: no_legend, no_body, empty_protos.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d677fa2ee63d"
VERSION = "3.1.0"  # WRONG-TASK rewrite: docstring claimed 'gallery / vertical pack' but the canonical rule is a legend-stamp expansion (top 3-row legend of 3 proto shapes + 8-divider + body markers -> stamp each marker with its proto pattern). Old gen made scattered motifs -> near-constant output (distinct 12). Now builds the real legend+body.
TASK_ID = "d677fa2ee63d"

SUMMARY = (
    "TOP 3-row LEGEND of 3 proto panels (pw wide, separated by single cols): each "
    "proto has a CENTER colour at local (1,1) + a small same-colour support pattern. "
    "Row 3 is an all-8 divider. BODY (rows 4+) holds single colour markers from the "
    "legend colours. Rule: stamp each body marker with its colour's proto support "
    "pattern. Output = the body region with markers expanded."
)

INVARIANTS = [
    "top 3 rows hold a 3-panel legend (each proto: center colour + same-colour support)",
    "row 3 is an all-8 divider",
    "body (rows 4+) holds single-cell markers using the 3 legend colours",
    "output = body with each marker stamped by its proto's support pattern",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_body", "empty_protos")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_w":        {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "body_h":         {"type": "int", "default": "rng 4..7", "valid": "3..12"},
    "n_markers":      {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "legend_top_body_below",
                       "valid": "legend_top_body_below"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|no_body|empty_protos"},
}


def _proto_support(rng, pw):
    """Cells (within the 3 x pw panel) for a support pattern incl. center (1,1)."""
    cells = {(1, 1)}                       # center always present
    all_cells = [(r, c) for r in range(3) for c in range(pw) if (r, c) != (1, 1)]
    k = rng.randint(1, min(4, len(all_cells)))
    for rc in rng.sample(all_cells, k):
        cells.add(rc)
    return sorted(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        pw = ctx.draw_int("panel_w", 3, 3); body_h = ctx.draw_int("body_h", 4, 5)
        n_markers = ctx.draw_int("n_markers", 3, 4)
    elif difficulty == "hard":
        pw = ctx.draw_int("panel_w", 4, 5); body_h = ctx.draw_int("body_h", 7, 11)
        n_markers = ctx.draw_int("n_markers", 6, 10)
    else:
        pw = ctx.draw_int("panel_w", 3, 4); body_h = ctx.draw_int("body_h", 5, 8)
        n_markers = ctx.draw_int("n_markers", 4, 7)
    rng = ctx.draw_rng("layout")
    w = 3 * pw + 2                          # 3 panels + 2 single-col separators
    h = 4 + body_h                          # 3 legend rows + divider row + body
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    # Legend separators: canonical examples use color-8 columns between
    # the three prototype panels, plus the full divider row below.
    for r in range(3):
        for c in (pw, 2 * pw + 1):
            g[r][c] = 8
    # legend: 3 proto panels at cols [0..], rows 0..2
    for i, color in enumerate(colors):
        left = i * (pw + 1)
        for dr, dc in _proto_support(rng, pw):
            g[dr][left + dc] = color
    # divider row (row 3) all 8
    for c in range(w):
        g[3][c] = 8
    # body markers (rows 4+) using the legend colours
    body_cells = [(r, c) for r in range(4, h) for c in range(w)]
    rng.shuffle(body_cells)
    for (r, c) in body_cells[:min(n_markers, len(body_cells))]:
        g[r][c] = rng.choice(colors)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the legend-stamp input format.

    Color 8 is reserved for separators/divider; legend keys and body markers
    must use three distinct non-8 colors so prototype lookup is not visually
    aliased with the separator.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h < 5:
        errs.append(f"expected at least 5 rows (3 legend + divider + body); got {h}")
        return errs
    if not all(grid[3][c] == 8 for c in range(w)):
        errs.append("row 3 is not an all-8 divider")
    sep_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(3))]
    if len(sep_cols) != 2:
        errs.append(f"expected exactly two 3-row legend separator columns; found {sep_cols}")
    panel_w = (w - 2) // 3
    if 3 * panel_w + 2 != w or panel_w < 3:
        errs.append(f"grid width {w} does not match three panels plus two separators")
        return errs
    centers = []
    for i in range(3):
        left = i * (panel_w + 1)
        color = grid[1][left + 1]
        centers.append(color)
        if color in (0, 8):
            errs.append(f"legend panel {i} center/key color is {color}, expected nonzero non-8")
        support = [(r, c) for r in range(3) for c in range(left, left + panel_w)
                   if grid[r][c] != 0]
        if not support:
            errs.append(f"legend panel {i} has empty prototype")
        bad_support = sorted({grid[r][c] for r, c in support if grid[r][c] != color})
        if bad_support:
            errs.append(f"legend panel {i} support has colors other than its key {color}: {bad_support}")
    if len(set(centers)) != 3:
        errs.append(f"legend key colors are not distinct: {centers}")
    keys = set(centers) - {0, 8}
    body_vals = [grid[r][c] for r in range(4, h) for c in range(w) if grid[r][c] != 0]
    if not body_vals:
        errs.append("body has no markers to stamp")
    bad_body = sorted({v for v in body_vals if v not in keys})
    if bad_body:
        errs.append(f"body markers contain colors not in non-8 legend keys: {bad_body}")
    return errs


def _draw_from_degenerate(name, rng):
    pw = 3
    w = 3 * pw + 2
    g = full_grid(8, w, 0)
    if name == "no_legend":
        # body markers but no legend -> no proto to stamp
        for c in range(w):
            g[3][c] = 8
        g[5][2] = 4; g[6][6] = 6
        return g
    if name == "no_body":
        # legend only -> nothing to stamp
        g[1][1] = 4; g[0][1] = 4
        for c in range(w):
            g[3][c] = 8
        return g
    if name == "empty_protos":
        # divider + body but legend panels empty -> stamps are no-ops
        for c in range(w):
            g[3][c] = 8
        g[5][2] = 4
        return g
    return g
