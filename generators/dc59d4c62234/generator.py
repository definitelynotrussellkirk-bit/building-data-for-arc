"""Generator for 458e3a53.

Rule: between full-row separators, solid square blocks are extracted
as rows of their colors.

Combinatorial axes (8): band_size, square_count, sep_color,
palette_kind, anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_separators, no_squares, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc59d4c62234"
VERSION = "2.1.2"  # cap bands/square_count to the 30x30 ARC box (medium was 31 tall on every draw)
TASK_ID = "dc59d4c62234"
SUMMARY = (
    "Grid with FULL-ROW SEPARATORS in some uniform "
    "non-bg color, partitioning the canvas into "
    "horizontal BANDS of equal height N. The border "
    "rows (top and bottom) are also separator-colored. "
    "Each band's height equals the SQUARE BLOCK SIZE N "
    "for that band. Inside each band, 2 SOLID N×N "
    "SQUARES are placed in two distinct colors against "
    "a noisy filler of other colors (any color except "
    "the separator color and the square colors). Rule: "
    "scan band-by-band top-to-bottom. For each band, "
    "DETECT the K solid N×N SQUARES inside (each in a "
    "distinct color) in left-to-right order. EMIT a "
    "1-row sequence of those K square-colors. Output: "
    "BANDS rows × K cols, one cell per square's color. "
    "Net: the separator-bound bands get reduced to a "
    "compact (bands × K) lookup table of solid-square "
    "colors."
)

INVARIANTS = [
    "full uniform rows separate horizontal bands",
    "each band height defines the square size for that band",
    "every band contains the same number of solid square blocks",
    "the output is the per-band list of solid-square colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_separators", "no_squares", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "band_size":      {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "square_count":   {"type": "int", "default": "2", "valid": "1..6"},
    "sep_color":      {"type": "color", "default": "rng !0",
                       "valid": "1..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "fixed",
                       "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # Output dims = bands x squares_per_band; both were FIXED at 2 -> out_shapes 1.
    # Vary both so the output matrix size varies.
    if difficulty == "easy":
        bs_lo, bs_hi = 5, 5
        bands = ctx.draw_int("bands", 4, 4); square_count = ctx.draw_int("square_count", 2, 3)
    elif difficulty == "hard":
        bs_lo, bs_hi = 5, 6
        bands = ctx.draw_int("bands", 4, 5); square_count = ctx.draw_int("square_count", 3, 4)
    else:
        bs_lo, bs_hi = 5, 5
        bands = ctx.draw_int("bands", 5, 5); square_count = ctx.draw_int("square_count", 3, 3)
    n = ctx.draw_int("band_size", bs_lo, bs_hi)
    sep_color = ctx.draw_color("separator", exclude={0})
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, 9, sep_color, rng)
    gap = 3                                   # filler gap between squares
    # ARC cap (30x30): h = 1 + bands*(n+1), w = 1 + (sc-1)*(n+gap) + n + 1.
    # medium's bands=5, n=5 gave h=31 on EVERY draw (validity-sweep find) —
    # shrink the counts, never the declared draws.
    bands = max(2, min(bands, (30 - 1) // (n + 1)))
    while square_count > 1 and 1 + (square_count - 1) * (n + gap) + n + 1 > 30:
        square_count -= 1
    # cycle the palette so every (band, square) slot gets a color
    colors = [pool[i % len(pool)] for i in range(bands * square_count)]
    square_cols = [1 + i * (n + gap) for i in range(square_count)]
    w = square_cols[-1] + n + 1
    h = 1 + bands * (n + 1)
    g = full_grid(h, w, sep_color)
    starts = [1 + i * (n + 1) for i in range(bands)]
    filler = [c for c in range(10) if c != sep_color]
    for bi, r0 in enumerate(starts):
        for r in range(n):
            for c in range(w):
                g[r0 + r][c] = filler[(r * 2 + c * 3 + bi) % len(filler)]
        for si, c0 in enumerate(square_cols):
            color = colors[bi * square_count + si]
            for r in range(n):
                for c in range(n):
                    g[r0 + r][c0 + c] = color
    return g


def _build_palette(kind, n, exclude_color, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != exclude_color]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool and c != exclude_color:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 5)
    if name == "no_separators":
        for r in range(h):
            for c in range(w):
                g[r][c] = (r + c) % 4 + 1
        return g
    if name == "no_squares":
        for r in range(1, 4):
            for c in range(w):
                g[r][c] = (r + c) % 3 + 1
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Full uniform rows act as horizontal band separators."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    has_sep = any(len(set(grid[r])) == 1 and grid[r][0] != 0 for r in range(h))
    if not has_sep:
        errs.append("no full uniform nonzero row found (band separator missing)")
    return errs
