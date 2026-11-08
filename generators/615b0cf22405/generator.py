"""Generator for puzzle 615b0cf22405.

Rule: for each color, find pairs of same-color cells in row/col; fill
between them with that color.  Vertical fills override horizontal fills when
both apply, matching the canonical rule.

Combinatorial axes: grid_h/w, n_pairs, palette_kind, orientation, gap_min,
gap_max, anchor_corner, asymmetry_force.
Degenerates: no_pairs, all_same_position, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "615b0cf22405"
VERSION = "2.2.0"  # output quality: default instances now use eval-like area and 4-5 endpoint pairs
TASK_ID = "615b0cf22405"
SUMMARY = (
    "0-bg grid (default h~18-28, w~10-18) with "
    "4-5 SAME-COLOR PAIRS, each aligned either in ROW or in COLUMN, "
    "with gap_min..gap_max empty cells between them. Each pair uses a "
    "DISTINCT color drawn from one of {warm, cool, broad, primary} palettes "
    "(excluding 0). Rule (SAME-COLOR PAIR FILL BETWEEN): for EACH PAIR of "
    "SAME-COLOR cells aligned in a row or column, FILL all cells STRICTLY "
    "BETWEEN them in that color; vertical fills override horizontal fills if "
    "two inferred lines cross. The two endpoint cells stay. Net: sparse dots "
    "become several colored horizontal/vertical strokes."
)

INVARIANTS = [
    "background is 0",
    ">=3 distinct same-color endpoint pairs in the default path",
    "each endpoint pair is row- or column-aligned and >=3 cells apart",
]

ORIENTATIONS = ("row", "col", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pairs", "all_same_position", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 18..28", "valid": "4..30"},
    "grid_w":         {"type": "int", "default": "rng 10..18", "valid": "6..24"},
    "n_pairs":        {"type": "int", "default": "rng 4..5", "valid": "1..6"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "|".join(ORIENTATIONS)},
    "gap_min":        {"type": "int", "default": "3", "valid": "2..8"},
    "gap_max":        {"type": "int", "default": "rng 6..12",
                       "valid": "3..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 14, 20
        w_lo, w_hi = 10, 14
        pair_lo, pair_hi = 3, 4
    elif difficulty == "hard":
        h_lo, h_hi = 24, 30
        w_lo, w_hi = 14, 20
        pair_lo, pair_hi = 5, 6
    else:
        h_lo, h_hi = 18, 28
        w_lo, w_hi = 10, 18
        pair_lo, pair_hi = 4, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_pairs = int(overrides.get("n_pairs",
                                ctx.draw_int("n_pairs", pair_lo, pair_hi)))
    n_pairs = max(1, min(6, n_pairs))
    orientation = (overrides.get("texture") or
                   overrides.get("orientation")
                   or ctx.draw_choice("orientation", list(ORIENTATIONS)))
    gap_min = int(overrides.get("gap_min", 3))
    gap_max = int(overrides.get("gap_max",
                                ctx.draw_int("gap_max", 6, 12)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, n_pairs, rng)

    # Try whole boards until every intended color gets exactly one visible pair.
    # The old default was often only 1-2 pairs on a small board, so it looked much
    # unlike the canonical examples' multi-color dot field and under-taught
    # vertical-over-horizontal behavior.
    for _board_attempt in range(60):
        g = full_grid(h, w, 0)
        placed_colors = 0
        for color in palette[:n_pairs]:
            placed = False
            for _ in range(80):
                ori = orientation if orientation != "rng" else rng.choice(["row", "col"])
                if ori == "row":
                    if w < gap_min + 1:
                        continue
                    gap = rng.randint(gap_min, min(gap_max, w - 1))
                    r = rng.randint(0, h - 1)
                    c0 = rng.randint(0, w - gap - 1)
                    c1 = c0 + gap
                    if g[r][c0] == 0 and g[r][c1] == 0:
                        g[r][c0] = color
                        g[r][c1] = color
                        placed = True
                        break
                else:
                    if h < gap_min + 1:
                        continue
                    gap = rng.randint(gap_min, min(gap_max, h - 1))
                    c = rng.randint(0, w - 1)
                    r0 = rng.randint(0, h - gap - 1)
                    r1 = r0 + gap
                    if g[r0][c] == 0 and g[r1][c] == 0:
                        g[r0][c] = color
                        g[r1][c] = color
                        placed = True
                        break
            if not placed:
                break
            placed_colors += 1
        if placed_colors == n_pairs:
            return g

    # Guaranteed fallback: canonical-shaped sparse field with five pairs.
    g = full_grid(max(h, 20), max(w, 14), 0)
    coords = [
        (3, 2, 3, 10),
        (7, 1, 7, 8),
        (1, 5, 15, 5),
        (4, 11, 18, 11),
        (12, 3, 12, 13),
    ]
    for color, (r0, c0, r1, c1) in zip(_build_palette("broad", 5, rng), coords):
        g[r0][c0] = color
        g[r1][c1] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid is empty or not a 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    by_color = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    errs = []
    if len(by_color) < 3:
        errs.append(f"only {len(by_color)} endpoint colors; expected at least 3 in default instances")
    for color, pts in by_color.items():
        if len(pts) != 2:
            errs.append(f"color {color} has {len(pts)} cells; expected exactly 2 endpoints")
            continue
        (r1, c1), (r2, c2) = pts
        if r1 != r2 and c1 != c2:
            errs.append(f"color {color} endpoints are not row/column aligned")
            continue
        gap = abs(r1 - r2) + abs(c1 - c2)
        if gap < 3:
            errs.append(f"color {color} endpoint gap {gap} is too small")
    return errs


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Single cells, no pair.
        g[1][1] = 3
        g[h - 2][w - 2] = 4
        return g
    if name == "all_same_position":
        # 2 cells too close to each other.
        g[1][1] = 3
        g[1][2] = 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3 if (r + c) % 2 == 0 else 4
        return g
    return g
