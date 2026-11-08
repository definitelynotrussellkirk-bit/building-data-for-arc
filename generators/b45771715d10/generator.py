"""Generator for arc_additional_puzzles_21_set22_bundle:H154.

Rule: the first two nonzero codes in row 0 transform the cropped motif
below the header.

Combinatorial axes (8): grid_h/w, palette_kind, code1, code2,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_codes, no_motif, codes_invalid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b45771715d10"
VERSION = "2.0.1"  # FIXED-MOTIF poison fix: every instance used the same 5-cell
# MOTIF, so output was just its ~8 dihedral orientations (distinct_out=8). Rule
# transforms whatever motif sits below row 0, so motif IS the content. v2 grows
# a random multi-color polyomino motif (varied shape, size, colors).
TASK_ID = "b45771715d10"
SUMMARY = "The first two nonzero top-row codes transform the cropped motif below the header."

INVARIANTS = [
    "top row contains exactly two leading transform codes",
    "motif lies below row 0 and has a non-square bounding box",
]

PALETTE_KINDS = ("default", "warm_codes", "cool_codes", "rainbow")
DEGENERATE_TEXTURES = ("no_codes", "no_motif", "codes_invalid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm_codes|cool_codes|rainbow"},
    "code1":          {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "code2":          {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "below_header",
                       "valid": "below_header"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm_codes|cool_codes|rainbow|no_codes|no_motif|codes_invalid"},
}


def _motif(rng, k, max_dim):
    """Random 4-conn polyomino (k cells, <= max_dim each side), each cell a
    random non-0 color. Returns list of (r, c, color) normalized to (0,0)."""
    cells = [(0, 0)]
    seen = {(0, 0)}
    tries = 0
    while len(cells) < k and tries < 120:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) in seen:
            continue
        cand = cells + [(nr, nc)]
        rs = [x for x, _ in cand]
        cs = [y for _, y in cand]
        if (max(rs) - min(rs) + 1 > max_dim) or (max(cs) - min(cs) + 1 > max_dim):
            continue
        cells.append((nr, nc))
        seen.add((nr, nc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    # color each cell; use 2-4 distinct colors so transforms are observable
    n_col = rng.randint(2, 4)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_col)
    return [(r - mr, c - mc, rng.choice(palette)) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = rng.randint(1, 6)
    g[0][1] = rng.randint(1, 6)
    max_dim = min(h - 2, w - 1, 5)
    for _ in range(80):
        motif = _motif(rng, rng.randint(3, 6), max(2, max_dim))
        mh = max(r for r, _, _ in motif) + 1
        mw = max(c for _, c, _ in motif) + 1
        if mh != mw:
            break
    else:
        # Non-square fallback keeps rotations/reflections visually identifiable.
        motif = [(0, 0, 3), (0, 1, 4), (0, 2, 5), (1, 0, 6)]
        mh, mw = 2, 3
    top = rng.randint(1, max(1, h - mh))
    left = rng.randint(0, max(0, w - mw))
    for dr, dc, color in motif:
        g[top + dr][left + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    _fixed = ((0, 0, 3), (0, 1, 3), (1, 1, 4), (2, 1, 4), (2, 2, 5))
    if name == "no_codes":
        # motif but no transform codes in row 0
        for dr, dc, color in _fixed:
            g[3 + dr][2 + dc] = color
        return g
    if name == "no_motif":
        # codes but no motif below — rule has nothing to transform
        g[0][0] = 2
        g[0][1] = 5
        return g
    if name == "codes_invalid":
        # codes outside {1..6} — rule cannot map them to a transform
        g[0][0] = 8
        g[0][1] = 9
        for dr, dc, color in _fixed:
            g[3 + dr][2 + dc] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (1 <= grid[0][0] <= 6 and 1 <= grid[0][1] <= 6):
        errors.append("top row must start with two transform codes in 1..6")
    if any(v != 0 for v in grid[0][2:]):
        errors.append("top row must contain exactly two leading non-zero codes")
    cells = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        errors.append("motif below the header is missing")
    else:
        mh = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        mw = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if mh == mw:
            errors.append(f"motif bbox must be non-square, got {mh}x{mw}")
    return errors

