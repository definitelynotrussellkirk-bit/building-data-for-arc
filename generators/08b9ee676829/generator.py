"""Generator for c92b942c.

Rule: 3x3 marker grid is tiled 3x3; rows containing markers get color
1 and diagonals adjacent to markers get color 3.

Combinatorial axes (8): size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, marker_count,
n_distinct_colors.
Degenerates: no_markers, all_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08b9ee676829"
VERSION = "2.1.1"  # match canonical one-color sparse-marker inputs; keep tiny-grid clamp + self_check
TASK_ID = "08b9ee676829"
SUMMARY = (
    "h x w marker grid tiled 3x3; marker rows fill with color 1; "
    "MAIN-DIAGONAL neighbors only ((r-1,c-1) and (r+1,c+1), computed "
    "in the tiled space so they cross tile boundaries) fill with "
    "color 3 — the anti-diagonal stays empty."
)

# Rivals: 'output same size as input' refuted by any demo (output is
# 3x per side). 'use marker color for diagonals' refuted by >=1 demo
# (diagonals are 3, not the marker's color). 'fill marker columns'
# refuted by >=2 demos (rule fills rows, not cols). 'BOTH diagonals
# get 3' refuted by every demo: the rule reuses dr for row AND col,
# so only the MAIN diagonal neighbors paint; anti-diagonal cells stay
# row-colored or 0. 4 demos with varied marker positions + sizes.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0",
    "input is an h x w grid (h, w independent, INCL. non-square) with >=1 nonzero marker",
    "all markers in one generated grid share one marker color, matching the canonical task convention",
    "marker colors exclude 0, 1, 3 (so the rule's row-1 / diagonal-3 fills are unambiguous)",
    "output is the 3x3-tiled board (3h x 3w), bounded to <=27 per side",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "all_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":       {"type": "int", "default": "rng 2..7", "valid": "2..9"},
    "grid_w":       {"type": "int", "default": "rng 2..7", "valid": "2..9"},
    "marker_count": {"type": "int", "default": "rng 1..3, capped by h*w-1",
                     "valid": "1..40"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "warm|cool|broad|primary"},
    "texture":      {"type": "str", "default": "alias for palette_kind",
                     "valid": "warm|cool|broad|primary|"
                              "no_markers|all_markers|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < 6:
        pool = pool + [c for c in [2, 4, 5, 6, 7, 8, 9] if c not in pool]
    # Vary input grid size INDEPENDENTLY per axis -- the canonical inputs
    # are NON-SQUARE (4x6, 2x4, 5x5, 3x3) and the 3x-tiling rule is fully
    # size-agnostic, so a square-only generator drops the rect axis the
    # task actually exercises. Output is 3x per side (cap each side at 9).
    if difficulty == "easy":
        gh = rng.randint(2, 4)
        gw = rng.randint(2, 4)
    elif difficulty == "hard":
        gh = rng.randint(4, 9)
        gw = rng.randint(4, 9)
    else:
        gh = rng.randint(2, 7)
        gw = rng.randint(2, 7)
    max_markers = max(1, gh * gw - 1)          # keep at least one background cell
    if "marker_count" in overrides:
        marker_count = max(1, min(int(overrides["marker_count"]), max_markers))
    else:
        marker_count = rng.randint(1, min(3, max_markers))
    g = full_grid(gh, gw, 0)
    marker_color = pool[0]
    # Place sparse markers at distinct positions.  Canonical inputs use one
    # marker color per grid; varying the color happens across episodes, not
    # inside a single generated grid.
    cells = [(r, c) for r in range(gh) for c in range(gw)]
    rng.shuffle(cells)
    for r, c in cells[:marker_count]:
        g[r][c] = marker_color
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 4, 6, 9]
    elif kind == "cool":
        pool = [5, 7, 8]
    elif kind == "primary":
        pool = [2, 4, 8]
    else:
        pool = [2, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 1, 3)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    """no_markers — blank: output is a blank 3hx3w grid. all_markers —
    every cell a marker: rows/diags fully shadowed. full_grid — one
    color everywhere: tiled copies only. rng-varied."""
    gh = rng.randint(2, 5)
    gw = rng.randint(2, 5)
    if name == "no_markers":
        return full_grid(gh, gw, 0)
    if name == "all_markers":
        pool = [c for c in range(2, 10) if c != 3]
        return [[rng.choice(pool) for _ in range(gw)] for _ in range(gh)]
    return full_grid(gh, gw, rng.choice([2, 4, 5, 6, 7, 8, 9]))

def self_check(grid, *, difficulty=None, meta=None):
    """Executable input-side invariants for generator_selfcheck.py.

    The canonical rule needs one or more nonzero markers whose colors do not
    collide with the rule's emitted row/diagonal colors (1 and 3).  Canonical
    inputs use one marker color per grid, so this also catches palette drift.
    """
    msgs = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid is not a nonempty list of rows"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        msgs.append("grid is ragged or has empty rows")
        return msgs
    h, w = len(grid), len(grid[0])
    if not (2 <= h <= 9 and 2 <= w <= 9):
        msgs.append(f"input dims out of contract: {h}x{w}")
    markers = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if len(markers) < 1:
        msgs.append("no markers")
    bad = sorted({v for _, _, v in markers if v in (1, 3) or not (0 <= v <= 9)})
    if bad:
        msgs.append(f"marker colors collide with output/reserved colors: {bad}")
    marker_colors = sorted({v for _, _, v in markers})
    if len(marker_colors) > 1:
        msgs.append(f"expected a single marker color per grid, got {marker_colors}")
    return msgs
