"""Generator for 97239e3d -- snap scattered markers to a 4-lattice, draw frames.

Rule (block size 4): for each non-{0,8} color, snap every marker cell's row
and column to the nearest 4-lattice line (lo = floor/4*4, hi = min(lo+4,
edge); ties keep both), then form a bounding rect from the snapped extremes.
The output keeps the markers and, for each 0-cell, paints it with a color if
it lies on that color's rect border OR at a lattice center (r%4==2 and
c%4==2) inside the rect. Colors are tried in ascending order (first match
wins on overlap).

This generator scatters markers of a few colors so the snapped rects and
lattice-center dots are diverse.

Combinatorial axes: grid size, the colors, marker counts and positions.
Degenerates: no_markers, single_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "10b0b0da4c28"
VERSION = "3.0.1"  # +self_check
TASK_ID = "10b0b0da4c28"
SUMMARY = (
    "Period-4 8-LATTICE background: at each block offset (rows/cols 1..3 of "
    "every 4-cell block) a 3x3 hollow 8-box, with 0 gutters on the lines "
    "(r%4==0 / c%4==0) and a 0 center (r%4==2,c%4==2). Scattered markers in "
    "2-3 colors (not 0/8) sit on the 0 cells. Rule: snap each color's markers "
    "to the nearest 4-lattice lines, form a bounding rect, paint its border + "
    "lattice-center dots (r%4==2,c%4==2) in that color (only over 0-cells; the "
    "8-boxes are preserved); markers are kept. Grid size/colors/positions vary."
)

INVARIANTS = [
    "period-4 8-lattice background of 3x3 hollow 8-boxes (0 gutters + 0 centers)",
    "markers are non-{0,8} colors placed on the 0 gutter/center cells",
    "each color's markers snap to a 4-lattice bounding rect",
    "the output paints rect borders + lattice-center dots per color over 0-cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "single_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = [1, 2, 3, 4, 5, 6, 7, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..20"},
    "n_colors":       {"type": "int", "default": "varies", "valid": "2..3"},
    "markers_each":   {"type": "int", "default": "varies", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|single_marker|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    # blocks_r/c = number of 4-cell lattice blocks per axis; grid is 4*blocks+1.
    if difficulty == "easy":
        br_r, bc_r, ncr, mkr = (2, 3), (2, 3), (2, 2), (3, 5)
    elif difficulty == "hard":
        br_r, bc_r, ncr, mkr = (4, 6), (4, 6), (2, 3), (5, 7)
    else:
        br_r, bc_r, ncr, mkr = (3, 4), (3, 5), (2, 3), (4, 6)

    for _attempt in range(40):
        bh = rng.randint(*br_r); bw = rng.randint(*bc_r)
        h = 4 * bh + 1; w = 4 * bw + 1
        nc = rng.randint(*ncr)
        colors = rng.sample(_COLORS, nc)
        g = _draw_lattice(h, w)
        # 0-cells available for markers: gutter lines + box centers.
        slots = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        rng.shuffle(slots)
        used = set()
        placed = 0
        for color in colors:
            k = rng.randint(*mkr)
            for _ in range(k):
                for _t in range(20):
                    if not slots:
                        break
                    r, c = slots.pop()
                    if (r, c) not in used:
                        g[r][c] = color; used.add((r, c)); placed += 1; break
        if placed >= 2:
            return g

    return g   # fallback (rare)


def _draw_lattice(h, w):
    """Period-4 background: a 3x3 hollow 8-box in each block (offsets 1..3),
    with 0 gutter lines (r%4==0 / c%4==0) and a 0 center (r%4==2,c%4==2)."""
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if r % 4 == 0 or c % 4 == 0:
                continue                      # gutter line -> 0
            if r % 4 == 2 and c % 4 == 2:
                continue                      # box center -> 0 (hollow)
            g[r][c] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the period-4 hollow-8 lattice and marker placement on legal 0
    gutter/center cells.  The rule relies on the 8-box texture; a bare 0-bg or
    markers painted on 8 walls is poison even when parity still runs."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h % 4 != 1 or w % 4 != 1:
        errs.append(f"grid shape must be 4*k+1 by 4*k+1, got {h}x{w}")
    marker_counts = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            wall = (r % 4 != 0 and c % 4 != 0 and not (r % 4 == 2 and c % 4 == 2))
            if wall:
                if v != 8:
                    errs.append(f"lattice wall cell {(r, c)} should be 8, found {v}")
                    if len(errs) > 8:
                        return errs
            elif v not in (0, 8):
                if v not in _COLORS:
                    errs.append(f"illegal marker color {v} at {(r, c)}")
                marker_counts[v] = marker_counts.get(v, 0) + 1
            elif v == 8:
                errs.append(f"stray 8 outside hollow-box wall at {(r, c)}")
                if len(errs) > 8:
                    return errs
    if not (2 <= len(marker_counts) <= 3):
        errs.append(f"expected markers in 2-3 colors, found {sorted(marker_counts)}")
    for color, count in sorted(marker_counts.items()):
        if count < 3:
            errs.append(f"marker color {color} has only {count} cells; expected >=3")
    return errs


def _draw_from_degenerate(name):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_markers":
        return g
    if name == "single_marker":
        g[5][5] = 2
        return g
    if name == "full_grid":
        return full_grid(h, w, 2)
    return g
