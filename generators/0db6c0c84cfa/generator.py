"""Generator for arc_puzzle_bank_seventeenth_21_bundle:easy_116_fill_diagonal_segments.

Rule: each color appearing twice as endpoints of a 45-degree diagonal
fills the diagonal between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, segments, texture.
Degenerates: no_pairs, axis_aligned, single_endpoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0db6c0c84cfa"
VERSION = "1.3.0"  # retry until requested diagonal segment count is realized; add self_check
TASK_ID = "0db6c0c84cfa"

SUMMARY = "Color pairs mark endpoints of separated diagonal segments."

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "endpoints lie on a 45-degree diagonal",
    "intervening diagonal cells are initially blank",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "axis_aligned", "single_endpoint")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "segments":       {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "= segments", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_diagonals",
                       "valid": "scattered_diagonals"},
    "n_distinct_colors": {"type": "int", "default": "= segments", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|axis_aligned|single_endpoint"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("segments", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        target = ctx.draw_int("segments", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 8, 14)
        target = ctx.draw_int("segments", 1, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    max_span = min(4 if target >= 4 else 6, h - 1, w - 1)

    def guard_for(pts):
        # Disallow actual overlap so each color still has exactly two endpoints
        # and blank interior cells. A full one-cell moat made 4-6 hard segments
        # impossible in some valid 13x13 canvases.
        return set(pts)

    candidates = []
    for span in range(2, max_span + 1):
        for r in range(0, h - span):
            for c0 in range(0, w - span):
                pts = [(r + d, c0 + d) for d in range(span + 1)]
                candidates.append((pts, guard_for(pts)))
                c1 = c0 + span
                pts = [(r + d, c1 - d) for d in range(span + 1)]
                candidates.append((pts, guard_for(pts)))
    rng.shuffle(candidates)

    for color in colors[:target]:
        chosen = None
        for pts, guard in candidates:
            if not (guard & reserved):
                chosen = (pts, guard)
                break
        if chosen is None:
            raise ValueError("could not realize requested separated diagonal segments")
        pts, guard = chosen
        g[pts[0][0]][pts[0][1]] = color
        g[pts[-1][0]][pts[-1][1]] = color
        reserved.update(guard)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no diagonal pairs to fill.
        return g
    if name == "axis_aligned":
        # Same color twice on row or column rather than a diagonal —
        # rule's 45-degree filter excludes them.
        g[3][2] = 4; g[3][7] = 4
        g[2][6] = 6; g[6][6] = 6
        return g
    if name == "single_endpoint":
        # Color appears once — rule's "exactly two endpoints"
        # filter excludes it.
        g[2][2] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from collections import defaultdict
    errors = []
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color[v].append((r, c))
    valid = 0
    for color, pts in by_color.items():
        if len(pts) != 2:
            errors.append(f"color {color} appears {len(pts)} times instead of twice")
            continue
        (r1, c1), (r2, c2) = pts
        if abs(r1 - r2) != abs(c1 - c2) or abs(r1 - r2) < 2:
            errors.append(f"color {color} endpoints are not a length>=2 diagonal")
            continue
        dr = 1 if r2 > r1 else -1
        dc = 1 if c2 > c1 else -1
        if any(grid[r1 + k * dr][c1 + k * dc] != 0 for k in range(1, abs(r2 - r1))):
            errors.append(f"color {color} diagonal interior is not blank")
            continue
        valid += 1
    min_valid = {"easy": 1, "hard": 4}.get(difficulty, 1)
    if valid < min_valid:
        errors.append(f"expected at least {min_valid} valid diagonal segments, found {valid}")
    return errors
